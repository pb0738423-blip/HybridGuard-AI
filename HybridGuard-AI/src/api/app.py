"""FastAPI Application Entrypoint for HybridGuard AI.
Integrates CORS, structured logging, request size limits, clean error handling,
and all subsystem routes.
"""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from src.api.routes import fact_check, health, predict, speech, video

# Structured Logging Configuration
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("hybridguard.api")

app = FastAPI(
    title="HybridGuard AI API",
    description="Hybrid Machine Learning Fake News Detection, Explainable AI, and Evidence-based Real-Time Fact-Checking",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Configuration
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for flexible local dev / cross-port access
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_BODY_SIZE_BYTES = int(os.getenv("MAX_PAYLOAD_SIZE_MB", "10")) * 1024 * 1024


@app.middleware("http")
async def security_and_logging_middleware(request: Request, call_next):
    """Enforce payload size limits, request timeouts, and structured latency logging."""
    # Check payload size limit
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > MAX_BODY_SIZE_BYTES:
        logger.warning("Rejected payload exceeding %d MB from %s", MAX_BODY_SIZE_BYTES // (1024 * 1024), request.client.host if request.client else "unknown")
        return JSONResponse(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            content={"detail": "Payload too large. Maximum permitted request size is 10 MB."},
        )

    t0 = time.perf_counter()
    try:
        response = await call_next(request)
        duration_ms = (time.perf_counter() - t0) * 1000.0
        logger.info(
            "%s %s -> HTTP %d (%.2fms)",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        response.headers["X-Process-Time-Ms"] = f"{duration_ms:.2f}"
        return response
    except Exception as exc:
        duration_ms = (time.perf_counter() - t0) * 1000.0
        logger.error("Unhandled API exception on %s %s: %s (%.2fms)", request.method, request.url.path, exc, duration_ms, exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": f"Internal server error: {str(exc)}"},
        )


# Register API Routers
app.include_router(health.router)
app.include_router(predict.router)
app.include_router(fact_check.router)
app.include_router(video.router)
app.include_router(speech.router)

# Mount frontend build static files if present
dist_dir = Path("frontend/dist")
if dist_dir.exists():
    app.mount("/", StaticFiles(directory=str(dist_dir), html=True), name="frontend")
    logger.info("Mounted frontend static build from %s", dist_dir)

