/**
 * Authentication Service
 * Handles login, register, and token management
 */
import apiClient from './api';

const authService = {
  /**
   * Register a new user
   * @param {Object} userData - User registration data
   * @returns {Promise} API response
   */
  register: async (userData) => {
    const response = await apiClient.post('/api/auth/register', userData);
    return response.data;
  },

  /**
   * Login user
   * @param {Object} credentials - Email and password
   * @returns {Promise} API response with token
   */
  login: async (credentials) => {
    const response = await apiClient.post('/api/auth/login', credentials);

    // Store token in localStorage
    if (response.data.access_token) {
      localStorage.setItem('access_token', response.data.access_token);
    }

    return response.data;
  },

  /**
   * Get current user profile
   * @returns {Promise} Current user data
   */
  getCurrentUser: async () => {
    const response = await apiClient.get('/api/auth/me');

    // Store user data in localStorage
    if (response.data) {
      localStorage.setItem('user', JSON.stringify(response.data));
    }

    return response.data;
  },

  /**
   * Logout user
   */
  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
  },

  /**
   * Check if user is authenticated
   * @returns {boolean} Authentication status
   */
  isAuthenticated: () => {
    return !!localStorage.getItem('access_token');
  },

  /**
   * Get stored token
   * @returns {string|null} Access token
   */
  getToken: () => {
    return localStorage.getItem('access_token');
  },

  /**
   * Get stored user data
   * @returns {Object|null} User object
   */
  getUser: () => {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  },
};

export default authService;
