import { useState } from 'react';
import {
  Box, Card, CardBody, CardHeader, Text, FormField,
  TextArea, Select, TextInput, Button, Collapsible, Grid,
} from 'grommet';
import { Expand, Contract, Save, StatusGood, InProgress, StatusCritical } from 'grommet-icons';

const CATEGORY_COLORS = {
  Desirability: { bg: '#E8F5E9', badge: '#388E3C', label: 'D' },
  Feasibility: { bg: '#E3F2FD', badge: '#1565C0', label: 'F' },
  Viability: { bg: '#FFF3E0', badge: '#E65100', label: 'V' },
};

const STRENGTH_COLORS = {
  Weak: '#FFB74D',
  Medium: '#64B5F6',
  Strong: '#81C784',
};

const STATUS_OPTIONS = [
  { label: 'Planned', value: 'planned' },
  { label: 'Running', value: 'running' },
  { label: 'Evidence Captured', value: 'evidence_captured' },
  { label: 'Decision Made', value: 'decision_made' },
];

const CONFIDENCE_OPTIONS = [
  { label: '—', value: '' },
  { label: 'Increased', value: 'increased' },
  { label: 'Decreased', value: 'decreased' },
  { label: 'Unchanged', value: 'unchanged' },
];

const DECISION_OPTIONS = [
  { label: '—', value: '' },
  { label: 'Continue to next test', value: 'continue' },
  { label: 'Refine and rerun', value: 'refine' },
  { label: 'Stop', value: 'stop' },
];

function StatusIcon({ status }) {
  if (status === 'decision_made') return <StatusGood color="status-ok" size="small" />;
  if (status === 'running' || status === 'evidence_captured')
    return <InProgress color="brand" size="small" />;
  return <Box width="14px" height="14px" round="full" border={{ color: 'border', size: 'small' }} />;
}

function CategoryBadge({ category }) {
  const cfg = CATEGORY_COLORS[category] || CATEGORY_COLORS.Desirability;
  return (
    <Box
      background={cfg.badge}
      round="xsmall"
      pad={{ horizontal: '8px', vertical: '2px' }}
      flex={false}
    >
      <Text size="xsmall" weight="bold" color="white">{cfg.label}</Text>
    </Box>
  );
}

function StrengthBadge({ strength }) {
  return (
    <Box
      background={STRENGTH_COLORS[strength] || STRENGTH_COLORS.Weak}
      round="xsmall"
      pad={{ horizontal: '8px', vertical: '2px' }}
      flex={false}
    >
      <Text size="xsmall" weight="bold">{strength}</Text>
    </Box>
  );
}

function StatusLabel({ value }) {
  const opt = STATUS_OPTIONS.find((o) => o.value === value);
  return opt?.label || value;
}

const ExperimentCard = ({ card, expanded, onToggle, onSave, saving }) => {
  const [localEvidence, setLocalEvidence] = useState(() => ({
    status: card.status || 'planned',
    owner: card.owner || '',
    date_started: card.date_started || '',
    date_completed: card.date_completed || '',
    what_customers_said: card.evidence?.what_customers_said || '',
    what_customers_did: card.evidence?.what_customers_did || '',
    what_surprised_us: card.evidence?.what_surprised_us || '',
    confidence_change: card.evidence?.confidence_change || '',
    decision: card.evidence?.decision || '',
    next_experiment: card.evidence?.next_experiment || '',
    notes: card.evidence?.notes || '',
  }));

  const [dirty, setDirty] = useState(false);

  const update = (field, value) => {
    setLocalEvidence((prev) => ({ ...prev, [field]: value }));
    setDirty(true);
  };

  const handleSave = () => {
    const payload = {
      status: localEvidence.status,
      owner: localEvidence.owner || null,
      date_started: localEvidence.date_started || null,
      date_completed: localEvidence.date_completed || null,
      evidence: {
        what_customers_said: localEvidence.what_customers_said || null,
        what_customers_did: localEvidence.what_customers_did || null,
        what_surprised_us: localEvidence.what_surprised_us || null,
        confidence_change: localEvidence.confidence_change || null,
        decision: localEvidence.decision || null,
        next_experiment: localEvidence.next_experiment || null,
        notes: localEvidence.notes || null,
      },
    };
    onSave(card.id, payload);
    setDirty(false);
  };

  const catCfg = CATEGORY_COLORS[card.category] || CATEGORY_COLORS.Desirability;

  return (
    <Card
      background="background-front"
      round="small"
      elevation="small"
      width={{ min: expanded ? '100%' : '320px', max: expanded ? '100%' : '360px' }}
      flex={expanded ? undefined : false}
      border={{ color: catCfg.badge, size: '2px', side: 'left' }}
    >
      {/* ---------- Summary header (always visible) ---------- */}
      <CardHeader
        pad={{ horizontal: 'small', vertical: 'small' }}
        background={catCfg.bg}
        onClick={onToggle}
        style={{ cursor: 'pointer' }}
        direction="row"
        align="center"
        gap="small"
      >
        <StatusIcon status={localEvidence.status} />
        <CategoryBadge category={card.category} />
        <StrengthBadge strength={card.evidence_strength} />
        <Box flex>
          <Text size="small" weight="bold" truncate>{card.card_name}</Text>
          <Text size="xsmall" color="text-weak" truncate>{card.assumption}</Text>
        </Box>
        <Box
          round="xsmall"
          pad={{ horizontal: '6px', vertical: '2px' }}
          background="background-contrast"
          flex={false}
        >
          <Text size="xsmall"><StatusLabel value={localEvidence.status} /></Text>
        </Box>
        {expanded ? <Contract size="small" /> : <Expand size="small" />}
      </CardHeader>

      {/* ---------- Expanded content ---------- */}
      <Collapsible open={expanded}>
        <CardBody pad="medium" gap="medium">
          {/* ---- Zone A: Hypothesis (read-only) ---- */}
          <Box gap="small">
            <Text size="small" weight="bold" color="text-strong">HYPOTHESIS</Text>
            <Box background="light-1" pad="small" round="xsmall">
              <Text size="small"><strong>Assumption:</strong> {card.assumption}</Text>
            </Box>
            <Grid columns={['1/2', '1/2']} gap="small">
              <Box>
                <Text size="xsmall" color="text-weak">What it tests</Text>
                <Text size="small">{card.what_it_tests}</Text>
              </Box>
              <Box>
                <Text size="xsmall" color="text-weak">Best used when</Text>
                <Text size="small">{card.best_used_when}</Text>
              </Box>
            </Grid>
            <Grid columns={['1/2', '1/2']} gap="small">
              <Box>
                <Text size="xsmall" color="text-weak">Primary metric</Text>
                <Text size="small">{card.primary_metric}</Text>
              </Box>
              <Box>
                <Text size="xsmall" color="text-weak">Sample size / Timebox</Text>
                <Text size="small">{card.sample_size} participants · {card.timebox}</Text>
              </Box>
            </Grid>
            <Grid columns={['1/3', '1/3', '1/3']} gap="small">
              <Box>
                <Text size="xsmall" color="status-ok">Success looks like</Text>
                <Text size="xsmall">{card.success_looks_like}</Text>
              </Box>
              <Box>
                <Text size="xsmall" color="status-critical">Failure looks like</Text>
                <Text size="xsmall">{card.failure_looks_like}</Text>
              </Box>
              <Box>
                <Text size="xsmall" color="status-warning">Ambiguous</Text>
                <Text size="xsmall">{card.ambiguous_looks_like}</Text>
              </Box>
            </Grid>

            {/* Evidence path */}
            {card.evidence_path && card.evidence_path.length > 1 && (
              <Box direction="row" gap="xsmall" align="center" wrap>
                <Text size="xsmall" color="text-weak">Path:</Text>
                {card.evidence_path.map((step, idx) => (
                  <Box key={step.step} direction="row" align="center" gap="xxsmall">
                    {idx > 0 && <Text size="xsmall" color="text-weak">→</Text>}
                    <Box
                      round="xsmall"
                      pad={{ horizontal: '6px', vertical: '1px' }}
                      background={STRENGTH_COLORS[step.evidence_strength]}
                    >
                      <Text size="xsmall">{step.card_name}</Text>
                    </Box>
                  </Box>
                ))}
              </Box>
            )}
          </Box>

          {/* ---- Separator ---- */}
          <Box border={{ side: 'top', color: 'border' }} />

          {/* ---- Zone B: Evidence (editable) ---- */}
          <Box gap="small">
            <Text size="small" weight="bold" color="text-strong">EVIDENCE</Text>

            <Grid columns={['1/3', '1/3', '1/3']} gap="small">
              <FormField label="Status" htmlFor={`status-${card.id}`}>
                <Select
                  id={`status-${card.id}`}
                  options={STATUS_OPTIONS}
                  labelKey="label"
                  valueKey={{ key: 'value', reduce: true }}
                  value={localEvidence.status}
                  onChange={({ value }) => update('status', value)}
                  size="small"
                />
              </FormField>
              <FormField label="Owner" htmlFor={`owner-${card.id}`}>
                <TextInput
                  id={`owner-${card.id}`}
                  value={localEvidence.owner}
                  onChange={(e) => update('owner', e.target.value)}
                  size="small"
                  placeholder="Who runs this"
                />
              </FormField>
              <FormField label="Date started" htmlFor={`date-start-${card.id}`}>
                <TextInput
                  id={`date-start-${card.id}`}
                  value={localEvidence.date_started}
                  onChange={(e) => update('date_started', e.target.value)}
                  size="small"
                  placeholder="YYYY-MM-DD"
                  type="date"
                />
              </FormField>
            </Grid>

            <FormField label="What customers said" htmlFor={`said-${card.id}`}>
              <TextArea
                id={`said-${card.id}`}
                value={localEvidence.what_customers_said}
                onChange={(e) => update('what_customers_said', e.target.value)}
                rows={3}
                resize="vertical"
                placeholder="Capture verbatim quotes and observations…"
              />
            </FormField>

            <FormField label="What customers did" htmlFor={`did-${card.id}`}>
              <TextArea
                id={`did-${card.id}`}
                value={localEvidence.what_customers_did}
                onChange={(e) => update('what_customers_did', e.target.value)}
                rows={3}
                resize="vertical"
                placeholder="Observable behaviors, actions taken or not taken…"
              />
            </FormField>

            <FormField label="What surprised us" htmlFor={`surprise-${card.id}`}>
              <TextArea
                id={`surprise-${card.id}`}
                value={localEvidence.what_surprised_us}
                onChange={(e) => update('what_surprised_us', e.target.value)}
                rows={2}
                resize="vertical"
                placeholder="Unexpected findings…"
              />
            </FormField>

            <Grid columns={['1/2', '1/2']} gap="small">
              <FormField label="Confidence change" htmlFor={`conf-${card.id}`}>
                <Select
                  id={`conf-${card.id}`}
                  options={CONFIDENCE_OPTIONS}
                  labelKey="label"
                  valueKey={{ key: 'value', reduce: true }}
                  value={localEvidence.confidence_change}
                  onChange={({ value }) => update('confidence_change', value)}
                  size="small"
                />
              </FormField>
              <FormField label="Decision" htmlFor={`dec-${card.id}`}>
                <Select
                  id={`dec-${card.id}`}
                  options={DECISION_OPTIONS}
                  labelKey="label"
                  valueKey={{ key: 'value', reduce: true }}
                  value={localEvidence.decision}
                  onChange={({ value }) => update('decision', value)}
                  size="small"
                />
              </FormField>
            </Grid>

            <FormField label="Next experiment" htmlFor={`next-${card.id}`}>
              <TextInput
                id={`next-${card.id}`}
                value={localEvidence.next_experiment}
                onChange={(e) => update('next_experiment', e.target.value)}
                size="small"
                placeholder={card.sequencing?.next_if_positive || 'Suggested next experiment'}
              />
            </FormField>

            <FormField label="Notes" htmlFor={`notes-${card.id}`}>
              <TextArea
                id={`notes-${card.id}`}
                value={localEvidence.notes}
                onChange={(e) => update('notes', e.target.value)}
                rows={2}
                resize="vertical"
                placeholder="Any additional context…"
              />
            </FormField>

            {/* Save button */}
            <Box direction="row" justify="end" gap="small">
              <Button
                primary
                label={saving ? 'Saving…' : 'Save Evidence'}
                icon={<Save size="small" />}
                size="small"
                disabled={!dirty || saving}
                onClick={handleSave}
              />
            </Box>
          </Box>
        </CardBody>
      </Collapsible>
    </Card>
  );
};

export default ExperimentCard;
