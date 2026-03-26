import { useContext } from 'react';
import { Box, ResponsiveContext, Text } from 'grommet';
import {
  StatusGood, InProgress, StatusCritical,
} from 'grommet-icons';

/**
 * The 8-step BMI workflow definition used across the frontend.
 */
export const STEPS = [
  { key: 'step1_signal', label: 'Signal Scan', shortLabel: 'Signals' },
  { key: 'step2_pattern', label: 'Pattern Direction', shortLabel: 'Patterns' },
  { key: 'step3_profile', label: 'Customer Profile', shortLabel: 'Profile' },
  { key: 'step4_vpm', label: 'Value Drivers', shortLabel: 'VDT' },
  { key: 'step5_define', label: 'Value Proposition', shortLabel: 'VPC' },
  { key: 'step6_design', label: 'Business Model', shortLabel: 'BMC' },
  { key: 'step7_risk', label: 'Risk Map', shortLabel: 'Risk' },
  { key: 'step8_pdsa', label: 'Experiment Plan', shortLabel: 'PDSA' },
];

function stepStatus(index, activeStep, runState) {
  if (!runState) return 'pending';
  if (index === activeStep) {
    if (runState.run_status === 'paused') return 'paused';
    return 'active';
  }
  if (index < activeStep) return 'completed';
  return 'pending';
}

function StatusIcon({ status }) {
  if (status === 'completed') return <StatusGood color="status-ok" size="small" />;
  if (status === 'active' || status === 'paused') return <InProgress color="brand" size="small" />;
  return <Box width="16px" height="16px" round="full" border={{ color: 'border', size: 'small' }} />;
}

const StepSidebar = ({ activeStep, runState, onStepClick }) => {
  const screenSize = useContext(ResponsiveContext);
  const isSmall = screenSize === 'small';

  return (
    <Box
      width={isSmall ? '56px' : '240px'}
      pad={{ vertical: 'medium', horizontal: 'xsmall' }}
      gap="xxsmall"
      border={{ side: 'right', color: 'border' }}
      background="background-front"
      style={{ flexShrink: 0, transition: 'width 0.2s ease' }}
    >
      {!isSmall && (
        <Text
          size="xsmall"
          weight="bold"
          color="text-weak"
          margin={{ bottom: 'small', left: 'small' }}
        >
          WORKFLOW STEPS
        </Text>
      )}
      {STEPS.map((step, index) => {
        const status = stepStatus(index, activeStep, runState);
        const isActive = index === activeStep;
        return (
          <Box
            key={step.key}
            direction="row"
            align="center"
            gap={isSmall ? 'none' : 'small'}
            pad={{ vertical: 'xsmall', horizontal: 'xsmall' }}
            round="small"
            background={isActive ? 'active-background' : undefined}
            hoverIndicator="active-background"
            onClick={() => onStepClick(index)}
            justify={isSmall ? 'center' : undefined}
            style={{ cursor: 'pointer' }}
            tip={isSmall ? step.label : undefined}
          >
            <Text size="small" color="text-weak" style={{ minWidth: '16px', textAlign: 'center' }}>
              {index + 1}
            </Text>
            {!isSmall && <StatusIcon status={status} />}
            {!isSmall && (
              <Text size="small" weight={isActive ? 'bold' : 'normal'}>
                {step.label}
              </Text>
            )}
          </Box>
        );
      })}
    </Box>
  );
};

export default StepSidebar;
