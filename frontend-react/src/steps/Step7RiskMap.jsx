import { useEffect } from 'react';
import { Box, Text, TextArea } from 'grommet';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const Step7RiskMap = ({ runState, editMode, editState, onEditChange }) => {
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

  if (editMode) {
    return (
      <Box gap="medium">
        <Box gap="xsmall">
          <Text weight="bold" size="small">Assumptions &amp; Risk Map (Markdown)</Text>
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
      </Box>
    );
  }

  return (
    <Box gap="medium">
      <Box gap="xsmall">
        <Text weight="bold" size="small" color="text-weak">Assumptions &amp; Risk Map</Text>
        <Box background="background-front" pad="medium" round="small">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {assumptions}
          </ReactMarkdown>
        </Box>
      </Box>
    </Box>
  );
};

export default Step7RiskMap;
