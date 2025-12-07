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
import { useAuth } from '../context/AuthContext';
import parkingService from '../services/parkingService';

const DashboardPage = () => {
  const navigate = useNavigate();
  const { user, logout, isAuthenticated } = useAuth();

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
  const [availableSpots, setAvailableSpots] = useState([]);
  const [selectedZone, setSelectedZone] = useState('');
  const [loadingSpots, setLoadingSpots] = useState(false);
  const [newVehicle, setNewVehicle] = useState({
    license_plate: '',
    make: '',
    model: '',
    color: '',
    vehicle_type: 'sedan',
  });
  const [newBooking, setNewBooking] = useState({
    spot_id: '',
    vehicle_id: '',
    start_time: '',
    end_time: '',
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

      setBookings(bookingsData);
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
        make: '',
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
      // Get spots available for the selected time range
      const spots = await parkingService.getAvailableSpotsForTime(
        zoneId,
        newBooking.start_time,
        newBooking.end_time
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

  const handleTimeChange = () => {
    // Reset zone and spots when time changes
    setSelectedZone('');
    setAvailableSpots([]);
    setNewBooking({ ...newBooking, spot_id: '' });
  };

  const handleCreateBooking = async () => {
    try {
      // Validation
      if (!newBooking.vehicle_id || !newBooking.spot_id || !newBooking.start_time || !newBooking.end_time) {
        setError('Пожалуйста, заполните все поля');
        return;
      }

      await parkingService.createBooking(newBooking);
      setOpenBookingDialog(false);
      setNewBooking({
        spot_id: '',
        vehicle_id: '',
        start_time: '',
        end_time: '',
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

  const handlePayment = async (paymentId, paymentMethod) => {
    if (window.confirm(`Подтвердить оплату через ${getPaymentMethodText(paymentMethod)}?`)) {
      try {
        // Simulate payment processing
        await parkingService.updatePaymentStatus(paymentId, {
          status: 'completed',
          transaction_id: `TXN-${Date.now()}`
        });
        await loadDashboardData();
      } catch (err) {
        setError(err.message || 'Ошибка обработки платежа');
      }
    }
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
            </Box>
            <Box sx={{ display: 'flex', gap: 2 }}>
              <Button variant="outlined" color="info" onClick={() => navigate('/history')}>
                История
              </Button>
              <Button variant="outlined" color="primary" onClick={() => navigate('/profile')}>
                Профиль
              </Button>
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

                      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                        <strong>Место:</strong> {session.spot_id}
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
                  {bookings.map((booking) => (
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
                          <Button
                            size="small"
                            color="error"
                            onClick={() => handleCancelBooking(booking.booking_id)}
                          >
                            Отменить
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
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
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Дата</TableCell>
                    <TableCell>Сумма</TableCell>
                    <TableCell>Метод оплаты</TableCell>
                    <TableCell>Статус</TableCell>
                    <TableCell>ID транзакции</TableCell>
                    <TableCell>Действия</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {payments.map((payment) => (
                    <TableRow key={payment.payment_id}>
                      <TableCell>
                        {new Date(payment.created_at).toLocaleString('ru-RU')}
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
                        <Typography variant="caption" color="text.secondary">
                          {payment.transaction_id || '-'}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        {payment.status === 'pending' && (
                          <Button
                            size="small"
                            color="success"
                            variant="outlined"
                            onClick={() => handlePayment(payment.payment_id, 'card')}
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
            value={newVehicle.make}
            onChange={(e) => setNewVehicle({ ...newVehicle, make: e.target.value })}
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
      <Dialog open={openBookingDialog} onClose={() => setOpenBookingDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Создать бронирование</DialogTitle>
        <DialogContent>
          <Alert severity="info" sx={{ mb: 2 }}>
            Выберите время, затем парковочную зону. Система покажет только свободные места на выбранное время.
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

          <Box sx={{ mt: 2 }}>
            <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5, display: 'block' }}>
              Начало бронирования
            </Typography>
            <TextField
              type="datetime-local"
              fullWidth
              value={newBooking.start_time}
              onChange={(e) => {
                setNewBooking({ ...newBooking, start_time: e.target.value });
                handleTimeChange();
              }}
              InputLabelProps={{
                shrink: true,
              }}
              inputProps={{
                min: new Date().toISOString().slice(0, 16)
              }}
            />
          </Box>

          <Box sx={{ mt: 2 }}>
            <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5, display: 'block' }}>
              Окончание бронирования
            </Typography>
            <TextField
              type="datetime-local"
              fullWidth
              value={newBooking.end_time}
              onChange={(e) => {
                setNewBooking({ ...newBooking, end_time: e.target.value });
                handleTimeChange();
              }}
              InputLabelProps={{
                shrink: true,
              }}
              inputProps={{
                min: newBooking.start_time || new Date().toISOString().slice(0, 16)
              }}
            />
          </Box>

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
                        Место {spot.spot_number} ({spot.spot_type})
                      </MenuItem>
                    ))
                  )}
                </TextField>
              </>
            )
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenBookingDialog(false)}>Отмена</Button>
          <Button onClick={handleCreateBooking} variant="contained" disabled={!newBooking.spot_id}>
            Создать
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default DashboardPage;
