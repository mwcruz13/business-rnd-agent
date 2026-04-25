import { useState, useEffect } from 'react';
import {
  Box, Button, DataTable, Heading, Layer, Tab, Tabs, Tag, Text,
  TextInput, Notification, Spinner,
} from 'grommet';
import { Close, Edit, Checkmark } from 'grommet-icons';
import { getPortfolioDetail, updatePortfolio } from '../api/workflowApi.js';

// --- Quadrant badge colours ---
const QUADRANT_COLORS = {
  'Test first': 'status-critical',
  Monitor: 'status-warning',
  Deprioritize: 'status-ok',
  'Safe zone': 'status-ok',
};

const EVIDENCE_COLORS = {
  None: 'status-critical',
  Weak: 'status-warning',
  Medium: 'status-ok',
};

const ProjectDetailPanel = ({ sessionId, onClose, onUpdate }) => {
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState({});
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!sessionId) return;
    setLoading(true);
    setError(null);
    getPortfolioDetail(sessionId)
      .then((data) => {
        setDetail(data);
        setForm({
          initiative_name: data.initiative_name || '',
          expected_revenue: data.expected_revenue || '',
          testing_cost: data.testing_cost || '',
          notes: data.notes || '',
        });
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [sessionId]);

  const handleSave = async () => {
    setSaving(true);
    try {
      await updatePortfolio(sessionId, form);
      setEditing(false);
      // Refresh detail
      const data = await getPortfolioDetail(sessionId);
      setDetail(data);
      if (onUpdate) onUpdate();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  if (!sessionId) return null;

  return (
    <Layer
      position="right"
      full="vertical"
      modal
      onClickOutside={onClose}
      onEsc={onClose}
    >
      <Box
        width={{ min: '420px', max: '560px' }}
        fill="vertical"
        overflow="auto"
        pad="medium"
        gap="medium"
      >
        {/* Header */}
        <Box direction="row" justify="between" align="center" flex={false}>
          <Heading level={3} margin="none" truncate>
            {detail?.initiative_name || 'Loading…'}
          </Heading>
          <Button icon={<Close />} onClick={onClose} plain />
        </Box>

        {error && (
          <Notification
            status="critical"
            message={error}
            onClose={() => setError(null)}
          />
        )}

        {loading ? (
          <Box align="center" pad="large"><Spinner size="medium" /></Box>
        ) : detail ? (
          <>
            {/* Summary badges */}
            <Box direction="row" gap="small" wrap flex={false}>
              <Tag size="small" value={detail.status} />
              <Tag size="small" value={detail.pattern_direction || 'unknown'} />
              <Tag size="small" value={`Step: ${detail.current_step}`} />
              <Tag size="small" value={`${detail.days_running}d running`} />
            </Box>

            {/* Score indicators */}
            <Box direction="row" gap="medium" flex={false}>
              <Box
                background="light-2"
                pad="small"
                round="small"
                align="center"
                width="small"
              >
                <Text size="xsmall" color="text-weak">Risk Score</Text>
                <Text size="xlarge" weight="bold" color={detail.risk_score > 60 ? 'status-critical' : detail.risk_score > 40 ? 'status-warning' : 'status-ok'}>
                  {detail.risk_score}
                </Text>
              </Box>
              <Box
                background="light-2"
                pad="small"
                round="small"
                align="center"
                width="small"
              >
                <Text size="xsmall" color="text-weak">Return Score</Text>
                <Text size="xlarge" weight="bold" color={detail.return_score > 60 ? 'status-ok' : detail.return_score > 40 ? 'status-warning' : 'status-critical'}>
                  {detail.return_score}
                </Text>
              </Box>
              <Box
                background="light-2"
                pad="small"
                round="small"
                align="center"
                width="small"
              >
                <Text size="xsmall" color="text-weak">Hypotheses</Text>
                <Text size="xlarge" weight="bold">{detail.assumption_count}</Text>
              </Box>
              <Box
                background="light-2"
                pad="small"
                round="small"
                align="center"
                width="small"
              >
                <Text size="xsmall" color="text-weak">Experiments</Text>
                <Text size="xlarge" weight="bold">{detail.experiment_count}</Text>
              </Box>
            </Box>

            {/* Tabs */}
            <Tabs flex>
              {/* Hypothesis Log */}
              <Tab title="Hypothesis Log">
                <Box pad={{ vertical: 'small' }} overflow="auto">
                  {detail.hypotheses && detail.hypotheses.length > 0 ? (
                    <DataTable
                      columns={[
                        {
                          property: 'assumption',
                          header: 'Assumption',
                          size: '50%',
                          render: (d) => <Text size="xsmall">{d.assumption}</Text>,
                        },
                        {
                          property: 'category',
                          header: 'Category',
                          render: (d) => (
                            <Tag size="small" value={d.category} />
                          ),
                        },
                        {
                          property: 'quadrant',
                          header: 'Risk',
                          render: (d) => (
                            <Text size="xsmall" color={QUADRANT_COLORS[d.quadrant] || 'text'}
                              weight="bold">
                              {d.quadrant}
                            </Text>
                          ),
                        },
                        {
                          property: 'evidence_strength',
                          header: 'Evidence',
                          render: (d) => (
                            <Text size="xsmall" color={EVIDENCE_COLORS[d.evidence_strength] || 'text'}
                              weight="bold">
                              {d.evidence_strength}
                            </Text>
                          ),
                        },
                      ]}
                      data={detail.hypotheses}
                      size="small"
                    />
                  ) : (
                    <Text size="small" color="text-weak">
                      No hypotheses yet — complete Step 7 (Risk Map) to generate DVF assumptions.
                    </Text>
                  )}
                </Box>
              </Tab>

              {/* Experiment Log */}
              <Tab title="Experiment Log">
                <Box pad={{ vertical: 'small' }} overflow="auto">
                  {detail.experiments && detail.experiments.length > 0 ? (
                    <DataTable
                      columns={[
                        {
                          property: 'name',
                          header: 'Experiment',
                          size: '40%',
                          render: (d) => <Text size="xsmall">{d.name}</Text>,
                        },
                        {
                          property: 'type',
                          header: 'Type',
                          render: (d) => <Text size="xsmall">{d.type}</Text>,
                        },
                        {
                          property: 'cost_estimate',
                          header: 'Cost',
                          render: (d) => <Text size="xsmall">{d.cost_estimate || '—'}</Text>,
                        },
                        {
                          property: 'duration',
                          header: 'Duration',
                          render: (d) => <Text size="xsmall">{d.duration || '—'}</Text>,
                        },
                      ]}
                      data={detail.experiments}
                      size="small"
                    />
                  ) : (
                    <Text size="small" color="text-weak">
                      No experiments yet — complete Step 8 to generate experiment cards.
                    </Text>
                  )}
                </Box>
              </Tab>

              {/* Learning Log */}
              <Tab title="Learning Log">
                <Box pad={{ vertical: 'small' }} gap="xsmall" overflow="auto">
                  {detail.completed_steps && detail.completed_steps.length > 0 ? (
                    detail.completed_steps.map((step, i) => (
                      <Box
                        key={i}
                        direction="row"
                        align="center"
                        gap="small"
                        pad={{ vertical: 'xxsmall' }}
                      >
                        <Box
                          width="24px"
                          height="24px"
                          round="full"
                          background="brand"
                          align="center"
                          justify="center"
                          flex={false}
                        >
                          <Text size="xsmall" color="white" weight="bold">
                            {i + 1}
                          </Text>
                        </Box>
                        <Text size="small">{step}</Text>
                      </Box>
                    ))
                  ) : (
                    <Text size="small" color="text-weak">No steps completed yet.</Text>
                  )}
                </Box>
              </Tab>

              {/* Actions (edit portfolio metadata) */}
              <Tab title="Actions">
                <Box pad={{ vertical: 'small' }} gap="small">
                  {!editing ? (
                    <>
                      <Box gap="xsmall">
                        <Text size="small" weight="bold">Initiative Name</Text>
                        <Text size="small">{detail.initiative_name || '—'}</Text>
                      </Box>
                      <Box gap="xsmall">
                        <Text size="small" weight="bold">Expected Revenue</Text>
                        <Text size="small">{detail.expected_revenue || '—'}</Text>
                      </Box>
                      <Box gap="xsmall">
                        <Text size="small" weight="bold">Testing Cost</Text>
                        <Text size="small">{detail.testing_cost || '—'}</Text>
                      </Box>
                      <Box gap="xsmall">
                        <Text size="small" weight="bold">Notes</Text>
                        <Text size="small">{detail.notes || '—'}</Text>
                      </Box>
                      <Button
                        secondary
                        label="Edit Metadata"
                        icon={<Edit size="small" />}
                        onClick={() => setEditing(true)}
                      />
                    </>
                  ) : (
                    <>
                      <Box gap="xsmall">
                        <Text size="small" weight="bold">Initiative Name</Text>
                        <TextInput
                          size="small"
                          value={form.initiative_name}
                          onChange={(e) => setForm({ ...form, initiative_name: e.target.value })}
                          placeholder="e.g. HBM Supply Chain Transformation"
                        />
                      </Box>
                      <Box gap="xsmall">
                        <Text size="small" weight="bold">Expected Revenue</Text>
                        <TextInput
                          size="small"
                          value={form.expected_revenue}
                          onChange={(e) => setForm({ ...form, expected_revenue: e.target.value })}
                          placeholder="e.g. $750 million"
                        />
                      </Box>
                      <Box gap="xsmall">
                        <Text size="small" weight="bold">Testing Cost</Text>
                        <TextInput
                          size="small"
                          value={form.testing_cost}
                          onChange={(e) => setForm({ ...form, testing_cost: e.target.value })}
                          placeholder="e.g. $5,800"
                        />
                      </Box>
                      <Box gap="xsmall">
                        <Text size="small" weight="bold">Notes</Text>
                        <TextInput
                          size="small"
                          value={form.notes}
                          onChange={(e) => setForm({ ...form, notes: e.target.value })}
                          placeholder="Add context for leadership…"
                        />
                      </Box>
                      <Box direction="row" gap="small">
                        <Button
                          primary
                          label={saving ? 'Saving…' : 'Save'}
                          icon={<Checkmark size="small" />}
                          onClick={handleSave}
                          disabled={saving}
                        />
                        <Button
                          secondary
                          label="Cancel"
                          onClick={() => setEditing(false)}
                        />
                      </Box>
                    </>
                  )}
                </Box>
              </Tab>
            </Tabs>
          </>
        ) : (
          <Text color="text-weak">No data available.</Text>
        )}
      </Box>
    </Layer>
  );
};

export default ProjectDetailPanel;
