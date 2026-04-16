import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { timetableAPI, attendanceAPI, reportsAPI } from '../utils/api';
import { auth } from '../utils/auth';
import { getSessionWindowStatus, canStartSession } from '../utils/sessionTime';

export default function Dashboard() {
    const [todayTimetable, setTodayTimetable] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [selectedDate, setSelectedDate] = useState('');
    const [sessions, setSessions] = useState([]);
    const [hasSearched, setHasSearched] = useState(false);

    // ── Test Mode ─────────────────────────────────────────────────────────────
    const [testMode, setTestMode] = useState(
        () => localStorage.getItem('attendnet_test_mode') === 'true'
    );

    // ── Live clock (ticks every 30 s so status badges auto-update) ───────────
    const [currentTime, setCurrentTime] = useState(new Date());

    const navigate = useNavigate();
    const className = auth.getClassName();

    // Persist test mode in localStorage
    useEffect(() => {
        localStorage.setItem('attendnet_test_mode', testMode);
    }, [testMode]);

    // Tick the clock every 30 seconds
    useEffect(() => {
        const interval = setInterval(() => setCurrentTime(new Date()), 30_000);
        return () => clearInterval(interval);
    }, []);

    useEffect(() => {
        loadTodayTimetable();
    }, []);

    const loadTodayTimetable = async () => {
        try {
            setLoading(true);
            const response = await timetableAPI.getToday();
            setTodayTimetable(response.data);
        } catch (err) {
            setError('Failed to load timetable');
        } finally {
            setLoading(false);
        }
    };

    const handleStartSession = async (period) => {
        try {
            const response = await attendanceAPI.startSession(
                todayTimetable.date,
                period.period,
                testMode          // pass test mode flag to API
            );
            navigate(`/session/${response.data.id}`, { state: { session: response.data } });
        } catch (err) {
            alert('Failed to start session: ' + (err.response?.data?.detail || err.message));
        }
    };

    const handleViewReport = (period) => {
        if (period.session_id) {
            navigate(`/report/${period.session_id}`);
        }
    };

    const loadSessionsByDate = async () => {
        if (!selectedDate) return;
        try {
            const response = await reportsAPI.getSessions(selectedDate);
            setSessions(response.data);
            setHasSearched(true);
        } catch (err) {
            alert('Failed to load sessions');
        }
    };

    const handleDownloadReport = async (sessionId) => {
        try {
            const response = await reportsAPI.exportSession(sessionId);
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `attendance_${sessionId}.xlsx`);
            document.body.appendChild(link);
            link.click();
            link.remove();
        } catch (err) {
            alert('Failed to download report');
        }
    };

    // ── Helpers ────────────────────────────────────────────────────────────────

    /**
     * Determine the *effective* window status for a period, merging the server
     * response with the live client-side clock so the UI stays accurate even
     * without a page refresh.
     */
    const getEffectiveStatus = useCallback((period) => {
        // If a DB session exists, trust its status (ongoing / completed)
        if (period.status === 'ongoing' || period.status === 'completed') {
            return period.status;
        }

        // Recompute from live clock so status updates without a reload
        const windowStatus = getSessionWindowStatus(period.start_time, currentTime);

        if (windowStatus === 'before_start') return 'before_start';
        if (windowStatus === 'open') return 'not_started'; // startable
        return 'expired';
    }, [currentTime]);

    const getStatusBadge = (period) => {
        const effectiveStatus = getEffectiveStatus(period);

        const config = {
            not_started:  { bg: '#FFF3CD', color: '#92400E', dot: '#F59E0B',  label: 'Open – Start Now' },
            before_start: { bg: '#F2F2F7', color: '#6E6E73', dot: '#AEAEB2',  label: 'Not Started' },
            ongoing:      { bg: '#D1FAE5', color: '#065F46', dot: '#10B981',  label: 'Ongoing' },
            completed:    { bg: '#D1F5DC', color: '#1A7A3D', dot: '#34C759',  label: 'Completed' },
            expired:      { bg: '#FFE4E4', color: '#991B1B', dot: '#EF4444',  label: 'Expired' },
        };

        const s = config[effectiveStatus] ?? config.before_start;

        return (
            <span style={{
                display: 'inline-flex', alignItems: 'center', gap: 5,
                padding: '3px 10px', borderRadius: 20,
                background: s.bg, color: s.color,
                fontSize: 12, fontWeight: 500, letterSpacing: '0.01em',
                whiteSpace: 'nowrap',
            }}>
                <span style={{ width: 7, height: 7, borderRadius: '50%', background: s.dot, flexShrink: 0 }} />
                {s.label}
            </span>
        );
    };

    const getActionButton = (period) => {
        const effectiveStatus = getEffectiveStatus(period);

        // ── Completed: always show View Report ──────────────────────────────
        if (effectiveStatus === 'completed') {
            return (
                <button onClick={() => handleViewReport(period)}
                    style={{ ...styles.btnPrimary, background: '#34C759' }}>
                    View Report
                </button>
            );
        }

        // ── Ongoing: re-open the session ────────────────────────────────────
        if (effectiveStatus === 'ongoing') {
            return (
                <button onClick={() => handleStartSession(period)}
                    style={{ ...styles.btnPrimary, background: '#10B981' }}>
                    Open Session
                </button>
            );
        }

        // ── Not started & window open: allow start ───────────────────────────
        if (effectiveStatus === 'not_started') {
            return (
                <button onClick={() => handleStartSession(period)}
                    style={styles.btnPrimary}>
                    Start Attendance
                </button>
            );
        }

        // ── Test-mode override: bypass restrictions ──────────────────────────
        if (testMode && (effectiveStatus === 'expired' || effectiveStatus === 'before_start')) {
            return (
                <button onClick={() => handleStartSession(period)}
                    style={{ ...styles.btnPrimary, background: '#F59E0B' }}>
                    Start (Test Mode)
                </button>
            );
        }

        // ── Before start: disabled placeholder ──────────────────────────────
        if (effectiveStatus === 'before_start') {
            return (
                <button disabled style={styles.btnDisabled}>
                    Not Started Yet
                </button>
            );
        }

        // ── Expired: disabled placeholder ────────────────────────────────────
        return (
            <button disabled style={{ ...styles.btnDisabled, color: '#EF4444', borderColor: '#FECACA' }}>
                Session Expired
            </button>
        );
    };

    if (loading) {
        return (
            <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#F5F5F7' }}>
                <div style={{ textAlign: 'center' }}>
                    <div style={{
                        width: 44, height: 44, borderRadius: '50%',
                        border: '3px solid #E5E5EA',
                        borderTopColor: '#007AFF',
                        animation: 'spin 0.8s linear infinite',
                        margin: '0 auto',
                    }} />
                    <p style={{ marginTop: 16, color: '#6E6E73', fontSize: 14, fontFamily: styles.font }}>Loading timetable…</p>
                </div>
            </div>
        );
    }

    return (
        <div style={{ minHeight: '100vh', background: '#F5F5F7', fontFamily: styles.font }}>

            {/* ── Header ── */}
            <header style={{
                background: '#1e3a8a',
                borderBottom: '1px solid rgba(0,0,0,0.18)',
                position: 'sticky', top: 0, zIndex: 100,
            }}>
                <div style={styles.container}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '14px 0', gap: 12 }}>

                        {/* Brand + greeting */}
                        <div>
                            <h1 style={{ margin: 0, fontSize: 20, fontWeight: 700, color: '#FFFFFF', letterSpacing: '-0.3px' }}>
                                AttendNet
                            </h1>
                            <p style={{ margin: '2px 0 0', fontSize: 13, color: 'rgba(255,255,255,0.65)' }}>
                                Welcome, {className}
                            </p>
                        </div>

                        {/* Right-side controls */}
                        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexShrink: 0 }}>

                            {/* ── Test Mode Toggle ─────────────────────────────────── */}
                            <div
                                id="test-mode-toggle"
                                title={testMode ? 'Test Mode ON – time restrictions bypassed' : 'Test Mode OFF – time restrictions enforced'}
                                style={{
                                    display: 'flex', alignItems: 'center', gap: 8,
                                    background: testMode ? 'rgba(245,158,11,0.18)' : 'rgba(255,255,255,0.10)',
                                    border: `1px solid ${testMode ? 'rgba(245,158,11,0.55)' : 'rgba(255,255,255,0.20)'}`,
                                    borderRadius: 10,
                                    padding: '5px 12px',
                                    cursor: 'pointer',
                                    transition: 'all 0.2s ease',
                                    userSelect: 'none',
                                }}
                                onClick={() => setTestMode(m => !m)}
                            >
                                {/* Toggle pill */}
                                <div style={{
                                    position: 'relative',
                                    width: 36, height: 20,
                                    background: testMode ? '#F59E0B' : 'rgba(255,255,255,0.25)',
                                    borderRadius: 10,
                                    transition: 'background 0.2s ease',
                                    flexShrink: 0,
                                }}>
                                    <div style={{
                                        position: 'absolute',
                                        top: 2, left: testMode ? 18 : 2,
                                        width: 16, height: 16,
                                        borderRadius: '50%',
                                        background: '#fff',
                                        transition: 'left 0.2s ease',
                                        boxShadow: '0 1px 3px rgba(0,0,0,0.25)',
                                    }} />
                                </div>

                                <span style={{
                                    fontSize: 12, fontWeight: 600,
                                    color: testMode ? '#FCD34D' : 'rgba(255,255,255,0.75)',
                                    letterSpacing: '0.02em',
                                    transition: 'color 0.2s ease',
                                }}>
                                    {testMode ? 'TEST ON' : 'TEST OFF'}
                                </span>
                            </div>

                            {/* Logout */}
                            <button
                                onClick={() => auth.logout()}
                                style={styles.btnSecondaryOnDark}
                            >
                                Logout
                            </button>
                        </div>
                    </div>
                </div>
            </header>

            {/* ── Test Mode Banner ── */}
            {testMode && (
                <div style={{
                    background: 'linear-gradient(90deg, #92400E 0%, #B45309 100%)',
                    color: '#FEF3C7',
                    textAlign: 'center',
                    padding: '7px 16px',
                    fontSize: 13,
                    fontWeight: 500,
                    letterSpacing: '0.01em',
                }}>
                    ⚠️ Test Mode is <strong>ON</strong> — time restrictions are bypassed. All sessions can be started regardless of schedule.
                </div>
            )}

            {/* ── Main ── */}
            <main style={{ ...styles.container, paddingTop: 48, paddingBottom: 48 }}>

                {/* Today's Schedule */}
                <section style={styles.card}>
                    <div style={styles.cardHeader}>
                        <div>
                            <h2 style={styles.cardTitle}>Today's Schedule</h2>
                            <p style={styles.cardSubtitle}>
                                {todayTimetable && new Date(todayTimetable.date).toLocaleDateString('en-US', {
                                    weekday: 'long', year: 'numeric', month: 'long', day: 'numeric',
                                })}
                            </p>
                        </div>
                    </div>

                    {error && (
                        <div style={{ margin: '0 16px 16px', padding: '12px 16px', background: '#FFF0F0', borderRadius: 10, borderLeft: '3px solid #FF3B30' }}>
                            <p style={{ margin: 0, color: '#FF3B30', fontSize: 14 }}>{error}</p>
                        </div>
                    )}

                    {/* Mobile Cards */}
                    <div className="block md:hidden" style={{ borderTop: '1px solid #F2F2F7' }}>
                        {todayTimetable?.periods.map((period) => (
                            <div key={period.id} style={{ padding: '16px', borderBottom: '1px solid #F2F2F7' }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                                    <span style={{ fontWeight: 600, color: '#1C1C1E', fontSize: 14 }}>Period {period.period}</span>
                                    {getStatusBadge(period)}
                                </div>
                                <p style={{ margin: '0 0 2px', fontSize: 13, color: '#6E6E73' }}>{period.start_time} – {period.end_time}</p>
                                <p style={{ margin: '0 0 2px', fontSize: 14, fontWeight: 500, color: '#1C1C1E' }}>{period.subject_name}</p>
                                <p style={{ margin: '0 0 14px', fontSize: 12, color: '#AEAEB2' }}>{period.subject_code}</p>
                                {getActionButton(period)}
                            </div>
                        ))}
                    </div>

                    {/* Desktop Table */}
                    <div className="hidden md:block" style={{ overflowX: 'auto', borderTop: '1px solid #F2F2F7' }}>
                        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                            <thead>
                                <tr style={{ background: '#F9F9FB' }}>
                                    {['Period', 'Time', 'Subject', 'Status', 'Action'].map(h => (
                                        <th key={h} style={styles.th}>{h}</th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody>
                                {todayTimetable?.periods.map((period, i) => (
                                    <tr key={period.id} style={{ background: i % 2 === 0 ? '#fff' : '#FAFAFA' }}>
                                        <td style={styles.td}>
                                            <span style={{ fontWeight: 600, color: '#1C1C1E', fontSize: 14 }}>Period {period.period}</span>
                                        </td>
                                        <td style={styles.td}>
                                            <span style={{ fontSize: 13, color: '#6E6E73' }}>{period.start_time} – {period.end_time}</span>
                                        </td>
                                        <td style={styles.td}>
                                            <div style={{ fontSize: 14, fontWeight: 500, color: '#1C1C1E' }}>{period.subject_name}</div>
                                            <div style={{ fontSize: 12, color: '#AEAEB2', marginTop: 2 }}>{period.subject_code}</div>
                                        </td>
                                        <td style={styles.td}>{getStatusBadge(period)}</td>
                                        <td style={styles.td}>{getActionButton(period)}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </section>

                {/* Previous Reports */}
                <section style={{ ...styles.card, marginTop: 24 }}>
                    <div style={styles.cardHeader}>
                        <div>
                            <h2 style={styles.cardTitle}>Previous Attendance Reports</h2>
                            <p style={styles.cardSubtitle}>Search by date to browse past sessions</p>
                        </div>
                    </div>

                    <div style={{ padding: '20px 24px' }}>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12, alignItems: 'flex-end', marginBottom: 24 }}>
                            <div style={{ flex: 1, minWidth: 180 }}>
                                <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: '#3C3C43', marginBottom: 6 }}>
                                    Select Date
                                </label>
                                <input
                                    type="date"
                                    value={selectedDate}
                                    onChange={(e) => setSelectedDate(e.target.value)}
                                    style={styles.input}
                                />
                            </div>
                            <button
                                onClick={loadSessionsByDate}
                                disabled={!selectedDate}
                                style={{
                                    ...styles.btnPrimary,
                                    opacity: !selectedDate ? 0.4 : 1,
                                    cursor: !selectedDate ? 'not-allowed' : 'pointer',
                                    width: 'auto', padding: '10px 22px',
                                }}
                            >
                                Load Sessions
                            </button>
                        </div>

                        {hasSearched && sessions.length === 0 && (
                            <div style={{ textAlign: 'center', padding: '48px 0' }}>
                                <div style={{ fontSize: 44, marginBottom: 12 }}>📭</div>
                                <h3 style={{ margin: 0, fontSize: 16, fontWeight: 600, color: '#1C1C1E' }}>No sessions recorded</h3>
                                <p style={{ margin: '6px 0 0', fontSize: 13, color: '#AEAEB2' }}>No attendance sessions were found for this date.</p>
                            </div>
                        )}

                        {sessions.length > 0 && (
                            <div style={{
                                display: 'grid',
                                gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))',
                                gap: 16,
                            }}>
                                {sessions.map((session) => (
                                    <div key={session.id} className="session-card" style={styles.sessionCard}>
                                        {/* Card top row: Period title + subject code badge */}
                                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 6 }}>
                                            <span style={{ fontSize: '1rem', fontWeight: 600, color: '#1F2937' }}>
                                                Period {session.period}
                                            </span>
                                            <span style={{
                                                fontSize: '0.75rem', fontWeight: 400, color: '#1D4ED8',
                                                background: '#EFF6FF', borderRadius: 6,
                                                padding: '2px 8px',
                                            }}>
                                                {session.subject_code}
                                            </span>
                                        </div>

                                        {/* Subject name */}
                                        <p style={{ margin: '0 0 4px', fontSize: '0.875rem', fontWeight: 400, color: '#4B5563' }}>
                                            {session.subject_name}
                                        </p>

                                        {/* Time */}
                                        <p style={{ margin: '0 0 16px', fontSize: '0.875rem', fontWeight: 400, color: '#4B5563' }}>
                                            {session.start_time} – {session.end_time}
                                        </p>

                                        {/* Action buttons */}
                                        <div style={{ display: 'flex', gap: 8 }}>
                                            <button
                                                onClick={() => navigate(`/report/${session.id}`)}
                                                style={styles.cardBtnView}
                                            >
                                                👁 View
                                            </button>
                                            <button
                                                onClick={() => handleDownloadReport(session.id)}
                                                style={styles.cardBtnExcel}
                                            >
                                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
                                                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                                                    <polyline points="7 10 12 15 17 10" />
                                                    <line x1="12" y1="15" x2="12" y2="3" />
                                                </svg>
                                                Excel
                                            </button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </section>
            </main>

            <style>{`
                @keyframes spin { to { transform: rotate(360deg); } }
                * { box-sizing: border-box; }
                .session-card:hover {
                    box-shadow: 0 6px 24px rgba(0,0,0,0.12);
                    transform: translateY(-2px);
                }
                #test-mode-toggle:hover {
                    filter: brightness(1.1);
                }
            `}</style>
        </div>
    );
}

// ── Design tokens ─────────────────────────────────────────────────────────────
const styles = {
    font: "-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'SF Pro Text', 'Helvetica Neue', Arial, sans-serif",

    container: {
        width: '100%',
        margin: '0 auto',
        padding: '0 32px',
    },

    card: {
        background: '#FFFFFF',
        borderRadius: 16,
        boxShadow: '0 1px 3px rgba(0,0,0,0.08), 0 4px 16px rgba(0,0,0,0.04)',
        overflow: 'hidden',
        border: '1px solid rgba(0,0,0,0.06)',
    },

    cardHeader: {
        padding: '20px 24px',
        borderBottom: '1px solid #F2F2F7',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
    },

    cardTitle: {
        margin: 0,
        fontSize: 17,
        fontWeight: 700,
        color: '#1C1C1E',
        letterSpacing: '-0.2px',
    },

    cardSubtitle: {
        margin: '3px 0 0',
        fontSize: 13,
        color: '#6E6E73',
    },

    th: {
        padding: '10px 20px',
        textAlign: 'left',
        fontSize: 11,
        fontWeight: 600,
        color: '#6E6E73',
        textTransform: 'uppercase',
        letterSpacing: '0.06em',
        borderBottom: '1px solid #F2F2F7',
    },

    td: {
        padding: '14px 20px',
        borderBottom: '1px solid #F2F2F7',
        verticalAlign: 'middle',
    },

    btnPrimary: {
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '8px 16px',
        background: '#007AFF',
        color: '#fff',
        border: 'none',
        borderRadius: 9,
        fontSize: 13,
        fontWeight: 500,
        cursor: 'pointer',
        letterSpacing: '-0.1px',
        transition: 'filter 0.15s',
        width: '100%',
        whiteSpace: 'nowrap',
    },

    btnDisabled: {
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '8px 16px',
        background: '#F2F2F7',
        color: '#8E8E93',
        border: '1px solid #E5E5EA',
        borderRadius: 9,
        fontSize: 13,
        fontWeight: 500,
        cursor: 'not-allowed',
        letterSpacing: '-0.1px',
        width: '100%',
        whiteSpace: 'nowrap',
        opacity: 0.85,
    },

    btnSecondary: {
        padding: '7px 16px',
        background: '#F2F2F7',
        color: '#3C3C43',
        border: 'none',
        borderRadius: 9,
        fontSize: 13,
        fontWeight: 500,
        cursor: 'pointer',
        transition: 'background 0.15s',
    },

    btnSecondaryOnDark: {
        padding: '7px 16px',
        background: 'rgba(255,255,255,0.15)',
        color: '#FFFFFF',
        border: '1px solid rgba(255,255,255,0.25)',
        borderRadius: 9,
        fontSize: 13,
        fontWeight: 500,
        cursor: 'pointer',
        transition: 'background 0.15s',
    },

    input: {
        width: '100%',
        padding: '10px 14px',
        border: '1px solid #D1D1D6',
        borderRadius: 10,
        fontSize: 14,
        color: '#1C1C1E',
        background: '#F9F9FB',
        outline: 'none',
        fontFamily: "-apple-system, BlinkMacSystemFont, 'SF Pro Text', sans-serif",
    },

    sessionCard: {
        background: '#FFFFFF',
        borderRadius: 14,
        border: '1px solid #E5E5EA',
        padding: '18px 18px 16px',
        boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
        transition: 'box-shadow 0.2s ease, transform 0.2s ease',
        cursor: 'default',
    },

    cardBtnView: {
        flex: 1,
        padding: '8px 0',
        background: '#fff',
        color: '#1C1C1E',
        border: '1px solid #D1D1D6',
        borderRadius: 9,
        fontSize: 13,
        fontWeight: 500,
        cursor: 'pointer',
        textAlign: 'center',
    },

    cardBtnExcel: {
        flex: 1,
        padding: '8px 0',
        background: '#16A34A',
        color: '#fff',
        border: 'none',
        borderRadius: 9,
        fontSize: 13,
        fontWeight: 500,
        cursor: 'pointer',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 6,
    },
};
