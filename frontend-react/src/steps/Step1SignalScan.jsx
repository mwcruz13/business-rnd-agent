import { useEffect, useState } from 'react';
import { Box, Text, DataTable, Tab, TextInput, Button, Spinner } from 'grommet';
import { Update } from 'grommet-icons';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import StepCard from '../components/StepCard.jsx';
import { regenerateStep1b } from '../api/workflowApi.js';

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

/**
 * Build editable column defs: each cell becomes a TextInput in edit mode.
 * `stateKey` is the editState field name (e.g. 'signals').
 */
const editableColumns = (cols, stateKey, data, onEditChange) =>
  cols.map(col => ({
    ...col,
    render: (datum) => {
      const idx = data.indexOf(datum);
      return (
        <TextInput
          plain
          size="small"
          value={String(datum[col.property] ?? '')}
          onChange={(e) => {
            if (idx < 0) return;
            const val = e.target.value;
            onEditChange(prev => {
              const arr = [...(prev[stateKey] || data)];
              arr[idx] = { ...arr[idx], [col.property]: val };
              return { ...prev, [stateKey]: arr };
            });
          }}
        />
      );
    },
  }));

const Step1SignalScan = ({ runState, editMode, editState, onEditChange, sessionId }) => {
  if (!runState) return <Text color="text-weak">Waiting for workflow to start…</Text>;

  const [regenerating, setRegenerating] = useState(false);
  const [regenError, setRegenError] = useState(null);

  const { agent_recommendation, signals, interpreted_signals, priority_matrix, coverage_gaps, voc_data } = runState;

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

  const handleRegenerate = async () => {
    setRegenerating(true);
    setRegenError(null);
    try {
      const result = await regenerateStep1b(sessionId, {
        signals: editState.signals ?? signals,
        interpreted_signals: editState.interpreted_signals ?? interpreted_signals,
      });
      // Update editState with regenerated fields from the LLM
      onEditChange(prev => ({
        ...prev,
        priority_matrix: result.priority_matrix ?? prev.priority_matrix,
        agent_recommendation: result.agent_recommendation ?? prev.agent_recommendation,
        signal_recommendations: result.signal_recommendations ?? prev.signal_recommendations,
        watching_briefs: result.watching_briefs ?? prev.watching_briefs,
        reinforcement_map: result.reinforcement_map ?? prev.reinforcement_map,
      }));
    } catch (err) {
      setRegenError(err.message || 'Regeneration failed');
    } finally {
      setRegenerating(false);
    }
  };

  return (
    <StepCard stepIndex={0} stepLabel="Signal Scan" runState={runState} sessionId={sessionId} onImport={handleImport}>
      <Tab title="Recommendation">
        <Box pad="medium" overflow="auto" gap="medium">
          {editMode && (
            <Box direction="row" align="center" gap="small">
              <Button
                label={regenerating ? 'Regenerating…' : 'Regenerate Recommendation'}
                icon={regenerating ? <Spinner size="xsmall" /> : <Update size="small" />}
                onClick={handleRegenerate}
                disabled={regenerating}
                secondary
              />
              {regenError && <Text color="status-critical" size="small">{regenError}</Text>}
            </Box>
          )}
          {(editState.agent_recommendation ?? agent_recommendation) ? (
            <Box background="background-front" pad="medium" round="small" className="markdown-body">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {editState.agent_recommendation ?? agent_recommendation}
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
              columns={editMode ? editableColumns(SIGNAL_COLUMNS, 'signals', editState.signals ?? signals ?? [], onEditChange) : SIGNAL_COLUMNS}
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
              columns={editMode ? editableColumns(INTERPRETED_COLUMNS, 'interpreted_signals', editState.interpreted_signals ?? interpreted_signals ?? [], onEditChange) : INTERPRETED_COLUMNS}
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
              columns={editMode ? editableColumns(PRIORITY_COLUMNS, 'priority_matrix', editState.priority_matrix ?? priority_matrix ?? [], onEditChange) : PRIORITY_COLUMNS}
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

      <Tab title="Source Input">
        <Box pad="medium" overflow="auto">
          {voc_data ? (
            <Box background="background-front" pad="medium" round="small">
              <pre style={{ fontSize: '13px', whiteSpace: 'pre-wrap', fontFamily: 'inherit' }}>
                {voc_data}
              </pre>
            </Box>
          ) : (
            <Text color="text-weak">No source input recorded.</Text>
          )}
        </Box>
      </Tab>
    </StepCard>
  );
};

export default Step1SignalScan;
