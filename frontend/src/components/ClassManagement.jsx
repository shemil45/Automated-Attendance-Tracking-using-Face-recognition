import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import AdminLayout from './AdminLayout';
import { adminAPI } from '../utils/api';

export default function ClassManagement() {
    const [classes, setClasses] = useState([]);
    const [className, setClassName] = useState('');
    const [password, setPassword] = useState('');
    const [message, setMessage] = useState('');
    const [error, setError] = useState('');

    const loadClasses = async () => {
        const response = await adminAPI.getClasses();
        setClasses(response.data);
    };

    useEffect(() => {
        loadClasses();
    }, []);

    const handleCreate = async (event) => {
        event.preventDefault();
        setError('');
        setMessage('');
        try {
            await adminAPI.createClass(className, password);
            setClassName('');
            setPassword('');
            setMessage('Class created');
            loadClasses();
        } catch (err) {
            setError(err.response?.data?.detail || 'Could not create class');
        }
    };

    const handlePasswordChange = async (classItem) => {
        const nextPassword = window.prompt(`New password for ${classItem.class_name}`);
        if (!nextPassword) return;

        try {
            await adminAPI.updateClass(classItem.id, { password: nextPassword });
            setMessage('Password updated');
            setError('');
        } catch (err) {
            setError(err.response?.data?.detail || 'Could not update password');
        }
    };

    const handleDelete = async (classItem) => {
        if (!window.confirm(`Delete ${classItem.class_name}?`)) return;
        try {
            await adminAPI.deleteClass(classItem.id);
            setMessage('Class deleted');
            setError('');
            loadClasses();
        } catch (err) {
            setError(err.response?.data?.detail || 'Could not delete class');
        }
    };

    return (
        <AdminLayout>
            <section style={styles.header}>
                <h2 style={styles.title}>Class Management</h2>
                <p style={styles.subtitle}>Create class logins and open timetable builders.</p>
            </section>

            {(message || error) && (
                <div style={error ? styles.error : styles.message}>{error || message}</div>
            )}

            <form onSubmit={handleCreate} style={styles.form}>
                <input
                    value={className}
                    onChange={(event) => setClassName(event.target.value)}
                    placeholder="Class name"
                    required
                    style={styles.input}
                />
                <input
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    placeholder="Class password"
                    type="password"
                    minLength={6}
                    required
                    style={styles.input}
                />
                <button style={styles.primary}>Create Class</button>
            </form>

            <section style={styles.table}>
                {classes.map((classItem) => (
                    <div key={classItem.id} style={styles.row}>
                        <strong>{classItem.class_name}</strong>
                        <div style={styles.actions}>
                            <Link
                                to={`/admin/timetable/${encodeURIComponent(classItem.class_name)}`}
                                style={styles.linkButton}
                            >
                                Timetable
                            </Link>
                            <button onClick={() => handlePasswordChange(classItem)} style={styles.secondary}>
                                Password
                            </button>
                            <button onClick={() => handleDelete(classItem)} style={styles.danger}>
                                Delete
                            </button>
                        </div>
                    </div>
                ))}
            </section>
        </AdminLayout>
    );
}

const buttonBase = {
    borderRadius: 8,
    padding: '9px 12px',
    fontWeight: 700,
    cursor: 'pointer',
    textDecoration: 'none',
    fontSize: 13,
};

const styles = {
    header: {
        marginBottom: 18,
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
    message: {
        background: '#ECFDF5',
        color: '#047857',
        padding: 12,
        borderRadius: 8,
        marginBottom: 14,
    },
    error: {
        background: '#FEF2F2',
        color: '#B91C1C',
        padding: 12,
        borderRadius: 8,
        marginBottom: 14,
    },
    form: {
        display: 'grid',
        gridTemplateColumns: 'minmax(180px, 1fr) minmax(180px, 1fr) auto',
        gap: 12,
        marginBottom: 24,
    },
    input: {
        padding: '11px 12px',
        border: '1px solid #CBD5E1',
        borderRadius: 8,
        fontSize: 14,
    },
    primary: {
        ...buttonBase,
        border: 'none',
        background: '#0F766E',
        color: '#FFFFFF',
    },
    table: {
        display: 'grid',
        gap: 10,
    },
    row: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        gap: 12,
        background: '#FFFFFF',
        border: '1px solid #E2E8F0',
        borderRadius: 8,
        padding: 14,
    },
    actions: {
        display: 'flex',
        gap: 8,
        flexWrap: 'wrap',
    },
    linkButton: {
        ...buttonBase,
        background: '#0F766E',
        color: '#FFFFFF',
    },
    secondary: {
        ...buttonBase,
        border: '1px solid #CBD5E1',
        background: '#FFFFFF',
        color: '#334155',
    },
    danger: {
        ...buttonBase,
        border: '1px solid #FCA5A5',
        background: '#FFFFFF',
        color: '#B91C1C',
    },
};
