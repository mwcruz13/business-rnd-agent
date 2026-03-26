import { useEffect } from 'react';
import { Box, Text, TextArea } from 'grommet';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const Step6BusinessModel = ({ runState, editMode, editState, onEditChange }) => {
  if (!runState) return <Text color="text-weak">Waiting for workflow to start…</Text>;

  const { business_model_canvas } = runState;

  useEffect(() => {
    if (editMode && Object.keys(editState).length === 0) {
      onEditChange({
        business_model_canvas: business_model_canvas || '',
      });
    }
  }, [editMode]);

  if (!business_model_canvas) {
    return <Text color="text-weak">Step 6 has not run yet.</Text>;
  }

  if (editMode) {
    return (
      <Box gap="medium">
        <Box gap="xsmall">
          <Text weight="bold" size="small">Business Model Canvas (Markdown)</Text>
          <TextArea
            value={editState.business_model_canvas ?? business_model_canvas ?? ''}
            onChange={(e) => onEditChange({ ...editState, business_model_canvas: e.target.value })}
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
        <Text weight="bold" size="small" color="text-weak">Business Model Canvas</Text>
        <Box background="background-front" pad="medium" round="small">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {business_model_canvas}
          </ReactMarkdown>
        </Box>
      </Box>
    </Box>
  );
};

export default Step6BusinessModel;
