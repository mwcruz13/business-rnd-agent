import { useState, useEffect, useCallback, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box, Button, Heading, Text, Select, DataTable, Layer, Card, CardBody,
  CardHeader, Spinner, Notification, Tag, ResponsiveContext,
} from 'grommet';
import { Analytics, Close, PlayFill } from 'grommet-icons';
import { useWorkflow } from '../context/WorkflowContext.jsx';
import {
  getSignalSummary, getSignals, getSignalDetail, startRunFromSignal,
} from '../api/workflowApi.js';

const TIER_COLORS = {
  Act: 'status-critical',
  Investigate: 'status-warning',
  Monitor: 'status-ok',
};

const SignalBrowserPage = () => {
  const navigate = useNavigate();
  const { loadSession } = useWorkflow();
  const size = useContext(ResponsiveContext);
  const isSmall = size === 'small';

  // Filter state
  const [buOptions, setBuOptions] = useState([]);
  const [selectedBu, setSelectedBu] = useState('');
  const [selectedSource, setSelectedSource] = useState('');
  const [sourceOptions, setSourceOptions] = useState([]);
  const [selectedTier, setSelectedTier] = useState('');
  const [tierOptions, setTierOptions] = useState([]);
  const [selectedClassification, setSelectedClassification] = useState('');
  const [classificationOptions, setClassificationOptions] = useState([]);

  // Data state
  const [signals, setSignals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Detail modal
  const [detailSignal, setDetailSignal] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);

  // Workflow launch
  const [launching, setLaunching] = useState(false);

  // Load BU summary for filter options + initial signals for tier options
  useEffect(() => {
    getSignalSummary()
      .then((data) => {
        const bus = [...new Set(data.map((d) => d.bu))].sort();
        const sources = [...new Set(data.map((d) => d.survey_source))].sort();
        setBuOptions(bus);
        setSourceOptions(sources);
      })
      .catch((err) => setError(err.message));
    // Load all signals once to extract tier and classification options
    getSignals()
      .then((data) => {
        const tiers = [...new Set(data.map((d) => d.action_tier).filter(Boolean))].sort();
        setTierOptions(tiers);
        const classifications = [...new Set(data.map((d) => d.classification).filter(Boolean))].sort();
        setClassificationOptions(classifications);
      })
      .catch(() => {});
  }, []);

  // Load signals when filters change
  const loadSignals = useCallback(() => {
    setLoading(true);
    setError(null);
    getSignals({
      bu: selectedBu || undefined,
      surveySource: selectedSource || undefined,
      actionTier: selectedTier || undefined,
      classification: selectedClassification || undefined,
    })
      .then(setSignals)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [selectedBu, selectedSource, selectedTier, selectedClassification]);

  useEffect(() => { loadSignals(); }, [loadSignals]);

  // Open signal detail
  const openDetail = async (id) => {
    setDetailLoading(true);
    try {
      const detail = await getSignalDetail(id);
      setDetailSignal(detail);
    } catch (err) {
      setError(err.message);
    } finally {
      setDetailLoading(false);
    }
  };

  // Launch CXIF workflow from signal
  const launchWorkflow = async (signalId, signalTitle) => {
    setLaunching(true);
    setError(null);
    try {
      const result = await startRunFromSignal({
        signalId,
        sessionName: `Signal: ${signalTitle}`.slice(0, 100),
      });
      await loadSession(result.session_id);
      navigate('/workflow');
    } catch (err) {
      setError(err.message);
    } finally {
      setLaunching(false);
    }
  };

  const columns = [
    {
      property: 'signal_title',
      header: 'Signal',
      primary: true,
      render: (datum) => (
        <Button plain onClick={() => openDetail(datum.id)}>
          <Text weight="bold" color="brand" style={{ wordBreak: 'break-word' }}>{datum.signal_title}</Text>
        </Button>
      ),
    },
    { property: 'bu', header: 'BU', size: 'small' },
    { property: 'signal_zone', header: 'Zone', size: 'small' },
    { property: 'classification', header: 'Classification', size: 'small' },
    {
      property: 'action_tier',
      header: 'Tier',
      size: 'xsmall',
      render: (datum) => (
        <Tag
          value={datum.action_tier}
          background={TIER_COLORS[datum.action_tier] || 'light-4'}
          size="xsmall"
        />
      ),
    },
    {
      property: 'priority_score',
      header: 'Score',
      size: 'xxsmall',
      align: 'end',
    },
    {
      property: 'actions',
      header: '',
      size: 'small',
      sortable: false,
      render: (datum) => (
        <Button
          icon={<PlayFill size="small" />}
          tip="Start CXIF Workflow"
          size="small"
          onClick={() => launchWorkflow(datum.id, datum.signal_title)}
          disabled={launching}
        />
      ),
    },
  ];

  return (
    <Box pad={isSmall ? 'small' : 'medium'} gap="medium" fill="horizontal">
      {/* Page header */}
      <Box direction="row" align="center" gap="small">
        <Analytics color="brand" size="medium" />
        <Heading level={2} margin="none">Signal Browser</Heading>
      </Box>
      <Text color="text-weak">
        Browse ingested signals of change from SOC Radar analysis. Select a signal to view details or launch a CXIF workflow seeded with signal intelligence.
      </Text>

      {error && (
        <Notification status="critical" title="Error" message={error} onClose={() => setError(null)} />
      )}

      {/* Filters */}
      <Box direction="row" gap="small" align="center">
        <Box flex={{ grow: 3, shrink: 1 }} basis="0">
          <Select
            placeholder="Filter by Business Unit"
            options={['', ...buOptions]}
            value={selectedBu}
            onChange={({ option }) => setSelectedBu(option)}
            labelKey={(o) => o || 'All Business Units'}
            valueKey={{ key: (o) => o, reduce: true }}
            clear={{ position: 'top', label: 'All Business Units' }}
          />
        </Box>
        <Box flex={{ grow: 3, shrink: 1 }} basis="0">
          <Select
            placeholder="Filter by Survey Source"
            options={['', ...sourceOptions]}
            value={selectedSource}
            onChange={({ option }) => setSelectedSource(option)}
            labelKey={(o) => o || 'All Sources'}
            valueKey={{ key: (o) => o, reduce: true }}
            clear={{ position: 'top', label: 'All Sources' }}
          />
        </Box>
        <Box flex={{ grow: 2, shrink: 1 }} basis="0">
          <Select
            placeholder="Action Tier"
            options={['', ...tierOptions]}
            value={selectedTier}
            onChange={({ option }) => setSelectedTier(option)}
            labelKey={(o) => o || 'All Tiers'}
            valueKey={{ key: (o) => o, reduce: true }}
            clear={{ position: 'top', label: 'All Tiers' }}
          />
        </Box>
        <Box flex={{ grow: 2, shrink: 1 }} basis="0">
          <Select
            placeholder="Classification"
            options={['', ...classificationOptions]}
            value={selectedClassification}
            onChange={({ option }) => setSelectedClassification(option)}
            labelKey={(o) => o || 'All Classifications'}
            valueKey={{ key: (o) => o, reduce: true }}
            clear={{ position: 'top', label: 'All Classifications' }}
          />
        </Box>
        <Box flex={false}>
          <Text size="small" color="text-weak" style={{ whiteSpace: 'nowrap' }}>
            {signals.length} signal{signals.length !== 1 ? 's' : ''}
          </Text>
        </Box>
      </Box>

      {/* Signals table */}
      {loading ? (
        <Box align="center" pad="large"><Spinner size="medium" /></Box>
      ) : (
        <DataTable
          columns={columns}
          data={signals}
          sortable
          step={25}
          paginate
          border={{ body: { side: 'bottom', color: 'border' } }}
          pad={{ body: { horizontal: 'small', vertical: 'xsmall' } }}
        />
      )}

      {/* Detail modal */}
      {(detailSignal || detailLoading) && (
        <Layer
          position="center"
          onEsc={() => setDetailSignal(null)}
          onClickOutside={() => setDetailSignal(null)}
          responsive
          margin="medium"
        >
          <Box width={{ min: 'medium', max: 'xlarge' }} style={{ maxHeight: '85vh' }} pad="medium" gap="medium">
            {detailLoading ? (
              <Box align="center" pad="large"><Spinner size="medium" /></Box>
            ) : detailSignal && (
              <>
                {/* Fixed header */}
                <Box flex={false} direction="row" justify="between" align="start" gap="small">
                  <Heading level={3} margin="none" style={{ wordBreak: 'break-word' }}>{detailSignal.signal_title}</Heading>
                  <Button icon={<Close />} onClick={() => setDetailSignal(null)} plain />
                </Box>

                {/* Scrollable content */}
                <Box flex overflow="auto" gap="small">
                  <Box direction="row" gap="small" wrap flex={false}>
                    <Tag value={detailSignal.bu} size="small" />
                    <Tag value={detailSignal.signal_zone} size="small" />
                    <Tag
                      value={detailSignal.action_tier}
                      background={TIER_COLORS[detailSignal.action_tier] || 'light-4'}
                      size="small"
                    />
                    <Tag value={`Score: ${detailSignal.priority_score}`} size="small" />
                  </Box>

                  <Text weight="bold" size="small">Classification</Text>
                  <Text size="small">{detailSignal.classification}</Text>

                  <Text weight="bold" size="small">Observable Behavior</Text>
                  <Text size="small">{detailSignal.observable_behavior}</Text>

                  {detailSignal.full_analysis?.phase_2_interpret && (
                    <>
                      <Text weight="bold" size="small">Disruptive Potential</Text>
                      <Text size="small">
                        {detailSignal.full_analysis.phase_2_interpret.disruptive_potential || 'N/A'}
                      </Text>
                      <Text weight="bold" size="small">Value Network Insight</Text>
                      <Text size="small">
                        {detailSignal.full_analysis.phase_2_interpret.value_network_insight || 'N/A'}
                      </Text>
                    </>
                  )}

                  {detailSignal.full_analysis?.phase_3_prioritize && (
                    <>
                      <Text weight="bold" size="small">Priority Rationale</Text>
                      <Text size="small">
                        {detailSignal.full_analysis.phase_3_prioritize.rationale
                          || `Impact: ${detailSignal.full_analysis.phase_3_prioritize.impact ?? 'N/A'} · Speed: ${detailSignal.full_analysis.phase_3_prioritize.speed ?? 'N/A'} · Score: ${detailSignal.full_analysis.phase_3_prioritize.priority_score ?? 'N/A'}`}
                      </Text>
                    </>
                  )}

                  {detailSignal.full_analysis?.phase_4_recommend && (
                    <>
                      {detailSignal.full_analysis.phase_4_recommend.what_we_know && (
                        <>
                          <Text weight="bold" size="small">What We Know</Text>
                          <Text size="small">{detailSignal.full_analysis.phase_4_recommend.what_we_know}</Text>
                        </>
                      )}
                      <Text weight="bold" size="small">Recommended Next Steps</Text>
                      <Box as="ul" margin={{ left: 'small', vertical: 'none' }} pad="none" gap="xsmall">
                        {(detailSignal.full_analysis.phase_4_recommend.next_steps || []).map((step, i) => (
                          <li key={i}>
                            <Text size="small">
                              {typeof step === 'string' ? step : step.action || JSON.stringify(step)}
                              {step.owner && <Text size="xsmall" color="text-weak"> — {step.owner}</Text>}
                            </Text>
                          </li>
                        ))}
                      </Box>
                    </>
                  )}
                </Box>

                {/* Fixed footer buttons */}
                <Box flex={false} direction="row" gap="small" justify="end" border={{ side: 'top', color: 'border' }} pad={{ top: 'small' }}>
                  <Button
                    label="Start CXIF Workflow"
                    icon={<PlayFill />}
                    primary
                    onClick={() => {
                      setDetailSignal(null);
                      launchWorkflow(detailSignal.id, detailSignal.signal_title);
                    }}
                    disabled={launching}
                  />
                  <Button label="Close" onClick={() => setDetailSignal(null)} />
                </Box>
              </>
            )}
          </Box>
        </Layer>
      )}
    </Box>
  );
};

export default SignalBrowserPage;
