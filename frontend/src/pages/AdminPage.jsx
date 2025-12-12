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
  Alert,
  CircularProgress,
  Chip,
  TablePagination
} from '@mui/material';
import {
  People,
  DirectionsCar,
  LocalParking,
  Payment
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
  ResponsiveContainer
} from 'recharts';
import apiClient from '../services/api';

function AdminPage() {
  const [tabValue, setTabValue] = useState(0);
  const [stats, setStats] = useState(null);
  const [zones, setZones] = useState([]);
  const [bookings, setBookings] = useState([]);
  const [payments, setPayments] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Пагинация
  const [bookingsPage, setBookingsPage] = useState(0);
  const [bookingsRowsPerPage, setBookingsRowsPerPage] = useState(10);
  const [bookingsTotal, setBookingsTotal] = useState(0);

  const [paymentsPage, setPaymentsPage] = useState(0);
  const [paymentsRowsPerPage, setPaymentsRowsPerPage] = useState(10);
  const [paymentsTotal, setPaymentsTotal] = useState(0);

  const [usersPage, setUsersPage] = useState(0);
  const [usersRowsPerPage, setUsersRowsPerPage] = useState(10);
  const [usersTotal, setUsersTotal] = useState(0);

  // Данные графиков
  const [dailyStats, setDailyStats] = useState([]);
  const [chartLoading, setChartLoading] = useState(false);

  useEffect(() => {
    loadAdminData();
    loadChartData();
  }, []);

  const loadAdminData = async () => {
    try {
      console.log('AdminPage: Starting to load admin data...');
      setLoading(true);

      // Загружаем статистику
      console.log('AdminPage: Fetching stats from /api/admin/stats/overview');
      const statsResponse = await apiClient.get('/api/admin/stats/overview');
      console.log('AdminPage: Stats response:', statsResponse.data);
      setStats(statsResponse.data);

      // Загружаем зоны
      console.log('AdminPage: Fetching zones from /api/zones');
      const zonesResponse = await apiClient.get('/api/zones');
      console.log('AdminPage: Zones response:', zonesResponse.data);
      setZones(zonesResponse.data);

      setError(null);
      console.log('AdminPage: Successfully loaded all admin data');
    } catch (err) {
      console.error('AdminPage: Error loading admin data:', err);
      console.error('AdminPage: Error details:', {
        message: err.message,
        status: err.status,
        data: err.data
      });
      setError(err.message || 'Ошибка загрузки данных');
    } finally {
      setLoading(false);
    }
  };

  const loadChartData = async () => {
    try {
      setChartLoading(true);
      const response = await apiClient.get('/api/admin/stats/daily', {
        params: { days: 21 }
      });

      // Форматируем данные для отображения
      const formattedData = response.data.daily_stats.map(stat => ({
        ...stat,
        date: new Date(stat.date).toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit' })
      }));

      setDailyStats(formattedData);
    } catch (err) {
      console.error('Error loading chart data:', err);
    } finally {
      setChartLoading(false);
    }
  };

  const loadBookings = async (page = bookingsPage, rowsPerPage = bookingsRowsPerPage) => {
    try {
      const skip = page * rowsPerPage;
      const response = await apiClient.get('/api/admin/bookings', {
        params: { skip, limit: rowsPerPage }
      });
      setBookings(response.data.bookings || []);
      setBookingsTotal(response.data.total || 0);
    } catch (err) {
      console.error('Error loading bookings:', err);
    }
  };

  const loadPayments = async (page = paymentsPage, rowsPerPage = paymentsRowsPerPage) => {
    try {
      const skip = page * rowsPerPage;
      const response = await apiClient.get('/api/admin/payments', {
        params: { skip, limit: rowsPerPage }
      });
      setPayments(response.data.payments || []);
      setPaymentsTotal(response.data.total || 0);
    } catch (err) {
      console.error('Error loading payments:', err);
    }
  };

  const loadUsers = async (page = usersPage, rowsPerPage = usersRowsPerPage) => {
    try {
      const skip = page * rowsPerPage;
      const response = await apiClient.get('/api/admin/users', {
        params: { skip, limit: rowsPerPage }
      });
      setUsers(response.data.users || []);
      setUsersTotal(response.data.total || 0);
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

  // Обработчики пагинации для бронирований
  const handleBookingsChangePage = (event, newPage) => {
    setBookingsPage(newPage);
    loadBookings(newPage, bookingsRowsPerPage);
  };

  const handleBookingsChangeRowsPerPage = (event) => {
    const newRowsPerPage = parseInt(event.target.value, 10);
    setBookingsRowsPerPage(newRowsPerPage);
    setBookingsPage(0);
    loadBookings(0, newRowsPerPage);
  };

  // Обработчики пагинации для платежей
  const handlePaymentsChangePage = (event, newPage) => {
    setPaymentsPage(newPage);
    loadPayments(newPage, paymentsRowsPerPage);
  };

  const handlePaymentsChangeRowsPerPage = (event) => {
    const newRowsPerPage = parseInt(event.target.value, 10);
    setPaymentsRowsPerPage(newRowsPerPage);
    setPaymentsPage(0);
    loadPayments(0, newRowsPerPage);
  };

  // Обработчики пагинации для пользователей
  const handleUsersChangePage = (event, newPage) => {
    setUsersPage(newPage);
    loadUsers(newPage, usersRowsPerPage);
  };

  const handleUsersChangeRowsPerPage = (event) => {
    const newRowsPerPage = parseInt(event.target.value, 10);
    setUsersRowsPerPage(newRowsPerPage);
    setUsersPage(0);
    loadUsers(0, newRowsPerPage);
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
        <Alert severity="error">
          {error === 'Not enough permissions. Admin access required.'
            ? 'У вас нет прав администратора. Пожалуйста, войдите с аккаунтом администратора.'
            : error}
        </Alert>
        {error === 'Not enough permissions. Admin access required.' && (
          <Typography variant="body2" sx={{ mt: 2 }}>
            Для доступа к админ-панели используйте аккаунт: admin@parking.com
          </Typography>
        )}
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
              {/* График выручки */}
              <Typography variant="h6" gutterBottom>
                Выручка за последние 3 недели
              </Typography>
              {chartLoading ? (
                <Box display="flex" justifyContent="center" p={4}>
                  <CircularProgress />
                </Box>
              ) : (
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={dailyStats}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="date"
                      angle={-45}
                      textAnchor="end"
                      height={80}
                    />
                    <YAxis />
                    <Tooltip
                      formatter={(value) => `${Number(value).toFixed(2)} ₽`}
                      labelStyle={{ color: '#000' }}
                    />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="revenue"
                      stroke="#f44336"
                      name="Выручка (₽)"
                      strokeWidth={2}
                      dot={{ r: 3 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              )}

              {/* График бронирований */}
              <Typography variant="h6" gutterBottom sx={{ mt: 4 }}>
                Бронирования за последние 3 недели
              </Typography>
              {chartLoading ? (
                <Box display="flex" justifyContent="center" p={4}>
                  <CircularProgress />
                </Box>
              ) : (
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={dailyStats}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="date"
                      angle={-45}
                      textAnchor="end"
                      height={80}
                    />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar
                      dataKey="bookings"
                      fill="#4caf50"
                      name="Бронирований"
                    />
                  </BarChart>
                </ResponsiveContainer>
              )}

              <Typography variant="h6" gutterBottom sx={{ mt: 4 }}>
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
            <>
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
              <TablePagination
                component="div"
                count={bookingsTotal}
                page={bookingsPage}
                onPageChange={handleBookingsChangePage}
                rowsPerPage={bookingsRowsPerPage}
                onRowsPerPageChange={handleBookingsChangeRowsPerPage}
                rowsPerPageOptions={[10, 25, 50, 100]}
                labelRowsPerPage="Строк на странице:"
                labelDisplayedRows={({ from, to, count }) => `${from}-${to} из ${count}`}
              />
            </>
          )}

          {/* Платежи */}
          {tabValue === 3 && (
            <>
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
              <TablePagination
                component="div"
                count={paymentsTotal}
                page={paymentsPage}
                onPageChange={handlePaymentsChangePage}
                rowsPerPage={paymentsRowsPerPage}
                onRowsPerPageChange={handlePaymentsChangeRowsPerPage}
                rowsPerPageOptions={[10, 25, 50, 100]}
                labelRowsPerPage="Строк на странице:"
                labelDisplayedRows={({ from, to, count }) => `${from}-${to} из ${count}`}
              />
            </>
          )}

          {/* Пользователи */}
          {tabValue === 4 && (
            <>
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
              <TablePagination
                component="div"
                count={usersTotal}
                page={usersPage}
                onPageChange={handleUsersChangePage}
                rowsPerPage={usersRowsPerPage}
                onRowsPerPageChange={handleUsersChangeRowsPerPage}
                rowsPerPageOptions={[10, 25, 50, 100]}
                labelRowsPerPage="Строк на странице:"
                labelDisplayedRows={({ from, to, count }) => `${from}-${to} из ${count}`}
              />
            </>
          )}
        </Box>
      </Paper>
    </Container>
  );
}

export default AdminPage;
