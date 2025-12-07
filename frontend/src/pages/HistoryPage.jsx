import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Box,
  Typography,
  Button,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  CircularProgress,
  Alert,
  Card,
  CardContent,
  Grid,
} from '@mui/material';
import { useAuth } from '../context/AuthContext';
import parkingService from '../services/parkingService';

const HistoryPage = () => {
  const navigate = useNavigate();
  const { user, isAuthenticated } = useAuth();

  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Statistics
  const [stats, setStats] = useState({
    totalSessions: 0,
    totalCost: 0,
    totalMinutes: 0,
  });

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login');
    } else {
      loadHistory();
    }
  }, [isAuthenticated, navigate]);

  const loadHistory = async () => {
    try {
      setLoading(true);
      setError('');

      const history = await parkingService.getSessionHistory();
      setSessions(history);

      // Calculate statistics
      const totalSessions = history.length;
      const totalCost = history.reduce((sum, s) => sum + parseFloat(s.total_cost || 0), 0);
      const totalMinutes = history.reduce((sum, s) => sum + (s.duration_minutes || 0), 0);

      setStats({ totalSessions, totalCost, totalMinutes });
    } catch (err) {
      setError(err.message || 'Ошибка загрузки истории');
    } finally {
      setLoading(false);
    }
  };

  const formatDuration = (minutes) => {
    if (!minutes) return '-';
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${hours}ч ${mins}мин`;
  };

  const getPaymentStatusColor = (status) => {
    switch (status) {
      case 'pending':
        return 'warning';
      case 'completed':
        return 'success';
      case 'failed':
        return 'error';
      default:
        return 'default';
    }
  };

  const getPaymentStatusText = (status) => {
    switch (status) {
      case 'pending':
        return 'Ожидает оплаты';
      case 'completed':
        return 'Оплачено';
      case 'failed':
        return 'Ошибка';
      case 'refunded':
        return 'Возврат';
      default:
        return status;
    }
  };

  if (!user) {
    return (
      <Container maxWidth="lg">
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '80vh' }}>
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  if (loading) {
    return (
      <Container maxWidth="lg">
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '80vh' }}>
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg">
      <Box sx={{ mt: 4, mb: 4 }}>
        {/* Header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h4">История парковок</Typography>
          <Button variant="outlined" onClick={() => navigate('/dashboard')}>
            Назад к Dashboard
          </Button>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError('')}>
            {error}
          </Alert>
        )}

        {/* Statistics */}
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography variant="h6" color="primary">
                  {stats.totalSessions}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Всего парковок
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography variant="h6" color="success.main">
                  {stats.totalCost.toFixed(2)} ₽
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Всего потрачено
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography variant="h6" color="info.main">
                  {formatDuration(stats.totalMinutes)}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Общее время парковки
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* History Table */}
        <Paper elevation={2} sx={{ p: 3 }}>
          <Typography variant="h5" sx={{ mb: 2 }}>
            Все парковки
          </Typography>
          {sessions.length === 0 ? (
            <Typography color="text.secondary">История парковок пуста</Typography>
          ) : (
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Дата и время</TableCell>
                    <TableCell>Место</TableCell>
                    <TableCell>Автомобиль</TableCell>
                    <TableCell>Длительность</TableCell>
                    <TableCell>Стоимость</TableCell>
                    <TableCell>Оплата</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {sessions.map((session) => (
                    <TableRow key={session.session_id}>
                      <TableCell>
                        <Typography variant="body2">
                          <strong>Въезд:</strong> {new Date(session.entry_time).toLocaleString('ru-RU')}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          <strong>Выезд:</strong> {new Date(session.exit_time).toLocaleString('ru-RU')}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          <strong>{session.spot.spot_number}</strong>
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {session.zone.name}
                        </Typography>
                        <br />
                        <Typography variant="caption" color="text.secondary">
                          {session.zone.address}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {session.vehicle.license_plate}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {session.vehicle.model}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        {formatDuration(session.duration_minutes)}
                      </TableCell>
                      <TableCell>
                        <Typography variant="body1" fontWeight="bold">
                          {parseFloat(session.total_cost || 0).toFixed(2)} ₽
                        </Typography>
                      </TableCell>
                      <TableCell>
                        {session.payment ? (
                          <Chip
                            label={getPaymentStatusText(session.payment.status)}
                            color={getPaymentStatusColor(session.payment.status)}
                            size="small"
                          />
                        ) : (
                          <Chip label="Нет оплаты" color="default" size="small" />
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </Paper>
      </Box>
    </Container>
  );
};

export default HistoryPage;
