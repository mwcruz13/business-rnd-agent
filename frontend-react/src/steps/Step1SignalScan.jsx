import { useEffect } from 'react';
import { Box, Text, TextArea, DataTable, Tab } from 'grommet';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import StepCard from '../components/StepCard.jsx';
import EditableTextArea from '../components/EditableTextArea.jsx';

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

const Step1SignalScan = ({ runState, editMode, editState, onEditChange, sessionId }) => {
  if (!runState) return <Text color="text-weak">Waiting for workflow to start…</Text>;

  const { agent_recommendation, signals, interpreted_signals, priority_matrix, coverage_gaps } = runState;

  useEffect(() => {
    if (editMode && Object.keys(editState).length === 0) {
      onEditChange(() => ({
        agent_recommendation: agent_recommendation || '',
        signals: signals || [],
        interpreted_signals: interpreted_signals || [],
        priority_matrix: priority_matrix || [],
      }));
    }
  }, [editMode]);

  if (!agent_recommendation && (!signals || signals.length === 0)) {
    return <Text color="text-weak">Step 1 has not run yet.</Text>;
  }

  const handleImport = (fields) => onEditChange(prev => ({ ...prev, ...fields }));

  return (
    <StepCard stepIndex={0} stepLabel="Signal Scan" runState={runState} sessionId={sessionId} onImport={handleImport}>
      <Tab title="Recommendation">
        <Box pad="medium" overflow="auto">
          {editMode ? (
            <EditableTextArea
              value={editState.agent_recommendation ?? agent_recommendation ?? ''}
              onChange={(e) => { const v = e.target.value; onEditChange(prev => ({ ...prev, agent_recommendation: v })); }}
              rows={6}
              resize="vertical"
            />
          ) : agent_recommendation ? (
            <Box background="background-front" pad="medium" round="small" className="markdown-body">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {agent_recommendation}
              </ReactMarkdown>
            </Box>
          ) : (
            <Text color="text-weak">No recommendation yet.</Text>
          )}
        </Box>
      </Tab>

      <Tab title={`Signals${signals?.length ? ` (${signals.length})` : ''}`}>
        <Box pad="medium" overflow="auto">
          {(editState.signals ?? signals)?.length > 0 ? (
            <DataTable
              columns={SIGNAL_COLUMNS}
              data={editState.signals ?? signals}
              size="medium"
            />
          ) : (
            <Text color="text-weak">No signals yet.</Text>
          )}
        </Box>
      </Tab>

      <Tab title={`Interpreted${interpreted_signals?.length ? ` (${interpreted_signals.length})` : ''}`}>
        <Box pad="medium" overflow="auto">
          {(editState.interpreted_signals ?? interpreted_signals)?.length > 0 ? (
            <DataTable
              columns={INTERPRETED_COLUMNS}
              data={editState.interpreted_signals ?? interpreted_signals}
              size="medium"
            />
          ) : (
            <Text color="text-weak">No interpreted signals yet.</Text>
          )}
        </Box>
      </Tab>

      <Tab title="Priority Matrix">
        <Box pad="medium" overflow="auto">
          {(editState.priority_matrix ?? priority_matrix)?.length > 0 ? (
            <DataTable
              columns={PRIORITY_COLUMNS}
              data={editState.priority_matrix ?? priority_matrix}
              size="medium"
            />
          ) : (
            <Text color="text-weak">No priority matrix yet.</Text>
          )}
        </Box>
      </Tab>

      <Tab title="Coverage Gaps">
        <Box pad="medium" overflow="auto">
          {coverage_gaps && coverage_gaps.length > 0 ? (
            <Box background="background-front" pad="medium" round="small">
              <pre style={{ fontSize: '13px', whiteSpace: 'pre-wrap' }}>
                {JSON.stringify(coverage_gaps, null, 2)}
              </pre>
            </Box>
          ) : (
            <Text color="text-weak">No coverage gaps identified.</Text>
          )}
        </Box>
      </Tab>
    </StepCard>
  );
};

export default Step1SignalScan;
