import { useState, useEffect, useCallback, useContext, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box, Button, Heading, Page, PageContent, PageHeader,
  Spinner, Text, Notification, ResponsiveContext, Tip,
  CheckBoxGroup, Select,
} from 'grommet';
import { Analytics, Home, Filter } from 'grommet-icons';
import {
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid,
  ReferenceLine, ResponsiveContainer, Tooltip, Cell, Label,
} from 'recharts';
import { getPortfolio } from '../api/workflowApi.js';
import ProjectDetailPanel from '../components/ProjectDetailPanel.jsx';

// --- Colour palette (HPE-aligned) ---
const COLOR_INVENT      = '#01a982';   // HPE green  (Explore / Invent)
const COLOR_SHIFT       = '#0d5265';   // HPE teal   (Exploit / Shift)
const COLOR_NOT_STARTED = '#cccccc';   // light gray (Not Started)
const COLOR_UNKNOWN     = '#999999';   // neutral

const isNotStarted = (entry) => (entry.completed_steps_count ?? 0) === 0;

const dotColor = (entry) => {
  if (isNotStarted(entry)) return COLOR_NOT_STARTED;
  if (entry.pattern_direction === 'invent') return COLOR_INVENT;
  if (entry.pattern_direction === 'shift') return COLOR_SHIFT;
  return COLOR_UNKNOWN;
};

// --- Deterministic jitter: hash session_id → small offset so overlapping dots spread ---
const hashCode = (str) => {
  let h = 0;
  for (let i = 0; i < str.length; i++) {
    h = ((h << 5) - h + str.charCodeAt(i)) | 0;
  }
  return h;
};

const JITTER_RANGE = 8; // ± points on the 0-100 scale

const applyJitter = (entries) =>
  entries.map((e) => {
    const h = hashCode(e.session_id);
    // Two independent pseudo-random channels from the same hash
    const dx = ((h & 0xffff) / 0xffff - 0.5) * 2 * JITTER_RANGE;
    const dy = (((h >>> 16) & 0xffff) / 0xffff - 0.5) * 2 * JITTER_RANGE;
    return {
      ...e,
      risk_jittered: Math.max(0, Math.min(100, e.risk_score + dx)),
      return_jittered: Math.max(0, Math.min(100, e.return_score + dy)),
    };
  });

// --- Data maturity → dot radius (more steps / data = bigger dot) ---
const DOT_MIN_R = 5;
const DOT_MAX_R = 14;

const maturityRadius = (entry) => {
  const steps = entry.completed_steps_count ?? 0;
  const assumptions = entry.assumption_count ?? 0;
  const experiments = entry.experiment_count ?? 0;
  // score: 0-9 steps + clamp(assumptions, 0, 10) + clamp(experiments, 0, 5) → 0-24
  const raw = steps + Math.min(assumptions, 10) + Math.min(experiments, 5);
  const t = Math.min(raw / 24, 1);
  return DOT_MIN_R + t * (DOT_MAX_R - DOT_MIN_R);
};

// --- Custom dot renderer (inspired by The Invincible Company) ---
const ProjectDot = ({ cx, cy, payload, isSelected, onClick }) => {
  if (cx == null || cy == null) return null;
  const selected = isSelected && isSelected(payload);
  const r = maturityRadius(payload);
  return (
    <g
      onClick={(e) => { e.stopPropagation(); onClick?.(payload); }}
      style={{ cursor: 'pointer' }}
    >
      {/* Dot — radius scales with data maturity */}
      <circle
        cx={cx}
        cy={cy}
        r={selected ? r + 2 : r}
        fill={dotColor(payload)}
        stroke={selected ? '#333' : 'white'}
        strokeWidth={selected ? 2 : 1}
        opacity={selected ? 1.0 : 0.75}
      />
      {/* Label — suppress for not-started projects; otherwise show when big enough */}
      {(!isNotStarted(payload) && payload.initiative_name && r >= 8) && (
        <text
          x={cx + r + 4}
          y={cy - 4}
          fill="#333"
          fontSize={11}
          fontWeight="bold"
        >
          {(payload.initiative_name || '').slice(0, 28)}
        </text>
      )}
      {/* Revenue / Cost sub-label — only for labeled, started dots */}
      {(!isNotStarted(payload) && r >= 8 && (payload.expected_revenue || payload.testing_cost)) && (
        <text
          x={cx + r + 4}
          y={cy + 10}
          fill="#666"
          fontSize={9}
        >
          {payload.expected_revenue ? payload.expected_revenue : ''}
          {payload.expected_revenue && payload.testing_cost ? '  •  ' : ''}
          {payload.testing_cost ? payload.testing_cost : ''}
          {payload.days_running ? ` / ${payload.days_running}d` : ''}
        </text>
      )}
    </g>
  );
};

// --- Custom tooltip ---
const ProjectTooltip = ({ active, payload }) => {
  if (!active || !payload || !payload.length) return null;
  const d = payload[0].payload;
  return (
    <Box
      background="background-front"
      pad="small"
      round="small"
      elevation="small"
      width={{ max: '300px' }}
    >
      <Text size="small" weight="bold">{d.initiative_name}</Text>
      <Text size="xsmall" color="text-weak">
        Risk: {d.risk_score} · Return: {d.return_score}
      </Text>
      <Text size="xsmall" color="text-weak">
        Pattern: {d.pattern_direction} · Step: {d.current_step}
      </Text>
      {d.expected_revenue && (
        <Text size="xsmall">Revenue: {d.expected_revenue}</Text>
      )}
      {d.testing_cost && (
        <Text size="xsmall">Cost: {d.testing_cost}</Text>
      )}
      <Text size="xsmall" color="text-weak">
        {d.assumption_count} hypotheses · {d.experiment_count} experiments · {d.days_running}d
      </Text>
    </Box>
  );
};

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

const PortfolioDashboardPage = () => {
  const navigate = useNavigate();
  const size = useContext(ResponsiveContext);
  const isSmall = size === 'small';

  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedId, setSelectedId] = useState(null);

  // Filter state
  const [patternFilter, setPatternFilter] = useState(['invent', 'shift', 'unknown', 'not-started']);
  const [maturityFilter, setMaturityFilter] = useState('all'); // 'all' | 'with-data' | 'early'

  const fetchData = useCallback(() => {
    setLoading(true);
    getPortfolio()
      .then(setEntries)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  // Apply filters + jitter
  const chartData = useMemo(() => {
    let filtered = entries;

    // Pattern direction filter (not-started is a virtual category)
    filtered = filtered.filter((e) => {
      if (isNotStarted(e)) return patternFilter.includes('not-started');
      const dir = e.pattern_direction || 'unknown';
      return patternFilter.includes(dir);
    });

    // Maturity filter
    if (maturityFilter === 'with-data') {
      filtered = filtered.filter((e) =>
        (e.assumption_count ?? 0) > 0 || (e.experiment_count ?? 0) > 0
      );
    } else if (maturityFilter === 'early') {
      filtered = filtered.filter((e) =>
        (e.assumption_count ?? 0) === 0 && (e.experiment_count ?? 0) === 0
      );
    }

    return applyJitter(filtered);
  }, [entries, patternFilter, maturityFilter]);

  // Summary metrics (from unfiltered)
  const summary = useMemo(() => {
    const notStarted = entries.filter((e) => isNotStarted(e)).length;
    const started = entries.filter((e) => !isNotStarted(e));
    const explore = started.filter((e) => e.pattern_direction === 'invent').length;
    const exploit = started.filter((e) => e.pattern_direction === 'shift').length;
    const unknown = started.length - explore - exploit;
    return { total: entries.length, explore, exploit, unknown, notStarted };
  }, [entries]);

  const handleDotClick = (entry) => {
    setSelectedId(entry.session_id);
  };

  const isSelected = (entry) => entry.session_id === selectedId;

  return (
    <Page kind="full">
      <PageHeader
        title="Business R&amp;D Portfolio"
        subtitle="Innovation Hedge Fund — Explore vs Exploit"
        parent={
          <Button
            plain
            onClick={() => navigate('/')}
            style={{ display: 'flex', alignItems: 'center', gap: '4px' }}
          >
            <Analytics size="small" />
            <Text size="small">Home</Text>
          </Button>
        }
        pad={{ horizontal: isSmall ? 'small' : 'medium', vertical: 'small' }}
      />

      <PageContent pad={{ horizontal: isSmall ? 'small' : 'medium', vertical: 'small' }}>
        {error && (
          <Notification
            status="critical"
            message={error}
            onClose={() => setError(null)}
          />
        )}

        {/* Summary bar */}
        <Box
          direction="row"
          gap="medium"
          pad={{ vertical: 'small' }}
          wrap
          flex={false}
        >
          <Box direction="row" gap="xsmall" align="center">
            <Text size="small" weight="bold">{summary.total}</Text>
            <Text size="small" color="text-weak">initiatives</Text>
          </Box>
          <Box direction="row" gap="xsmall" align="center">
            <Box width="12px" height="12px" round="full" background={COLOR_INVENT} flex={false} />
            <Text size="small">{summary.explore} Explore</Text>
          </Box>
          <Box direction="row" gap="xsmall" align="center">
            <Box width="12px" height="12px" round="full" background={COLOR_SHIFT} flex={false} />
            <Text size="small">{summary.exploit} Exploit</Text>
          </Box>
          {summary.unknown > 0 && (
            <Box direction="row" gap="xsmall" align="center">
              <Box width="12px" height="12px" round="full" background={COLOR_UNKNOWN} flex={false} />
              <Text size="small">{summary.unknown} Unclassified</Text>
            </Box>
          )}
          {summary.notStarted > 0 && (
            <Box direction="row" gap="xsmall" align="center">
              <Box width="12px" height="12px" round="full" background={COLOR_NOT_STARTED} flex={false} />
              <Text size="small">{summary.notStarted} Not Started</Text>
            </Box>
          )}
        </Box>

        {/* Legend */}
        <Box
          direction="row"
          gap="medium"
          pad={{ vertical: 'xsmall' }}
          flex={false}
          wrap
          align="center"
        >
          <Text size="xsmall" color="text-weak">
            <strong>Dot size</strong> = data maturity &nbsp; | &nbsp;
            <strong>X</strong> = Innovation Risk (high ← → low) &nbsp; | &nbsp;
            <strong>Y</strong> = Expected Return &nbsp; | &nbsp;
            Showing <strong>{chartData.length}</strong> of {summary.total}
          </Text>
        </Box>

        {/* Filter controls */}
        <Box
          direction="row"
          gap="medium"
          pad={{ vertical: 'xsmall' }}
          flex={false}
          wrap
          align="center"
          border={{ side: 'bottom', color: 'border', size: 'xsmall' }}
        >
          <Box direction="row" gap="xsmall" align="center">
            <Filter size="small" color="text-weak" />
            <Text size="xsmall" weight="bold">Filter:</Text>
          </Box>
          <CheckBoxGroup
            direction="row"
            options={[
              { label: 'Explore (Invent)', value: 'invent' },
              { label: 'Exploit (Shift)', value: 'shift' },
              { label: 'Unclassified', value: 'unknown' },
              { label: 'Not Started', value: 'not-started' },
            ]}
            value={patternFilter}
            onChange={({ value }) => setPatternFilter(value)}
          />
          <Box width="160px" flex={false}>
            <Select
              size="small"
              options={['all', 'with-data', 'early']}
              value={maturityFilter}
              onChange={({ option }) => setMaturityFilter(option)}
              labelKey={(o) =>
                o === 'all' ? 'All stages' :
                o === 'with-data' ? 'Has assumptions/experiments' :
                'Early stage only'
              }
            />
          </Box>
        </Box>

        {/* Quadrant Chart */}
        {loading ? (
          <Box align="center" pad="large"><Spinner size="medium" /></Box>
        ) : (
          <Box
            height={{ min: '500px' }}
            flex="grow"
            border={{ color: 'border', size: 'xsmall' }}
            round="small"
            background="background-front"
            pad="small"
          >
            <ResponsiveContainer width="100%" height={560}>
              <ScatterChart margin={{ top: 30, right: 40, bottom: 30, left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />

                <XAxis
                  type="number"
                  dataKey="risk_jittered"
                  domain={[0, 100]}
                  ticks={[0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]}
                  name="Innovation Risk"
                  tick={{ fontSize: 11 }}
                  tickLine={false}
                  reversed
                  allowDataOverflow
                >
                  <Label
                    value="← Innovation Risk"
                    position="insideBottomRight"
                    offset={-5}
                    style={{ fontSize: 12, fill: '#666' }}
                  />
                </XAxis>

                <YAxis
                  type="number"
                  dataKey="return_jittered"
                  domain={[0, 100]}
                  name="Expected Return"
                  tick={{ fontSize: 11 }}
                  tickLine={false}
                >
                  <Label
                    value="Expected Return →"
                    position="insideTopLeft"
                    offset={10}
                    angle={-90}
                    style={{ fontSize: 12, fill: '#666' }}
                  />
                </YAxis>

                {/* Quadrant dividers */}
                <ReferenceLine x={50} stroke="#ccc" strokeDasharray="6 4" />
                <ReferenceLine y={50} stroke="#ccc" strokeDasharray="6 4" />

                {/* Quadrant watermark labels */}
                <text x="22%" y="75%" textAnchor="middle" fill="#e0e0e0" fontSize={28} fontWeight="bold">
                  Explore
                </text>
                <text x="78%" y="25%" textAnchor="middle" fill="#e0e0e0" fontSize={28} fontWeight="bold">
                  Exploit
                </text>
                <text x="12%" y="50%" textAnchor="middle" fill="#e8e8e8" fontSize={14} fontStyle="italic">
                  Not Started
                </text>

                <Tooltip content={<ProjectTooltip />} />

                <Scatter
                  data={chartData}
                  shape={(props) => (
                    <ProjectDot
                      {...props}
                      isSelected={isSelected}
                      onClick={handleDotClick}
                    />
                  )}
                >
                  {chartData.map((entry) => (
                    <Cell key={entry.session_id} fill={dotColor(entry)} />
                  ))}
                </Scatter>
              </ScatterChart>
            </ResponsiveContainer>
          </Box>
        )}
      </PageContent>

      {/* Detail side panel */}
      {selectedId && (
        <ProjectDetailPanel
          sessionId={selectedId}
          onClose={() => setSelectedId(null)}
          onUpdate={fetchData}
        />
      )}
    </Page>
  );
};

export default PortfolioDashboardPage;
