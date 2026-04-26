import { useEffect } from 'react';
import { Box, Text, TextArea, Tab, DataTable } from 'grommet';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import StepCard from '../components/StepCard.jsx';
import EditableTextArea from '../components/EditableTextArea.jsx';

const EVIDENCE_COLORS = { None: 'status-unknown', Weak: 'status-warning', Medium: 'status-ok' };

const AUDIT_COLUMNS = [
  { property: 'category', header: 'Category', size: 'small' },
  { property: 'assumption', header: 'Assumption', size: 'large' },
  {
    property: 'existing_evidence_level',
    header: 'Evidence',
    size: 'xsmall',
    render: (row) => (
      <Text size="small" color={EVIDENCE_COLORS[row.existing_evidence_level] || 'text'} weight="bold">
        {row.existing_evidence_level}
      </Text>
    ),
  },
  { property: 'evidence_summary', header: 'Summary', size: 'medium' },
];

const Step7RiskMap = ({ runState, editMode, editState, onEditChange, sessionId }) => {
  if (!runState) return <Text color="text-weak">Waiting for workflow to start…</Text>;

  const { assumptions, assumption_evidence_audit } = runState;

  useEffect(() => {
    if (editMode && Object.keys(editState).length === 0) {
      onEditChange(() => ({
        assumptions: assumptions || '',
      }));
    }
  }, [editMode]);

  if (!assumptions) {
    return <Text color="text-weak">Step 7 has not run yet.</Text>;
  }

  const handleImport = (fields) => onEditChange(prev => ({ ...prev, ...fields }));

  return (
    <StepCard stepIndex={6} stepLabel="Risk Map" runState={runState} sessionId={sessionId} onImport={handleImport}>
      <Tab title="Assumptions & Risk Map">
        <Box pad="medium" overflow="auto">
          {editMode ? (
            <Box gap="xsmall">
              <Text size="xsmall" color="text-weak">
                Edit the assumption list, DVF categories, and evidence strength assessments.
              </Text>
              <EditableTextArea
                value={editState.assumptions ?? assumptions ?? ''}
                onChange={(e) => { const v = e.target.value; onEditChange(prev => ({ ...prev, assumptions: v })); }}
                rows={16}
                resize="vertical"
              />
            </Box>
          ) : (
            <Box background="background-front" pad="medium" round="small" className="markdown-body">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {assumptions}
              </ReactMarkdown>
            </Box>
          )}
        </Box>
      </Tab>

      {assumption_evidence_audit?.length > 0 && (
        <Tab title={`Evidence Audit (${assumption_evidence_audit.length})`}>
          <Box pad="medium" overflow="auto">
            <Box margin={{ bottom: 'small' }}>
              <Text size="xsmall" color="text-weak">
                Pre-experiment evidence classification based on upstream VoC and signal data.
              </Text>
            </Box>
            <DataTable
              columns={AUDIT_COLUMNS}
              data={assumption_evidence_audit}
              size="medium"
            />
          </Box>
        </Tab>
      )}
    </StepCard>
  );
};

export default Step7RiskMap;
