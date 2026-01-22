/**
 * Authentication utilities
 */

export const auth = {
    /**
     * Login user
     */
    login: (token, className) => {
        localStorage.setItem('access_token', token);
        localStorage.setItem('class_name', className);
    },

    /**
     * Logout user
     */
    logout: () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('class_name');
        window.location.href = '/';
    },

    /**
     * Get stored token
     */
    getToken: () => {
        return localStorage.getItem('access_token');
    },

    /**
     * Get stored class name
     */
    getClassName: () => {
        return localStorage.getItem('class_name');
    },

    /**
     * Check if user is authenticated
     */
    isAuthenticated: () => {
        return !!localStorage.getItem('access_token');
    },
};
