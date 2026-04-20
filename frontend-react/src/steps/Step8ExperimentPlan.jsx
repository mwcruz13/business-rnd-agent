import { useState, useEffect, useCallback } from 'react';
import { Box, Text, TextArea, Tab, Button, Spinner } from 'grommet';
import { DocumentDownload, DocumentPpt } from 'grommet-icons';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import StepCard from '../components/StepCard.jsx';
import ExperimentCardDeck from '../components/ExperimentCardDeck.jsx';
import { downloadExport } from '../api/workflowApi.js';

const Step8ExperimentPlan = ({ runState, editMode, editState, onEditChange, sessionId }) => {
  const [exporting, setExporting] = useState(null); // 'md' | 'pptx' | null

  if (!runState) return <Text color="text-weak">Waiting for workflow to start…</Text>;

  const {
    experiment_selections, experiment_plans, experiment_worksheets, experiment_cards,
  } = runState;

  useEffect(() => {
    if (editMode && Object.keys(editState).length === 0) {
      onEditChange({
        experiment_selections: experiment_selections || '',
        experiment_plans: experiment_plans || '',
        experiment_worksheets: experiment_worksheets || '',
      });
    }
  }, [editMode]);

  if (!experiment_selections && !experiment_plans && (!experiment_cards || experiment_cards.length === 0)) {
    return <Text color="text-weak">Step 8 has not run yet.</Text>;
  }

  const handleImport = (fields) => onEditChange({ ...editState, ...fields });

  const handleExport = async (format) => {
    setExporting(format);
    try { await downloadExport(sessionId, format); }
    catch (err) { console.error('Export failed:', err); }
    finally { setExporting(null); }
  };

  const handleCardUpdated = useCallback((cardId, updatedCard) => {
    // Update the local runState experiment_cards optimistically
    if (!runState.experiment_cards) return;
    const idx = runState.experiment_cards.findIndex((c) => c.id === cardId);
    if (idx >= 0) {
      runState.experiment_cards[idx] = updatedCard;
    }
  }, [runState]);

  return (
    <StepCard stepIndex={7} stepLabel="Experiment Plan" runState={runState} sessionId={sessionId} onImport={handleImport}>
      {runState?.run_status === 'completed' && (
        <Box direction="row" gap="small" pad={{ vertical: 'small' }} align="center">
          <Text weight="bold" size="small">Export Full Report:</Text>
          <Button
            label={exporting === 'md' ? 'Exporting…' : 'Markdown'}
            icon={exporting === 'md' ? <Spinner size="xsmall" /> : <DocumentDownload size="small" />}
            size="small"
            secondary
            disabled={!!exporting}
            onClick={() => handleExport('md')}
          />
          <Button
            label={exporting === 'pptx' ? 'Exporting…' : 'PowerPoint'}
            icon={exporting === 'pptx' ? <Spinner size="xsmall" /> : <DocumentPpt size="small" />}
            size="small"
            secondary
            disabled={!!exporting}
            onClick={() => handleExport('pptx')}
          />
        </Box>
      )}
      {/* Primary tab: interactive cards */}
      <Tab title="Experiment Cards">
        <Box pad="medium" overflow="auto">
          {experiment_cards && experiment_cards.length > 0 ? (
            <ExperimentCardDeck
              cards={experiment_cards}
              sessionId={sessionId}
              onCardUpdated={handleCardUpdated}
            />
          ) : (
            <Text color="text-weak">No experiment cards yet. Check the Selections tab for the raw output.</Text>
          )}
        </Box>
      </Tab>

      <Tab title="Selections">
        <Box pad="medium" overflow="auto">
          {editMode ? (
            <TextArea
              value={editState.experiment_selections ?? experiment_selections ?? ''}
              onChange={(e) => onEditChange({ ...editState, experiment_selections: e.target.value })}
              rows={8}
              resize="vertical"
            />
          ) : experiment_selections ? (
            <Box background="background-front" pad="medium" round="small" className="markdown-body">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {experiment_selections}
              </ReactMarkdown>
            </Box>
          ) : (
            <Text color="text-weak">No experiment selections yet.</Text>
          )}
        </Box>
      </Tab>

      <Tab title="Plans">
        <Box pad="medium" overflow="auto">
          {editMode ? (
            <TextArea
              value={editState.experiment_plans ?? experiment_plans ?? ''}
              onChange={(e) => onEditChange({ ...editState, experiment_plans: e.target.value })}
              rows={10}
              resize="vertical"
            />
          ) : experiment_plans ? (
            <Box background="background-front" pad="medium" round="small" className="markdown-body">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {experiment_plans}
              </ReactMarkdown>
            </Box>
          ) : (
            <Text color="text-weak">No experiment plans yet.</Text>
          )}
        </Box>
      </Tab>

      <Tab title="Worksheets">
        <Box pad="medium" overflow="auto">
          {editMode ? (
            <TextArea
              value={editState.experiment_worksheets ?? experiment_worksheets ?? ''}
              onChange={(e) => onEditChange({ ...editState, experiment_worksheets: e.target.value })}
              rows={10}
              resize="vertical"
            />
          ) : experiment_worksheets ? (
            <Box background="background-front" pad="medium" round="small" className="markdown-body">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {experiment_worksheets}
              </ReactMarkdown>
            </Box>
          ) : (
            <Text color="text-weak">No experiment worksheets yet.</Text>
          )}
        </Box>
      </Tab>
    </StepCard>
  );
};

export default Step8ExperimentPlan;
