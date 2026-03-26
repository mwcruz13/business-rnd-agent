import { Component } from 'react';
import { Box, Heading, Text, Button } from 'grommet';

class ErrorBoundaryInner extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <Box fill align="center" justify="center" pad="large">
          <Box width="large" pad="large" gap="medium">
            <Heading level={2}>Something went wrong</Heading>
            <Text>{this.state.error?.message || 'An unexpected error occurred.'}</Text>
            <Button
              label="Reload"
              onClick={() => window.location.reload()}
              primary
            />
          </Box>
        </Box>
      );
    }
    return this.props.children;
  }
}

export { ErrorBoundaryInner as ErrorBoundary };
