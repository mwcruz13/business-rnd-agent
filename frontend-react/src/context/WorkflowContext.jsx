import { createContext, useContext, useState, useCallback } from 'react';
import { startRun, getRunState, resumeRun, startFromStep as apiStartFromStep, restartFromStep as apiRestartFromStep } from '../api/workflowApi.js';

const WorkflowContext = createContext(null);

/**
 * Maps backend current_step values to wizard step indices (0-based).
 */
const STEP_INDEX_BY_NAME = {
  signal_scan: 0,
  pattern_select: 1,
  empathize: 2,
  measure_define: 3,
  value_proposition: 4,
  design_fit: 5,
  risk_map: 6,
  pdsa_plan: 7,
};

function resolveStepIndex(runState) {
  if (!runState) return 0;
  return STEP_INDEX_BY_NAME[runState.current_step] ?? 0;
}

export function WorkflowProvider({ children }) {
  const [sessionId, setSessionId] = useState(
    () => localStorage.getItem('bmi_session_id') || null,
  );
  const [runState, setRunState] = useState(null);
  const [activeStep, setActiveStep] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const persistSession = useCallback((id) => {
    setSessionId(id);
    if (id) localStorage.setItem('bmi_session_id', id);
    else localStorage.removeItem('bmi_session_id');
  }, []);

  const startWorkflow = useCallback(async (vocData, inputFormat, llmBackend) => {
    setIsLoading(true);
    setError(null);
    try {
      const state = await startRun({ inputText: vocData, inputFormat, llmBackend });
      setRunState(state);
      persistSession(state.session_id);
      setActiveStep(resolveStepIndex(state));
      return state;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [persistSession]);

  const loadSession = useCallback(async (id) => {
    setIsLoading(true);
    setError(null);
    try {
      const state = await getRunState(id);
      setRunState(state);
      persistSession(state.session_id);
      setActiveStep(resolveStepIndex(state));
      return state;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [persistSession]);

  const resumeWorkflow = useCallback(async (decision, editState) => {
    if (!sessionId) throw new Error('No active session');
    setIsLoading(true);
    setError(null);
    try {
      const state = await resumeRun(sessionId, { decision, editState });
      setRunState(state);
      setActiveStep(resolveStepIndex(state));
      return state;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [sessionId]);

  const startFromStep = useCallback(async (stepNumber, initialState, llmBackend) => {
    setIsLoading(true);
    setError(null);
    try {
      const state = await apiStartFromStep({ stepNumber, initialState, llmBackend });
      setRunState(state);
      persistSession(state.session_id);
      setActiveStep(resolveStepIndex(state));
      return state;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [persistSession]);

  const restartFromStep = useCallback(async (stepNumber, editState) => {
    if (!sessionId) throw new Error('No active session');
    setIsLoading(true);
    setError(null);
    try {
      const state = await apiRestartFromStep(sessionId, { stepNumber, editState });
      setRunState(state);
      setActiveStep(resolveStepIndex(state));
      return state;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [sessionId]);

  const goToStep = useCallback((index) => {
    setActiveStep(index);
  }, []);

  const clearSession = useCallback(() => {
    setRunState(null);
    setActiveStep(0);
    setError(null);
    persistSession(null);
  }, [persistSession]);

  const value = {
    sessionId,
    runState,
    activeStep,
    isLoading,
    error,
    startWorkflow,
    startFromStep,
    restartFromStep,
    loadSession,
    resumeWorkflow,
    goToStep,
    clearSession,
    setError,
  };

  return (
    <WorkflowContext.Provider value={value}>
      {children}
    </WorkflowContext.Provider>
  );
}

export function useWorkflow() {
  const ctx = useContext(WorkflowContext);
  if (!ctx) throw new Error('useWorkflow must be used within WorkflowProvider');
  return ctx;
}
