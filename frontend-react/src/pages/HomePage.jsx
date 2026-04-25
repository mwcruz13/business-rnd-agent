import { useState, useContext, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box, Button, Heading, Text, TextArea, TextInput, Select, FileInput,
  Card, CardBody, CardHeader, Notification, ResponsiveContext, DataTable,
} from 'grommet';
import { PlayFill, Document, Analytics } from 'grommet-icons';
import { useWorkflow } from '../context/WorkflowContext.jsx';

const ENTRY_STEPS = [
  { label: 'Step 1 – Signal Scan (default)', value: 1 },
  { label: 'Step 2 – Pattern Direction', value: 2 },
  { label: 'Step 3 – Customer Profile', value: 3 },
  { label: 'Step 4 – Value Drivers', value: 4 },
  { label: 'Step 5 – Value Proposition', value: 5 },
  { label: 'Step 6 – Business Model', value: 6 },
  { label: 'Step 7 – Risk Map', value: 7 },
  { label: 'Step 8 – Experiment Plan', value: 8 },
];

/**
 * Describes the upstream fields required when starting at a step > 1.
 * Each entry maps a field key to a user-facing label and placeholder.
 */
const UPSTREAM_FIELDS_BY_STEP = {
  2: [
    { key: 'signals', label: 'Signals JSON', placeholder: '[{"signal": "...", "source": "...", "strength": "strong"}]', type: 'json' },
  ],
  3: [
    { key: 'signals', label: 'Signals JSON', placeholder: '[{"signal": "...", "source": "...", "strength": "strong"}]', type: 'json' },
    { key: 'pattern_direction', label: 'Pattern Direction', placeholder: 'shift or invent', type: 'text' },
    { key: 'selected_patterns', label: 'Selected Patterns (comma-separated)', placeholder: 'Cost Differentiators, Market Explorers', type: 'csv' },
  ],
  4: [
    { key: 'signals', label: 'Signals JSON', placeholder: '[{"signal": "..."}]', type: 'json' },
    { key: 'pattern_direction', label: 'Pattern Direction', placeholder: 'shift or invent', type: 'text' },
    { key: 'selected_patterns', label: 'Selected Patterns (comma-separated)', placeholder: 'Cost Differentiators', type: 'csv' },
    { key: 'customer_profile', label: 'Customer Profile (markdown)', placeholder: '## Customer Profile\n...', type: 'textarea' },
  ],
  5: [
    { key: 'signals', label: 'Signals JSON', placeholder: '[{"signal": "..."}]', type: 'json' },
    { key: 'pattern_direction', label: 'Pattern Direction', placeholder: 'shift or invent', type: 'text' },
    { key: 'selected_patterns', label: 'Selected Patterns (comma-separated)', placeholder: 'Cost Differentiators', type: 'csv' },
    { key: 'customer_profile', label: 'Customer Profile', placeholder: '## Customer Profile\n...', type: 'textarea' },
    { key: 'value_driver_tree', label: 'Value Driver Tree', placeholder: '## Value Driver Tree\n...', type: 'textarea' },
    { key: 'actionable_insights', label: 'Actionable Insights', placeholder: '## Actionable Insights\n...', type: 'textarea' },
  ],
  6: [
    { key: 'signals', label: 'Signals JSON', placeholder: '[{"signal": "..."}]', type: 'json' },
    { key: 'pattern_direction', label: 'Pattern Direction', placeholder: 'shift or invent', type: 'text' },
    { key: 'selected_patterns', label: 'Selected Patterns (comma-separated)', placeholder: 'Cost Differentiators', type: 'csv' },
    { key: 'customer_profile', label: 'Customer Profile', placeholder: '...', type: 'textarea' },
    { key: 'value_driver_tree', label: 'Value Driver Tree', placeholder: '...', type: 'textarea' },
    { key: 'actionable_insights', label: 'Actionable Insights', placeholder: '...', type: 'textarea' },
    { key: 'vp_alternatives', label: 'VP Alternatives JSON', placeholder: '[{"name": "..."}]', type: 'json' },
    { key: 'selected_vp_indices', label: 'Selected VP Indices', placeholder: '[0, 1]', type: 'json' },
    { key: 'value_proposition_canvas', label: 'Value Proposition Canvas', placeholder: '...', type: 'textarea' },
    { key: 'fit_assessment', label: 'Fit Assessment', placeholder: '...', type: 'textarea' },
  ],
  7: [
    { key: 'signals', label: 'Signals JSON', placeholder: '[{"signal": "..."}]', type: 'json' },
    { key: 'pattern_direction', label: 'Pattern Direction', placeholder: 'shift or invent', type: 'text' },
    { key: 'selected_patterns', label: 'Selected Patterns (comma-separated)', placeholder: 'Cost Differentiators', type: 'csv' },
    { key: 'customer_profile', label: 'Customer Profile', placeholder: '...', type: 'textarea' },
    { key: 'value_driver_tree', label: 'Value Driver Tree', placeholder: '...', type: 'textarea' },
    { key: 'actionable_insights', label: 'Actionable Insights', placeholder: '...', type: 'textarea' },
    { key: 'vp_alternatives', label: 'VP Alternatives JSON', placeholder: '[{"name": "..."}]', type: 'json' },
    { key: 'selected_vp_indices', label: 'Selected VP Indices', placeholder: '[0, 1]', type: 'json' },
    { key: 'value_proposition_canvas', label: 'Value Proposition Canvas', placeholder: '...', type: 'textarea' },
    { key: 'fit_assessment', label: 'Fit Assessment', placeholder: '...', type: 'textarea' },
    { key: 'business_model_canvas', label: 'Business Model Canvas', placeholder: '...', type: 'textarea' },
  ],
  8: [
    { key: 'signals', label: 'Signals JSON', placeholder: '[{"signal": "..."}]', type: 'json' },
    { key: 'pattern_direction', label: 'Pattern Direction', placeholder: 'shift or invent', type: 'text' },
    { key: 'selected_patterns', label: 'Selected Patterns (comma-separated)', placeholder: 'Cost Differentiators', type: 'csv' },
    { key: 'customer_profile', label: 'Customer Profile', placeholder: '...', type: 'textarea' },
    { key: 'value_driver_tree', label: 'Value Driver Tree', placeholder: '...', type: 'textarea' },
    { key: 'actionable_insights', label: 'Actionable Insights', placeholder: '...', type: 'textarea' },
    { key: 'vp_alternatives', label: 'VP Alternatives JSON', placeholder: '[{"name": "..."}]', type: 'json' },
    { key: 'selected_vp_indices', label: 'Selected VP Indices', placeholder: '[0, 1]', type: 'json' },
    { key: 'value_proposition_canvas', label: 'Value Proposition Canvas', placeholder: '...', type: 'textarea' },
    { key: 'fit_assessment', label: 'Fit Assessment', placeholder: '...', type: 'textarea' },
    { key: 'business_model_canvas', label: 'Business Model Canvas', placeholder: '...', type: 'textarea' },
    { key: 'assumptions', label: 'Assumptions', placeholder: '...', type: 'textarea' },
    { key: 'experiment_selections', label: 'Experiment Selections', placeholder: '...', type: 'textarea' },
  ],
};

/**
 * Parse a raw form value into the shape the backend expects.
 */
function parseFieldValue(rawValue, type) {
  const trimmed = (rawValue || '').trim();
  if (!trimmed) return undefined;
  if (type === 'json') return JSON.parse(trimmed);
  if (type === 'csv') return trimmed.split(',').map((s) => s.trim()).filter(Boolean);
  return trimmed;
}

const HomePage = () => {
  const navigate = useNavigate();
  const { startWorkflow, startFromStep, loadSession, fetchSessions, isLoading, error, setError } = useWorkflow();

  const [vocText, setVocText] = useState('');
  const [inputFormat, setInputFormat] = useState('text');
  const [llmBackend, setLlmBackend] = useState('azure');
  const [entryStep, setEntryStep] = useState(1);
  const [upstreamFields, setUpstreamFields] = useState({});
  const [existingSessionId, setExistingSessionId] = useState('');
  const [sessionName, setSessionName] = useState('');
  const [sessions, setSessions] = useState([]);
  const [sessionsLoading, setSessionsLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setSessionsLoading(true);
    fetchSessions().then((data) => {
      if (!cancelled) {
        setSessions(data || []);
        setSessionsLoading(false);
      }
    });
    return () => { cancelled = true; };
  }, [fetchSessions]);

  const handleFileUpload = (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (e) => {
      setVocText(e.target.result);
      if (file.name.endsWith('.csv')) setInputFormat('csv');
    };
    reader.readAsText(file);
  };

  const handleStart = async () => {
    if (!vocText.trim()) {
      setError('Please enter VoC data or upload a file');
      return;
    }

    try {
      if (entryStep === 1) {
        await startWorkflow(vocText, inputFormat, llmBackend, sessionName.trim() || undefined);
      } else {
        const initialState = { voc_data: vocText };
        const fields = UPSTREAM_FIELDS_BY_STEP[entryStep] || [];
        for (const field of fields) {
          try {
            const parsed = parseFieldValue(upstreamFields[field.key], field.type);
            if (parsed !== undefined) initialState[field.key] = parsed;
          } catch (parseErr) {
            setError(`Invalid ${field.label}: ${parseErr.message}`);
            return;
          }
        }
        await startFromStep(entryStep, initialState, llmBackend, sessionName.trim() || undefined);
      }
      navigate('/workflow');
    } catch {
      // error already set in context
    }
  };

  const handleEntryStepChange = ({ option }) => {
    setEntryStep(option.value);
    setUpstreamFields({});
  };

  const handleUpstreamChange = (key, value) => {
    setUpstreamFields((prev) => ({ ...prev, [key]: value }));
  };

  const handleLoadSession = async () => {
    if (!existingSessionId.trim()) {
      setError('Please enter a session ID');
      return;
    }
    try {
      await loadSession(existingSessionId.trim());
      navigate('/workflow');
    } catch {
      // error already set in context
    }
  };

  const size = useContext(ResponsiveContext);
  const isSmall = size === 'small';

  return (
    <Box align="center" pad={{ horizontal: isSmall ? 'medium' : 'large', vertical: 'medium' }} gap="medium" fill="horizontal" flex={false}>
      <Box width={{ max: 'xlarge' }} fill="horizontal" gap="medium">
        <Heading level={2} margin="none">CXIF AI Coach</Heading>
        <Text color="text-weak">
          Start a new business model innovation workflow or resume an existing session.
        </Text>

        {/* Portfolio Dashboard quick-access */}
        <Card background="background-front" elevation="small">
          <CardBody pad="medium" direction="row" align="center" justify="between">
            <Box gap="xsmall">
              <Heading level={4} margin="none">Innovation Portfolio</Heading>
              <Text size="small" color="text-weak">
                View the Explore / Exploit quadrant chart for all initiatives.
              </Text>
            </Box>
            <Button
              secondary
              label="Open Dashboard"
              icon={<Analytics size="small" />}
              onClick={() => navigate('/portfolio')}
            />
          </CardBody>
        </Card>

        {error && (
          <Notification
            status="critical"
            message={error}
            onClose={() => setError(null)}
          />
        )}

        {/* New Workflow */}
        <Card background="background-front" elevation="small">
          <CardHeader pad="medium">
            <Heading level={3} margin="none">New Workflow</Heading>
          </CardHeader>
          <CardBody pad="medium" gap="medium">
            <Box gap="xsmall">
              <Text size="small" weight="bold">Session Name (optional)</Text>
              <TextInput
                placeholder="e.g. HBM Supply Chain Analysis"
                value={sessionName}
                onChange={(e) => setSessionName(e.target.value)}
              />
              <Text size="xsmall" color="text-weak">
                Give your session a memorable name so you can find it later.
              </Text>
            </Box>

            <Box gap="xsmall">
              <Text size="small" weight="bold">Voice of Customer Data</Text>
              <TextArea
                placeholder="Paste interview transcripts, survey results, or customer feedback…"
                value={vocText}
                onChange={(e) => setVocText(e.target.value)}
                rows={8}
                resize="vertical"
              />
            </Box>

            <Box gap="xsmall">
              <Text size="small" weight="bold">Or upload a file</Text>
              <FileInput
                accept=".txt,.csv,.md"
                onChange={handleFileUpload}
                messages={{ dropPromptMultiple: 'Drop file here or' }}
              />
            </Box>

            <Box direction="row" gap="medium" wrap>
              <Box gap="xsmall" width={{ min: '200px' }} flex="grow">
                <Text size="small" weight="bold">Input Format</Text>
                <Select
                  options={['text', 'csv']}
                  value={inputFormat}
                  onChange={({ option }) => setInputFormat(option)}
                />
              </Box>
              <Box gap="xsmall" width={{ min: '200px' }} flex="grow">
                <Text size="small" weight="bold">LLM Backend</Text>
                <Select
                  options={['azure', 'ollama']}
                  value={llmBackend}
                  onChange={({ option }) => setLlmBackend(option)}
                />
              </Box>
            </Box>

            <Box gap="xsmall">
              <Text size="small" weight="bold">Entry Point</Text>
              <Select
                options={ENTRY_STEPS}
                labelKey="label"
                valueKey={{ key: 'value', reduce: true }}
                value={entryStep}
                onChange={handleEntryStepChange}
              />
              {entryStep > 1 && (
                <Text size="xsmall" color="text-weak">
                  Starting at a later step requires pre-filled upstream data.
                </Text>
              )}
            </Box>

            {entryStep > 1 && UPSTREAM_FIELDS_BY_STEP[entryStep] && (
              <Box
                gap="small"
                pad="medium"
                round="small"
                background="background-contrast"
              >
                <Text size="small" weight="bold">
                  Required Upstream State for {ENTRY_STEPS.find((s) => s.value === entryStep)?.label}
                </Text>
                {UPSTREAM_FIELDS_BY_STEP[entryStep].map((field) =>
                  field.type === 'textarea' ? (
                    <Box key={field.key} gap="xsmall">
                      <Text size="xsmall" weight="bold">{field.label}</Text>
                      <TextArea
                        placeholder={field.placeholder}
                        value={upstreamFields[field.key] || ''}
                        onChange={(e) => handleUpstreamChange(field.key, e.target.value)}
                        rows={4}
                        resize="vertical"
                      />
                    </Box>
                  ) : (
                    <Box key={field.key} gap="xsmall">
                      <Text size="xsmall" weight="bold">{field.label}</Text>
                      <TextInput
                        placeholder={field.placeholder}
                        value={upstreamFields[field.key] || ''}
                        onChange={(e) => handleUpstreamChange(field.key, e.target.value)}
                      />
                    </Box>
                  ),
                )}
              </Box>
            )}

            <Button
              primary
              label={isLoading ? 'Starting…' : 'Start Workflow'}
              icon={<PlayFill size="small" />}
              onClick={handleStart}
              disabled={isLoading}
            />
          </CardBody>
        </Card>

        {/* Resume Session */}
        <Card background="background-front" elevation="small">
          <CardHeader pad="medium">
            <Heading level={3} margin="none">Resume Session</Heading>
          </CardHeader>
          <CardBody pad="medium" gap="medium">
            {sessionsLoading ? (
              <Text color="text-weak">Loading sessions…</Text>
            ) : sessions.length > 0 ? (
              <Box gap="small">
                <Text size="small" weight="bold">Recent Sessions</Text>
                <DataTable
                  columns={[
                    {
                      property: 'session_name',
                      header: 'Name',
                      render: (datum) => (
                        <Text size="small" truncate>
                          {datum.session_name || '(unnamed)'}
                        </Text>
                      ),
                    },
                    {
                      property: 'session_id',
                      header: 'ID',
                      render: (datum) => (
                        <Text size="xsmall" color="text-weak">
                          {datum.session_id.slice(0, 12)}…
                        </Text>
                      ),
                    },
                    {
                      property: 'status',
                      header: 'Status',
                      render: (datum) => (
                        <Text size="xsmall">{datum.status}</Text>
                      ),
                    },
                    {
                      property: 'current_step',
                      header: 'Step',
                      render: (datum) => (
                        <Text size="xsmall">{datum.current_step}</Text>
                      ),
                    },
                    {
                      property: 'created_at',
                      header: 'Created',
                      render: (datum) => (
                        <Text size="xsmall">
                          {datum.created_at ? new Date(datum.created_at).toLocaleDateString() : '—'}
                        </Text>
                      ),
                    },
                  ]}
                  data={sessions}
                  primaryKey="session_id"
                  onClickRow={({ datum }) => {
                    loadSession(datum.session_id).then(() => navigate('/workflow')).catch(() => {});
                  }}
                  step={10}
                  paginate
                  size="small"
                />
              </Box>
            ) : (
              <Text size="small" color="text-weak">No previous sessions found.</Text>
            )}

            <Box border={{ side: 'top', color: 'border' }} pad={{ top: 'medium' }} gap="xsmall">
              <Text size="small" weight="bold">Or enter a Session ID directly</Text>
              <TextInput
                placeholder="e.g. f30832a1-…"
                value={existingSessionId}
                onChange={(e) => setExistingSessionId(e.target.value)}
              />
            </Box>
            <Button
              secondary
              label={isLoading ? 'Loading…' : 'Load Session'}
              icon={<Document size="small" />}
              onClick={handleLoadSession}
              disabled={isLoading}
            />
          </CardBody>
        </Card>
      </Box>
    </Box>
  );
};

export default HomePage;
