import { useEffect, useCallback } from 'react';
import { Box, Text, TextArea, Tab } from 'grommet';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import StepCard from '../components/StepCard.jsx';
import ExperimentCardDeck from '../components/ExperimentCardDeck.jsx';

const Step8ExperimentPlan = ({ runState, editMode, editState, onEditChange, sessionId }) => {
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
            <Box background="background-front" pad="medium" round="small">
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
            <Box background="background-front" pad="medium" round="small">
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
            <Box background="background-front" pad="medium" round="small">
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
