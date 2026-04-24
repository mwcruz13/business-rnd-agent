import { useEffect, useState } from 'react';
import { Box, Text, TextArea, Tab, CheckBox, DataTable, Heading } from 'grommet';
import { Star } from 'grommet-icons';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import StepCard from '../components/StepCard.jsx';

/**
 * Renders a single VP Alternative card (collapsed/expanded).
 */
const VPAlternativeCard = ({ alt, index, isSelected, onToggle, editMode, isRecommended }) => (
  <Box
    border={{ color: isSelected ? 'brand' : 'border', size: isSelected ? '2px' : '1px' }}
    round="small"
    pad="medium"
    margin={{ bottom: 'small' }}
    background={isSelected ? 'light-1' : 'background-front'}
  >
    <Box direction="row" align="center" gap="small">
      {editMode && (
        <CheckBox
          checked={isSelected}
          onChange={() => onToggle(index)}
        />
      )}
      <Heading level={4} margin="none">
        {index + 1}. {alt.name}
      </Heading>
      {isRecommended && <Star size="small" color="status-warning" />}
    </Box>
    <Box margin={{ top: 'small' }} gap="xsmall">
      <Text size="small"><strong>Pattern Flavor:</strong> {alt.pattern_flavor_applied}</Text>
      <Text size="small"><strong>Target Segment:</strong> {alt.target_segment}</Text>
      <Text size="small"><strong>Primary Job:</strong> {alt.primary_job_focus}</Text>
      <Text size="small"><strong>Context:</strong> {alt.context_scenario}</Text>
      <Text size="small"><strong>Rationale:</strong> {alt.strategic_rationale}</Text>
      {alt.ad_lib_prototype?.statement && (
        <Box background="light-2" pad="small" round="xsmall" margin={{ top: 'xsmall' }}>
          <Text size="small" style={{ fontStyle: 'italic' }}>{alt.ad_lib_prototype.statement}</Text>
        </Box>
      )}
      {alt.products_services?.length > 0 && (
        <Text size="small"><strong>Products/Services:</strong> {alt.products_services.map(p => p.product_service).join(', ')}</Text>
      )}
    </Box>
  </Box>
);

/**
 * Step 5 — VP Portfolio: Ideation, Scoring & Selection.
 *
 * - At checkpoint_5a: shows VP alternatives for review
 * - At checkpoint_5b: shows scoring + selection checkboxes (edit mode)
 * - After completion: shows final selected VPs and combined canvas
 */
const Step5ValueProposition = ({ runState, editMode, editState, onEditChange, sessionId }) => {
  if (!runState) return <Text color="text-weak">Waiting for workflow to start…</Text>;

  const {
    value_proposition_canvas,
    fit_assessment,
    vp_alternatives,
    vp_rankings,
    vp_recommended,
    vp_scoring_summary,
    selected_vp_indices,
    pending_checkpoint,
  } = runState;

  // Track selection state for checkpoint_5b editing
  const [localSelection, setLocalSelection] = useState([]);

  useEffect(() => {
    // Initialize local selection from LLM recommendations or existing selection
    if (selected_vp_indices?.length) {
      setLocalSelection(selected_vp_indices);
    } else if (vp_recommended?.length) {
      setLocalSelection(vp_recommended);
    }
  }, [selected_vp_indices, vp_recommended]);

  // When entering edit mode at checkpoint_5b, seed editState with current selection
  useEffect(() => {
    if (editMode && pending_checkpoint === 'checkpoint_5b' && Object.keys(editState).length === 0) {
      const selection = selected_vp_indices?.length ? selected_vp_indices : (vp_recommended || []);
      onEditChange({ selected_vp_indices: selection });
      setLocalSelection(selection);
    } else if (editMode && pending_checkpoint !== 'checkpoint_5b' && Object.keys(editState).length === 0) {
      // Fallback for non-5b edit mode (e.g., editing the canvas text)
      onEditChange({
        value_proposition_canvas: value_proposition_canvas || '',
        fit_assessment: fit_assessment || '',
      });
    }
  }, [editMode]);

  const handleToggle = (index) => {
    const updated = localSelection.includes(index)
      ? localSelection.filter(i => i !== index)
      : [...localSelection, index].sort((a, b) => a - b);
    setLocalSelection(updated);
    onEditChange({ ...editState, selected_vp_indices: updated });
  };

  // No VP data at all — step hasn't run
  if (!vp_alternatives?.length && !value_proposition_canvas) {
    return <Text color="text-weak">Step 5 has not run yet.</Text>;
  }

  const handleImport = (fields) => onEditChange({ ...editState, ...fields });
  const isAt5b = pending_checkpoint === 'checkpoint_5b';
  const isAt5a = pending_checkpoint === 'checkpoint_5a';

  return (
    <StepCard stepIndex={4} stepLabel="Value Proposition Portfolio" runState={runState} sessionId={sessionId} onImport={handleImport}>
      {/* Tab: VP Alternatives (always shown when available) */}
      <Tab title="VP Alternatives">
        <Box pad="medium" overflow="auto" gap="small">
          {vp_alternatives?.length ? (
            <>
              {isAt5b && (
                <Box background="status-warning" pad="small" round="xsmall" margin={{ bottom: 'small' }}>
                  <Text size="small" weight="bold">
                    Select which VP alternatives to carry forward.
                    {!editMode && ' Click "Edit" to change the selection.'}
                    {' '}⭐ = LLM recommended.
                  </Text>
                </Box>
              )}
              {isAt5a && (
                <Box background="light-3" pad="small" round="xsmall" margin={{ bottom: 'small' }}>
                  <Text size="small">
                    Review the ideated VP alternatives below. Approve to proceed to scoring.
                  </Text>
                </Box>
              )}
              {vp_alternatives.map((alt, i) => (
                <VPAlternativeCard
                  key={i}
                  alt={alt}
                  index={i}
                  isSelected={(editMode && isAt5b) ? localSelection.includes(i) : (selected_vp_indices || []).includes(i)}
                  isRecommended={(vp_recommended || []).includes(i)}
                  onToggle={handleToggle}
                  editMode={editMode && isAt5b}
                />
              ))}
            </>
          ) : (
            <Text color="text-weak">VP ideation has not completed yet.</Text>
          )}
        </Box>
      </Tab>

      {/* Tab: Scoring (shown after 5b runs) */}
      {vp_rankings?.length > 0 && (
        <Tab title="Scoring">
          <Box pad="medium" overflow="auto">
            <DataTable
              columns={[
                { property: 'rank', header: '#', size: 'xxsmall' },
                { property: 'name', header: 'Alternative' },
                { property: 'coverage_score', header: 'Coverage', size: 'xsmall' },
                { property: 'evidence_score', header: 'Evidence', size: 'xsmall' },
                { property: 'pattern_fit_score', header: 'Pattern Fit', size: 'xsmall' },
                { property: 'differentiation_score', header: 'Differentiation', size: 'xsmall' },
                { property: 'testability_score', header: 'Testability', size: 'xsmall' },
                { property: 'overall_recommendation', header: 'Recommendation' },
              ]}
              data={vp_rankings.map((r, i) => ({
                rank: i + 1,
                name: r.alternative_name + ((vp_recommended || []).includes(i) ? ' ⭐' : ''),
                coverage_score: r.coverage_score,
                evidence_score: r.evidence_score,
                pattern_fit_score: r.pattern_fit_score,
                differentiation_score: r.differentiation_score,
                testability_score: r.testability_score,
                overall_recommendation: r.overall_recommendation,
              }))}
              size="small"
            />
            {vp_scoring_summary && (
              <Box margin={{ top: 'medium' }} background="background-front" pad="medium" round="small" className="markdown-body">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{vp_scoring_summary}</ReactMarkdown>
              </Box>
            )}
          </Box>
        </Tab>
      )}

      {/* Tab: Combined VP Canvas (backward compatible view) */}
      <Tab title="VP Canvas">
        <Box pad="medium" overflow="auto">
          {editMode && !isAt5b ? (
            <TextArea
              value={editState.value_proposition_canvas ?? value_proposition_canvas ?? ''}
              onChange={(e) => onEditChange({ ...editState, value_proposition_canvas: e.target.value })}
              rows={14}
              resize="vertical"
            />
          ) : value_proposition_canvas ? (
            <Box background="background-front" pad="medium" round="small" className="markdown-body">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {value_proposition_canvas}
              </ReactMarkdown>
            </Box>
          ) : (
            <Text color="text-weak">VP canvas will be generated after ideation completes.</Text>
          )}
        </Box>
      </Tab>

      {/* Tab: Fit Assessment (shown when available — from step 6) */}
      {fit_assessment && (
        <Tab title="Fit Assessment">
          <Box pad="medium" overflow="auto">
            {editMode && !isAt5b ? (
              <TextArea
                value={editState.fit_assessment ?? fit_assessment ?? ''}
                onChange={(e) => onEditChange({ ...editState, fit_assessment: e.target.value })}
                rows={6}
                resize="vertical"
              />
            ) : (
              <Box background="background-front" pad="medium" round="small" className="markdown-body">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {fit_assessment}
                </ReactMarkdown>
              </Box>
            )}
          </Box>
        </Tab>
      )}
    </StepCard>
  );
};

export default Step5ValueProposition;
