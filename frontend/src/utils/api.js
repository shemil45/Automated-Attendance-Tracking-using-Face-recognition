/**
 * API utility for making requests to backend.
 */
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

api.interceptors.request.use(
    (config) => {
        const isAdminRequest = config.url?.startsWith('/admin');
        const token = isAdminRequest
            ? sessionStorage.getItem('admin_access_token')
            : sessionStorage.getItem('access_token');

        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            const requestUrl = error.config?.url || '';
            if (requestUrl.startsWith('/admin')) {
                sessionStorage.removeItem('admin_access_token');
                sessionStorage.removeItem('admin_username');
                window.location.href = '/admin/login';
            } else {
                sessionStorage.removeItem('access_token');
                sessionStorage.removeItem('class_name');
                window.location.href = '/';
            }
        }
        return Promise.reject(error);
    }
);

export const authAPI = {
    login: (username, password) =>
        api.post('/auth/login', { username, password }),
    logout: () =>
        api.post('/auth/logout'),
};

export const adminAPI = {
    login: (username, password) =>
        api.post('/admin/auth/login', { username, password }),
    getClasses: () => api.get('/admin/classes'),
    createClass: (className, password) =>
        api.post('/admin/classes', { class_name: className, password }),
    updateClass: (classId, payload) =>
        api.patch(`/admin/classes/${classId}`, payload),
    deleteClass: (classId) =>
        api.delete(`/admin/classes/${classId}`),
    getTimetable: (className) =>
        api.get(`/admin/classes/${encodeURIComponent(className)}/timetable`),
    replaceTimetable: (className, entries) =>
        api.put(`/admin/classes/${encodeURIComponent(className)}/timetable`, entries),
    createTimetableEntry: (className, entry) =>
        api.post(`/admin/classes/${encodeURIComponent(className)}/timetable`, entry),
    updateTimetableEntry: (entryId, entry) =>
        api.patch(`/admin/timetable/${entryId}`, entry),
    deleteTimetableEntry: (entryId) =>
        api.delete(`/admin/timetable/${entryId}`),
};

export const timetableAPI = {
    getToday: () => api.get('/timetable/today'),
};

export const attendanceAPI = {
    startSession: (date, period, testMode = false) =>
        api.post('/attendance/start-session', { date, period, test_mode: testMode }),
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

export const reportsAPI = {
    getSessions: (date) => api.get('/reports/sessions', { params: { date } }),
    getSessionReport: (sessionId) =>
        api.get(`/reports/session/${sessionId}/report`),
    exportSession: (sessionId) =>
        api.get(`/reports/session/${sessionId}/export`, {
            responseType: 'blob',
        }),
};

export const utilityAPI = {
    reloadEncodings: () => api.post('/reload-encodings'),
    syncStudents: () => api.post('/students/sync'),
    healthCheck: () => api.get('/health'),
};

export default api;
