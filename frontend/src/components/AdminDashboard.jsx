import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import AdminLayout from './AdminLayout';
import { adminAPI } from '../utils/api';

export default function AdminDashboard() {
    const [classes, setClasses] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        adminAPI.getClasses()
            .then((response) => setClasses(response.data))
            .finally(() => setLoading(false));
    }, []);

    return (
        <AdminLayout>
            <section style={styles.hero}>
                <h2 style={styles.title}>Dashboard</h2>
                <p style={styles.subtitle}>Choose a class to edit its timetable.</p>
            </section>

            <section style={styles.grid}>
                <div style={styles.stat}>
                    <span style={styles.statLabel}>Classes</span>
                    <strong style={styles.statValue}>{loading ? '-' : classes.length}</strong>
                </div>
                <Link to="/admin/classes" style={styles.action}>Manage Classes</Link>
            </section>

            <section style={styles.list}>
                {classes.map((classItem) => (
                    <Link
                        key={classItem.id}
                        to={`/admin/timetable/${encodeURIComponent(classItem.class_name)}`}
                        style={styles.row}
                    >
                        <span>{classItem.class_name}</span>
                        <span style={styles.rowAction}>Edit Timetable</span>
                    </Link>
                ))}
                {!loading && classes.length === 0 && (
                    <p style={styles.empty}>No classes yet.</p>
                )}
            </section>
        </AdminLayout>
    );
}

const styles = {
    hero: {
        marginBottom: 24,
    },
    title: {
        margin: 0,
        fontSize: 28,
        letterSpacing: 0,
    },
    subtitle: {
        margin: '6px 0 0',
        color: '#64748B',
    },
    grid: {
        display: 'grid',
        gridTemplateColumns: 'minmax(180px, 260px) minmax(180px, 260px)',
        gap: 16,
        marginBottom: 24,
    },
    stat: {
        background: '#FFFFFF',
        border: '1px solid #E2E8F0',
        borderRadius: 8,
        padding: 18,
    },
    statLabel: {
        display: 'block',
        color: '#64748B',
        fontSize: 13,
    },
    statValue: {
        display: 'block',
        marginTop: 6,
        fontSize: 30,
        color: '#0F766E',
    },
    action: {
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: '#0F766E',
        color: '#FFFFFF',
        borderRadius: 8,
        textDecoration: 'none',
        fontWeight: 800,
    },
    list: {
        display: 'grid',
        gap: 10,
    },
    row: {
        display: 'flex',
        justifyContent: 'space-between',
        gap: 12,
        padding: 16,
        background: '#FFFFFF',
        border: '1px solid #E2E8F0',
        borderRadius: 8,
        color: '#111827',
        textDecoration: 'none',
        fontWeight: 700,
    },
    rowAction: {
        color: '#0F766E',
        fontSize: 13,
    },
    empty: {
        color: '#64748B',
    },
};
