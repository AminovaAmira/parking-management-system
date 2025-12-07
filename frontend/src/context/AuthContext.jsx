/**
 * AuthContext - Authentication state management
 */
import React, { createContext, useState, useContext, useEffect } from 'react';
import authService from '../services/authService';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Check if user is already logged in on mount
  useEffect(() => {
    const initAuth = async () => {
      try {
        if (authService.isAuthenticated()) {
          const userData = await authService.getCurrentUser();
          setUser(userData);
        }
      } catch (err) {
        console.error('Failed to fetch user:', err);
        // Clear invalid token
        authService.logout();
      } finally {
        setLoading(false);
      }
    };

    initAuth();
  }, []);

  /**
   * Register a new user
   */
  const register = async (userData) => {
    try {
      setError(null);
      setLoading(true);
      await authService.register(userData);
      // Auto-login after registration
      await login({ email: userData.email, password: userData.password });
      return { success: true };
    } catch (err) {
      const errorMsg = err.message || 'Registration failed';
      setError(errorMsg);
      return { success: false, error: errorMsg };
    } finally {
      setLoading(false);
    }
  };

  /**
   * Login user
   */
  const login = async (credentials) => {
    try {
      setError(null);
      setLoading(true);
      await authService.login(credentials);
      const userData = await authService.getCurrentUser();
      setUser(userData);
      return { success: true };
    } catch (err) {
      const errorMsg = err.message || 'Login failed';
      setError(errorMsg);
      return { success: false, error: errorMsg };
    } finally {
      setLoading(false);
    }
  };

  /**
   * Logout user
   */
  const logout = () => {
    authService.logout();
    setUser(null);
    setError(null);
  };

  /**
   * Update user profile
   * @param {Object} userData - Optional user data to set directly
   */
  const updateUser = async (userData = null) => {
    try {
      if (userData) {
        // If userData provided, set it directly
        setUser(userData);
      } else {
        // Otherwise fetch from server
        const freshUserData = await authService.getCurrentUser();
        setUser(freshUserData);
      }
    } catch (err) {
      console.error('Failed to update user:', err);
    }
  };

  const value = {
    user,
    loading,
    error,
    isAuthenticated: !!user,
    register,
    login,
    logout,
    updateUser,
    setError,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

/**
 * Custom hook to use auth context
 */
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;
