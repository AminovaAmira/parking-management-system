/**
 * Parking Service
 * Handles zones, spots, bookings, and sessions
 */
import apiClient from './api';

const parkingService = {
  // ========== Parking Zones ==========

  /**
   * Get all parking zones
   * @returns {Promise} List of zones
   */
  getZones: async () => {
    const response = await apiClient.get('/api/zones/');
    return response.data;
  },

  /**
   * Get zone by ID
   * @param {string} zoneId - Zone ID
   * @returns {Promise} Zone data
   */
  getZoneById: async (zoneId) => {
    const response = await apiClient.get(`/api/zones/${zoneId}`);
    return response.data;
  },

  /**
   * Get spots in a zone
   * @param {string} zoneId - Zone ID
   * @param {Object} filters - Optional filters (is_occupied, spot_type)
   * @returns {Promise} List of spots
   */
  getZoneSpots: async (zoneId, filters = {}) => {
    const response = await apiClient.get(`/api/zones/${zoneId}/spots`, { params: filters });
    return response.data;
  },

  // ========== Bookings ==========

  /**
   * Create a new booking
   * @param {Object} bookingData - Booking details
   * @returns {Promise} Created booking
   */
  createBooking: async (bookingData) => {
    const response = await apiClient.post('/api/bookings/', bookingData);
    return response.data;
  },

  /**
   * Get user bookings
   * @param {string} status - Optional status filter
   * @returns {Promise} List of bookings
   */
  getBookings: async (status = null) => {
    const params = status ? { status } : {};
    const response = await apiClient.get('/api/bookings/', { params });
    return response.data;
  },

  /**
   * Get booking by ID
   * @param {string} bookingId - Booking ID
   * @returns {Promise} Booking data
   */
  getBookingById: async (bookingId) => {
    const response = await apiClient.get(`/api/bookings/${bookingId}`);
    return response.data;
  },

  /**
   * Cancel a booking
   * @param {string} bookingId - Booking ID
   * @returns {Promise} Response
   */
  cancelBooking: async (bookingId) => {
    const response = await apiClient.delete(`/api/bookings/${bookingId}`);
    return response.data;
  },

  // ========== Parking Sessions ==========

  /**
   * Start a parking session
   * @param {Object} sessionData - Session details
   * @returns {Promise} Created session
   */
  startSession: async (sessionData) => {
    const response = await apiClient.post('/api/sessions', sessionData);
    return response.data;
  },

  /**
   * Get user sessions
   * @param {string} status - Optional status filter
   * @returns {Promise} List of sessions
   */
  getSessions: async (status = null) => {
    const params = status ? { status } : {};
    const response = await apiClient.get('/api/sessions', { params });
    return response.data;
  },

  /**
   * Get active sessions
   * @returns {Promise} List of active sessions
   */
  getActiveSessions: async () => {
    const response = await apiClient.get('/api/sessions/active');
    return response.data;
  },

  /**
   * End a parking session
   * @param {string} sessionId - Session ID
   * @returns {Promise} Updated session
   */
  endSession: async (sessionId) => {
    const response = await apiClient.patch(`/api/sessions/${sessionId}/end`);
    return response.data;
  },

  // ========== Payments ==========

  /**
   * Create a payment
   * @param {Object} paymentData - Payment details
   * @returns {Promise} Created payment
   */
  createPayment: async (paymentData) => {
    const response = await apiClient.post('/api/payments', paymentData);
    return response.data;
  },

  /**
   * Get payment history
   * @returns {Promise} List of payments
   */
  getPayments: async () => {
    const response = await apiClient.get('/api/payments');
    return response.data;
  },

  /**
   * Calculate session cost
   * @param {string} sessionId - Session ID
   * @returns {Promise} Cost calculation
   */
  calculateSessionCost: async (sessionId) => {
    const response = await apiClient.get(`/api/payments/session/${sessionId}/calculate`);
    return response.data;
  },

  // ========== Vehicles ==========

  /**
   * Get user vehicles
   * @returns {Promise} List of vehicles
   */
  getVehicles: async () => {
    const response = await apiClient.get('/api/vehicles/');
    return response.data;
  },

  /**
   * Add a new vehicle
   * @param {Object} vehicleData - Vehicle details
   * @returns {Promise} Created vehicle
   */
  addVehicle: async (vehicleData) => {
    const response = await apiClient.post('/api/vehicles/', vehicleData);
    return response.data;
  },

  /**
   * Delete a vehicle
   * @param {string} vehicleId - Vehicle ID
   * @returns {Promise} Response
   */
  deleteVehicle: async (vehicleId) => {
    const response = await apiClient.delete(`/api/vehicles/${vehicleId}`);
    return response.data;
  },

  // ========== Aliases for convenience ==========
  getMyVehicles: async () => {
    return parkingService.getVehicles();
  },

  getMyBookings: async (status = null) => {
    return parkingService.getBookings(status);
  },
};

export default parkingService;
