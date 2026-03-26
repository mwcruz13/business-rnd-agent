import { useState, useMemo } from 'react';
import { Box, Heading, Text, Notification, Spinner } from 'grommet';
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
    resumeWorkflow, goToStep, setError,
  } = useWorkflow();

  const [editMode, setEditMode] = useState(false);
  const [editState, setEditState] = useState({});

  const currentCheckpoint = runState?.pending_checkpoint || null;

  // Determine which step component to render
  const StepComponent = STEP_COMPONENTS[activeStep] ?? null;
  const stepDef = STEPS[activeStep];

  const handleApprove = async () => {
    try {
      if (editMode) {
        await resumeWorkflow('edit', editState);
        setEditMode(false);
        setEditState({});
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
    setEditMode(false);
    setEditState({});
  };

  return (
    <Box direction="row" fill>
      {/* Sidebar */}
      <StepSidebar
        activeStep={activeStep}
        runState={runState}
        onStepClick={goToStep}
      />

      {/* Main content */}
      <Box flex pad="medium" gap="small" overflow="auto">
        {/* Header */}
        <Box direction="row" align="center" justify="between">
          <Box>
            <Heading level={3} margin="none">
              Step {activeStep + 1}: {stepDef?.label}
            </Heading>
            <Text size="small" color="text-weak">
              Session: {sessionId}
            </Text>
          </Box>
          {isLoading && <Spinner size="small" />}
        </Box>

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
        <Box flex overflow="auto">
          {StepComponent ? (
            <StepComponent
              runState={runState}
              editMode={editMode}
              editState={editState}
              onEditChange={setEditState}
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
      </Box>
    </Box>
  );
};

export default StepWizard;
