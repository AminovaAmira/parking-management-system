/**
 * Centralized Axios API client configuration
 */
import axios from 'axios';

// Base API URL from environment or fallback to localhost
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000, // 15 seconds
});

// Request interceptor: Add auth token to requests
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor: Handle errors globally
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // Handle 401 Unauthorized - token expired or invalid
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }

    // Handle other errors
    let errorMessage = 'An error occurred';

    if (error.response?.data?.detail) {
      const detail = error.response.data.detail;

      // If detail is an array (validation errors from FastAPI/Pydantic)
      if (Array.isArray(detail)) {
        // Extract and format validation error messages
        errorMessage = detail.map(err => err.msg || JSON.stringify(err)).join(', ');
      } else if (typeof detail === 'string') {
        // If detail is a string
        errorMessage = detail;
      } else {
        // If detail is an object
        errorMessage = JSON.stringify(detail);
      }
    } else if (error.message) {
      errorMessage = error.message;
    }

    return Promise.reject({
      message: errorMessage,
      status: error.response?.status,
      data: error.response?.data,
    });
  }
);

export default apiClient;
