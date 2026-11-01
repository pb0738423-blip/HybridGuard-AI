# HybridGuard AI — Troubleshooting & Operations Guide

## 1. Common Installation & Runtime Issues

### Issue 1: Model artifacts missing (`503 Service Unavailable`)
- **Symptom**: Calling `/api/predict` returns `Model artifacts not yet trained or loaded`.
- **Cause**: The models have not been trained yet, or `models/artifacts/` is empty.
- **Resolution**:
  Run the offline training script:
  ```powershell
  python -m src.ml.train --subsample 25000 --cv 5
  ```
  This trains all 3 baseline classifiers and the stacking ensemble, evaluates on the held-out test split, and writes serialized `.joblib` artifacts to `models/artifacts/`.

### Issue 2: YouTube Captions Disabled (`422 Unprocessable Entity`)
- **Symptom**: Calling `/api/video/analyze` returns `"Transcript unavailable: Captions may be disabled, private, or non-English"`.
- **Cause**: Some YouTube video creators explicitly disable closed captions or automatic transcripts.
- **Resolution**:
  Use the **Manual Transcript Fallback**:
  1. Expand the "Manual Transcript Fallback" accordion in the UI.
  2. Paste the spoken transcript with timestamps (e.g., `[00:15] Claim text here...`) or plain text.
  3. Click "Analyze Video". The system will process the manual transcript directly.

### Issue 3: Port Collision (`Address already in use`)
- **Symptom**: Uvicorn fails to start with `[Errno 10048] error while attempting to bind on address ('0.0.0.0', 8000)`.
- **Resolution**:
  Find the process occupying port 8000:
  ```powershell
  Get-NetTCPConnection -LocalPort 8000 | Select-Object OwningProcess
  Stop-Process -Id <PID>
  ```
  Or change the port: `uvicorn src.api.app:app --host 0.0.0.0 --port 8080`.

### Issue 4: Frontend Development Proxy vs Production Serving
- **Development Mode**:
  Run backend (`uvicorn src.api.app:app --reload`) on port 8000 and frontend (`npm run dev`) on port 5173. Vite automatically proxies `/api` and `/health` to port 8000.
- **Production Mode**:
  Build the frontend with `npm run build` in `frontend/`. FastAPI automatically serves the static bundle from `frontend/dist/` at `http://127.0.0.1:8000/`.

---

## 2. Fact-Checking External Provider Troubleshooting

### Wikipedia API Rate Limiting or Timeouts
- **Symptom**: Fact-check requests return `Insufficient Evidence` on common topics.
- **Cause**: MediaWiki API requires an identifiable `User-Agent` header as per Wikimedia Foundation policy.
- **Resolution**:
  Ensure `.env` contains:
  ```env
  USER_AGENT=HybridGuardAI/1.0 (academic-research-fact-check; contact@hybridguard.ai)
  ```
  The system automatically falls back to DuckDuckGo if Wikipedia fails.

