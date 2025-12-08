import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  ToggleButton,
  ToggleButtonGroup,
  Grid,
  Chip,
  Button,
  CircularProgress,
  Alert,
  Tooltip,
  useTheme,
} from '@mui/material';
import {
  DirectionsCar,
  CheckCircle,
  Cancel,
  Info as InfoIcon,
} from '@mui/icons-material';
import parkingService from '../services/parkingService';

const ParkingMapView = ({ onSpotSelect, selectedSpotId }) => {
  const theme = useTheme();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [zones, setZones] = useState([]);
  const [selectedZone, setSelectedZone] = useState(null);
  const [spots, setSpots] = useState([]);
  const [floor, setFloor] = useState(1);

  useEffect(() => {
    loadZones();
  }, []);

  useEffect(() => {
    if (selectedZone) {
      loadSpots(selectedZone);
    }
  }, [selectedZone]);

  const loadZones = async () => {
    try {
      setLoading(true);
      const data = await parkingService.getZones();
      setZones(data);
      if (data.length > 0) {
        setSelectedZone(data[0].zone_id);
      }
    } catch (err) {
      setError('Ошибка загрузки зон');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadSpots = async (zoneId) => {
    try {
      setLoading(true);
      const data = await parkingService.getZoneSpots(zoneId);
      setSpots(data);
    } catch (err) {
      setError('Ошибка загрузки мест');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleZoneChange = (event, newZone) => {
    if (newZone !== null) {
      setSelectedZone(newZone);
      setFloor(1);
    }
  };

  const handleFloorChange = (event, newFloor) => {
    if (newFloor !== null) {
      setFloor(newFloor);
    }
  };

  const handleSpotClick = (spot) => {
    if (spot.is_active && !spot.is_occupied) {
      if (onSpotSelect) {
        onSpotSelect(spot);
      }
    }
  };

  // Группируем места по этажам (используем spot_number для определения этажа)
  const getFloorFromSpotNumber = (spotNumber) => {
    // Формат номера: "1-A-01" где первая цифра - этаж
    const match = spotNumber.match(/^(\d+)-/);
    return match ? parseInt(match[1]) : 1;
  };

  // Фильтруем места по выбранному этажу
  const floorsAvailable = [...new Set(spots.map(s => getFloorFromSpotNumber(s.spot_number)))].sort();
  const currentFloorSpots = spots.filter(s => getFloorFromSpotNumber(s.spot_number) === floor);

  // Группируем места по секциям (буква в номере)
  const getSectionFromSpotNumber = (spotNumber) => {
    const match = spotNumber.match(/-([A-Z])-/);
    return match ? match[1] : 'A';
  };

  const sections = {};
  currentFloorSpots.forEach(spot => {
    const section = getSectionFromSpotNumber(spot.spot_number);
    if (!sections[section]) {
      sections[section] = [];
    }
    sections[section].push(spot);
  });

  // Статистика
  const totalSpots = currentFloorSpots.length;
  const occupiedSpots = currentFloorSpots.filter(s => s.is_occupied).length;
  const availableSpots = totalSpots - occupiedSpots;

  const getSpotColor = (spot) => {
    if (!spot.is_active) return theme.palette.grey[700];
    if (spot.is_occupied) return theme.palette.error.main;
    if (selectedSpotId === spot.spot_id) return theme.palette.info.main;
    return theme.palette.success.main;
  };

  const getSpotIcon = (spot) => {
    if (!spot.is_active) return <Cancel />;
    if (spot.is_occupied) return <DirectionsCar />;
    return <CheckCircle />;
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }

  const currentZone = zones.find(z => z.zone_id === selectedZone);

  return (
    <Paper elevation={2} sx={{ p: 3 }}>
      <Typography variant="h5" gutterBottom>
        План парковки
      </Typography>

      {/* Выбор зоны */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="subtitle2" gutterBottom>
          Выберите парковочную зону:
        </Typography>
        <ToggleButtonGroup
          value={selectedZone}
          exclusive
          onChange={handleZoneChange}
          aria-label="parking zone"
          fullWidth
          sx={{ flexWrap: 'wrap' }}
        >
          {zones.map((zone) => (
            <ToggleButton key={zone.zone_id} value={zone.zone_id}>
              <Box>
                <Typography variant="body2">{zone.name}</Typography>
                <Typography variant="caption" color="text.secondary">
                  {zone.available_spots}/{zone.total_spots} свободно
                </Typography>
              </Box>
            </ToggleButton>
          ))}
        </ToggleButtonGroup>
      </Box>

      {currentZone && (
        <>
          {/* Информация о зоне */}
          <Box sx={{ mb: 2, p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
            <Typography variant="h6">{currentZone.name}</Typography>
            <Typography variant="body2" color="text.secondary">
              {currentZone.address}
            </Typography>
          </Box>

          {/* Выбор этажа */}
          {floorsAvailable.length > 1 && (
            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle2" gutterBottom>
                Выберите этаж:
              </Typography>
              <ToggleButtonGroup
                value={floor}
                exclusive
                onChange={handleFloorChange}
                aria-label="floor"
              >
                {floorsAvailable.map((f) => (
                  <ToggleButton key={f} value={f}>
                    Этаж {f}
                  </ToggleButton>
                ))}
              </ToggleButtonGroup>
            </Box>
          )}

          {/* Статистика этажа */}
          <Box sx={{ mb: 3, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
            <Chip
              icon={<DirectionsCar />}
              label={`Всего: ${totalSpots}`}
              color="primary"
              variant="outlined"
            />
            <Chip
              icon={<CheckCircle />}
              label={`Свободно: ${availableSpots}`}
              color="success"
              variant="outlined"
            />
            <Chip
              icon={<Cancel />}
              label={`Занято: ${occupiedSpots}`}
              color="error"
              variant="outlined"
            />
          </Box>

          {/* Легенда */}
          <Box sx={{ mb: 3, p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
            <Typography variant="subtitle2" gutterBottom>
              Легенда:
            </Typography>
            <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Box
                  sx={{
                    width: 24,
                    height: 24,
                    bgcolor: theme.palette.success.main,
                    borderRadius: 1,
                  }}
                />
                <Typography variant="caption">Свободно</Typography>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Box
                  sx={{
                    width: 24,
                    height: 24,
                    bgcolor: theme.palette.error.main,
                    borderRadius: 1,
                  }}
                />
                <Typography variant="caption">Занято</Typography>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Box
                  sx={{
                    width: 24,
                    height: 24,
                    bgcolor: theme.palette.info.main,
                    borderRadius: 1,
                  }}
                />
                <Typography variant="caption">Выбрано</Typography>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Box
                  sx={{
                    width: 24,
                    height: 24,
                    bgcolor: theme.palette.grey[700],
                    borderRadius: 1,
                  }}
                />
                <Typography variant="caption">Недоступно</Typography>
              </Box>
            </Box>
          </Box>

          {/* План парковки по секциям */}
          <Box>
            <Typography variant="h6" gutterBottom>
              Этаж {floor}
            </Typography>

            {Object.keys(sections).sort().map((section) => (
              <Box key={section} sx={{ mb: 4 }}>
                <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 'bold' }}>
                  Секция {section}
                </Typography>

                <Grid container spacing={2}>
                  {sections[section].map((spot) => (
                    <Grid item key={spot.spot_id} xs={6} sm={4} md={3} lg={2}>
                      <Tooltip
                        title={
                          <Box>
                            <Typography variant="caption">
                              Место: {spot.spot_number}
                            </Typography>
                            <br />
                            <Typography variant="caption">
                              Тип: {spot.spot_type}
                            </Typography>
                            <br />
                            <Typography variant="caption">
                              Статус:{' '}
                              {!spot.is_active
                                ? 'Неактивно'
                                : spot.is_occupied
                                ? 'Занято'
                                : 'Свободно'}
                            </Typography>
                          </Box>
                        }
                        arrow
                      >
                        <Button
                          fullWidth
                          variant={selectedSpotId === spot.spot_id ? 'contained' : 'outlined'}
                          onClick={() => handleSpotClick(spot)}
                          disabled={!spot.is_active || spot.is_occupied}
                          sx={{
                            height: 80,
                            borderColor: getSpotColor(spot),
                            color: getSpotColor(spot),
                            '&:hover': {
                              borderColor: getSpotColor(spot),
                              bgcolor: !spot.is_occupied && spot.is_active ? 'action.hover' : 'transparent',
                            },
                            display: 'flex',
                            flexDirection: 'column',
                            gap: 1,
                          }}
                        >
                          {getSpotIcon(spot)}
                          <Typography variant="caption" sx={{ fontWeight: 'bold' }}>
                            {spot.spot_number}
                          </Typography>
                          <Typography variant="caption" sx={{ fontSize: '0.65rem' }}>
                            {spot.spot_type}
                          </Typography>
                        </Button>
                      </Tooltip>
                    </Grid>
                  ))}
                </Grid>
              </Box>
            ))}

            {Object.keys(sections).length === 0 && (
              <Alert severity="info" icon={<InfoIcon />}>
                На этом этаже нет парковочных мест
              </Alert>
            )}
          </Box>
        </>
      )}
    </Paper>
  );
};

export default ParkingMapView;
