import { useEffect } from 'react';
import { Box, Text, TextArea, DataTable } from 'grommet';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const Section = ({ title, children }) => (
  <Box gap="xsmall" margin={{ bottom: 'medium' }}>
    <Text weight="bold" size="small" color="text-weak">{title}</Text>
    {children}
  </Box>
);

const SIGNAL_COLUMNS = [
  { property: 'signal_id', header: 'ID', size: 'xsmall' },
  { property: 'signal', header: 'Signal', size: 'medium' },
  { property: 'zone', header: 'Zone', size: 'small' },
  { property: 'source_type', header: 'Source', size: 'small' },
];

const INTERPRETED_COLUMNS = [
  { property: 'signal', header: 'Signal', size: 'medium' },
  { property: 'zone', header: 'Zone', size: 'small' },
  { property: 'classification', header: 'Classification', size: 'small' },
  { property: 'confidence', header: 'Confidence', size: 'xsmall' },
];

const PRIORITY_COLUMNS = [
  { property: 'signal', header: 'Signal', size: 'medium' },
  { property: 'impact', header: 'Impact', size: 'xsmall' },
  { property: 'speed', header: 'Speed', size: 'xsmall' },
  { property: 'score', header: 'Score', size: 'xsmall' },
  { property: 'tier', header: 'Tier', size: 'xsmall' },
];

const Step1SignalScan = ({ runState, editMode, editState, onEditChange }) => {
  if (!runState) return <Text color="text-weak">Waiting for workflow to start…</Text>;

  const { agent_recommendation, signals, interpreted_signals, priority_matrix, coverage_gaps } = runState;

  // Initialize edit state from runState when entering edit mode
  useEffect(() => {
    if (editMode && Object.keys(editState).length === 0) {
      onEditChange({
        agent_recommendation: agent_recommendation || '',
        signals: signals || [],
        interpreted_signals: interpreted_signals || [],
        priority_matrix: priority_matrix || [],
      });
    }
  }, [editMode]);

  if (!agent_recommendation && (!signals || signals.length === 0)) {
    return <Text color="text-weak">Step 1 has not run yet.</Text>;
  }

  if (editMode) {
    return (
      <Box gap="medium">
        <Section title="Agent Recommendation">
          <TextArea
            value={editState.agent_recommendation ?? agent_recommendation ?? ''}
            onChange={(e) => onEditChange({ ...editState, agent_recommendation: e.target.value })}
            rows={6}
            resize="vertical"
          />
        </Section>

        {(editState.signals ?? signals)?.length > 0 && (
          <Section title={`Signals (${(editState.signals ?? signals).length})`}>
            <Box background="background-front" pad="small" round="small" overflow="auto">
              <DataTable
                columns={SIGNAL_COLUMNS}
                data={editState.signals ?? signals}
                size="medium"
              />
            </Box>
          </Section>
        )}

        {(editState.interpreted_signals ?? interpreted_signals)?.length > 0 && (
          <Section title={`Interpreted Signals (${(editState.interpreted_signals ?? interpreted_signals).length})`}>
            <Box background="background-front" pad="small" round="small" overflow="auto">
              <DataTable
                columns={INTERPRETED_COLUMNS}
                data={editState.interpreted_signals ?? interpreted_signals}
                size="medium"
              />
            </Box>
          </Section>
        )}

        {(editState.priority_matrix ?? priority_matrix)?.length > 0 && (
          <Section title="Priority Matrix">
            <Box background="background-front" pad="small" round="small" overflow="auto">
              <DataTable
                columns={PRIORITY_COLUMNS}
                data={editState.priority_matrix ?? priority_matrix}
                size="medium"
              />
            </Box>
          </Section>
        )}
      </Box>
    );
  }

  // Read-only view
  return (
    <Box gap="small">
      {agent_recommendation && (
        <Section title="Agent Recommendation">
          <Box background="background-front" pad="medium" round="small">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {agent_recommendation}
            </ReactMarkdown>
          </Box>
        </Section>
      )}

      {signals && signals.length > 0 && (
        <Section title={`Signals (${signals.length})`}>
          <Box background="background-front" pad="small" round="small" overflow="auto">
            <DataTable columns={SIGNAL_COLUMNS} data={signals} size="medium" />
          </Box>
        </Section>
      )}

      {interpreted_signals && interpreted_signals.length > 0 && (
        <Section title={`Interpreted Signals (${interpreted_signals.length})`}>
          <Box background="background-front" pad="small" round="small" overflow="auto">
            <DataTable columns={INTERPRETED_COLUMNS} data={interpreted_signals} size="medium" />
          </Box>
        </Section>
      )}

      {priority_matrix && priority_matrix.length > 0 && (
        <Section title="Priority Matrix">
          <Box background="background-front" pad="small" round="small" overflow="auto">
            <DataTable columns={PRIORITY_COLUMNS} data={priority_matrix} size="medium" />
          </Box>
        </Section>
      )}

      {coverage_gaps && coverage_gaps.length > 0 && (
        <Section title="Coverage Gaps">
          <Box background="background-front" pad="medium" round="small" overflow="auto">
            <pre style={{ fontSize: '13px', whiteSpace: 'pre-wrap' }}>
              {JSON.stringify(coverage_gaps, null, 2)}
            </pre>
          </Box>
        </Section>
      )}
    </Box>
  );
};

export default Step1SignalScan;
