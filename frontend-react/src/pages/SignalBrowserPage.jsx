import { useState, useEffect, useCallback, useContext, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box, Button, Heading, Text, TextInput, Select, DataTable, Layer,
  Page, PageContent, PageHeader,
  Spinner, Notification, Tag, ResponsiveContext,
} from 'grommet';
import {
  Analytics, Close, Filter, FormClose, PlayFill, Search,
  StatusCritical, StatusWarning, StatusGood, StatusUnknown,
} from 'grommet-icons';
import { useWorkflow } from '../context/WorkflowContext.jsx';
import {
  getSignalSummary, getSignals, getSignalDetail, startRunFromSignal,
} from '../api/workflowApi.js';

// --- HPE Status Indicator pattern (icon + color + text = WCAG 3/4) ---
const TIER_CONFIG = {
  Act:               { icon: StatusCritical, color: 'status-critical', label: 'Act' },
  'Sustaining — Act': { icon: StatusCritical, color: 'status-critical', label: 'Sustaining — Act' },
  Investigate:       { icon: StatusWarning,  color: 'status-warning',  label: 'Investigate' },
  Watch:             { icon: StatusWarning,  color: 'status-warning',  label: 'Watch' },
  Monitor:           { icon: StatusGood,     color: 'status-ok',       label: 'Monitor' },
  'Monitor (Positive — sustains competitive position)': { icon: StatusGood, color: 'status-ok', label: 'Monitor+' },
};

const TierIndicator = ({ tier }) => {
  const cfg = TIER_CONFIG[tier] || { icon: StatusUnknown, color: 'text-weak', label: tier };
  const Icon = cfg.icon;
  return (
    <Box direction="row" align="center" gap="xsmall">
      <Icon size="small" color={cfg.color} />
      <Text size="xsmall" weight="bold" color={cfg.color}>{cfg.label}</Text>
    </Box>
  );
};

// --- Active filter count badge ---
const activeFilterCount = (...filters) => filters.filter(Boolean).length;

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

  // Search
  const [searchText, setSearchText] = useState('');

  // Filter drawer visibility
  const [showFilters, setShowFilters] = useState(false);

  // Data state
  const [allSignals, setAllSignals] = useState([]);  // unfiltered for total count
  const [signals, setSignals] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Detail modal
  const [detailSignal, setDetailSignal] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);

  // Workflow launch
  const [launching, setLaunching] = useState(false);

  // Load filter options + total count on mount
  useEffect(() => {
    getSignalSummary()
      .then((data) => {
        const bus = [...new Set(data.map((d) => d.bu))].sort();
        const sources = [...new Set(data.map((d) => d.survey_source))].sort();
        setBuOptions(bus);
        setSourceOptions(sources);
      })
      .catch((err) => setError(err.message));
    getSignals()
      .then((data) => {
        setTotalCount(data.length);
        setAllSignals(data);
        const tiers = [...new Set(data.map((d) => d.action_tier).filter(Boolean))].sort();
        setTierOptions(tiers);
        const classifications = [...new Set(data.map((d) => d.classification).filter(Boolean))].sort();
        setClassificationOptions(classifications);
      })
      .catch(() => {});
  }, []);

  // Load signals when server-side filters change
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

  // Client-side search filter (HPE Filtering: search above data)
  const filteredSignals = useMemo(() => {
    if (!searchText.trim()) return signals;
    const q = searchText.toLowerCase();
    return signals.filter((s) =>
      s.signal_title?.toLowerCase().includes(q) ||
      s.bu?.toLowerCase().includes(q) ||
      s.classification?.toLowerCase().includes(q) ||
      s.signal_zone?.toLowerCase().includes(q)
    );
  }, [signals, searchText]);

  const filtersActive = activeFilterCount(selectedBu, selectedSource, selectedTier, selectedClassification);

  const clearAllFilters = () => {
    setSelectedBu('');
    setSelectedSource('');
    setSelectedTier('');
    setSelectedClassification('');
    setSearchText('');
  };

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
      size: '50%',
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
      render: (datum) => <TierIndicator tier={datum.action_tier} />,
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
    <Page kind="full">
      <PageContent>
        <Box gap="medium" pad={{ vertical: 'medium' }}>
          {/* Page header — HPE PageHeader pattern */}
          <PageHeader
            title="Signal Browser"
            subtitle="Browse signals of change from SOC Radar analysis. Select a signal to view details or launch a CXIF workflow."
            parent={
              <Button plain onClick={() => navigate('/')}>
                <Box direction="row" align="center" gap="xsmall">
                  <Analytics color="brand" size="small" />
                  <Text size="small" color="brand">Home</Text>
                </Box>
              </Button>
            }
          />

          {error && (
            <Notification status="critical" title="Error" message={error} onClose={() => setError(null)} />
          )}

          {/* Toolbar — search + filter button + summary */}
          <Box direction="row" gap="small" align="center">
            <Box width="medium">
              <TextInput
                icon={<Search />}
                placeholder="Search signals…"
                value={searchText}
                onChange={(e) => setSearchText(e.target.value)}
                type="search"
              />
            </Box>

            <Button
              icon={<Filter />}
              label={filtersActive > 0 ? `Filters (${filtersActive})` : 'Filters'}
              onClick={() => setShowFilters(true)}
            />

            {(filtersActive > 0 || searchText) && (
              <Button
                icon={<FormClose />}
                label="Clear all"
                onClick={clearAllFilters}
                size="small"
              />
            )}

            <Box flex />
            <Text size="small" color="text-weak">
              {filtersActive > 0 || searchText
                ? `${filteredSignals.length} results of ${totalCount} items`
                : `${totalCount} items`}
            </Text>
          </Box>

          {/* Signals table */}
          {loading ? (
            <Box align="center" pad="large"><Spinner size="medium" /></Box>
          ) : (
            <DataTable
              columns={columns}
              data={filteredSignals}
              sortable
              step={25}
              paginate
              border={{ body: { side: 'bottom', color: 'border' } }}
              pad={{ body: { horizontal: 'small', vertical: 'xsmall' } }}
            />
          )}
        </Box>
      </PageContent>

      {/* Filter side-drawer */}
      {showFilters && (
        <Layer
          position="right"
          full="vertical"
          onEsc={() => setShowFilters(false)}
          onClickOutside={() => setShowFilters(false)}
        >
          <Box
            width="medium"
            fill="vertical"
            pad="medium"
            gap="medium"
            overflow="auto"
          >
            <Box flex={false} direction="row" justify="between" align="center">
              <Heading level={3} margin="none">Filters</Heading>
              <Button icon={<Close />} onClick={() => setShowFilters(false)} plain />
            </Box>

            <Box gap="medium">
              <Box gap="xsmall">
                <Text size="small" weight="bold">Business Unit</Text>
                <Select
                  placeholder="All Business Units"
                  options={['', ...buOptions]}
                  value={selectedBu}
                  onChange={({ option }) => setSelectedBu(option)}
                  labelKey={(o) => o || 'All Business Units'}
                  valueKey={{ key: (o) => o, reduce: true }}
                  clear={{ position: 'top', label: 'All Business Units' }}
                />
              </Box>

              <Box gap="xsmall">
                <Text size="small" weight="bold">Survey Source</Text>
                <Select
                  placeholder="All Sources"
                  options={['', ...sourceOptions]}
                  value={selectedSource}
                  onChange={({ option }) => setSelectedSource(option)}
                  labelKey={(o) => o || 'All Sources'}
                  valueKey={{ key: (o) => o, reduce: true }}
                  clear={{ position: 'top', label: 'All Sources' }}
                />
              </Box>

              <Box gap="xsmall">
                <Text size="small" weight="bold">Action Tier</Text>
                <Select
                  placeholder="All Tiers"
                  options={['', ...tierOptions]}
                  value={selectedTier}
                  onChange={({ option }) => setSelectedTier(option)}
                  labelKey={(o) => o || 'All Tiers'}
                  valueKey={{ key: (o) => o, reduce: true }}
                  clear={{ position: 'top', label: 'All Tiers' }}
                />
              </Box>

              <Box gap="xsmall">
                <Text size="small" weight="bold">Classification</Text>
                <Select
                  placeholder="All Classifications"
                  options={['', ...classificationOptions]}
                  value={selectedClassification}
                  onChange={({ option }) => setSelectedClassification(option)}
                  labelKey={(o) => o || 'All Classifications'}
                  valueKey={{ key: (o) => o, reduce: true }}
                  clear={{ position: 'top', label: 'All Classifications' }}
                />
              </Box>
            </Box>

            <Box flex={false} direction="row" gap="small" margin={{ top: 'auto' }} border={{ side: 'top', color: 'border' }} pad={{ top: 'small' }}>
              <Button label="Clear Filters" onClick={clearAllFilters} />
              <Button label="Done" primary onClick={() => setShowFilters(false)} />
            </Box>
          </Box>
        </Layer>
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
                  {/* Tags with HPE Status Indicator for tier */}
                  <Box direction="row" gap="small" wrap flex={false} align="center">
                    <Tag value={detailSignal.bu} size="small" />
                    <Tag value={detailSignal.signal_zone} size="small" />
                    <TierIndicator tier={detailSignal.action_tier} />
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
    </Page>
  );
};

export default SignalBrowserPage;
