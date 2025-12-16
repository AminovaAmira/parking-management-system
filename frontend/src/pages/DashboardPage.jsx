import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Box,
  Typography,
  Button,
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
  TablePagination,
  Chip,
  CircularProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
} from '@mui/material';
import { DateTimePicker } from '@mui/x-date-pickers/DateTimePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import dayjs from 'dayjs';
import 'dayjs/locale/ru';
import { useAuth } from '../context/AuthContext';
import parkingService from '../services/parkingService';
import AnalyticsDashboard from '../components/AnalyticsDashboard';
import OCRUpload from '../components/OCRUpload';
import ParkingMapView from '../components/ParkingMapView';
import PaymentDialog from '../components/PaymentDialog';
import BalanceTopUpDialog from '../components/BalanceTopUpDialog';

// Set dayjs locale to Russian
dayjs.locale('ru');

const DashboardPage = () => {
  const navigate = useNavigate();
  const { user, logout, isAuthenticated, updateUser } = useAuth();

  const [bookings, setBookings] = useState([]);
  const [zones, setZones] = useState([]);
  const [vehicles, setVehicles] = useState([]);
  const [activeSessions, setActiveSessions] = useState([]);
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Dialog states
  const [openVehicleDialog, setOpenVehicleDialog] = useState(false);
  const [openBookingDialog, setOpenBookingDialog] = useState(false);
  const [openPaymentDialog, setOpenPaymentDialog] = useState(false);
  const [openBalanceDialog, setOpenBalanceDialog] = useState(false);
  const [selectedPayment, setSelectedPayment] = useState(null);
  const [availableSpots, setAvailableSpots] = useState([]);
  const [selectedZone, setSelectedZone] = useState('');
  const [loadingSpots, setLoadingSpots] = useState(false);
  const [viewMode, setViewMode] = useState('list'); // 'list' or 'map'

  // Pagination states
  const [bookingsPage, setBookingsPage] = useState(0);
  const [bookingsRowsPerPage, setBookingsRowsPerPage] = useState(10);
  const [paymentsPage, setPaymentsPage] = useState(0);
  const [paymentsRowsPerPage, setPaymentsRowsPerPage] = useState(10);
  const [newVehicle, setNewVehicle] = useState({
    license_plate: '',
    brand: '',
    model: '',
    color: '',
    vehicle_type: 'sedan',
  });
  const [newBooking, setNewBooking] = useState({
    spot_id: '',
    vehicle_id: '',
    start_time: null,
    end_time: null,
  });

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login');
    } else {
      loadDashboardData();
    }
  }, [isAuthenticated, navigate]);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError('');

      const [bookingsData, zonesData, vehiclesData, sessionsData, paymentsData] = await Promise.all([
        parkingService.getMyBookings(),
        parkingService.getZones(),
        parkingService.getMyVehicles(),
        parkingService.getActiveSessions(),
        parkingService.getPayments(),
      ]);

      // Filter out completed bookings from the list
      const activeBookings = bookingsData.filter(b => b.status !== 'completed');

      setBookings(activeBookings);
      setZones(zonesData);
      setVehicles(vehiclesData);
      setActiveSessions(sessionsData);
      setPayments(paymentsData);
    } catch (err) {
      setError(err.message || 'Ошибка загрузки данных');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const handleAddVehicle = async () => {
    try {
      await parkingService.addVehicle(newVehicle);
      setOpenVehicleDialog(false);
      setNewVehicle({
        license_plate: '',
        brand: '',
        model: '',
        color: '',
        vehicle_type: 'sedan',
      });
      await loadDashboardData();
    } catch (err) {
      setError(err.message || 'Ошибка добавления автомобиля');
    }
  };

  const handleDeleteVehicle = async (vehicleId) => {
    if (window.confirm('Удалить автомобиль?')) {
      try {
        await parkingService.deleteVehicle(vehicleId);
        await loadDashboardData();
      } catch (err) {
        setError(err.message || 'Ошибка удаления автомобиля');
      }
    }
  };

  const handleCancelBooking = async (bookingId) => {
    if (window.confirm('Отменить бронирование?')) {
      try {
        await parkingService.cancelBooking(bookingId);
        await loadDashboardData();
      } catch (err) {
        setError(err.message || 'Ошибка отмены бронирования');
      }
    }
  };

  const handleConfirmEntry = async (booking) => {
    if (window.confirm('Подтвердить въезд на территорию? Начнется парковочная сессия.')) {
      try {
        // Создаем парковочную сессию с привязкой к бронированию
        await parkingService.startSession({
          vehicle_id: booking.vehicle.vehicle_id,
          spot_id: booking.spot.spot_id,
          booking_id: booking.booking_id
        });
        await loadDashboardData();
      } catch (err) {
        setError(err.message || 'Ошибка подтверждения въезда');
      }
    }
  };

  const handleZoneChange = async (zoneId) => {
    setSelectedZone(zoneId);
    setNewBooking({ ...newBooking, spot_id: '' });

    if (!zoneId) {
      setAvailableSpots([]);
      return;
    }

    // Check if time is selected
    if (!newBooking.start_time || !newBooking.end_time) {
      setError('Пожалуйста, сначала выберите время начала и окончания');
      setSelectedZone('');
      return;
    }

    try {
      setLoadingSpots(true);
      // Convert dayjs to ISO string for API request
      const startTimeISO = newBooking.start_time.toISOString();
      const endTimeISO = newBooking.end_time.toISOString();

      // Get spots available for the selected time range
      const spots = await parkingService.getAvailableSpotsForTime(
        zoneId,
        startTimeISO,
        endTimeISO
      );
      setAvailableSpots(spots);

      if (spots.length === 0) {
        setError('В выбранной зоне нет свободных мест на указанное время');
      }
    } catch (err) {
      setError(err.message || 'Ошибка загрузки мест');
      setAvailableSpots([]);
    } finally {
      setLoadingSpots(false);
    }
  };

  const handleSpotSelectFromMap = (spot) => {
    setNewBooking({ ...newBooking, spot_id: spot.spot_id });
  };

  const handleCreateBooking = async () => {
    try {
      // Validation
      if (!newBooking.vehicle_id || !newBooking.spot_id || !newBooking.start_time || !newBooking.end_time) {
        setError('Пожалуйста, заполните все поля');
        return;
      }

      // Convert dayjs to ISO string for API
      const bookingData = {
        vehicle_id: newBooking.vehicle_id,
        spot_id: newBooking.spot_id,
        start_time: newBooking.start_time.toISOString(),
        end_time: newBooking.end_time.toISOString(),
      };

      await parkingService.createBooking(bookingData);
      setOpenBookingDialog(false);
      setNewBooking({
        spot_id: '',
        vehicle_id: '',
        start_time: null,
        end_time: null,
      });
      setSelectedZone('');
      setAvailableSpots([]);
      await loadDashboardData();
    } catch (err) {
      setError(err.message || 'Ошибка создания бронирования');
    }
  };

  const handleEndSession = async (sessionId) => {
    if (window.confirm('Завершить парковочную сессию? Будет рассчитана итоговая стоимость.')) {
      try {
        const exitTime = new Date().toISOString();
        await parkingService.endSession(sessionId, { exit_time: exitTime });
        await loadDashboardData();
      } catch (err) {
        setError(err.message || 'Ошибка завершения сессии');
      }
    }
  };

  const handleOpenPaymentDialog = (payment) => {
    setSelectedPayment(payment);
    setOpenPaymentDialog(true);
  };

  const handleClosePaymentDialog = () => {
    setOpenPaymentDialog(false);
    setSelectedPayment(null);
  };

  const handlePayment = async (paymentId, paymentMethod) => {
    try {
      // Simulate payment processing
      await parkingService.updatePaymentStatus(paymentId, {
        status: 'completed',
        transaction_id: `TXN-${Date.now()}`
      });
      await loadDashboardData();
    } catch (err) {
      setError(err.message || 'Ошибка обработки платежа');
      throw err;
    }
  };

  const handleBalanceTopUpSuccess = async () => {
    // Refresh user data to get updated balance
    await updateUser();
    // Reload dashboard data
    await loadDashboardData();
  };

  const getPaymentMethodText = (method) => {
    switch (method) {
      case 'card':
        return 'Карта';
      case 'cash':
        return 'Наличные';
      case 'online':
        return 'Онлайн';
      case 'pending':
        return 'Не выбран';
      default:
        return method;
    }
  };

  const getPaymentStatusColor = (status) => {
    switch (status) {
      case 'pending':
        return 'warning';
      case 'completed':
        return 'success';
      case 'failed':
        return 'error';
      case 'refunded':
        return 'default';
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

  const formatDuration = (entryTime) => {
    const entry = new Date(entryTime);
    const now = new Date();
    const diff = Math.floor((now - entry) / 1000 / 60); // minutes

    const hours = Math.floor(diff / 60);
    const minutes = diff % 60;

    return `${hours}ч ${minutes}мин`;
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'pending':
        return 'warning';
      case 'confirmed':
        return 'success';
      case 'cancelled':
        return 'error';
      case 'completed':
        return 'default';
      default:
        return 'default';
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'pending':
        return 'Ожидает';
      case 'confirmed':
        return 'Подтверждено';
      case 'cancelled':
        return 'Отменено';
      case 'completed':
        return 'Завершено';
      default:
        return status;
    }
  };

  if (!user) {
    return null;
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
        <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Box>
              <Typography variant="h4" gutterBottom>
                Добро пожаловать, {user.first_name}!
              </Typography>
              <Typography variant="body1" color="text.secondary">
                {user.email}
              </Typography>
              <Box sx={{ mt: 1, display: 'flex', gap: 1, alignItems: 'center' }}>
                <Chip
                  label={`Баланс: ${parseFloat(user.balance || 0).toFixed(2)} ₽`}
                  color="success"
                  sx={{ fontWeight: 'bold' }}
                />
                <Button
                  size="small"
                  variant="contained"
                  color="success"
                  onClick={() => setOpenBalanceDialog(true)}
                >
                  Пополнить
                </Button>
              </Box>
            </Box>
            <Box sx={{ display: 'flex', gap: 2 }}>
              <Button variant="outlined" color="info" onClick={() => navigate('/history')}>
                История
              </Button>
              <Button variant="outlined" color="primary" onClick={() => navigate('/profile')}>
                Профиль
              </Button>
              {user?.is_admin && (
                <Button variant="outlined" color="error" onClick={() => navigate('/admin')}>
                  Админ-панель
                </Button>
              )}
              <Button variant="outlined" color="secondary" onClick={handleLogout}>
                Выйти
              </Button>
            </Box>
          </Box>
        </Paper>

        {error && (
          <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError('')}>
            {error}
          </Alert>
        )}

        {/* Statistics Cards */}
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Typography variant="h6" color="success.main">
                  {activeSessions.length}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Активных парковок
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Typography variant="h6" color="primary">
                  {bookings.length}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Активных бронирований
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Typography variant="h6" color="primary">
                  {vehicles.length}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Автомобилей
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Typography variant="h6" color="primary">
                  {zones.reduce((sum, zone) => sum + zone.available_spots, 0)}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Свободных мест
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Analytics Dashboard */}
        <AnalyticsDashboard />

        {/* My Vehicles */}
        <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h5">
              Мои автомобили
            </Typography>
            <Button variant="contained" onClick={() => setOpenVehicleDialog(true)}>
              Добавить автомобиль
            </Button>
          </Box>
          {vehicles.length === 0 ? (
            <Typography color="text.secondary">Нет зарегистрированных автомобилей</Typography>
          ) : (
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Номер</TableCell>
                    <TableCell>Марка</TableCell>
                    <TableCell>Модель</TableCell>
                    <TableCell>Цвет</TableCell>
                    <TableCell>Тип</TableCell>
                    <TableCell>Действия</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {vehicles.map((vehicle) => (
                    <TableRow key={vehicle.vehicle_id}>
                      <TableCell>{vehicle.license_plate}</TableCell>
                      <TableCell>{vehicle.brand || '-'}</TableCell>
                      <TableCell>{vehicle.model}</TableCell>
                      <TableCell>{vehicle.color}</TableCell>
                      <TableCell>{vehicle.vehicle_type}</TableCell>
                      <TableCell>
                        <Button
                          size="small"
                          color="error"
                          onClick={() => handleDeleteVehicle(vehicle.vehicle_id)}
                        >
                          Удалить
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </Paper>

        {/* Active Parking Sessions */}
        {activeSessions.length > 0 && (
          <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
            <Typography variant="h5" sx={{ mb: 2 }}>
              Активные парковки
            </Typography>
            <Grid container spacing={2}>
              {activeSessions.map((session) => (
                <Grid item xs={12} md={6} key={session.session_id}>
                  <Card variant="outlined" sx={{ border: '2px solid', borderColor: 'success.main' }}>
                    <CardContent>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                        <Typography variant="h6" color="success.main">
                          Парковка активна
                        </Typography>
                        <Chip label="АКТИВНО" color="success" size="small" />
                      </Box>

                      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                        <strong>Время въезда:</strong> {new Date(session.entry_time).toLocaleString('ru-RU')}
                      </Typography>

                      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                        <strong>Длительность:</strong> {formatDuration(session.entry_time)}
                      </Typography>

                      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                        <strong>Место:</strong> {session.spot?.spot_number || 'N/A'}
                      </Typography>

                      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                        <strong>Зона:</strong> {session.zone?.name || 'N/A'}
                      </Typography>

                      <Button
                        variant="contained"
                        color="error"
                        fullWidth
                        onClick={() => handleEndSession(session.session_id)}
                      >
                        Завершить парковку
                      </Button>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </Paper>
        )}

        {/* My Bookings */}
        <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h5">
              Мои бронирования
            </Typography>
            <Button
              variant="contained"
              color="primary"
              onClick={() => setOpenBookingDialog(true)}
              disabled={vehicles.length === 0}
            >
              Создать бронирование
            </Button>
          </Box>
          {vehicles.length === 0 && (
            <Alert severity="info" sx={{ mb: 2 }}>
              Добавьте автомобиль, чтобы создать бронирование
            </Alert>
          )}
          {bookings.length === 0 ? (
            <Typography color="text.secondary">Нет активных бронирований</Typography>
          ) : (
            <>
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Место</TableCell>
                      <TableCell>Начало</TableCell>
                      <TableCell>Окончание</TableCell>
                      <TableCell>Статус</TableCell>
                      <TableCell>Действия</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {bookings
                      .slice(bookingsPage * bookingsRowsPerPage, bookingsPage * bookingsRowsPerPage + bookingsRowsPerPage)
                      .map((booking) => (
                        <TableRow key={booking.booking_id}>
                          <TableCell>
                            <strong>{booking.spot?.spot_number || 'N/A'}</strong>
                            <br />
                            <Typography variant="caption" color="text.secondary">
                              {booking.zone?.name || 'N/A'}
                            </Typography>
                          </TableCell>
                          <TableCell>{new Date(booking.start_time).toLocaleString('ru-RU')}</TableCell>
                          <TableCell>{new Date(booking.end_time).toLocaleString('ru-RU')}</TableCell>
                          <TableCell>
                            <Chip
                              label={getStatusText(booking.status)}
                              color={getStatusColor(booking.status)}
                              size="small"
                            />
                          </TableCell>
                          <TableCell>
                            {booking.status === 'pending' && (
                              <Box sx={{ display: 'flex', gap: 1 }}>
                                <Button
                                  size="small"
                                  color="success"
                                  variant="contained"
                                  onClick={() => handleConfirmEntry(booking)}
                                >
                                  Подтвердить въезд
                                </Button>
                                <Button
                                  size="small"
                                  color="error"
                                  onClick={() => handleCancelBooking(booking.booking_id)}
                                >
                                  Отменить
                                </Button>
                              </Box>
                            )}
                            {booking.status === 'confirmed' && (
                              <Chip
                                label="Парковка началась"
                                color="success"
                                size="small"
                              />
                            )}
                          </TableCell>
                        </TableRow>
                      ))}
                  </TableBody>
                </Table>
              </TableContainer>
              <TablePagination
                rowsPerPageOptions={[5, 10, 25, 50]}
                component="div"
                count={bookings.length}
                rowsPerPage={bookingsRowsPerPage}
                page={bookingsPage}
                onPageChange={(e, newPage) => setBookingsPage(newPage)}
                onRowsPerPageChange={(e) => {
                  setBookingsRowsPerPage(parseInt(e.target.value, 10));
                  setBookingsPage(0);
                }}
                labelRowsPerPage="Строк на странице:"
                labelDisplayedRows={({ from, to, count }) => `${from}-${to} из ${count}`}
              />
            </>
          )}
        </Paper>

        {/* My Payments */}
        <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
          <Typography variant="h5" sx={{ mb: 2 }}>
            Мои платежи
          </Typography>
          {payments.length === 0 ? (
            <Typography color="text.secondary">Нет платежей</Typography>
          ) : (
            <>
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Место/Период</TableCell>
                      <TableCell>Сумма</TableCell>
                      <TableCell>Метод оплаты</TableCell>
                      <TableCell>Статус</TableCell>
                      <TableCell>Действия</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {payments
                      .slice(paymentsPage * paymentsRowsPerPage, paymentsPage * paymentsRowsPerPage + paymentsRowsPerPage)
                      .map((payment) => (
                        <TableRow key={payment.payment_id}>
                          <TableCell>
                            {payment.spot && payment.zone ? (
                              <>
                                <Typography variant="body2" fontWeight="bold">
                                  Место {payment.spot.spot_number}
                                </Typography>
                                <Typography variant="body2" color="text.secondary" display="block">
                                  {payment.zone.name}
                                </Typography>
                                {payment.booking && (
                                  <Typography variant="body2" color="text.secondary" display="block">
                                    {new Date(payment.booking.start_time).toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit' })}
                                    {' '}
                                    {new Date(payment.booking.start_time).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })}
                                    {' - '}
                                    {new Date(payment.booking.end_time).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })}
                                  </Typography>
                                )}
                              </>
                            ) : (
                              <Typography variant="body2" color="text.secondary">
                                {new Date(payment.created_at).toLocaleDateString('ru-RU')}
                              </Typography>
                            )}
                          </TableCell>
                          <TableCell>
                            <Typography variant="body1" fontWeight="bold">
                              {parseFloat(payment.amount).toFixed(2)} ₽
                            </Typography>
                          </TableCell>
                          <TableCell>
                            {getPaymentMethodText(payment.payment_method)}
                          </TableCell>
                          <TableCell>
                            <Chip
                              label={getPaymentStatusText(payment.status)}
                              color={getPaymentStatusColor(payment.status)}
                              size="small"
                            />
                          </TableCell>
                          <TableCell>
                            {payment.status === 'pending' && (
                              <Button
                                size="small"
                                color="success"
                                variant="contained"
                                onClick={() => handleOpenPaymentDialog(payment)}
                              >
                                Оплатить
                              </Button>
                            )}
                          </TableCell>
                        </TableRow>
                      ))}
                  </TableBody>
                </Table>
              </TableContainer>
              <TablePagination
                rowsPerPageOptions={[5, 10, 25, 50]}
                component="div"
                count={payments.length}
                rowsPerPage={paymentsRowsPerPage}
                page={paymentsPage}
                onPageChange={(e, newPage) => setPaymentsPage(newPage)}
                onRowsPerPageChange={(e) => {
                  setPaymentsRowsPerPage(parseInt(e.target.value, 10));
                  setPaymentsPage(0);
                }}
                labelRowsPerPage="Строк на странице:"
                labelDisplayedRows={({ from, to, count }) => `${from}-${to} из ${count}`}
              />
            </>
          )}
        </Paper>

        {/* Parking Zones */}
        <Paper elevation={2} sx={{ p: 3 }}>
          <Typography variant="h5" sx={{ mb: 2 }}>
            Парковочные зоны
          </Typography>
          <Grid container spacing={2}>
            {zones.map((zone) => (
              <Grid item xs={12} md={6} key={zone.zone_id}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="h6">
                      {zone.name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      {zone.address}
                    </Typography>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Typography variant="body2">
                        Свободно: <strong>{zone.available_spots}</strong> из {zone.total_spots}
                      </Typography>
                      <Chip
                        label={zone.is_active ? 'Активна' : 'Неактивна'}
                        color={zone.is_active ? 'success' : 'default'}
                        size="small"
                      />
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Paper>
      </Box>

      {/* Add Vehicle Dialog */}
      <Dialog open={openVehicleDialog} onClose={() => setOpenVehicleDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Добавить автомобиль</DialogTitle>
        <DialogContent>
          <OCRUpload
            onPlateRecognized={(plate) => setNewVehicle({ ...newVehicle, license_plate: plate })}
          />
          <TextField
            margin="dense"
            label="Номер (А123ВС777)"
            fullWidth
            value={newVehicle.license_plate}
            onChange={(e) => setNewVehicle({ ...newVehicle, license_plate: e.target.value })}
          />
          <TextField
            margin="dense"
            label="Марка"
            fullWidth
            value={newVehicle.brand}
            onChange={(e) => setNewVehicle({ ...newVehicle, brand: e.target.value })}
          />
          <TextField
            margin="dense"
            label="Модель"
            fullWidth
            value={newVehicle.model}
            onChange={(e) => setNewVehicle({ ...newVehicle, model: e.target.value })}
          />
          <TextField
            margin="dense"
            label="Цвет"
            fullWidth
            value={newVehicle.color}
            onChange={(e) => setNewVehicle({ ...newVehicle, color: e.target.value })}
          />
          <TextField
            margin="dense"
            label="Тип"
            select
            fullWidth
            value={newVehicle.vehicle_type}
            onChange={(e) => setNewVehicle({ ...newVehicle, vehicle_type: e.target.value })}
          >
            <MenuItem value="sedan">Седан</MenuItem>
            <MenuItem value="suv">Внедорожник</MenuItem>
            <MenuItem value="truck">Грузовик</MenuItem>
            <MenuItem value="motorcycle">Мотоцикл</MenuItem>
          </TextField>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenVehicleDialog(false)}>Отмена</Button>
          <Button onClick={handleAddVehicle} variant="contained">Добавить</Button>
        </DialogActions>
      </Dialog>

      {/* Create Booking Dialog */}
      <Dialog
        open={openBookingDialog}
        onClose={() => setOpenBookingDialog(false)}
        maxWidth={viewMode === 'map' ? 'lg' : 'sm'}
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span>Создать бронирование</span>
            <Box>
              <Button
                size="small"
                variant={viewMode === 'list' ? 'contained' : 'outlined'}
                onClick={() => setViewMode('list')}
                sx={{ mr: 1 }}
              >
                Список
              </Button>
              <Button
                size="small"
                variant={viewMode === 'map' ? 'contained' : 'outlined'}
                onClick={() => setViewMode('map')}
              >
                План
              </Button>
            </Box>
          </Box>
        </DialogTitle>
        <DialogContent>
          <Alert severity="info" sx={{ mb: 2 }}>
            {viewMode === 'list'
              ? 'Выберите время, затем парковочную зону. Система покажет только свободные места на выбранное время.'
              : 'Выберите время, затем выберите место на плане парковки.'}
          </Alert>

          <Alert severity="warning" sx={{ mb: 2 }}>
            <strong>Важно:</strong> При создании бронирования стоимость будет сразу списана с вашего баланса.
            После завершения парковки неиспользованные средства будут возвращены, либо будет списана доплата за превышение времени.
          </Alert>

          <TextField
            margin="dense"
            label="Выберите автомобиль"
            select
            fullWidth
            value={newBooking.vehicle_id}
            onChange={(e) => setNewBooking({ ...newBooking, vehicle_id: e.target.value })}
          >
            {vehicles.map((vehicle) => (
              <MenuItem key={vehicle.vehicle_id} value={vehicle.vehicle_id}>
                {vehicle.license_plate} - {vehicle.model}
              </MenuItem>
            ))}
          </TextField>

          <LocalizationProvider dateAdapter={AdapterDayjs} adapterLocale="ru">
            <DateTimePicker
              label="Начало бронирования"
              value={newBooking.start_time}
              onChange={(newValue) => {
                setNewBooking({ ...newBooking, start_time: newValue, spot_id: '' });
                setSelectedZone('');
                setAvailableSpots([]);
              }}
              minDateTime={dayjs()}
              slotProps={{
                textField: {
                  fullWidth: true,
                  margin: "dense",
                },
              }}
              ampm={false}
            />
          </LocalizationProvider>

          <LocalizationProvider dateAdapter={AdapterDayjs} adapterLocale="ru">
            <DateTimePicker
              label="Окончание бронирования"
              value={newBooking.end_time}
              onChange={(newValue) => {
                setNewBooking({ ...newBooking, end_time: newValue, spot_id: '' });
                setSelectedZone('');
                setAvailableSpots([]);
              }}
              minDateTime={newBooking.start_time || dayjs()}
              slotProps={{
                textField: {
                  fullWidth: true,
                  margin: "dense",
                },
              }}
              ampm={false}
            />
          </LocalizationProvider>

          {viewMode === 'list' ? (
            <>
              <TextField
                margin="dense"
                label="Выберите парковочную зону"
                select
                fullWidth
                value={selectedZone}
                onChange={(e) => handleZoneChange(e.target.value)}
                disabled={!newBooking.start_time || !newBooking.end_time}
                helperText={!newBooking.start_time || !newBooking.end_time ? "Сначала выберите время" : ""}
              >
                {zones.map((zone) => (
                  <MenuItem key={zone.zone_id} value={zone.zone_id}>
                    {zone.name} - {zone.address}
                  </MenuItem>
                ))}
              </TextField>

              {loadingSpots ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', my: 2 }}>
                  <CircularProgress size={24} />
                  <Typography sx={{ ml: 2 }}>Поиск свободных мест...</Typography>
                </Box>
              ) : (
                selectedZone && (
                  <>
                    {availableSpots.length > 0 && (
                      <Alert severity="success" sx={{ mt: 2, mb: 1 }}>
                        Найдено {availableSpots.length} свободных мест на выбранное время
                      </Alert>
                    )}
                    <TextField
                      margin="dense"
                      label="Выберите место"
                      select
                      fullWidth
                      value={newBooking.spot_id}
                      onChange={(e) => setNewBooking({ ...newBooking, spot_id: e.target.value })}
                      disabled={availableSpots.length === 0}
                    >
                      {availableSpots.length === 0 ? (
                        <MenuItem disabled>Нет свободных мест на выбранное время</MenuItem>
                      ) : (
                        availableSpots.map((spot) => (
                          <MenuItem key={spot.spot_id} value={spot.spot_id}>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
                              <span>Место {spot.spot_number} ({spot.spot_type})</span>
                              {spot.price_per_hour && (
                                <Chip
                                  label={`${parseFloat(spot.price_per_hour).toFixed(0)} ₽/ч`}
                                  size="small"
                                  color="primary"
                                  sx={{ ml: 2 }}
                                />
                              )}
                            </Box>
                          </MenuItem>
                        ))
                      )}
                    </TextField>

                    {/* Show estimated cost if spot is selected */}
                    {newBooking.spot_id && availableSpots.length > 0 && (() => {
                      const selectedSpot = availableSpots.find(s => s.spot_id === newBooking.spot_id);
                      if (selectedSpot && selectedSpot.price_per_hour && newBooking.start_time && newBooking.end_time) {
                        const duration = (newBooking.end_time - newBooking.start_time) / (1000 * 60 * 60); // hours
                        const estimatedCost = parseFloat(selectedSpot.price_per_hour) * duration;
                        return (
                          <Alert severity="success" sx={{ mt: 2 }}>
                            <Typography variant="body2" fontWeight="bold">
                              Примерная стоимость: {estimatedCost.toFixed(2)} ₽
                            </Typography>
                            <Typography variant="caption" color="text.secondary" display="block">
                              {duration.toFixed(1)} ч × {parseFloat(selectedSpot.price_per_hour).toFixed(0)} ₽/ч
                            </Typography>
                            <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                              💰 Эта сумма будет списана с вашего баланса ({parseFloat(user.balance || 0).toFixed(2)} ₽) при подтверждении бронирования.
                            </Typography>
                          </Alert>
                        );
                      }
                      return null;
                    })()}
                  </>
                )
              )}
            </>
          ) : (
            <Box sx={{ mt: 2 }}>
              {newBooking.start_time && newBooking.end_time ? (
                <ParkingMapView
                  onSpotSelect={handleSpotSelectFromMap}
                  selectedSpotId={newBooking.spot_id}
                />
              ) : (
                <Alert severity="warning" sx={{ mt: 2 }}>
                  Пожалуйста, сначала выберите время начала и окончания бронирования
                </Alert>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenBookingDialog(false)}>Отмена</Button>
          <Button onClick={handleCreateBooking} variant="contained" disabled={!newBooking.spot_id}>
            Создать
          </Button>
        </DialogActions>
      </Dialog>

      {/* Payment Dialog */}
      <PaymentDialog
        open={openPaymentDialog}
        onClose={handleClosePaymentDialog}
        payment={selectedPayment}
        onPaymentSuccess={handlePayment}
      />

      {/* Balance Top-Up Dialog */}
      <BalanceTopUpDialog
        open={openBalanceDialog}
        onClose={() => setOpenBalanceDialog(false)}
        onSuccess={handleBalanceTopUpSuccess}
      />
    </Container>
  );
};

export default DashboardPage;
