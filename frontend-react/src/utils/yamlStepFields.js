import yaml from 'js-yaml';
import { STEPS } from '../components/StepSidebar.jsx';

/**
 * Per-step YAML field configuration.
 * Each entry (indexed 0–7) lists the state fields that belong to that step,
 * used for YAML download/upload serialisation.
 */
export const STEP_YAML_FIELDS = [
  // Step 0 → Step 1 — Signal Scan
  [
    { key: 'agent_recommendation', label: 'Agent Recommendation', type: 'text' },
    { key: 'signals', label: 'Signals', type: 'json' },
    { key: 'interpreted_signals', label: 'Interpreted Signals', type: 'json' },
    { key: 'priority_matrix', label: 'Priority Matrix', type: 'json' },
    { key: 'coverage_gaps', label: 'Coverage Gaps', type: 'json' },
  ],
  // Step 1 → Step 2 — Pattern Direction
  [
    { key: 'pattern_direction', label: 'Pattern Direction', type: 'text' },
    { key: 'selected_patterns', label: 'Selected Patterns', type: 'json' },
    { key: 'pattern_rationale', label: 'Rationale', type: 'text' },
  ],
  // Step 2 → Step 3 — Customer Profile
  [
    { key: 'customer_profile', label: 'Customer Profile', type: 'text' },
    { key: 'empathy_gap_questions', label: 'Empathy Gap Questions', type: 'text' },
    { key: 'supplemental_voc', label: 'Supplemental VoC', type: 'text' },
  ],
  // Step 3 → Step 4 — Value Drivers
  [
    { key: 'value_driver_tree', label: 'Value Driver Tree', type: 'text' },
    { key: 'actionable_insights', label: 'Actionable Insights', type: 'text' },
  ],
  // Step 4 → Step 5 — Value Proposition
  [
    { key: 'value_proposition_canvas', label: 'VP Canvas', type: 'text' },
    { key: 'fit_assessment', label: 'Fit Assessment', type: 'text' },
  ],
  // Step 5 → Step 6 — Business Model
  [
    { key: 'business_model_canvas', label: 'Business Model Canvas', type: 'text' },
  ],
  // Step 6 → Step 7 — Risk Map
  [
    { key: 'assumptions', label: 'Assumptions & Risk Map', type: 'text' },
  ],
  // Step 7 → Step 8 — Experiment Plan
  [
    { key: 'experiment_selections', label: 'Experiment Selections', type: 'text' },
    { key: 'experiment_plans', label: 'Experiment Plans', type: 'text' },
    { key: 'experiment_worksheets', label: 'Experiment Worksheets', type: 'text' },
    { key: 'experiment_cards', label: 'Experiment Cards', type: 'json' },
  ],
];

/**
 * Serialize the relevant fields of a step's runState into a YAML string.
 */
export function stepFieldsToYaml(stepIndex, runState) {
  const fields = STEP_YAML_FIELDS[stepIndex];
  if (!fields || !runState) return '';

  const obj = {};
  for (const field of fields) {
    const value = runState[field.key];
    if (value !== undefined && value !== null && value !== '') {
      obj[field.key] = value;
    }
  }
  return yaml.dump(obj, { lineWidth: -1, noRefs: true });
}

/**
 * Parse a YAML string and return an object containing only the known
 * fields for the given step — safe for passing to onEditChange.
 */
export function yamlToStepFields(stepIndex, yamlString) {
  const fields = STEP_YAML_FIELDS[stepIndex];
  if (!fields) return {};

  const parsed = yaml.load(yamlString);
  if (!parsed || typeof parsed !== 'object') return {};

  const allowedKeys = new Set(fields.map((f) => f.key));
  const result = {};
  for (const [key, value] of Object.entries(parsed)) {
    if (allowedKeys.has(key)) {
      result[key] = value;
    }
  }
  return result;
}

/**
 * Build a download filename for a step's YAML export.
 */
export function stepYamlFilename(stepIndex, sessionId) {
  const label = STEPS[stepIndex]?.key || `step${stepIndex + 1}`;
  const shortId = sessionId ? `_${sessionId.slice(0, 8)}` : '';
  return `${label}${shortId}.yaml`;
}
