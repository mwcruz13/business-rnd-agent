import { useEffect } from 'react';
import { Box, Text, TextArea, Tab } from 'grommet';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import StepCard from '../components/StepCard.jsx';

const Step7RiskMap = ({ runState, editMode, editState, onEditChange, sessionId }) => {
  if (!runState) return <Text color="text-weak">Waiting for workflow to start…</Text>;

  const { assumptions } = runState;

  useEffect(() => {
    if (editMode && Object.keys(editState).length === 0) {
      onEditChange({
        assumptions: assumptions || '',
      });
    }
  }, [editMode]);

  if (!assumptions) {
    return <Text color="text-weak">Step 7 has not run yet.</Text>;
  }

  const handleImport = (fields) => onEditChange({ ...editState, ...fields });

  return (
    <StepCard stepIndex={6} stepLabel="Risk Map" runState={runState} sessionId={sessionId} onImport={handleImport}>
      <Tab title="Assumptions & Risk Map">
        <Box pad="medium" overflow="auto">
          {editMode ? (
            <Box gap="xsmall">
              <Text size="xsmall" color="text-weak">
                Edit the assumption list, DVF categories, and evidence strength assessments.
              </Text>
              <TextArea
                value={editState.assumptions ?? assumptions ?? ''}
                onChange={(e) => onEditChange({ ...editState, assumptions: e.target.value })}
                rows={16}
                resize="vertical"
              />
            </Box>
          ) : (
            <Box background="background-front" pad="medium" round="small">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {assumptions}
              </ReactMarkdown>
            </Box>
          )}
        </Box>
      </Tab>
    </StepCard>
  );
};

export default Step7RiskMap;
