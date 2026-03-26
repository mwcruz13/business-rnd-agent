/**
 * Backend API client for the BMI Consultant workflow.
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

export async function startRun({ inputText, inputFormat, llmBackend, pauseAtCheckpoints = true }) {
  return request('POST', '/runs', {
    body: {
      input_text: inputText,
      input_format: inputFormat || null,
      llm_backend: llmBackend || 'azure',
      pause_at_checkpoints: pauseAtCheckpoints,
    },
    timeout: 300000,
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
    timeout: 300000,
  });
}

export async function startFromStep({ stepNumber, initialState, llmBackend, sessionId }) {
  return request('POST', '/runs/start-from-step', {
    body: {
      step_number: stepNumber,
      initial_state: initialState,
      llm_backend: llmBackend || 'azure',
      session_id: sessionId || undefined,
    },
    timeout: 300000,
  });
}

export async function getStepOutput(sessionId, stepNumber) {
  return request('GET', `/runs/${encodeURIComponent(sessionId)}/step/${stepNumber}`);
}

export { ApiError };
