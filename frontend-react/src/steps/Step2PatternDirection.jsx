import { useEffect } from 'react';
import { Box, Text, Tag, Select, TextArea, CheckBox } from 'grommet';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const INVENT_PATTERNS = [
  'Market Explorers',
  'Gravity Creators',
  'Channel Kings',
  'Resource Castles',
  'Activity Differentiators',
  'Scalers',
  'Partner Builders',
  'Cost Differentiators',
  'Revenue Differentiators',
  'Profit-Formula Disruptors',
];

const SHIFT_PATTERNS = [
  'Product to Recurring Service',
  'Low Touch to High Touch',
  'From Reselling to Platform',
  'Free to Enterprise Model',
  'B2B to B2B2C',
];

const Step2PatternDirection = ({ runState, editMode, editState, onEditChange }) => {
  if (!runState) return <Text color="text-weak">Waiting for workflow to start…</Text>;

  const { pattern_direction, selected_patterns, pattern_rationale } = runState;

  useEffect(() => {
    if (editMode && Object.keys(editState).length === 0) {
      onEditChange({
        pattern_direction: pattern_direction || '',
        selected_patterns: selected_patterns || [],
        pattern_rationale: pattern_rationale || '',
      });
    }
  }, [editMode]);

  if (!pattern_direction && !pattern_rationale) {
    return <Text color="text-weak">Step 2 has not run yet.</Text>;
  }

  if (editMode) {
    const currentDirection = editState.pattern_direction ?? pattern_direction ?? '';
    const currentPatterns = editState.selected_patterns ?? selected_patterns ?? [];
    const availablePatterns = currentDirection === 'invent' ? INVENT_PATTERNS : SHIFT_PATTERNS;

    const handleTogglePattern = (pattern) => {
      const updated = currentPatterns.includes(pattern)
        ? currentPatterns.filter((p) => p !== pattern)
        : [...currentPatterns, pattern];
      onEditChange({ ...editState, selected_patterns: updated });
    };

    return (
      <Box gap="medium">
        <Box gap="xsmall">
          <Text weight="bold" size="small">Pattern Direction *</Text>
          <Select
            options={['invent', 'shift']}
            value={currentDirection}
            onChange={({ option }) =>
              onEditChange({ ...editState, pattern_direction: option, selected_patterns: [] })
            }
          />
        </Box>

        {currentDirection && (
          <Box gap="xsmall">
            <Text weight="bold" size="small">
              Selected Patterns ({currentDirection === 'invent' ? 'Invent' : 'Shift'})
            </Text>
            <Box background="background-front" pad="medium" round="small" gap="small">
              {availablePatterns.map((p) => (
                <CheckBox
                  key={p}
                  label={p}
                  checked={currentPatterns.includes(p)}
                  onChange={() => handleTogglePattern(p)}
                />
              ))}
            </Box>
          </Box>
        )}

        <Box gap="xsmall">
          <Text weight="bold" size="small">Rationale</Text>
          <TextArea
            value={editState.pattern_rationale ?? pattern_rationale ?? ''}
            onChange={(e) => onEditChange({ ...editState, pattern_rationale: e.target.value })}
            rows={4}
            resize="vertical"
          />
        </Box>
      </Box>
    );
  }

  // Read-only view
  return (
    <Box gap="medium">
      {pattern_direction && (
        <Box gap="xsmall">
          <Text weight="bold" size="small" color="text-weak">Pattern Direction</Text>
          <Box background="background-front" pad="medium" round="small">
            <Text size="large" weight="bold" color="brand">
              {pattern_direction.toUpperCase()}
            </Text>
          </Box>
        </Box>
      )}

      {pattern_rationale && (
        <Box gap="xsmall">
          <Text weight="bold" size="small" color="text-weak">Rationale</Text>
          <Box background="background-front" pad="medium" round="small">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {pattern_rationale}
            </ReactMarkdown>
          </Box>
        </Box>
      )}

      {selected_patterns && selected_patterns.length > 0 && (
        <Box gap="xsmall">
          <Text weight="bold" size="small" color="text-weak">Selected Patterns</Text>
          <Box direction="row" gap="small" wrap>
            {selected_patterns.map((p) => (
              <Tag key={p} value={p} />
            ))}
          </Box>
        </Box>
      )}
    </Box>
  );
};

export default Step2PatternDirection;
