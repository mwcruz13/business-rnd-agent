import { useEffect } from 'react';
import { Box, Text, TextArea, Tab } from 'grommet';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import StepCard from '../components/StepCard.jsx';

const Step5ValueProposition = ({ runState, editMode, editState, onEditChange, sessionId }) => {
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

  const handleImport = (fields) => onEditChange({ ...editState, ...fields });

  return (
    <StepCard stepIndex={4} stepLabel="Value Proposition" runState={runState} sessionId={sessionId} onImport={handleImport}>
      <Tab title="VP Canvas">
        <Box pad="medium" overflow="auto">
          {editMode ? (
            <TextArea
              value={editState.value_proposition_canvas ?? value_proposition_canvas ?? ''}
              onChange={(e) => onEditChange({ ...editState, value_proposition_canvas: e.target.value })}
              rows={14}
              resize="vertical"
            />
          ) : (
            <Box background="background-front" pad="medium" round="small" className="markdown-body">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {value_proposition_canvas}
              </ReactMarkdown>
            </Box>
          )}
        </Box>
      </Tab>

      <Tab title="Fit Assessment">
        <Box pad="medium" overflow="auto">
          {editMode ? (
            <TextArea
              value={editState.fit_assessment ?? fit_assessment ?? ''}
              onChange={(e) => onEditChange({ ...editState, fit_assessment: e.target.value })}
              rows={6}
              resize="vertical"
            />
          ) : fit_assessment ? (
            <Box background="background-front" pad="medium" round="small" className="markdown-body">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {fit_assessment}
              </ReactMarkdown>
            </Box>
          ) : (
            <Text color="text-weak">No fit assessment yet.</Text>
          )}
        </Box>
      </Tab>
    </StepCard>
  );
};

export default Step5ValueProposition;
