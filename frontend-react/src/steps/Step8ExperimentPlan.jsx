import { useEffect } from 'react';
import { Box, Text, TextArea } from 'grommet';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const Step8ExperimentPlan = ({ runState, editMode, editState, onEditChange }) => {
  if (!runState) return <Text color="text-weak">Waiting for workflow to start…</Text>;

  const { experiment_selections, experiment_plans, experiment_worksheets } = runState;

  useEffect(() => {
    if (editMode && Object.keys(editState).length === 0) {
      onEditChange({
        experiment_selections: experiment_selections || '',
        experiment_plans: experiment_plans || '',
        experiment_worksheets: experiment_worksheets || '',
      });
    }
  }, [editMode]);

  if (!experiment_selections && !experiment_plans) {
    return <Text color="text-weak">Step 8 has not run yet.</Text>;
  }

  if (editMode) {
    return (
      <Box gap="medium">
        <Box gap="xsmall">
          <Text weight="bold" size="small">Experiment Selections (Markdown)</Text>
          <TextArea
            value={editState.experiment_selections ?? experiment_selections ?? ''}
            onChange={(e) => onEditChange({ ...editState, experiment_selections: e.target.value })}
            rows={8}
            resize="vertical"
          />
        </Box>
        <Box gap="xsmall">
          <Text weight="bold" size="small">Experiment Plans (Markdown)</Text>
          <TextArea
            value={editState.experiment_plans ?? experiment_plans ?? ''}
            onChange={(e) => onEditChange({ ...editState, experiment_plans: e.target.value })}
            rows={10}
            resize="vertical"
          />
        </Box>
        <Box gap="xsmall">
          <Text weight="bold" size="small">Experiment Worksheets (Markdown)</Text>
          <TextArea
            value={editState.experiment_worksheets ?? experiment_worksheets ?? ''}
            onChange={(e) => onEditChange({ ...editState, experiment_worksheets: e.target.value })}
            rows={10}
            resize="vertical"
          />
        </Box>
      </Box>
    );
  }

  return (
    <Box gap="medium">
      {experiment_selections && (
        <Box gap="xsmall">
          <Text weight="bold" size="small" color="text-weak">Experiment Selections</Text>
          <Box background="background-front" pad="medium" round="small">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {experiment_selections}
            </ReactMarkdown>
          </Box>
        </Box>
      )}

      {experiment_plans && (
        <Box gap="xsmall">
          <Text weight="bold" size="small" color="text-weak">Experiment Plans</Text>
          <Box background="background-front" pad="medium" round="small">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {experiment_plans}
            </ReactMarkdown>
          </Box>
        </Box>
      )}

      {experiment_worksheets && (
        <Box gap="xsmall">
          <Text weight="bold" size="small" color="text-weak">Experiment Worksheets</Text>
          <Box background="background-front" pad="medium" round="small">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {experiment_worksheets}
            </ReactMarkdown>
          </Box>
        </Box>
      )}
    </Box>
  );
};

export default Step8ExperimentPlan;
