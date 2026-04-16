import React from 'react';
import { Navigate } from 'react-router-dom';
import { adminAuth } from '../utils/auth';

export default function AdminProtectedRoute({ children }) {
    if (!adminAuth.isAuthenticated()) {
        return <Navigate to="/admin/login" replace />;
    }

    return children;
}
