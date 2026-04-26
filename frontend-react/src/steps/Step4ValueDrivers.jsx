import { useEffect } from 'react';
import { Box, Text, TextArea, Tab } from 'grommet';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import StepCard from '../components/StepCard.jsx';
import EditableTextArea from '../components/EditableTextArea.jsx';

const Step4ValueDrivers = ({ runState, editMode, editState, onEditChange, sessionId }) => {
  if (!runState) return <Text color="text-weak">Waiting for workflow to start…</Text>;

  const { value_driver_tree, actionable_insights } = runState;

  useEffect(() => {
    if (editMode && Object.keys(editState).length === 0) {
      onEditChange(() => ({
        value_driver_tree: value_driver_tree || '',
        actionable_insights: actionable_insights || '',
      }));
    }
  }, [editMode]);

  if (!value_driver_tree) {
    return <Text color="text-weak">Step 4 has not run yet.</Text>;
  }

  const handleImport = (fields) => onEditChange(prev => ({ ...prev, ...fields }));

  return (
    <StepCard stepIndex={3} stepLabel="Value Drivers" runState={runState} sessionId={sessionId} onImport={handleImport}>
      <Tab title="Value Driver Tree">
        <Box pad="medium" overflow="auto">
          {editMode ? (
            <EditableTextArea
              value={editState.value_driver_tree ?? value_driver_tree ?? ''}
              onChange={(e) => { const v = e.target.value; onEditChange(prev => ({ ...prev, value_driver_tree: v })); }}
              rows={12}
              resize="vertical"
            />
          ) : (
            <Box background="background-front" pad="medium" round="small" className="markdown-body">
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
            <EditableTextArea
              value={editState.actionable_insights ?? actionable_insights ?? ''}
              onChange={(e) => { const v = e.target.value; onEditChange(prev => ({ ...prev, actionable_insights: v })); }}
              rows={8}
              resize="vertical"
            />
          ) : actionable_insights ? (
            <Box background="background-front" pad="medium" round="small" className="markdown-body">
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
