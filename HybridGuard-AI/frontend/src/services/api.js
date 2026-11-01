/**
 * API Client for HybridGuard AI
 * Connects React frontend directly to FastAPI backend endpoints.
 */

const API_BASE = '/api';

async function handleResponse(res) {
  if (!res.ok) {
    let errorDetail = `HTTP ${res.status}`;
    try {
      const errJson = await res.json();
      if (errJson.detail) {
        if (typeof errJson.detail === 'string') {
          errorDetail = errJson.detail;
        } else if (errJson.detail.message) {
          errorDetail = errJson.detail.message;
        } else {
          errorDetail = JSON.stringify(errJson.detail);
        }
      }
    } catch (e) {
      // use status text
      errorDetail = res.statusText || errorDetail;
    }
    throw new Error(errorDetail);
  }
  return res.json();
}

export const api = {
  // System Health
  async getHealth() {
    const res = await fetch('/health');
    return handleResponse(res);
  },

  // Model Metadata & Saved Metrics
  async getModelInfo() {
    const res = await fetch(`${API_BASE}/model-info`);
    return handleResponse(res);
  },

  async getMetrics() {
    const res = await fetch(`${API_BASE}/metrics`);
    return handleResponse(res);
  },

  // Fake News ML Prediction
  async predictNews(text, explain = true, topNWords = 10) {
    const res = await fetch(`${API_BASE}/predict`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text,
        explain,
        top_n_words: topNWords,
      }),
    });
    return handleResponse(res);
  },

  // Fact Checking & Claim Extraction
  async verifyClaim(claim, maxResults = 4) {
    const res = await fetch(`${API_BASE}/fact-check`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        claim,
        max_evidence_results: maxResults,
      }),
    });
    return handleResponse(res);
  },

  async extractClaims(text, maxClaims = 8) {
    const res = await fetch(`${API_BASE}/claims/extract`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text,
        max_claims: maxClaims,
      }),
    });
    return handleResponse(res);
  },

  async verifyArticleClaims(text, maxClaims = 5) {
    const res = await fetch(`${API_BASE}/fact-check/article`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text,
        max_claims: maxClaims,
      }),
    });
    return handleResponse(res);
  },

  // YouTube Video & Shorts Analysis
  async analyzeVideo(url, manualTranscript = null, maxClaims = 6) {
    const res = await fetch(`${API_BASE}/video/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        url,
        manual_transcript: manualTranscript,
        max_claims: maxClaims,
      }),
    });
    return handleResponse(res);
  },

  async analyzeManualTranscript(transcript, videoId = null, maxClaims = 6) {
    const res = await fetch(`${API_BASE}/transcript/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        transcript,
        video_id: videoId,
        max_claims: maxClaims,
      }),
    });
    return handleResponse(res);
  },

  // Real-Time Speech Verification
  async createSpeechSession() {
    const res = await fetch(`${API_BASE}/speech/session`, { method: 'POST' });
    return handleResponse(res);
  },

  async sendSpeechChunk(sessionId, text, timestampSec, isFinal = true) {
    const res = await fetch(`${API_BASE}/speech/chunk`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        text,
        timestamp_sec: timestampSec,
        is_final: isFinal,
      }),
    });
    return handleResponse(res);
  },

  async getSpeechStatus(sessionId) {
    const res = await fetch(`${API_BASE}/speech/status/${sessionId}`);
    return handleResponse(res);
  },
};

