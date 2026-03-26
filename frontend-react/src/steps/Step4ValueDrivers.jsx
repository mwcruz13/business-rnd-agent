import { useEffect } from 'react';
import { Box, Text, TextArea, Tab } from 'grommet';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import StepCard from '../components/StepCard.jsx';

const Step4ValueDrivers = ({ runState, editMode, editState, onEditChange, sessionId }) => {
  if (!runState) return <Text color="text-weak">Waiting for workflow to start…</Text>;

  const { value_driver_tree, actionable_insights } = runState;

  useEffect(() => {
    if (editMode && Object.keys(editState).length === 0) {
      onEditChange({
        value_driver_tree: value_driver_tree || '',
        actionable_insights: actionable_insights || '',
      });
    }
  }, [editMode]);

  if (!value_driver_tree) {
    return <Text color="text-weak">Step 4 has not run yet.</Text>;
  }

  const handleImport = (fields) => onEditChange({ ...editState, ...fields });

  return (
    <StepCard stepIndex={3} stepLabel="Value Drivers" runState={runState} sessionId={sessionId} onImport={handleImport}>
      <Tab title="Value Driver Tree">
        <Box pad="medium" overflow="auto">
          {editMode ? (
            <TextArea
              value={editState.value_driver_tree ?? value_driver_tree ?? ''}
              onChange={(e) => onEditChange({ ...editState, value_driver_tree: e.target.value })}
              rows={12}
              resize="vertical"
            />
          ) : (
            <Box background="background-front" pad="medium" round="small">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {value_driver_tree}
              </ReactMarkdown>
            </Box>
          )}
        </Box>
      </Tab>

      <Tab title="Actionable Insights">
        <Box pad="medium" overflow="auto">
          {editMode ? (
            <TextArea
              value={editState.actionable_insights ?? actionable_insights ?? ''}
              onChange={(e) => onEditChange({ ...editState, actionable_insights: e.target.value })}
              rows={8}
              resize="vertical"
            />
          ) : actionable_insights ? (
            <Box background="background-front" pad="medium" round="small">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {actionable_insights}
              </ReactMarkdown>
            </Box>
          ) : (
            <Text color="text-weak">No actionable insights yet.</Text>
          )}
        </Box>
      </Tab>
    </StepCard>
  );
};

export default Step4ValueDrivers;
