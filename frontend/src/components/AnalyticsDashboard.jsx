import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  LinearProgress,
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  AttachMoney as MoneyIcon,
  DirectionsCar as CarIcon,
  AccessTime as TimeIcon,
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import parkingService from '../services/parkingService';

const AnalyticsDashboard = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStatistics();
  }, []);

  const loadStatistics = async () => {
    try {
      setLoading(true);
      const data = await parkingService.getMonthlyStatistics(6);
      setStats(data);
    } catch (err) {
      console.error('Failed to load statistics:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatMonth = (monthStr) => {
    if (!monthStr) return '';
    const [year, month] = monthStr.split('-');
    const date = new Date(year, parseInt(month) - 1);
    return date.toLocaleDateString('ru-RU', { month: 'short', year: 'numeric' });
  };

  const calculateTrend = (data) => {
    if (!data || data.length < 2) return 0;
    const last = data[data.length - 1];
    const prev = data[data.length - 2];
    if (prev === 0) return last > 0 ? 100 : 0;
    return ((last - prev) / prev) * 100;
  };

  const getTrendIcon = (trend) => {
    if (trend > 0) return <TrendingUpIcon color="success" />;
    if (trend < 0) return <TrendingDownIcon color="error" />;
    return null;
  };

  if (loading) {
    return (
      <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" sx={{ mb: 2 }}>Аналитика</Typography>
        <LinearProgress />
      </Paper>
    );
  }

  if (!stats || stats.months.length === 0) {
    return (
      <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" sx={{ mb: 2 }}>Аналитика</Typography>
        <Typography color="text.secondary">
          Недостаточно данных для отображения статистики
        </Typography>
      </Paper>
    );
  }

  const costTrend = calculateTrend(stats.total_cost);
  const sessionsTrend = calculateTrend(stats.sessions_count);
  const hoursTrend = calculateTrend(stats.total_hours);

  const totalSessions = stats.sessions_count.reduce((sum, val) => sum + val, 0);
  const totalCost = stats.total_cost.reduce((sum, val) => sum + val, 0);
  const totalHours = stats.total_hours.reduce((sum, val) => sum + val, 0);

  const avgCostPerSession = totalSessions > 0 ? totalCost / totalSessions : 0;
  const avgHoursPerSession = totalSessions > 0 ? totalHours / totalSessions : 0;

  // Prepare data for charts
  const chartData = stats.months.map((month, index) => ({
    month: formatMonth(month),
    cost: stats.total_cost[index],
    sessions: stats.sessions_count[index],
    hours: stats.total_hours[index],
  }));

  return (
    <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
      <Typography variant="h5" sx={{ mb: 3 }}>
        Аналитика за последние {stats.months.length} месяцев
      </Typography>

      {/* Summary Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} md={3}>
          <Card variant="outlined">
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <MoneyIcon color="primary" sx={{ mr: 1 }} />
                <Typography variant="body2" color="text.secondary">
                  Всего потрачено
                </Typography>
              </Box>
              <Typography variant="h5" color="primary">
                {totalCost.toFixed(2)} ₽
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                {getTrendIcon(costTrend)}
                <Typography
                  variant="caption"
                  color={costTrend > 0 ? 'success.main' : 'error.main'}
                  sx={{ ml: 0.5 }}
                >
                  {Math.abs(costTrend).toFixed(1)}% vs прошлый месяц
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card variant="outlined">
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <CarIcon color="info" sx={{ mr: 1 }} />
                <Typography variant="body2" color="text.secondary">
                  Всего парковок
                </Typography>
              </Box>
              <Typography variant="h5" color="info.main">
                {totalSessions}
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                {getTrendIcon(sessionsTrend)}
                <Typography
                  variant="caption"
                  color={sessionsTrend > 0 ? 'success.main' : 'error.main'}
                  sx={{ ml: 0.5 }}
                >
                  {Math.abs(sessionsTrend).toFixed(1)}% vs прошлый месяц
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card variant="outlined">
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <TimeIcon color="warning" sx={{ mr: 1 }} />
                <Typography variant="body2" color="text.secondary">
                  Общее время
                </Typography>
              </Box>
              <Typography variant="h5" color="warning.main">
                {totalHours.toFixed(1)} ч
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                {getTrendIcon(hoursTrend)}
                <Typography
                  variant="caption"
                  color={hoursTrend > 0 ? 'success.main' : 'error.main'}
                  sx={{ ml: 0.5 }}
                >
                  {Math.abs(hoursTrend).toFixed(1)}% vs прошлый месяц
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card variant="outlined">
            <CardContent>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                Средняя стоимость
              </Typography>
              <Typography variant="h5">
                {avgCostPerSession.toFixed(2)} ₽
              </Typography>
              <Typography variant="caption" color="text.secondary">
                за парковку
              </Typography>
              <Typography variant="caption" display="block" color="text.secondary" sx={{ mt: 1 }}>
                Ср. время: {avgHoursPerSession.toFixed(1)}ч
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Charts */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        {/* Cost Trend Chart */}
        <Grid item xs={12} md={6}>
          <Paper variant="outlined" sx={{ p: 2 }}>
            <Typography variant="h6" sx={{ mb: 2 }}>
              Динамика расходов
            </Typography>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip
                  formatter={(value) => `${value.toFixed(2)} ₽`}
                  labelStyle={{ color: '#000' }}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="cost"
                  name="Расходы, ₽"
                  stroke="#1976d2"
                  strokeWidth={2}
                  dot={{ r: 4 }}
                  activeDot={{ r: 6 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* Sessions Bar Chart */}
        <Grid item xs={12} md={6}>
          <Paper variant="outlined" sx={{ p: 2 }}>
            <Typography variant="h6" sx={{ mb: 2 }}>
              Количество парковок
            </Typography>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip
                  formatter={(value) => `${value} шт`}
                  labelStyle={{ color: '#000' }}
                />
                <Legend />
                <Bar
                  dataKey="sessions"
                  name="Парковок"
                  fill="#0288d1"
                  radius={[8, 8, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* Hours Chart */}
        <Grid item xs={12}>
          <Paper variant="outlined" sx={{ p: 2 }}>
            <Typography variant="h6" sx={{ mb: 2 }}>
              Время парковки по месяцам
            </Typography>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip
                  formatter={(value) => `${value.toFixed(1)} ч`}
                  labelStyle={{ color: '#000' }}
                />
                <Legend />
                <Bar
                  dataKey="hours"
                  name="Часов"
                  fill="#ed6c02"
                  radius={[8, 8, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>
      </Grid>

      {/* Monthly Table */}
      <TableContainer>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell><strong>Месяц</strong></TableCell>
              <TableCell align="right"><strong>Парковок</strong></TableCell>
              <TableCell align="right"><strong>Часов</strong></TableCell>
              <TableCell align="right"><strong>Потрачено</strong></TableCell>
              <TableCell align="right"><strong>Средняя стоимость</strong></TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {stats.months.map((month, index) => {
              const count = stats.sessions_count[index];
              const hours = stats.total_hours[index];
              const cost = stats.total_cost[index];
              const avgCost = count > 0 ? cost / count : 0;

              return (
                <TableRow key={month}>
                  <TableCell>{formatMonth(month)}</TableCell>
                  <TableCell align="right">
                    <Chip label={count} size="small" color="info" />
                  </TableCell>
                  <TableCell align="right">{hours.toFixed(1)}</TableCell>
                  <TableCell align="right">
                    <Typography variant="body2" fontWeight="bold">
                      {cost.toFixed(2)} ₽
                    </Typography>
                  </TableCell>
                  <TableCell align="right">
                    {avgCost.toFixed(2)} ₽
                  </TableCell>
                </TableRow>
              );
            })}
            <TableRow sx={{ backgroundColor: 'action.hover' }}>
              <TableCell><strong>Итого</strong></TableCell>
              <TableCell align="right">
                <Chip label={totalSessions} size="small" color="primary" />
              </TableCell>
              <TableCell align="right"><strong>{totalHours.toFixed(1)}</strong></TableCell>
              <TableCell align="right">
                <Typography variant="body1" fontWeight="bold" color="primary">
                  {totalCost.toFixed(2)} ₽
                </Typography>
              </TableCell>
              <TableCell align="right">
                <strong>{avgCostPerSession.toFixed(2)} ₽</strong>
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </TableContainer>
    </Paper>
  );
};

export default AnalyticsDashboard;
