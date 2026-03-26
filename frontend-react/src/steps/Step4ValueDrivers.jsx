import { useEffect } from 'react';
import { Box, Text, TextArea } from 'grommet';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const Step4ValueDrivers = ({ runState, editMode, editState, onEditChange }) => {
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

  if (editMode) {
    return (
      <Box gap="medium">
        <Box gap="xsmall">
          <Text weight="bold" size="small">Value Driver Tree (Markdown)</Text>
          <TextArea
            value={editState.value_driver_tree ?? value_driver_tree ?? ''}
            onChange={(e) => onEditChange({ ...editState, value_driver_tree: e.target.value })}
            rows={12}
            resize="vertical"
          />
        </Box>
        <Box gap="xsmall">
          <Text weight="bold" size="small">Actionable Insights (Markdown)</Text>
          <TextArea
            value={editState.actionable_insights ?? actionable_insights ?? ''}
            onChange={(e) => onEditChange({ ...editState, actionable_insights: e.target.value })}
            rows={8}
            resize="vertical"
          />
        </Box>
      </Box>
    );
  }

  return (
    <Box gap="medium">
      <Box gap="xsmall">
        <Text weight="bold" size="small" color="text-weak">Value Driver Tree</Text>
        <Box background="background-front" pad="medium" round="small">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {value_driver_tree}
          </ReactMarkdown>
        </Box>
      </Box>

      {actionable_insights && (
        <Box gap="xsmall">
          <Text weight="bold" size="small" color="text-weak">Actionable Insights</Text>
          <Box background="background-front" pad="medium" round="small">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {actionable_insights}
            </ReactMarkdown>
          </Box>
        </Box>
      )}
    </Box>
  );
};

export default Step4ValueDrivers;
