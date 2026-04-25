import { useState, useEffect, useCallback, useContext, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box, Button, Heading, Page, PageContent, PageHeader,
  Spinner, Text, Notification, ResponsiveContext, Tip,
} from 'grommet';
import { Analytics, Home } from 'grommet-icons';
import {
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid,
  ReferenceLine, ResponsiveContainer, Tooltip, Cell, Label,
} from 'recharts';
import { getPortfolio } from '../api/workflowApi.js';
import ProjectDetailPanel from '../components/ProjectDetailPanel.jsx';

// --- Colour palette (HPE-aligned) ---
const COLOR_INVENT = '#01a982';   // HPE green  (Explore / Invent)
const COLOR_SHIFT  = '#0d5265';   // HPE teal   (Exploit / Shift)
const COLOR_UNKNOWN = '#999999';  // neutral

const dotColor = (entry) => {
  if (entry.pattern_direction === 'invent') return COLOR_INVENT;
  if (entry.pattern_direction === 'shift') return COLOR_SHIFT;
  return COLOR_UNKNOWN;
};

// --- Custom dot renderer (inspired by The Invincible Company) ---
const ProjectDot = ({ cx, cy, payload, isSelected, onClick }) => {
  if (cx == null || cy == null) return null;
  const selected = isSelected && isSelected(payload);
  return (
    <g
      onClick={(e) => { e.stopPropagation(); onClick?.(payload); }}
      style={{ cursor: 'pointer' }}
    >
      {/* Dot */}
      <circle
        cx={cx}
        cy={cy}
        r={selected ? 8 : 6}
        fill={dotColor(payload)}
        stroke={selected ? '#333' : 'white'}
        strokeWidth={selected ? 2 : 1}
        opacity={0.9}
      />
      {/* Label */}
      <text
        x={cx + 10}
        y={cy - 10}
        fill="#333"
        fontSize={11}
        fontWeight="bold"
      >
        {(payload.initiative_name || '').slice(0, 28)}
      </text>
      {/* Revenue / Cost sub-label */}
      {(payload.expected_revenue || payload.testing_cost) && (
        <text
          x={cx + 10}
          y={cy + 4}
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

  const fetchData = useCallback(() => {
    setLoading(true);
    getPortfolio()
      .then(setEntries)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  // Summary metrics
  const summary = useMemo(() => {
    const explore = entries.filter((e) => e.pattern_direction === 'invent').length;
    const exploit = entries.filter((e) => e.pattern_direction === 'shift').length;
    return { total: entries.length, explore, exploit, unknown: entries.length - explore - exploit };
  }, [entries]);

  const handleDotClick = (entry) => {
    setSelectedId(entry.session_id);
  };

  const isSelected = (entry) => entry.session_id === selectedId;

  return (
    <Page kind="full">
      <PageHeader
        title="Business Model Portfolio"
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
        </Box>

        {/* Legend */}
        <Box
          direction="row"
          gap="medium"
          pad={{ vertical: 'xsmall' }}
          flex={false}
        >
          <Text size="xsmall" color="text-weak">
            <strong>Dot</strong> = Initiative &nbsp; | &nbsp;
            <strong>X-Axis</strong> = Innovation Risk (0–100) &nbsp; | &nbsp;
            <strong>Y-Axis</strong> = Expected Return (0–100)
          </Text>
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
                  dataKey="risk_score"
                  domain={[0, 100]}
                  name="Innovation Risk"
                  tick={{ fontSize: 11 }}
                  tickLine={false}
                >
                  <Label
                    value="Innovation Risk →"
                    position="insideBottomRight"
                    offset={-5}
                    style={{ fontSize: 12, fill: '#666' }}
                  />
                </XAxis>

                <YAxis
                  type="number"
                  dataKey="return_score"
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

                <Tooltip content={<ProjectTooltip />} />

                <Scatter
                  data={entries}
                  shape={(props) => (
                    <ProjectDot
                      {...props}
                      isSelected={isSelected}
                      onClick={handleDotClick}
                    />
                  )}
                >
                  {entries.map((entry) => (
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
