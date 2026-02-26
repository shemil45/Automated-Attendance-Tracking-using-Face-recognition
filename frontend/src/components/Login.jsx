import React, { useState } from 'react';
import { authAPI } from '../utils/api';
import { auth } from '../utils/auth';

const font = "-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'SF Pro Text', 'Helvetica Neue', Arial, sans-serif";

export default function Login({ onLogin }) {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            const response = await authAPI.login(username, password);
            const { access_token, class_name } = response.data;
            auth.login(access_token, class_name);
            onLogin();
        } catch (err) {
            setError(err.response?.data?.detail || 'Login failed. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={{
            minHeight: '100vh',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: '#F5F5F7',
            fontFamily: font,
            padding: 20,
        }}>
            <div style={{ width: '100%', maxWidth: 400 }}>

                {/* Logo mark */}
                <div style={{ textAlign: 'center', marginBottom: 28 }}>
                    <div style={{
                        width: 60, height: 60,
                        background: '#007AFF',
                        borderRadius: 16,
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        margin: '0 auto 14px',
                        boxShadow: '0 4px 16px rgba(0,122,255,0.3)',
                    }}>
                        <svg width="30" height="30" fill="none" stroke="#fff" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                                d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                        </svg>
                    </div>
                    <h1 style={{ margin: 0, fontSize: 26, fontWeight: 700, color: '#1C1C1E', letterSpacing: '-0.4px' }}>
                        Faculty Portal
                    </h1>
                    <p style={{ margin: '6px 0 0', fontSize: 14, color: '#6E6E73' }}>
                        Attendance Management System
                    </p>
                </div>

                {/* Card */}
                <div style={{
                    background: '#FFFFFF',
                    borderRadius: 20,
                    padding: '32px 28px',
                    boxShadow: '0 1px 3px rgba(0,0,0,0.08), 0 8px 32px rgba(0,0,0,0.06)',
                    border: '1px solid rgba(0,0,0,0.06)',
                }}>
                    {error && (
                        <div style={{
                            marginBottom: 20,
                            padding: '12px 14px',
                            background: '#FFF0F0',
                            border: '1px solid rgba(255,59,48,0.25)',
                            borderRadius: 10,
                            fontSize: 13,
                            color: '#FF3B30',
                        }}>
                            {error}
                        </div>
                    )}

                    <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
                        <div>
                            <label htmlFor="username" style={labelStyle}>Class Name</label>
                            <input
                                type="text"
                                id="username"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                placeholder="e.g., AIML-A"
                                required
                                style={inputStyle}
                                onFocus={e => e.target.style.borderColor = '#007AFF'}
                                onBlur={e => e.target.style.borderColor = '#D1D1D6'}
                            />
                        </div>

                        <div>
                            <label htmlFor="password" style={labelStyle}>Password</label>
                            <input
                                type="password"
                                id="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                placeholder="Enter your password"
                                required
                                style={inputStyle}
                                onFocus={e => e.target.style.borderColor = '#007AFF'}
                                onBlur={e => e.target.style.borderColor = '#D1D1D6'}
                            />
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            style={{
                                marginTop: 6,
                                padding: '13px',
                                background: loading ? '#A2C4FF' : '#007AFF',
                                color: '#fff',
                                border: 'none',
                                borderRadius: 12,
                                fontSize: 15,
                                fontWeight: 600,
                                cursor: loading ? 'not-allowed' : 'pointer',
                                letterSpacing: '-0.1px',
                                transition: 'background 0.15s',
                                fontFamily: font,
                                display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
                            }}
                        >
                            {loading ? (
                                <>
                                    <span style={{
                                        width: 16, height: 16,
                                        border: '2px solid rgba(255,255,255,0.4)',
                                        borderTopColor: '#fff',
                                        borderRadius: '50%',
                                        display: 'inline-block',
                                        animation: 'spin 0.8s linear infinite',
                                    }} />
                                    Logging in…
                                </>
                            ) : 'Login'}
                        </button>
                    </form>
                </div>

                <p style={{ marginTop: 20, textAlign: 'center', fontSize: 12, color: '#AEAEB2' }}>
                    Powered by Face Recognition Technology
                </p>
            </div>

            <style>{`
                @keyframes spin { to { transform: rotate(360deg); } }
                * { box-sizing: border-box; }
            `}</style>
        </div>
    );
}

const labelStyle = {
    display: 'block',
    fontSize: 13,
    fontWeight: 500,
    color: '#3C3C43',
    marginBottom: 7,
};

const inputStyle = {
    width: '100%',
    padding: '11px 14px',
    border: '1px solid #D1D1D6',
    borderRadius: 10,
    fontSize: 15,
    color: '#1C1C1E',
    background: '#F9F9FB',
    outline: 'none',
    transition: 'border-color 0.15s',
    fontFamily: "-apple-system, BlinkMacSystemFont, 'SF Pro Text', sans-serif",
};
