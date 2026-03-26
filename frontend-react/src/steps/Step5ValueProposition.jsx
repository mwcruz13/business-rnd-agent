import { useEffect } from 'react';
import { Box, Text, TextArea } from 'grommet';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const Step5ValueProposition = ({ runState, editMode, editState, onEditChange }) => {
  if (!runState) return <Text color="text-weak">Waiting for workflow to start…</Text>;

  const { value_proposition_canvas, fit_assessment } = runState;

  useEffect(() => {
    if (editMode && Object.keys(editState).length === 0) {
      onEditChange({
        value_proposition_canvas: value_proposition_canvas || '',
        fit_assessment: fit_assessment || '',
      });
    }
  }, [editMode]);

  if (!value_proposition_canvas) {
    return <Text color="text-weak">Step 5 has not run yet.</Text>;
  }

  if (editMode) {
    return (
      <Box gap="medium">
        <Box gap="xsmall">
          <Text weight="bold" size="small">Value Proposition Canvas (Markdown)</Text>
          <TextArea
            value={editState.value_proposition_canvas ?? value_proposition_canvas ?? ''}
            onChange={(e) => onEditChange({ ...editState, value_proposition_canvas: e.target.value })}
            rows={14}
            resize="vertical"
          />
        </Box>
        <Box gap="xsmall">
          <Text weight="bold" size="small">Fit Assessment (Markdown)</Text>
          <TextArea
            value={editState.fit_assessment ?? fit_assessment ?? ''}
            onChange={(e) => onEditChange({ ...editState, fit_assessment: e.target.value })}
            rows={6}
            resize="vertical"
          />
        </Box>
      </Box>
    );
  }

  return (
    <Box gap="medium">
      <Box gap="xsmall">
        <Text weight="bold" size="small" color="text-weak">Value Proposition Canvas</Text>
        <Box background="background-front" pad="medium" round="small">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {value_proposition_canvas}
          </ReactMarkdown>
        </Box>
      </Box>

      {fit_assessment && (
        <Box gap="xsmall">
          <Text weight="bold" size="small" color="text-weak">Fit Assessment</Text>
          <Box background="background-front" pad="medium" round="small">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {fit_assessment}
            </ReactMarkdown>
          </Box>
        </Box>
      )}
    </Box>
  );
};

export default Step5ValueProposition;
