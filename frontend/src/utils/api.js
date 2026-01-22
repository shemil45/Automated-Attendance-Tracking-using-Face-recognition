/**
 * API utility for making requests to backend
 */
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

// Create axios instance
const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Request interceptor to add auth token
api.interceptors.request.use(
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

// Response interceptor for error handling
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            // Unauthorized - clear token and redirect to login
            localStorage.removeItem('access_token');
            localStorage.removeItem('class_name');
            window.location.href = '/';
        }
        return Promise.reject(error);
    }
);

// Auth API
export const authAPI = {
    login: (username, password) =>
        api.post('/auth/login', { username, password }),
};

// Timetable API
export const timetableAPI = {
    getToday: () => api.get('/timetable/today'),
};

// Attendance API
export const attendanceAPI = {
    startSession: (date, period) =>
        api.post('/attendance/start-session', { date, period }),
    getSession: (sessionId) => api.get(`/attendance/session/${sessionId}`),
    endSession: (sessionId) =>
        api.post(`/attendance/end-session/${sessionId}`),
    getSessionStudents: (sessionId) =>
        api.get(`/attendance/session/${sessionId}/students`),
    manualOverride: (sessionId, regNo, status) =>
        api.post('/attendance/manual-override', {
            session_id: sessionId,
            reg_no: regNo,
            status,
        }),
    recognizeFace: (sessionId, formData) =>
        api.post(`/attendance/session/${sessionId}/recognize`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        }),
};

// Reports API
export const reportsAPI = {
    getSessions: (date) => api.get('/reports/sessions', { params: { date } }),
    getSessionReport: (sessionId) =>
        api.get(`/reports/session/${sessionId}/report`),
    exportSession: (sessionId) =>
        api.get(`/reports/session/${sessionId}/export`, {
            responseType: 'blob',
        }),
};

// Utility API
export const utilityAPI = {
    reloadEncodings: () => api.post('/reload-encodings'),
    syncStudents: () => api.post('/students/sync'),
    healthCheck: () => api.get('/health'),
};

export default api;
