import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline, Container, Typography, Box, CircularProgress } from '@mui/material';
import axios from 'axios';

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

function App() {
  const [apiStatus, setApiStatus] = useState('checking...');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check API connection
    const checkAPI = async () => {
      try {
        const response = await axios.get('http://localhost:8000/health');
        setApiStatus(`API is ${response.data.status}`);
      } catch (error) {
        setApiStatus('API connection failed');
      } finally {
        setLoading(false);
      }
    };

    checkAPI();
  }, []);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Container maxWidth="lg">
          <Box sx={{ my: 4, textAlign: 'center' }}>
            <Typography variant="h2" component="h1" gutterBottom>
              Parking Management System
            </Typography>
            <Typography variant="h5" component="h2" gutterBottom color="text.secondary">
              Система управления парковкой
            </Typography>
            <Box sx={{ mt: 4 }}>
              {loading ? (
                <CircularProgress />
              ) : (
                <Typography variant="body1" color={apiStatus.includes('healthy') ? 'success.main' : 'error.main'}>
                  Status: {apiStatus}
                </Typography>
              )}
            </Box>
          </Box>
        </Container>
      </Router>
    </ThemeProvider>
  );
}

export default App;
