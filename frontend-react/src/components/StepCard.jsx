import { Box, Card, CardBody, Tabs } from 'grommet';
import StepToolbar from './StepToolbar.jsx';

/**
 * Generic card wrapper for every workflow step.
 * Combines the StepToolbar (title + YAML download/upload) with a
 * Grommet <Tabs> shell. Children should be <Tab> elements.
 */
const StepCard = ({
  stepIndex,
  stepLabel,
  runState,
  sessionId,
  onImport,
  children,
}) => (
  <Card
    background="background-front"
    round="small"
    elevation="small"
    fill
    overflow={{ horizontal: 'hidden', vertical: 'auto' }}
  >
    <StepToolbar
      stepIndex={stepIndex}
      stepLabel={stepLabel}
      runState={runState}
      sessionId={sessionId}
      onImport={onImport}
    />
    <CardBody pad="none" flex>
      <Tabs flex justify="start">
        {children}
      </Tabs>
    </CardBody>
  </Card>
);

export default StepCard;
