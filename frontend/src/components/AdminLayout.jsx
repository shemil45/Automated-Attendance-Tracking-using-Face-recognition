import React from 'react';
import { NavLink } from 'react-router-dom';
import { adminAuth } from '../utils/auth';

const font = "-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'SF Pro Text', 'Helvetica Neue', Arial, sans-serif";

export default function AdminLayout({ children }) {
    return (
        <div style={styles.page}>
            <header style={styles.header}>
                <div>
                    <h1 style={styles.brand}>AttendNet Admin</h1>
                    <p style={styles.user}>{adminAuth.getUsername()}</p>
                </div>
                <nav style={styles.nav}>
                    <NavLink to="/admin/dashboard" style={linkStyle}>Dashboard</NavLink>
                    <NavLink to="/admin/classes" style={linkStyle}>Classes</NavLink>
                    <button onClick={adminAuth.logout} style={styles.logout}>Logout</button>
                </nav>
            </header>
            <main style={styles.main}>{children}</main>
        </div>
    );
}

const linkStyle = ({ isActive }) => ({
    color: isActive ? '#0F766E' : '#475569',
    textDecoration: 'none',
    fontWeight: 700,
    fontSize: 14,
});

const styles = {
    page: {
        minHeight: '100vh',
        background: '#F6F7F9',
        fontFamily: font,
        color: '#111827',
    },
    header: {
        position: 'sticky',
        top: 0,
        zIndex: 20,
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        gap: 18,
        padding: '16px 32px',
        background: '#FFFFFF',
        borderBottom: '1px solid #E2E8F0',
    },
    brand: {
        margin: 0,
        fontSize: 20,
        letterSpacing: 0,
    },
    user: {
        margin: '2px 0 0',
        color: '#64748B',
        fontSize: 13,
    },
    nav: {
        display: 'flex',
        alignItems: 'center',
        gap: 18,
        flexWrap: 'wrap',
    },
    logout: {
        border: '1px solid #CBD5E1',
        background: '#FFFFFF',
        borderRadius: 8,
        padding: '8px 12px',
        cursor: 'pointer',
        color: '#334155',
        fontWeight: 700,
    },
    main: {
        width: '100%',
        padding: 32,
    },
};
