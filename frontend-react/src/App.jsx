import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import { Box, Header, Heading, Nav, Anchor, Text } from 'grommet';
import { Hpe } from 'grommet-icons';
import { WorkflowProvider } from './context/WorkflowContext.jsx';
import { ErrorBoundary } from './components/ErrorBoundary.jsx';
import { useWorkflow } from './context/WorkflowContext.jsx';
import HomePage from './pages/HomePage.jsx';
import WorkflowPage from './pages/WorkflowPage.jsx';

const AppHeader = () => {
  const { sessionId, clearSession } = useWorkflow();
  const location = useLocation();
  const onWorkflowPage = location.pathname === '/workflow';

  return (
    <Header
      background="background-front"
      pad={{ horizontal: 'medium', vertical: 'small' }}
      border={{ side: 'bottom', color: 'border' }}
    >
      <Box direction="row" align="center" gap="small">
        <Hpe color="brand" size="medium" />
        <Heading level={4} margin="none">BMI Consultant</Heading>
      </Box>
      <Nav direction="row" gap="medium" align="center">
        {onWorkflowPage && sessionId && (
          <Text size="xsmall" color="text-weak">
            Session: {sessionId.slice(0, 12)}…
          </Text>
        )}
        {onWorkflowPage && (
          <Anchor
            as={Link}
            to="/"
            label="New Session"
            size="small"
            onClick={clearSession}
          />
        )}
        {!onWorkflowPage && sessionId && (
          <Anchor as={Link} to="/workflow" label="Resume" size="small" />
        )}
      </Nav>
    </Header>
  );
};

const App = () => {
  return (
    <ErrorBoundary>
      <WorkflowProvider>
        <BrowserRouter>
          <Box fill background="background-back">
            <AppHeader />
            <Box flex overflow="auto">
              <Routes>
                <Route path="/" element={<HomePage />} />
                <Route path="/workflow" element={<WorkflowPage />} />
              </Routes>
            </Box>
          </Box>
        </BrowserRouter>
      </WorkflowProvider>
    </ErrorBoundary>
  );
};

export default App;
