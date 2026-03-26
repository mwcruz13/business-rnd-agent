import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Box, Spinner, Text } from 'grommet';
import { useWorkflow } from '../context/WorkflowContext.jsx';
import StepWizard from '../components/StepWizard.jsx';

const WorkflowPage = () => {
  const navigate = useNavigate();
  const { sessionId, runState, loadSession, isLoading } = useWorkflow();

  useEffect(() => {
    if (!sessionId) {
      navigate('/', { replace: true });
      return;
    }
    // Refresh state from backend on mount if we have a session but no runState
    if (!runState) {
      loadSession(sessionId).catch(() => navigate('/', { replace: true }));
    }
  }, [sessionId, runState, loadSession, navigate]);

  if (!sessionId) return null;

  if (isLoading && !runState) {
    return (
      <Box fill align="center" justify="center" gap="small">
        <Spinner size="medium" />
        <Text>Loading workflow…</Text>
      </Box>
    );
  }

  return <StepWizard />;
};

export default WorkflowPage;
