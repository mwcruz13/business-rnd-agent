import { useContext } from 'react';
import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import { Box, Header, Heading, Nav, Anchor, Text, ResponsiveContext } from 'grommet';
import { Hpe } from 'grommet-icons';
import { WorkflowProvider } from './context/WorkflowContext.jsx';
import { ErrorBoundary } from './components/ErrorBoundary.jsx';
import { useWorkflow } from './context/WorkflowContext.jsx';
import HomePage from './pages/HomePage.jsx';
import WorkflowPage from './pages/WorkflowPage.jsx';
import SignalBrowserPage from './pages/SignalBrowserPage.jsx';

const AppHeader = () => {
  const { sessionId, sessionName, clearSession } = useWorkflow();
  const location = useLocation();
  const onWorkflowPage = location.pathname === '/workflow';
  const size = useContext(ResponsiveContext);
  const isSmall = size === 'small';

  return (
    <Header
      background="background-front"
      pad={{ horizontal: isSmall ? 'small' : 'medium', vertical: 'small' }}
      border={{ side: 'bottom', color: 'border' }}
      responsive
    >
      <Box direction="row" align="center" gap="small">
        <Hpe color="brand" size="medium" />
        {!isSmall && <Heading level={4} margin="none">BMI Consultant</Heading>}
      </Box>
      <Nav direction="row" gap="medium" align="center">
        <Anchor as={Link} to="/signals" label="Signals" size="small" />
        {onWorkflowPage && sessionId && (
          <Text size="xsmall" color="text-weak">
            {sessionName ? sessionName : `Session: ${sessionId.slice(0, 12)}…`}
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
          <Box fill background="background-back" style={{ minHeight: '100vh' }}>
            <AppHeader />
            <Box flex overflow="auto" style={{ minHeight: 0 }}>
              <Routes>
                <Route path="/" element={<HomePage />} />
                <Route path="/signals" element={<SignalBrowserPage />} />
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
