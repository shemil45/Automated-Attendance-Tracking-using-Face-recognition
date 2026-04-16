import React, { useEffect, useMemo, useState } from 'react';
import { useParams } from 'react-router-dom';
import AdminLayout from './AdminLayout';
import { adminAPI } from '../utils/api';

const days = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN'];

const makeEmptyEntry = (day, period) => ({
    day,
    period,
    subject_code: '',
    subject_name: '',
    start_time: '',
    end_time: '',
    is_break: false,
});

export default function TimetableBuilder() {
    const { className: encodedClassName } = useParams();
    const className = decodeURIComponent(encodedClassName);
    const [entries, setEntries] = useState([]);
    const [periodCount, setPeriodCount] = useState(8);
    const [activeDays, setActiveDays] = useState(['MON', 'TUE', 'WED', 'THU', 'FRI']);
    const [message, setMessage] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        adminAPI.getTimetable(className)
            .then((response) => {
                setEntries(response.data);
                const maxPeriod = Math.max(1, ...response.data.map((entry) => entry.period));
                setPeriodCount(maxPeriod || 8);
                const usedDays = [...new Set(response.data.map((entry) => entry.day))];
                if (usedDays.length) setActiveDays(usedDays);
            })
            .catch((err) => setError(err.response?.data?.detail || 'Could not load timetable'))
            .finally(() => setLoading(false));
    }, [className]);

    const entryMap = useMemo(() => {
        const map = new Map();
        entries.forEach((entry) => {
            map.set(`${entry.day}-${entry.period}`, entry);
        });
        return map;
    }, [entries]);

    const visiblePeriods = Array.from({ length: periodCount }, (_, index) => index + 1);

    const getEntry = (day, period) => {
        return entryMap.get(`${day}-${period}`) || makeEmptyEntry(day, period);
    };

    const updateEntry = (day, period, patch) => {
        const current = getEntry(day, period);
        const next = {
            ...current,
            ...patch,
        };

        if (next.is_break) {
            next.subject_code = '';
            next.subject_name = '';
        }

        setEntries((previous) => {
            const withoutCurrent = previous.filter((entry) => !(entry.day === day && entry.period === period));
            return [...withoutCurrent, next];
        });
    };

    const toggleDay = (day) => {
        setActiveDays((previous) => {
            if (previous.includes(day)) {
                return previous.filter((item) => item !== day);
            }
            return [...previous, day].sort((a, b) => days.indexOf(a) - days.indexOf(b));
        });
    };

    const normalizeEntriesForSave = () => {
        const payload = [];
        activeDays.forEach((day) => {
            visiblePeriods.forEach((period) => {
                const entry = getEntry(day, period);
                if (!entry.start_time || !entry.end_time) {
                    throw new Error(`Set start and end time for ${day} period ${period}`);
                }
                payload.push({
                    day,
                    period,
                    subject_code: entry.is_break ? null : (entry.subject_code || null),
                    subject_name: entry.is_break ? null : (entry.subject_name || null),
                    start_time: entry.start_time,
                    end_time: entry.end_time,
                    is_break: Boolean(entry.is_break),
                });
            });
        });
        return payload;
    };

    const handleSave = async () => {
        setError('');
        setMessage('');
        try {
            const payload = normalizeEntriesForSave();
            const response = await adminAPI.replaceTimetable(className, payload);
            setEntries(response.data);
            setMessage('Timetable saved');
        } catch (err) {
            setError(err.response?.data?.detail || err.message || 'Could not save timetable');
        }
    };

    return (
        <AdminLayout>
            <section style={styles.header}>
                <div>
                    <h2 style={styles.title}>{className} Timetable</h2>
                    <p style={styles.subtitle}>Set periods, times, subjects, and breaks.</p>
                </div>
                <button onClick={handleSave} style={styles.save}>Save Timetable</button>
            </section>

            {(message || error) && (
                <div style={error ? styles.error : styles.message}>{error || message}</div>
            )}

            <section style={styles.controls}>
                <label style={styles.controlLabel}>
                    Periods
                    <input
                        type="number"
                        min="1"
                        max="12"
                        value={periodCount}
                        onChange={(event) => setPeriodCount(Number(event.target.value))}
                        style={styles.periodInput}
                    />
                </label>

                <div style={styles.dayToggles}>
                    {days.map((day) => (
                        <button
                            key={day}
                            onClick={() => toggleDay(day)}
                            style={activeDays.includes(day) ? styles.dayActive : styles.dayButton}
                        >
                            {day}
                        </button>
                    ))}
                </div>
            </section>

            {loading ? (
                <p style={styles.subtitle}>Loading timetable...</p>
            ) : (
                <div style={styles.gridWrap}>
                    <div
                        style={{
                            ...styles.grid,
                            gridTemplateColumns: `88px repeat(${visiblePeriods.length}, minmax(210px, 1fr))`,
                        }}
                    >
                        <div style={styles.corner}>Day</div>
                        {visiblePeriods.map((period) => (
                            <div key={period} style={styles.periodHead}>Period {period}</div>
                        ))}

                        {activeDays.map((day) => (
                            <React.Fragment key={day}>
                                <div style={styles.dayHead}>{day}</div>
                                {visiblePeriods.map((period) => {
                                    const entry = getEntry(day, period);
                                    return (
                                        <div key={`${day}-${period}`} style={entry.is_break ? styles.breakCell : styles.cell}>
                                            <div style={styles.timeRow}>
                                                <input
                                                    type="time"
                                                    value={entry.start_time}
                                                    onChange={(event) => updateEntry(day, period, { start_time: event.target.value })}
                                                    style={styles.timeInput}
                                                />
                                                <input
                                                    type="time"
                                                    value={entry.end_time}
                                                    onChange={(event) => updateEntry(day, period, { end_time: event.target.value })}
                                                    style={styles.timeInput}
                                                />
                                            </div>
                                            <label style={styles.breakLabel}>
                                                <input
                                                    type="checkbox"
                                                    checked={Boolean(entry.is_break)}
                                                    onChange={(event) => updateEntry(day, period, { is_break: event.target.checked })}
                                                />
                                                Break
                                            </label>
                                            <input
                                                value={entry.subject_code || ''}
                                                onChange={(event) => updateEntry(day, period, { subject_code: event.target.value })}
                                                placeholder="Subject code"
                                                disabled={entry.is_break}
                                                style={styles.textInput}
                                            />
                                            <input
                                                value={entry.subject_name || ''}
                                                onChange={(event) => updateEntry(day, period, { subject_name: event.target.value })}
                                                placeholder={entry.is_break ? 'Break period' : 'Subject name'}
                                                disabled={entry.is_break}
                                                style={styles.textInput}
                                            />
                                        </div>
                                    );
                                })}
                            </React.Fragment>
                        ))}
                    </div>
                </div>
            )}
        </AdminLayout>
    );
}

const styles = {
    header: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        gap: 16,
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
    save: {
        border: 'none',
        background: '#0F766E',
        color: '#FFFFFF',
        borderRadius: 8,
        padding: '11px 16px',
        fontWeight: 800,
        cursor: 'pointer',
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
    controls: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        gap: 16,
        flexWrap: 'wrap',
        marginBottom: 18,
    },
    controlLabel: {
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        fontWeight: 800,
        color: '#334155',
    },
    periodInput: {
        width: 76,
        padding: '9px 10px',
        border: '1px solid #CBD5E1',
        borderRadius: 8,
    },
    dayToggles: {
        display: 'flex',
        gap: 8,
        flexWrap: 'wrap',
    },
    dayButton: {
        border: '1px solid #CBD5E1',
        background: '#FFFFFF',
        color: '#334155',
        borderRadius: 8,
        padding: '9px 12px',
        fontWeight: 800,
        cursor: 'pointer',
    },
    dayActive: {
        border: '1px solid #0F766E',
        background: '#CCFBF1',
        color: '#115E59',
        borderRadius: 8,
        padding: '9px 12px',
        fontWeight: 800,
        cursor: 'pointer',
    },
    gridWrap: {
        overflowX: 'auto',
        border: '1px solid #E2E8F0',
        borderRadius: 8,
        background: '#FFFFFF',
    },
    grid: {
        display: 'grid',
        minWidth: 980,
    },
    corner: {
        padding: 12,
        background: '#F8FAFC',
        borderRight: '1px solid #E2E8F0',
        borderBottom: '1px solid #E2E8F0',
        fontWeight: 800,
    },
    periodHead: {
        padding: 12,
        background: '#F8FAFC',
        borderRight: '1px solid #E2E8F0',
        borderBottom: '1px solid #E2E8F0',
        fontWeight: 800,
        textAlign: 'center',
    },
    dayHead: {
        padding: 12,
        borderRight: '1px solid #E2E8F0',
        borderBottom: '1px solid #E2E8F0',
        fontWeight: 800,
        color: '#0F766E',
    },
    cell: {
        display: 'grid',
        gap: 8,
        padding: 10,
        borderRight: '1px solid #E2E8F0',
        borderBottom: '1px solid #E2E8F0',
        minHeight: 178,
    },
    breakCell: {
        display: 'grid',
        gap: 8,
        padding: 10,
        borderRight: '1px solid #E2E8F0',
        borderBottom: '1px solid #E2E8F0',
        minHeight: 178,
        background: '#F0FDFA',
    },
    timeRow: {
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: 6,
    },
    timeInput: {
        minWidth: 0,
        padding: '8px 6px',
        border: '1px solid #CBD5E1',
        borderRadius: 8,
        fontSize: 13,
    },
    breakLabel: {
        display: 'flex',
        alignItems: 'center',
        gap: 6,
        fontSize: 13,
        fontWeight: 700,
        color: '#334155',
    },
    textInput: {
        minWidth: 0,
        padding: '9px 8px',
        border: '1px solid #CBD5E1',
        borderRadius: 8,
        fontSize: 13,
    },
};
