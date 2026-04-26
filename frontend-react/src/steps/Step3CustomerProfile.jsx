import { useEffect } from 'react';
import { Box, Text, TextArea, Tab } from 'grommet';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import StepCard from '../components/StepCard.jsx';
import EditableTextArea from '../components/EditableTextArea.jsx';

const Step3CustomerProfile = ({ runState, editMode, editState, onEditChange, sessionId }) => {
  if (!runState) return <Text color="text-weak">Waiting for workflow to start…</Text>;

  const { customer_profile, empathy_gap_questions, supplemental_voc } = runState;

  useEffect(() => {
    if (editMode && Object.keys(editState).length === 0) {
      onEditChange(() => ({
        customer_profile: customer_profile || '',
        supplemental_voc: supplemental_voc || '',
      }));
    }
  }, [editMode]);

  if (!customer_profile) {
    return <Text color="text-weak">Step 3 has not run yet.</Text>;
  }

  const handleImport = (fields) => onEditChange(prev => ({ ...prev, ...fields }));

  return (
    <StepCard stepIndex={2} stepLabel="Customer Profile" runState={runState} sessionId={sessionId} onImport={handleImport}>
      <Tab title="Profile">
        <Box pad="medium" overflow="auto">
          {editMode ? (
            <EditableTextArea
              value={editState.customer_profile ?? customer_profile ?? ''}
              onChange={(e) => { const v = e.target.value; onEditChange(prev => ({ ...prev, customer_profile: v })); }}
              rows={12}
              resize="vertical"
            />
          ) : (
            <Box background="background-front" pad="medium" round="small" className="markdown-body">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {customer_profile}
              </ReactMarkdown>
            </Box>
          )}
        </Box>
      </Tab>

      <Tab title="Empathy Questions">
        <Box pad="medium" overflow="auto">
          {empathy_gap_questions ? (
            <Box background="background-front" pad="medium" round="small" className="markdown-body">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {empathy_gap_questions}
              </ReactMarkdown>
            </Box>
          ) : (
            <Text color="text-weak">No empathy gap questions yet.</Text>
          )}
        </Box>
      </Tab>

      <Tab title="Supplemental VoC">
        <Box pad="medium" overflow="auto">
          {editMode ? (
            <Box gap="xsmall">
              <Text size="xsmall" color="text-weak">
                Add additional customer insights to strengthen the profile.
              </Text>
              <EditableTextArea
                value={editState.supplemental_voc ?? supplemental_voc ?? ''}
                onChange={(e) => { const v = e.target.value; onEditChange(prev => ({ ...prev, supplemental_voc: v })); }}
                rows={6}
                resize="vertical"
                placeholder="Paste additional interview notes, survey results, or observations…"
              />
            </Box>
          ) : supplemental_voc ? (
            <Box background="background-front" pad="medium" round="small" className="markdown-body">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {supplemental_voc}
              </ReactMarkdown>
            </Box>
          ) : (
            <Text color="text-weak">No supplemental VoC yet.</Text>
          )}
        </Box>
      </Tab>
    </StepCard>
  );
};

export default Step3CustomerProfile;
