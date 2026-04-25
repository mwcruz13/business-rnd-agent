/**
 * Backend API client for the CXIF AI Coach workflow.
 *
 * All requests go through the Vite proxy (/api -> backend:8000)
 * so the browser never needs to know the backend host.
 */

const BASE = '/api';

class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

async function request(method, path, { body, timeout = 30000 } = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeout);

  try {
    const options = {
      method,
      headers: { 'Content-Type': 'application/json' },
      signal: controller.signal,
    };
    if (body) options.body = JSON.stringify(body);

    const response = await fetch(`${BASE}${path}`, options);

    if (response.ok) return response.json();

    let detail;
    try {
      const err = await response.json();
      detail = err.detail || `Request failed with status ${response.status}`;
    } catch {
      detail = `Request failed with status ${response.status}`;
    }
    throw new ApiError(detail, response.status);
  } catch (err) {
    if (err.name === 'AbortError') {
      throw new ApiError(
        `Request to ${path} timed out after ${timeout / 1000}s. The workflow may still be running.`,
        0,
      );
    }
    if (err instanceof ApiError) throw err;
    throw new ApiError(`Cannot reach backend: ${err.message}`, 0);
  } finally {
    clearTimeout(timer);
  }
}

export async function getHealth() {
  return request('GET', '/health');
}

export async function startRun({ inputText, inputFormat, llmBackend, sessionName, pauseAtCheckpoints = true }) {
  return request('POST', '/runs', {
    body: {
      input_text: inputText,
      input_format: inputFormat || null,
      llm_backend: llmBackend || 'azure',
      session_name: sessionName || null,
      pause_at_checkpoints: pauseAtCheckpoints,
    },
    timeout: 900000,
  });
}

export async function getRunState(sessionId) {
  return request('GET', `/runs/${encodeURIComponent(sessionId)}`);
}

export async function resumeRun(sessionId, { decision, editState }) {
  const body = { decision };
  if (editState) body.edit_state = editState;
  return request('POST', `/runs/${encodeURIComponent(sessionId)}/resume`, {
    body,
    timeout: 900000,
  });
}

export async function startFromStep({ stepNumber, initialState, llmBackend, sessionId, sessionName }) {
  return request('POST', '/runs/start-from-step', {
    body: {
      step_number: stepNumber,
      initial_state: initialState,
      llm_backend: llmBackend || 'azure',
      session_id: sessionId || undefined,
      session_name: sessionName || null,
    },
    timeout: 900000,
  });
}

export async function listSessions() {
  return request('GET', '/sessions');
}

export async function renameSession(sessionId, sessionName) {
  return request('PATCH', `/runs/${encodeURIComponent(sessionId)}/name`, {
    body: { session_name: sessionName },
  });
}

export async function restartFromStep(sessionId, { stepNumber, editState }) {
  const body = { step_number: stepNumber };
  if (editState) body.edit_state = editState;
  return request('POST', `/runs/${encodeURIComponent(sessionId)}/restart`, {
    body,
    timeout: 900000,
  });
}

export async function getStepOutput(sessionId, stepNumber) {
  return request('GET', `/runs/${encodeURIComponent(sessionId)}/step/${stepNumber}`);
}

export async function updateExperimentCard(sessionId, cardId, updates) {
  return request('PATCH', `/runs/${encodeURIComponent(sessionId)}/experiment-cards/${encodeURIComponent(cardId)}`, {
    body: { updates },
  });
}


/**
 * Download a file export (Markdown or PPTX) as a browser download.
 * @param {'md'|'pptx'} format
 */
export async function downloadExport(sessionId, format) {
  const path = `/runs/${encodeURIComponent(sessionId)}/export/${format}`;
  const response = await fetch(`${BASE}${path}`);
  if (!response.ok) {
    let detail;
    try {
      const err = await response.json();
      detail = err.detail || `Export failed (${response.status})`;
    } catch {
      detail = `Export failed (${response.status})`;
    }
    throw new ApiError(detail, response.status);
  }
  const blob = await response.blob();
  const disposition = response.headers.get('content-disposition') || '';
  const filenameMatch = disposition.match(/filename="?([^"]+)"?/);
  const filename = filenameMatch ? filenameMatch[1] : `report.${format}`;

  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}


// ---------------------------------------------------------------------------
// Signal Browser API
// ---------------------------------------------------------------------------

export async function getSignalSummary() {
  return request('GET', '/signals/summary');
}

export async function getSignals({ bu, surveySource, classification, actionTier, minScore } = {}) {
  const params = new URLSearchParams();
  if (bu) params.set('bu', bu);
  if (surveySource) params.set('survey_source', surveySource);
  if (classification) params.set('classification', classification);
  if (actionTier) params.set('action_tier', actionTier);
  if (minScore) params.set('min_score', minScore);
  const qs = params.toString();
  return request('GET', `/signals${qs ? `?${qs}` : ''}`);
}

export async function getSignalDetail(id) {
  return request('GET', `/signals/${encodeURIComponent(id)}`);
}

export async function getSignalReports() {
  return request('GET', '/signals/reports');
}

export async function startRunFromSignal({ signalId, sessionName, llmBackend }) {
  return request('POST', '/runs/from-signal', {
    body: {
      signal_id: signalId,
      session_name: sessionName || null,
      llm_backend: llmBackend || 'azure',
      pause_at_checkpoints: true,
    },
    timeout: 900000,
  });
}


// ---------------------------------------------------------------------------
// Portfolio Dashboard API
// ---------------------------------------------------------------------------

export async function getPortfolio() {
  return request('GET', '/portfolio');
}

export async function getPortfolioDetail(sessionId) {
  return request('GET', `/portfolio/${encodeURIComponent(sessionId)}/detail`);
}

export async function updatePortfolio(sessionId, updates) {
  return request('PATCH', `/portfolio/${encodeURIComponent(sessionId)}`, {
    body: updates,
  });
}

export { ApiError };
