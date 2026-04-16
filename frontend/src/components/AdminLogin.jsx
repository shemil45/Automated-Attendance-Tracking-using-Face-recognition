import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { adminAPI } from '../utils/api';
import { adminAuth } from '../utils/auth';

const font = "-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'SF Pro Text', 'Helvetica Neue', Arial, sans-serif";

export default function AdminLogin({ onLogin }) {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    const handleSubmit = async (event) => {
        event.preventDefault();
        setError('');
        setLoading(true);

        try {
            const response = await adminAPI.login(username, password);
            adminAuth.login(response.data.access_token, response.data.username);
            onLogin?.();
            navigate('/admin/dashboard');
        } catch (err) {
            setError(err.response?.data?.detail || 'Admin login failed');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={styles.page}>
            <div style={styles.panel}>
                <h1 style={styles.title}>Admin Portal</h1>
                <p style={styles.subtitle}>Manage classes and timetables</p>

                {error && <div style={styles.error}>{error}</div>}

                <form onSubmit={handleSubmit} style={styles.form}>
                    <label style={styles.label} htmlFor="admin-username">Username</label>
                    <input
                        id="admin-username"
                        value={username}
                        onChange={(event) => setUsername(event.target.value)}
                        required
                        style={styles.input}
                    />

                    <label style={styles.label} htmlFor="admin-password">Password</label>
                    <input
                        id="admin-password"
                        type="password"
                        value={password}
                        onChange={(event) => setPassword(event.target.value)}
                        required
                        style={styles.input}
                    />

                    <button disabled={loading} style={styles.button}>
                        {loading ? 'Logging in...' : 'Login'}
                    </button>
                </form>
            </div>
        </div>
    );
}

const styles = {
    page: {
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: '#F6F7F9',
        padding: 20,
        fontFamily: font,
    },
    panel: {
        width: '100%',
        maxWidth: 420,
        background: '#FFFFFF',
        border: '1px solid #E2E8F0',
        borderRadius: 8,
        padding: 28,
        boxShadow: '0 10px 28px rgba(15, 23, 42, 0.08)',
    },
    title: {
        margin: 0,
        fontSize: 28,
        color: '#111827',
        letterSpacing: 0,
    },
    subtitle: {
        margin: '6px 0 24px',
        color: '#64748B',
        fontSize: 14,
    },
    error: {
        padding: 12,
        marginBottom: 16,
        borderRadius: 8,
        background: '#FEF2F2',
        color: '#B91C1C',
        fontSize: 14,
    },
    form: {
        display: 'flex',
        flexDirection: 'column',
        gap: 10,
    },
    label: {
        fontSize: 13,
        fontWeight: 600,
        color: '#334155',
    },
    input: {
        padding: '11px 12px',
        border: '1px solid #CBD5E1',
        borderRadius: 8,
        fontSize: 15,
        marginBottom: 8,
        outline: 'none',
    },
    button: {
        marginTop: 6,
        padding: 12,
        border: 'none',
        borderRadius: 8,
        background: '#0F766E',
        color: '#FFFFFF',
        fontWeight: 700,
        cursor: 'pointer',
    },
};
