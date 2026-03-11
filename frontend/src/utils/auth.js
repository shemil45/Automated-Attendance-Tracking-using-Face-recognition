/**
 * Authentication utilities
 * Uses sessionStorage so tokens are automatically cleared when the tab is closed.
 */
import api from './api';

export const auth = {
    /**
     * Login user — store token in sessionStorage
     */
    login: (token, className) => {
        sessionStorage.setItem('access_token', token);
        sessionStorage.setItem('class_name', className);
    },

    /**
     * Logout user — blacklist token on the server, then clear local storage
     */
    logout: async () => {
        try {
            // Tell the backend to invalidate this token
            await api.post('/auth/logout');
        } catch (_) {
            // Even if the request fails, clear local state
        } finally {
            sessionStorage.removeItem('access_token');
            sessionStorage.removeItem('class_name');
            window.location.href = '/';
        }
    },

    /**
     * Get stored token
     */
    getToken: () => {
        return sessionStorage.getItem('access_token');
    },

    /**
     * Get stored class name
     */
    getClassName: () => {
        return sessionStorage.getItem('class_name');
    },

    /**
     * Check if user is authenticated
     */
    isAuthenticated: () => {
        return !!sessionStorage.getItem('access_token');
    },
};
