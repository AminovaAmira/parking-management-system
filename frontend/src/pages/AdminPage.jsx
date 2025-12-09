import React, { useState, useEffect } from 'react';
import {
  Container,
  Grid,
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
  CircularProgress,
  Chip
} from '@mui/material';
import {
  People,
  DirectionsCar,
  LocalParking,
  Payment,
  TrendingUp
} from '@mui/icons-material';
import parkingService from '../services/parkingService';

function AdminPage() {
  const [tabValue, setTabValue] = useState(0);
  const [stats, setStats] = useState(null);
  const [zones, setZones] = useState([]);
  const [bookings, setBookings] = useState([]);
  const [payments, setPayments] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadAdminData();
  }, []);

  const loadAdminData = async () => {
    try {
      setLoading(true);
      // Загружаем статистику
      const statsResponse = await parkingService.get('/admin/stats/overview');
      setStats(statsResponse.data);

      // Загружаем зоны
      const zonesResponse = await parkingService.get('/zones');
      setZones(zonesResponse.data);

      setError(null);
    } catch (err) {
      console.error('Error loading admin data:', err);
      setError(err.response?.data?.detail || 'Ошибка загрузки данных');
    } finally {
      setLoading(false);
    }
  };

  const loadBookings = async () => {
    try {
      const response = await parkingService.get('/admin/bookings');
      setBookings(response.data.bookings || []);
    } catch (err) {
      console.error('Error loading bookings:', err);
    }
  };

  const loadPayments = async () => {
    try {
      const response = await parkingService.get('/admin/payments');
      setPayments(response.data.payments || []);
    } catch (err) {
      console.error('Error loading payments:', err);
    }
  };

  const loadUsers = async () => {
    try {
      const response = await parkingService.get('/admin/users');
      setUsers(response.data.users || []);
    } catch (err) {
      console.error('Error loading users:', err);
    }
  };

  const handleTabChange = async (event, newValue) => {
    setTabValue(newValue);
    if (newValue === 2 && bookings.length === 0) {
      await loadBookings();
    } else if (newValue === 3 && payments.length === 0) {
      await loadPayments();
    } else if (newValue === 4 && users.length === 0) {
      await loadUsers();
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="80vh">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Alert severity="error">{error}</Alert>
        <Typography variant="body2" sx={{ mt: 2 }}>
          У вас нет прав администратора. Пожалуйста, войдите с аккаунтом администратора.
        </Typography>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        Панель Администратора
      </Typography>

      {/* Статистика */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Пользователей
                  </Typography>
                  <Typography variant="h4">
                    {stats?.users_count || 0}
                  </Typography>
                </Box>
                <People sx={{ fontSize: 48, color: 'primary.main', opacity: 0.3 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Активных сессий
                  </Typography>
                  <Typography variant="h4">
                    {stats?.active_sessions || 0}
                  </Typography>
                </Box>
                <DirectionsCar sx={{ fontSize: 48, color: 'success.main', opacity: 0.3 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Парковочных мест
                  </Typography>
                  <Typography variant="h4">
                    {stats?.parking_spots?.total || 0}
                  </Typography>
                  <Typography variant="caption" color="textSecondary">
                    Занято: {stats?.parking_spots?.occupied || 0}
                  </Typography>
                </Box>
                <LocalParking sx={{ fontSize: 48, color: 'warning.main', opacity: 0.3 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Общая выручка
                  </Typography>
                  <Typography variant="h4">
                    {stats?.total_revenue?.toFixed(2) || 0} ₽
                  </Typography>
                </Box>
                <Payment sx={{ fontSize: 48, color: 'error.main', opacity: 0.3 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Табы */}
      <Paper>
        <Tabs value={tabValue} onChange={handleTabChange}>
          <Tab label="Обзор" />
          <Tab label="Парковочные зоны" />
          <Tab label="Бронирования" />
          <Tab label="Платежи" />
          <Tab label="Пользователи" />
        </Tabs>

        <Box sx={{ p: 3 }}>
          {/* Обзор */}
          {tabValue === 0 && (
            <Box>
              <Typography variant="h6" gutterBottom>
                Занятость парковочных мест
              </Typography>
              <Typography variant="body1">
                Всего мест: {stats?.parking_spots?.total || 0}
              </Typography>
              <Typography variant="body1">
                Занято: {stats?.parking_spots?.occupied || 0}
              </Typography>
              <Typography variant="body1">
                Свободно: {stats?.parking_spots?.available || 0}
              </Typography>
              <Typography variant="body1">
                Процент занятости: {stats?.parking_spots?.occupancy_rate || 0}%
              </Typography>

              <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>
                Бронирования по статусам
              </Typography>
              {stats?.bookings_by_status && Object.entries(stats.bookings_by_status).map(([status, count]) => (
                <Typography key={status} variant="body1">
                  {status}: {count}
                </Typography>
              ))}
            </Box>
          )}

          {/* Парковочные зоны */}
          {tabValue === 1 && (
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Название</TableCell>
                    <TableCell>Адрес</TableCell>
                    <TableCell align="center">Всего мест</TableCell>
                    <TableCell align="center">Доступно</TableCell>
                    <TableCell align="center">Статус</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {zones.map((zone) => (
                    <TableRow key={zone.zone_id}>
                      <TableCell>{zone.name}</TableCell>
                      <TableCell>{zone.address}</TableCell>
                      <TableCell align="center">{zone.total_spots}</TableCell>
                      <TableCell align="center">{zone.available_spots}</TableCell>
                      <TableCell align="center">
                        <Chip
                          label={zone.is_active ? 'Активна' : 'Неактивна'}
                          color={zone.is_active ? 'success' : 'default'}
                          size="small"
                        />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}

          {/* Бронирования */}
          {tabValue === 2 && (
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>ID</TableCell>
                    <TableCell>Клиент</TableCell>
                    <TableCell>Время начала</TableCell>
                    <TableCell>Время окончания</TableCell>
                    <TableCell>Статус</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {bookings.map((booking) => (
                    <TableRow key={booking.booking_id}>
                      <TableCell>{booking.booking_id.substring(0, 8)}</TableCell>
                      <TableCell>{booking.customer_id.substring(0, 8)}</TableCell>
                      <TableCell>{new Date(booking.start_time).toLocaleString()}</TableCell>
                      <TableCell>{new Date(booking.end_time).toLocaleString()}</TableCell>
                      <TableCell>
                        <Chip
                          label={booking.status}
                          color={
                            booking.status === 'confirmed' ? 'success' :
                            booking.status === 'pending' ? 'warning' : 'default'
                          }
                          size="small"
                        />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}

          {/* Платежи */}
          {tabValue === 3 && (
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>ID</TableCell>
                    <TableCell>Сумма</TableCell>
                    <TableCell>Метод оплаты</TableCell>
                    <TableCell>Статус</TableCell>
                    <TableCell>Дата</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {payments.map((payment) => (
                    <TableRow key={payment.payment_id}>
                      <TableCell>{payment.payment_id.substring(0, 8)}</TableCell>
                      <TableCell>{payment.amount} ₽</TableCell>
                      <TableCell>{payment.payment_method}</TableCell>
                      <TableCell>
                        <Chip
                          label={payment.status}
                          color={
                            payment.status === 'completed' ? 'success' :
                            payment.status === 'pending' ? 'warning' : 'error'
                          }
                          size="small"
                        />
                      </TableCell>
                      <TableCell>{new Date(payment.created_at).toLocaleString()}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}

          {/* Пользователи */}
          {tabValue === 4 && (
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Email</TableCell>
                    <TableCell>Имя</TableCell>
                    <TableCell>Телефон</TableCell>
                    <TableCell>Роль</TableCell>
                    <TableCell>Дата регистрации</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {users.map((user) => (
                    <TableRow key={user.customer_id}>
                      <TableCell>{user.email}</TableCell>
                      <TableCell>{user.first_name} {user.last_name}</TableCell>
                      <TableCell>{user.phone}</TableCell>
                      <TableCell>
                        <Chip
                          label={user.is_admin ? 'Админ' : 'Пользователь'}
                          color={user.is_admin ? 'error' : 'default'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>{new Date(user.created_at).toLocaleString()}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </Box>
      </Paper>
    </Container>
  );
}

export default AdminPage;
