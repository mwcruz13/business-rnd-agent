import { useEffect } from 'react';
import { Box, Text, TextArea, Tab } from 'grommet';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import StepCard from '../components/StepCard.jsx';
import EditableTextArea from '../components/EditableTextArea.jsx';

const Step6BusinessModel = ({ runState, editMode, editState, onEditChange, sessionId }) => {
  if (!runState) return <Text color="text-weak">Waiting for workflow to start…</Text>;

  const { business_model_canvas } = runState;

  useEffect(() => {
    if (editMode && Object.keys(editState).length === 0) {
      onEditChange(() => ({
        business_model_canvas: business_model_canvas || '',
      }));
    }
  }, [editMode]);

  if (!business_model_canvas) {
    return <Text color="text-weak">Step 6 has not run yet.</Text>;
  }

  const handleImport = (fields) => onEditChange(prev => ({ ...prev, ...fields }));

  return (
    <StepCard stepIndex={5} stepLabel="Business Model" runState={runState} sessionId={sessionId} onImport={handleImport}>
      <Tab title="Business Model Canvas">
        <Box pad="medium" overflow="auto">
          {editMode ? (
            <EditableTextArea
              value={editState.business_model_canvas ?? business_model_canvas ?? ''}
              onChange={(e) => { const v = e.target.value; onEditChange(prev => ({ ...prev, business_model_canvas: v })); }}
              rows={16}
              resize="vertical"
            />
          ) : (
            <Box background="background-front" pad="medium" round="small" className="markdown-body">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {business_model_canvas}
              </ReactMarkdown>
            </Box>
          )}
        </Box>
      </Tab>
    </StepCard>
  );
};

export default Step6BusinessModel;
