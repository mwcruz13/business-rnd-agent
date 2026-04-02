import { useState, useCallback } from 'react';
import { Box, Text, Button } from 'grommet';
import { Filter } from 'grommet-icons';
import ExperimentCard from './ExperimentCard.jsx';
import { updateExperimentCard } from '../api/workflowApi.js';

const FILTER_OPTIONS = [
  { label: 'All', value: 'all' },
  { label: 'Planned', value: 'planned' },
  { label: 'Running', value: 'running' },
  { label: 'Completed', value: 'decision_made' },
];

const ExperimentCardDeck = ({ cards, sessionId, onCardUpdated }) => {
  const [expandedId, setExpandedId] = useState(cards?.[0]?.id || null);
  const [filter, setFilter] = useState('all');
  const [savingId, setSavingId] = useState(null);

  const handleToggle = useCallback((cardId) => {
    setExpandedId((prev) => (prev === cardId ? null : cardId));
  }, []);

  const handleSave = useCallback(async (cardId, updates) => {
    if (!sessionId) return;
    setSavingId(cardId);
    try {
      const updated = await updateExperimentCard(sessionId, cardId, updates);
      if (onCardUpdated) onCardUpdated(cardId, updated);
    } catch (err) {
      console.error('Failed to save experiment card:', err);
    } finally {
      setSavingId(null);
    }
  }, [sessionId, onCardUpdated]);

  if (!cards || cards.length === 0) {
    return <Text color="text-weak">No experiment cards available.</Text>;
  }

  const filtered = filter === 'all'
    ? cards
    : filter === 'decision_made'
      ? cards.filter((c) => c.status === 'decision_made' || c.status === 'evidence_captured')
      : cards.filter((c) => c.status === filter);

  const completedCount = cards.filter(
    (c) => c.status === 'decision_made' || c.status === 'evidence_captured',
  ).length;

  return (
    <Box gap="medium" fill>
      {/* ---- Toolbar: filter + progress ---- */}
      <Box
        direction="row"
        align="center"
        justify="between"
        pad={{ horizontal: 'small', vertical: 'xsmall' }}
        flex={false}
      >
        <Box direction="row" gap="xsmall" align="center">
          <Filter size="small" color="text-weak" />
          {FILTER_OPTIONS.map((opt) => (
            <Button
              key={opt.value}
              label={opt.label}
              size="small"
              primary={filter === opt.value}
              onClick={() => setFilter(opt.value)}
              style={{ fontWeight: filter === opt.value ? 700 : 400 }}
            />
          ))}
        </Box>
        <Text size="small" color="text-weak">
          {completedCount} of {cards.length} experiments completed
        </Text>
      </Box>

      {/* ---- Card deck ---- */}
      <Box
        direction="row"
        gap="small"
        wrap
        overflow={{ horizontal: 'auto' }}
        pad={{ bottom: 'small' }}
      >
        {filtered.map((card) => (
          <ExperimentCard
            key={card.id}
            card={card}
            expanded={expandedId === card.id}
            onToggle={() => handleToggle(card.id)}
            onSave={handleSave}
            saving={savingId === card.id}
          />
        ))}
      </Box>

      {filtered.length === 0 && (
        <Box pad="medium" align="center">
          <Text color="text-weak">No experiments match the current filter.</Text>
        </Box>
      )}
    </Box>
  );
};

export default ExperimentCardDeck;
