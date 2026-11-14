/**
 * Curriculum Gap Analysis Pipeline - Frontend API Service
 * Interacts with the FastAPI backend on /api/*
 */

const API_BASE = '/api';

export async function fetchHealth() {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error('Backend health check failed');
  return res.json();
}

export async function fetchSamples() {
  const res = await fetch(`${API_BASE}/samples`);
  if (!res.ok) throw new Error('Failed to load sample syllabi');
  return res.json();
}

export async function fetchSampleContent(filename) {
  const res = await fetch(`${API_BASE}/samples/${filename}`);
  if (!res.ok) throw new Error(`Failed to load sample ${filename}`);
  return res.json();
}

export async function runAnalysisText({ domain, text, coveredThreshold = 0.75, partialThreshold = 0.45 }) {
  const res = await fetch(`${API_BASE}/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      domain,
      syllabus_text: text,
      covered_threshold: coveredThreshold,
      partial_threshold: partialThreshold,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Analysis failed' }));
    throw new Error(err.detail || 'Analysis failed');
  }
  return res.json();
}

export async function runAnalysisUpload({ domain, file, coveredThreshold = 0.75, partialThreshold = 0.45 }) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('domain', domain);
  formData.append('covered_threshold', coveredThreshold.toString());
  formData.append('partial_threshold', partialThreshold.toString());

  const res = await fetch(`${API_BASE}/analyze/upload`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Upload failed' }));
    throw new Error(err.detail || 'Upload failed');
  }
  return res.json();
}

export async function fetchRuns(limit = 50) {
  const res = await fetch(`${API_BASE}/runs?limit=${limit}`);
  if (!res.ok) throw new Error('Failed to fetch runs');
  return res.json();
}

export async function fetchRunDetail(runId) {
  const res = await fetch(`${API_BASE}/runs/${runId}`);
  if (!res.ok) throw new Error(`Failed to fetch run ${runId}`);
  return res.json();
}

export async function fetchRunEvents(runId) {
  const res = await fetch(`${API_BASE}/runs/${runId}/events`);
  if (!res.ok) throw new Error(`Failed to fetch trace events for ${runId}`);
  return res.json();
}

export async function fetchRunGaps(runId) {
  const res = await fetch(`${API_BASE}/runs/${runId}/gaps`);
  if (!res.ok) throw new Error(`Failed to fetch gaps for ${runId}`);
  return res.json();
}

export async function fetchRunRecommendations(runId) {
  const res = await fetch(`${API_BASE}/runs/${runId}/recommendations`);
  if (!res.ok) throw new Error(`Failed to fetch recommendations for ${runId}`);
  return res.json();
}

export async function fetchRunReport(runId) {
  const res = await fetch(`${API_BASE}/runs/${runId}/report`);
  if (!res.ok) throw new Error(`Failed to fetch report for ${runId}`);
  return res.json();
}

export function getPdfDownloadUrl(runId) {
  return `${API_BASE}/runs/${runId}/report/pdf`;
}

export function getJsonDownloadUrl(runId) {
  return `${API_BASE}/runs/${runId}/report/json`;
}

export async function fetchEvaluation(force = false) {
  const res = await fetch(`${API_BASE}/evaluate?force=${force}`);
  if (!res.ok) throw new Error('Failed to run benchmark evaluation');
  return res.json();
}

export async function fetchFrameworks() {
  const res = await fetch(`${API_BASE}/frameworks`);
  if (!res.ok) throw new Error('Failed to fetch frameworks metadata');
  return res.json();
}

export async function triggerReindexing() {
  const res = await fetch(`${API_BASE}/frameworks/ingest`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to reindex frameworks');
  return res.json();
}
