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
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Dialog states
  const [openVehicleDialog, setOpenVehicleDialog] = useState(false);
  const [openBookingDialog, setOpenBookingDialog] = useState(false);
  const [newVehicle, setNewVehicle] = useState({
    license_plate: '',
    make: '',
    model: '',
    color: '',
    vehicle_type: 'sedan',
  });
  const [newBooking, setNewBooking] = useState({
    zone_id: '',
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

      const [bookingsData, zonesData, vehiclesData] = await Promise.all([
        parkingService.getMyBookings(),
        parkingService.getZones(),
        parkingService.getMyVehicles(),
      ]);

      setBookings(bookingsData);
      setZones(zonesData);
      setVehicles(vehiclesData);
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
            <Button variant="outlined" color="secondary" onClick={handleLogout}>
              Выйти
            </Button>
          </Box>
        </Paper>

        {error && (
          <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError('')}>
            {error}
          </Alert>
        )}

        {/* Statistics Cards */}
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} md={4}>
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
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography variant="h6" color="primary">
                  {vehicles.length}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Зарегистрированных автомобилей
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={4}>
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

        {/* My Bookings */}
        <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
          <Typography variant="h5" sx={{ mb: 2 }}>
            Мои бронирования
          </Typography>
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
                      <TableCell>{booking.spot_id}</TableCell>
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
    </Container>
  );
};

export default DashboardPage;
