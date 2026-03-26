import { useEffect } from 'react';
import { Box, Text, TextArea } from 'grommet';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const Step3CustomerProfile = ({ runState, editMode, editState, onEditChange }) => {
  if (!runState) return <Text color="text-weak">Waiting for workflow to start…</Text>;

  const { customer_profile, empathy_gap_questions, supplemental_voc } = runState;

  useEffect(() => {
    if (editMode && Object.keys(editState).length === 0) {
      onEditChange({
        customer_profile: customer_profile || '',
        supplemental_voc: supplemental_voc || '',
      });
    }
  }, [editMode]);

  if (!customer_profile) {
    return <Text color="text-weak">Step 3 has not run yet.</Text>;
  }

  if (editMode) {
    return (
      <Box gap="medium">
        <Box gap="xsmall">
          <Text weight="bold" size="small">Customer Profile (Markdown)</Text>
          <TextArea
            value={editState.customer_profile ?? customer_profile ?? ''}
            onChange={(e) => onEditChange({ ...editState, customer_profile: e.target.value })}
            rows={12}
            resize="vertical"
          />
        </Box>

        {empathy_gap_questions && (
          <Box gap="xsmall">
            <Text weight="bold" size="small" color="text-weak">Empathy Gap Questions (read-only)</Text>
            <Box background="background-front" pad="medium" round="small">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {empathy_gap_questions}
              </ReactMarkdown>
            </Box>
          </Box>
        )}

        <Box gap="xsmall">
          <Text weight="bold" size="small">Supplemental VoC</Text>
          <Text size="xsmall" color="text-weak">
            Add additional customer insights to strengthen the profile.
          </Text>
          <TextArea
            value={editState.supplemental_voc ?? supplemental_voc ?? ''}
            onChange={(e) => onEditChange({ ...editState, supplemental_voc: e.target.value })}
            rows={6}
            resize="vertical"
            placeholder="Paste additional interview notes, survey results, or observations…"
          />
        </Box>
      </Box>
    );
  }

  return (
    <Box gap="medium">
      <Box gap="xsmall">
        <Text weight="bold" size="small" color="text-weak">Customer Profile</Text>
        <Box background="background-front" pad="medium" round="small">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {customer_profile}
          </ReactMarkdown>
        </Box>
      </Box>

      {empathy_gap_questions && (
        <Box gap="xsmall">
          <Text weight="bold" size="small" color="text-weak">Empathy Gap Questions</Text>
          <Box background="background-front" pad="medium" round="small">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {empathy_gap_questions}
            </ReactMarkdown>
          </Box>
        </Box>
      )}

      {supplemental_voc && (
        <Box gap="xsmall">
          <Text weight="bold" size="small" color="text-weak">Supplemental VoC</Text>
          <Box background="background-front" pad="medium" round="small">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {supplemental_voc}
            </ReactMarkdown>
          </Box>
        </Box>
      )}
    </Box>
  );
};

export default Step3CustomerProfile;
