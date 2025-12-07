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
  TextField,
  MenuItem,
  Collapse,
  IconButton,
} from '@mui/material';
import { FilterList as FilterIcon, GetApp as ExportIcon } from '@mui/icons-material';
import { useAuth } from '../context/AuthContext';
import parkingService from '../services/parkingService';

const HistoryPage = () => {
  const navigate = useNavigate();
  const { user, isAuthenticated } = useAuth();

  const [sessions, setSessions] = useState([]);
  const [filteredSessions, setFilteredSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showFilters, setShowFilters] = useState(false);

  // Filters
  const [filters, setFilters] = useState({
    dateFrom: '',
    dateTo: '',
    vehicle: '',
    zone: '',
    paymentStatus: '',
  });

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

  // Apply filters whenever sessions or filters change
  useEffect(() => {
    applyFilters();
  }, [sessions, filters]);

  const loadHistory = async () => {
    try {
      setLoading(true);
      setError('');

      const history = await parkingService.getSessionHistory();
      setSessions(history);
    } catch (err) {
      setError(err.message || 'Ошибка загрузки истории');
    } finally {
      setLoading(false);
    }
  };

  const applyFilters = () => {
    let filtered = [...sessions];

    // Filter by date range
    if (filters.dateFrom) {
      const fromDate = new Date(filters.dateFrom);
      filtered = filtered.filter(s => new Date(s.entry_time) >= fromDate);
    }
    if (filters.dateTo) {
      const toDate = new Date(filters.dateTo);
      toDate.setHours(23, 59, 59);
      filtered = filtered.filter(s => new Date(s.entry_time) <= toDate);
    }

    // Filter by vehicle
    if (filters.vehicle) {
      filtered = filtered.filter(s =>
        s.vehicle.license_plate.toLowerCase().includes(filters.vehicle.toLowerCase())
      );
    }

    // Filter by zone
    if (filters.zone) {
      filtered = filtered.filter(s =>
        s.zone.name.toLowerCase().includes(filters.zone.toLowerCase())
      );
    }

    // Filter by payment status
    if (filters.paymentStatus) {
      filtered = filtered.filter(s =>
        s.payment && s.payment.status === filters.paymentStatus
      );
    }

    setFilteredSessions(filtered);

    // Recalculate statistics for filtered data
    const totalSessions = filtered.length;
    const totalCost = filtered.reduce((sum, s) => sum + parseFloat(s.total_cost || 0), 0);
    const totalMinutes = filtered.reduce((sum, s) => sum + (s.duration_minutes || 0), 0);

    setStats({ totalSessions, totalCost, totalMinutes });
  };

  const handleResetFilters = () => {
    setFilters({
      dateFrom: '',
      dateTo: '',
      vehicle: '',
      zone: '',
      paymentStatus: '',
    });
  };

  const handleExportCSV = () => {
    const csvContent = [
      ['Дата въезда', 'Дата выезда', 'Место', 'Зона', 'Автомобиль', 'Длительность', 'Стоимость', 'Статус оплаты'],
      ...filteredSessions.map(s => [
        new Date(s.entry_time).toLocaleString('ru-RU'),
        new Date(s.exit_time).toLocaleString('ru-RU'),
        s.spot.spot_number,
        s.zone.name,
        s.vehicle.license_plate,
        formatDuration(s.duration_minutes),
        `${parseFloat(s.total_cost || 0).toFixed(2)} ₽`,
        s.payment ? getPaymentStatusText(s.payment.status) : 'Нет оплаты'
      ])
    ].map(row => row.join(',')).join('\n');

    const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `parking_history_${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
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
          <Box sx={{ display: 'flex', gap: 2 }}>
            <Button
              variant="outlined"
              startIcon={<FilterIcon />}
              onClick={() => setShowFilters(!showFilters)}
            >
              Фильтры
            </Button>
            <Button
              variant="outlined"
              startIcon={<ExportIcon />}
              onClick={handleExportCSV}
              disabled={filteredSessions.length === 0}
            >
              Экспорт CSV
            </Button>
            <Button variant="outlined" onClick={() => navigate('/dashboard')}>
              Назад
            </Button>
          </Box>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError('')}>
            {error}
          </Alert>
        )}

        {/* Filters Panel */}
        <Collapse in={showFilters}>
          <Paper elevation={1} sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" sx={{ mb: 2 }}>Фильтры</Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} md={3}>
                <TextField
                  label="Дата с"
                  type="date"
                  fullWidth
                  value={filters.dateFrom}
                  onChange={(e) => setFilters({ ...filters, dateFrom: e.target.value })}
                  InputLabelProps={{ shrink: true }}
                />
              </Grid>
              <Grid item xs={12} md={3}>
                <TextField
                  label="Дата по"
                  type="date"
                  fullWidth
                  value={filters.dateTo}
                  onChange={(e) => setFilters({ ...filters, dateTo: e.target.value })}
                  InputLabelProps={{ shrink: true }}
                />
              </Grid>
              <Grid item xs={12} md={2}>
                <TextField
                  label="Автомобиль"
                  fullWidth
                  value={filters.vehicle}
                  onChange={(e) => setFilters({ ...filters, vehicle: e.target.value })}
                  placeholder="А123ВС777"
                />
              </Grid>
              <Grid item xs={12} md={2}>
                <TextField
                  label="Зона"
                  fullWidth
                  value={filters.zone}
                  onChange={(e) => setFilters({ ...filters, zone: e.target.value })}
                  placeholder="Центральная"
                />
              </Grid>
              <Grid item xs={12} md={2}>
                <TextField
                  label="Статус оплаты"
                  select
                  fullWidth
                  value={filters.paymentStatus}
                  onChange={(e) => setFilters({ ...filters, paymentStatus: e.target.value })}
                >
                  <MenuItem value="">Все</MenuItem>
                  <MenuItem value="pending">Ожидает оплаты</MenuItem>
                  <MenuItem value="completed">Оплачено</MenuItem>
                  <MenuItem value="failed">Ошибка</MenuItem>
                </TextField>
              </Grid>
              <Grid item xs={12}>
                <Button
                  variant="outlined"
                  onClick={handleResetFilters}
                  size="small"
                >
                  Сбросить фильтры
                </Button>
              </Grid>
            </Grid>
          </Paper>
        </Collapse>

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
            {filteredSessions.length === sessions.length
              ? 'Все парковки'
              : `Найдено: ${filteredSessions.length} из ${sessions.length}`}
          </Typography>
          {filteredSessions.length === 0 ? (
            <Typography color="text.secondary">
              {sessions.length === 0 ? 'История парковок пуста' : 'Нет результатов по выбранным фильтрам'}
            </Typography>
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
                  {filteredSessions.map((session) => (
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
