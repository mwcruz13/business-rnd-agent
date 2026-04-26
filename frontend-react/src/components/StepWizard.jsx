import { useState, useContext, useCallback, useEffect, useRef } from 'react';
import { Box, Text, Notification, Spinner, Button, ResponsiveContext } from 'grommet';
import { Revert } from 'grommet-icons';
import { useWorkflow } from '../context/WorkflowContext.jsx';
import StepSidebar, { STEPS } from './StepSidebar.jsx';
import CheckpointActions from './CheckpointActions.jsx';

// Dynamic step component imports (lazy-style, but kept simple for Phase 3)
import Step1SignalScan from '../steps/Step1SignalScan.jsx';
import Step2PatternDirection from '../steps/Step2PatternDirection.jsx';
import Step3CustomerProfile from '../steps/Step3CustomerProfile.jsx';
import Step4ValueDrivers from '../steps/Step4ValueDrivers.jsx';
import Step5ValueProposition from '../steps/Step5ValueProposition.jsx';
import Step6BusinessModel from '../steps/Step6BusinessModel.jsx';
import Step7RiskMap from '../steps/Step7RiskMap.jsx';
import Step8ExperimentPlan from '../steps/Step8ExperimentPlan.jsx';

const STEP_COMPONENTS = [
  Step1SignalScan,
  Step2PatternDirection,
  Step3CustomerProfile,
  Step4ValueDrivers,
  Step5ValueProposition,
  Step6BusinessModel,
  Step7RiskMap,
  Step8ExperimentPlan,
];

const StepWizard = () => {
  const {
    sessionId, runState, activeStep, isLoading, error,
    resumeWorkflow, restartFromStep, goToStep, setError,
  } = useWorkflow();

  const [editMode, setEditMode] = useState(() => {
    try { return sessionStorage.getItem('bmi_edit_mode') === 'true'; } catch { return false; }
  });
  const [editState, setEditState] = useState(() => {
    try { return JSON.parse(sessionStorage.getItem('bmi_edit_state') || '{}'); } catch { return {}; }
  });
  const size = useContext(ResponsiveContext);
  const isSmall = size === 'small';

  // Persist edit state to sessionStorage so HMR remounts don't lose edits.
  const editStateRef = useRef(editState);
  editStateRef.current = editState;
  useEffect(() => {
    try {
      sessionStorage.setItem('bmi_edit_mode', editMode ? 'true' : 'false');
      sessionStorage.setItem('bmi_edit_state', JSON.stringify(editState));
    } catch { /* quota exceeded — non-critical */ }
  }, [editMode, editState]);

  // Wrap setEditState so children can pass either an object or a functional updater.
  // This eliminates stale-closure bugs when typing quickly in TextAreas.
  const handleEditChange = useCallback((valueOrFn) => {
    if (typeof valueOrFn === 'function') {
      setEditState(valueOrFn);
    } else {
      setEditState(valueOrFn);
    }
  }, []);

  const currentCheckpoint = runState?.pending_checkpoint || null;
  const completedSteps = runState?.completed_steps || [];

  // The step name the user is currently viewing in the sidebar.
  const viewingStepKey = STEPS[activeStep]?.key;

  // True when the user is viewing a step that was already completed and is
  // NOT the step where the workflow is currently paused.  This covers both
  // "completed" runs and "paused" runs where the user navigates back.
  const isViewingCompletedStep =
    completedSteps.includes(viewingStepKey) &&
    runState?.run_status !== 'in_progress' &&
    // Don't show restart bar on the step that's pending checkpoint approval —
    // that step already has the checkpoint Approve/Edit bar.
    !(currentCheckpoint && activeStep === completedSteps.length);

  // Determine which step component to render
  const StepComponent = STEP_COMPONENTS[activeStep] ?? null;

  const clearEditSession = useCallback(() => {
    setEditMode(false);
    setEditState({});
    try {
      sessionStorage.removeItem('bmi_edit_mode');
      sessionStorage.removeItem('bmi_edit_state');
    } catch { /* non-critical */ }
  }, []);

  const handleApprove = async () => {
    try {
      if (editMode) {
        await resumeWorkflow('edit', editState);
        clearEditSession();
      } else {
        await resumeWorkflow('approve');
      }
    } catch {
      // error already set in context
    }
  };

  const handleEdit = () => {
    setEditMode(true);
  };

  const handleCancel = () => {
    clearEditSession();
  };

  const handleRestartFromHere = async () => {
    try {
      const stepNumber = activeStep + 1; // 1-based
      if (editMode) {
        await restartFromStep(stepNumber, editState);
        clearEditSession();
      } else {
        await restartFromStep(stepNumber);
      }
    } catch {
      // error already set in context
    }
  };

  return (
    <Box direction="row" fill style={{ minHeight: 0 }}>
      {/* Sidebar */}
      <StepSidebar
        activeStep={activeStep}
        runState={runState}
        onStepClick={goToStep}
      />

      {/* Main content */}
      <Box flex pad={isSmall ? 'small' : 'medium'} gap="small" overflow="auto" style={{ minHeight: 0 }}>
        {/* Loading indicator */}
        {isLoading && (
          <Box direction="row" justify="end">
            <Spinner size="small" />
          </Box>
        )}

        {/* Error notification */}
        {error && (
          <Notification
            status="critical"
            message={error}
            onClose={() => setError(null)}
          />
        )}

        {/* Status banner */}
        {runState?.run_status === 'paused' && currentCheckpoint && (
          <Notification
            status="warning"
            message={`Workflow paused at ${currentCheckpoint}. Review the output below and Approve or Edit.`}
          />
        )}
        {runState?.run_status === 'completed' && (
          <Notification
            status="normal"
            message="Workflow completed. You can review all steps using the sidebar."
          />
        )}

        {/* Step content */}
        <Box>
          {StepComponent ? (
            <StepComponent
              runState={runState}
              editMode={editMode}
              editState={editState}
              onEditChange={handleEditChange}
              sessionId={sessionId}
            />
          ) : (
            <Text>Unknown step</Text>
          )}
        </Box>

        {/* Checkpoint actions */}
        {currentCheckpoint && runState?.run_status === 'paused' && (
          <CheckpointActions
            checkpointId={currentCheckpoint}
            onApprove={handleApprove}
            onEdit={handleEdit}
            onCancel={handleCancel}
            isLoading={isLoading}
            editMode={editMode}
          />
        )}

        {/* Restart-from-step actions for previously completed steps */}
        {isViewingCompletedStep && (
          <Box
            direction="row"
            wrap
            gap="small"
            pad="small"
            border={{ side: 'top', color: 'border' }}
            justify="end"
            align="center"
            background="background-front"
          >
            <Text size="small" color="text-weak" margin={{ right: 'auto' }}>
              Reviewing completed step {activeStep + 1}
            </Text>
            {editMode ? (
              <>
                <Button
                  label="Cancel"
                  onClick={handleCancel}
                  disabled={isLoading}
                  secondary
                  size="small"
                />
                <Button
                  label="Save & Restart from here"
                  icon={<Revert size="small" />}
                  onClick={handleRestartFromHere}
                  disabled={isLoading}
                  primary
                  size="small"
                />
              </>
            ) : (
              <>
                <Button
                  label="Edit"
                  onClick={handleEdit}
                  disabled={isLoading}
                  secondary
                  size="small"
                />
                <Button
                  label="Restart from here"
                  icon={<Revert size="small" />}
                  onClick={handleRestartFromHere}
                  disabled={isLoading}
                  primary
                  size="small"
                />
              </>
            )}
          </Box>
        )}
      </Box>
    </Box>
  );
};

export default StepWizard;
