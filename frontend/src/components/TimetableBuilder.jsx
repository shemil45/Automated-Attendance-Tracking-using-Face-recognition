import React, { useEffect, useMemo, useState } from 'react';
import { useParams } from 'react-router-dom';
import AdminLayout from './AdminLayout';
import { adminAPI } from '../utils/api';

const days = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN'];
const dayLabels = {
    MON: 'Mon',
    TUE: 'Tue',
    WED: 'Wed',
    THU: 'Thu',
    FRI: 'Fri',
    SAT: 'Sat',
    SUN: 'Sun',
};
const subjectColors = ['bg-gray-950', 'bg-gray-700', 'bg-gray-500', 'bg-neutral-600', 'bg-zinc-400'];

const makeEmptyEntry = (day, period) => ({
    day,
    period,
    subject_code: '',
    subject_name: '',
    start_time: '',
    end_time: '',
    is_break: false,
    is_free: false,
});

function getSubjectColor(value) {
    if (!value) return 'bg-gray-300';
    const index = value.split('').reduce((sum, char) => sum + char.charCodeAt(0), 0);
    return subjectColors[index % subjectColors.length];
}

function DayTabs({ activeDay, enabledDays, onChange }) {
    return (
        <div className="sticky top-0 z-20 -mx-4 mb-6 border-b border-gray-200 bg-gray-50/95 px-4 py-3 backdrop-blur sm:-mx-6 sm:px-6 lg:-mx-8 lg:px-8">
            <div className="overflow-x-auto">
                <div className="flex min-w-max gap-2">
                    {days.map((day) => {
                        const isActive = activeDay === day;
                        const isEnabled = enabledDays.includes(day);
                        return (
                            <button
                                key={day}
                                type="button"
                                onClick={() => onChange(day)}
                                className={`min-h-11 rounded-xl px-5 text-sm font-semibold transition ${
                                    isActive
                                        ? 'bg-gray-950 text-white shadow-sm'
                                        : 'bg-white text-gray-700 ring-1 ring-gray-200 hover:bg-gray-100'
                                }`}
                            >
                                <span className="flex items-center gap-2">
                                    <span>{dayLabels[day]}</span>
                                    <span className={`h-1.5 w-1.5 rounded-full ${isEnabled ? 'bg-gray-950' : 'bg-gray-300'}`} />
                                </span>
                            </button>
                        );
                    })}
                </div>
            </div>
        </div>
    );
}

function Toggle({ checked, onChange, label }) {
    return (
        <button
            type="button"
            onClick={() => onChange(!checked)}
            className={`inline-flex min-h-11 items-center gap-3 rounded-xl px-2 transition focus:outline-none focus:ring-2 focus:ring-gray-950 focus:ring-offset-2 ${
                checked ? 'text-gray-950' : 'text-gray-600'
            }`}
            aria-pressed={checked}
        >
            <span className={`relative h-7 w-12 rounded-full transition ${checked ? 'bg-gray-950' : 'bg-gray-300'}`}>
                <span className={`absolute top-1 h-5 w-5 rounded-full bg-white shadow-sm transition ${checked ? 'left-6' : 'left-1'}`} />
            </span>
            <span className="text-sm font-semibold">{label}</span>
        </button>
    );
}

function ControlPanel({
    periodCount,
    breakCount,
    isDayActive,
    saving,
    loading,
    onPeriodCountChange,
    onAddBreak,
    onSave,
    onDayActiveChange,
}) {
    return (
        <section className="mb-6 rounded-2xl border border-gray-200 bg-white p-4 shadow-sm sm:p-5">
            <div className="grid gap-4 lg:grid-cols-[1fr_auto_auto_auto] lg:items-center">
                <label className="flex min-h-11 items-center justify-between gap-4 rounded-xl border border-gray-200 bg-gray-50 px-3">
                    <span className="text-sm font-bold text-gray-800">Periods</span>
                    <input
                        type="number"
                        min="1"
                        max="12"
                        value={periodCount}
                        onChange={(event) => onPeriodCountChange(Number(event.target.value))}
                        className="min-h-11 w-20 bg-transparent text-right text-sm font-semibold text-gray-950 outline-none"
                    />
                </label>

                <div className="flex min-h-11 items-center justify-between gap-3 rounded-xl border border-gray-200 bg-gray-50 px-3 lg:min-w-36">
                    <span className="text-sm font-bold text-gray-800">Breaks</span>
                    <span className="rounded-lg bg-white px-3 py-1 text-sm font-bold text-gray-950 shadow-sm ring-1 ring-gray-200">
                        {breakCount}
                    </span>
                </div>

                <button
                    type="button"
                    onClick={onAddBreak}
                    className="min-h-11 rounded-xl border border-gray-200 bg-white px-4 text-sm font-bold text-gray-950 transition hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-gray-950 focus:ring-offset-2"
                >
                    + Add Break
                </button>

                <button
                    type="button"
                    onClick={onSave}
                    disabled={saving || loading}
                    className="min-h-11 rounded-xl bg-gray-950 px-5 text-sm font-bold text-white shadow-sm transition hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-gray-950 focus:ring-offset-2 disabled:cursor-not-allowed disabled:bg-gray-400"
                >
                    {saving ? 'Saving...' : 'Save Changes'}
                </button>
            </div>

            <div className="mt-4 border-t border-gray-200 pt-4">
                <Toggle
                    checked={isDayActive}
                    onChange={onDayActiveChange}
                    label={isDayActive ? 'Day Active' : 'Day Inactive'}
                />
            </div>
        </section>
    );
}

function BreakSection({ breaks, onChange, onDelete }) {
    return (
        <section className="mb-6 rounded-2xl border border-gray-200 bg-white p-4 shadow-sm sm:p-5">
            <div className="mb-4 flex items-end justify-between gap-4">
                <div>
                    <h3 className="text-lg font-bold text-gray-950">Breaks</h3>
                    <p className="mt-1 text-sm text-gray-500">Define shared break windows outside period cards.</p>
                </div>
            </div>

            {breaks.length === 0 ? (
                <div className="rounded-xl border border-dashed border-gray-300 bg-gray-50 p-5 text-sm text-gray-500">
                    No breaks added for this day.
                </div>
            ) : (
                <div className="space-y-3">
                    {breaks.map((breakItem, index) => (
                        <div
                            key={breakItem.id}
                            className="grid gap-3 rounded-xl border border-gray-200 bg-gray-50 p-3 sm:grid-cols-[auto_1fr_1fr_auto] sm:items-end"
                        >
                            <div className="flex min-h-11 items-center text-sm font-bold text-gray-950">
                                Break {index + 1}
                            </div>

                            <label className="space-y-2">
                                <span className="text-sm font-medium text-gray-700">Start time</span>
                                <input
                                    type="time"
                                    value={breakItem.start_time}
                                    onChange={(event) => onChange(breakItem.id, { start_time: event.target.value })}
                                    className="min-h-11 w-full rounded-xl border border-gray-200 bg-white px-3 text-sm text-gray-950 outline-none transition focus:border-gray-950 focus:ring-2 focus:ring-gray-200"
                                />
                            </label>

                            <label className="space-y-2">
                                <span className="text-sm font-medium text-gray-700">End time</span>
                                <input
                                    type="time"
                                    value={breakItem.end_time}
                                    onChange={(event) => onChange(breakItem.id, { end_time: event.target.value })}
                                    className="min-h-11 w-full rounded-xl border border-gray-200 bg-white px-3 text-sm text-gray-950 outline-none transition focus:border-gray-950 focus:ring-2 focus:ring-gray-200"
                                />
                            </label>

                            <button
                                type="button"
                                onClick={() => onDelete(breakItem.id)}
                                className="min-h-11 rounded-xl border border-gray-200 bg-white px-4 text-sm font-bold text-gray-700 transition hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-gray-950 focus:ring-offset-2"
                            >
                                Delete
                            </button>
                        </div>
                    ))}
                </div>
            )}
        </section>
    );
}

function PeriodCard({ entry, onChange }) {
    const subjectColor = getSubjectColor(entry.subject_code || entry.subject_name);
    const isFree = Boolean(entry.is_free);

    const updateEntry = (patch) => {
        const next = { ...entry, ...patch };
        if (next.is_free) {
            next.start_time = '';
            next.end_time = '';
            next.subject_code = '';
            next.subject_name = '';
        }
        onChange(next);
    };

    return (
        <section className={`rounded-2xl border border-gray-200 bg-white p-4 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md sm:p-5 ${isFree ? 'bg-gray-50' : ''}`}>
            <div className="mb-5 flex items-start justify-between gap-4">
                <div className="flex min-w-0 items-start gap-3">
                    <span className={`mt-1 h-3 w-3 shrink-0 rounded-full ${isFree ? 'bg-gray-300' : subjectColor}`} />
                    <div className="min-w-0">
                        <h2 className="text-base font-bold text-gray-950">Period {entry.period}</h2>
                        <p className="mt-1 text-sm text-gray-500">
                            {isFree ? 'Free period' : `${entry.start_time || '--:--'} - ${entry.end_time || '--:--'}`}
                        </p>
                    </div>
                </div>

                <label className="flex min-h-11 shrink-0 items-center gap-2 rounded-xl px-2 text-sm font-semibold text-gray-700">
                    <input
                        type="checkbox"
                        checked={isFree}
                        onChange={(event) => updateEntry({ is_free: event.target.checked })}
                        className="h-4 w-4 rounded border-gray-300 text-gray-950 focus:ring-gray-950"
                    />
                    Free
                </label>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
                <label className="space-y-2">
                    <span className="text-sm font-medium text-gray-700">Start time</span>
                    <input
                        type="time"
                        value={entry.start_time || ''}
                        disabled={isFree}
                        onChange={(event) => updateEntry({ start_time: event.target.value })}
                        className="min-h-11 w-full rounded-xl border border-gray-200 bg-gray-50 px-3 text-sm text-gray-950 outline-none transition focus:border-gray-950 focus:bg-white focus:ring-2 focus:ring-gray-200 disabled:cursor-not-allowed disabled:bg-gray-100 disabled:text-gray-400"
                    />
                </label>

                <label className="space-y-2">
                    <span className="text-sm font-medium text-gray-700">End time</span>
                    <input
                        type="time"
                        value={entry.end_time || ''}
                        disabled={isFree}
                        onChange={(event) => updateEntry({ end_time: event.target.value })}
                        className="min-h-11 w-full rounded-xl border border-gray-200 bg-gray-50 px-3 text-sm text-gray-950 outline-none transition focus:border-gray-950 focus:bg-white focus:ring-2 focus:ring-gray-200 disabled:cursor-not-allowed disabled:bg-gray-100 disabled:text-gray-400"
                    />
                </label>

                <label className="space-y-2 sm:col-span-2">
                    <span className="text-sm font-medium text-gray-700">Subject name</span>
                    <input
                        value={entry.subject_name || ''}
                        disabled={isFree}
                        placeholder={isFree ? 'Free period' : 'Enter subject name'}
                        onChange={(event) => updateEntry({ subject_name: event.target.value })}
                        className="min-h-11 w-full rounded-xl border border-gray-200 bg-gray-50 px-3 text-sm text-gray-950 outline-none transition placeholder:text-gray-400 focus:border-gray-950 focus:bg-white focus:ring-2 focus:ring-gray-200 disabled:cursor-not-allowed disabled:bg-gray-100 disabled:text-gray-400"
                    />
                </label>

                <label className="space-y-2 sm:col-span-2">
                    <span className="text-sm font-medium text-gray-700">Subject code</span>
                    <input
                        value={entry.subject_code || ''}
                        disabled={isFree}
                        placeholder={isFree ? 'No code needed' : 'Enter subject code'}
                        onChange={(event) => updateEntry({ subject_code: event.target.value })}
                        className="min-h-11 w-full rounded-xl border border-gray-200 bg-gray-50 px-3 text-sm text-gray-950 outline-none transition placeholder:text-gray-400 focus:border-gray-950 focus:bg-white focus:ring-2 focus:ring-gray-200 disabled:cursor-not-allowed disabled:bg-gray-100 disabled:text-gray-400"
                    />
                </label>
            </div>
        </section>
    );
}

export default function TimetableBuilder() {
    const { className: encodedClassName } = useParams();
    const className = decodeURIComponent(encodedClassName);
    const [entries, setEntries] = useState([]);
    const [breaksByDay, setBreaksByDay] = useState({});
    const [periodCount, setPeriodCount] = useState(8);
    const [enabledDays, setEnabledDays] = useState(['MON', 'TUE', 'WED', 'THU', 'FRI']);
    const [activeDay, setActiveDay] = useState('MON');
    const [message, setMessage] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);

    useEffect(() => {
        adminAPI.getTimetable(className)
            .then((response) => {
                const teachingEntries = response.data.filter((entry) => !entry.is_break);
                const breakEntries = response.data.filter((entry) => entry.is_break);
                const nextBreaksByDay = {};
                const teachingEntriesByDay = {};

                breakEntries.forEach((entry) => {
                    nextBreaksByDay[entry.day] = [
                        ...(nextBreaksByDay[entry.day] || []),
                        {
                            id: entry.id || `${entry.day}-${entry.start_time}-${entry.end_time}`,
                            start_time: entry.start_time || '',
                            end_time: entry.end_time || '',
                        },
                    ];
                });

                teachingEntries.forEach((entry) => {
                    teachingEntriesByDay[entry.day] = [
                        ...(teachingEntriesByDay[entry.day] || []),
                        entry,
                    ];
                });

                const normalizedTeachingEntries = Object.entries(teachingEntriesByDay).flatMap(([, dayEntries]) => (
                    dayEntries
                        .sort((a, b) => a.period - b.period)
                        .map((entry, index) => ({
                            ...entry,
                            period: index + 1,
                            is_break: false,
                            is_free: !entry.subject_code && !entry.subject_name,
                        }))
                ));

                setEntries(normalizedTeachingEntries);
                setBreaksByDay(nextBreaksByDay);

                const maxTeachingPeriod = Math.max(
                    1,
                    ...Object.values(teachingEntriesByDay).map((dayEntries) => dayEntries.length)
                );
                setPeriodCount(maxTeachingPeriod || 8);

                const usedDays = [...new Set(response.data.map((entry) => entry.day))];
                if (usedDays.length) {
                    const sortedDays = usedDays.sort((a, b) => days.indexOf(a) - days.indexOf(b));
                    setEnabledDays(sortedDays);
                    setActiveDay(sortedDays[0]);
                }
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

    const visiblePeriods = useMemo(
        () => Array.from({ length: periodCount }, (_, index) => index + 1),
        [periodCount]
    );

    const getEntry = (day, period) => entryMap.get(`${day}-${period}`) || makeEmptyEntry(day, period);
    const activeEntries = visiblePeriods.map((period) => getEntry(activeDay, period));
    const activeBreaks = breaksByDay[activeDay] || [];
    const isActiveDayEnabled = enabledDays.includes(activeDay);

    const updateEntry = (updatedEntry) => {
        setMessage('');
        setEntries((previous) => {
            const withoutCurrent = previous.filter(
                (entry) => !(entry.day === updatedEntry.day && entry.period === updatedEntry.period)
            );
            return [...withoutCurrent, { ...updatedEntry, is_break: false }];
        });
        setEnabledDays((previous) => (
            previous.includes(updatedEntry.day)
                ? previous
                : [...previous, updatedEntry.day].sort((a, b) => days.indexOf(a) - days.indexOf(b))
        ));
    };

    const updateActiveBreaks = (updater) => {
        setMessage('');
        setBreaksByDay((previous) => ({
            ...previous,
            [activeDay]: updater(previous[activeDay] || []),
        }));
    };

    const addBreak = () => {
        updateActiveBreaks((currentBreaks) => [
            ...currentBreaks,
            {
                id: `new-${activeDay}-${Date.now()}`,
                start_time: '',
                end_time: '',
            },
        ]);
        setEnabledDays((previous) => (
            previous.includes(activeDay)
                ? previous
                : [...previous, activeDay].sort((a, b) => days.indexOf(a) - days.indexOf(b))
        ));
    };

    const updateBreak = (breakId, patch) => {
        updateActiveBreaks((currentBreaks) => (
            currentBreaks.map((breakItem) => (
                breakItem.id === breakId ? { ...breakItem, ...patch } : breakItem
            ))
        ));
    };

    const deleteBreak = (breakId) => {
        updateActiveBreaks((currentBreaks) => currentBreaks.filter((breakItem) => breakItem.id !== breakId));
    };

    const toggleActiveDay = (enabled) => {
        setMessage('');
        setEnabledDays((previous) => {
            if (enabled) {
                return previous.includes(activeDay)
                    ? previous
                    : [...previous, activeDay].sort((a, b) => days.indexOf(a) - days.indexOf(b));
            }
            return previous.filter((day) => day !== activeDay);
        });
    };

    const normalizeEntriesForSave = () => {
        const payload = [];
        enabledDays.forEach((day) => {
            visiblePeriods.forEach((period) => {
                const entry = getEntry(day, period);
                if (entry.is_free) {
                    return;
                }
                if (!entry.start_time || !entry.end_time) {
                    throw new Error(`Set start and end time for ${dayLabels[day]} period ${period}`);
                }
                payload.push({
                    day,
                    period,
                    subject_code: entry.subject_code || null,
                    subject_name: entry.subject_name || null,
                    start_time: entry.start_time,
                    end_time: entry.end_time,
                    is_break: false,
                });
            });

            (breaksByDay[day] || []).forEach((breakItem, index) => {
                if (!breakItem.start_time || !breakItem.end_time) {
                    throw new Error(`Set start and end time for ${dayLabels[day]} break ${index + 1}`);
                }
                payload.push({
                    day,
                    period: periodCount + index + 1,
                    subject_code: null,
                    subject_name: null,
                    start_time: breakItem.start_time,
                    end_time: breakItem.end_time,
                    is_break: true,
                });
            });
        });
        return payload;
    };

    const handleSave = async () => {
        setError('');
        setMessage('');
        setSaving(true);
        try {
            const freeEntries = enabledDays.flatMap((day) => (
                visiblePeriods
                    .map((period) => getEntry(day, period))
                    .filter((entry) => entry.is_free)
                    .map((entry) => ({
                        ...entry,
                        start_time: '',
                        end_time: '',
                        subject_code: '',
                        subject_name: '',
                        is_break: false,
                        is_free: true,
                    }))
            ));
            const payload = normalizeEntriesForSave();
            const response = await adminAPI.replaceTimetable(className, payload);
            setEntries([
                ...response.data
                    .filter((entry) => !entry.is_break)
                    .map((entry) => ({ ...entry, is_free: false })),
                ...freeEntries,
            ]);
            setBreaksByDay(
                response.data
                    .filter((entry) => entry.is_break)
                    .reduce((acc, entry) => ({
                        ...acc,
                        [entry.day]: [
                            ...(acc[entry.day] || []),
                            {
                                id: entry.id,
                                start_time: entry.start_time,
                                end_time: entry.end_time,
                            },
                        ],
                    }), {})
            );
            setMessage('Timetable saved');
        } catch (err) {
            setError(err.response?.data?.detail || err.message || 'Could not save timetable');
        } finally {
            setSaving(false);
        }
    };

    return (
        <AdminLayout>
            <DayTabs activeDay={activeDay} enabledDays={enabledDays} onChange={setActiveDay} />

            <section className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
                <div>
                    <p className="text-sm font-semibold uppercase text-gray-500">Admin Timetable</p>
                    <h2 className="mt-2 text-3xl font-bold tracking-normal text-gray-950">
                        {className} - {dayLabels[activeDay]} Schedule
                    </h2>
                    <p className="mt-2 max-w-2xl text-sm leading-6 text-gray-600">
                        Manage periods and define breaks separately for a cleaner schedule.
                    </p>
                </div>
            </section>

            {(message || error) && (
                <div className={`mb-5 rounded-xl border px-4 py-3 text-sm font-medium ${
                    error
                        ? 'border-gray-300 bg-white text-gray-950'
                        : 'border-gray-200 bg-gray-100 text-gray-800'
                }`}>
                    {error || message}
                </div>
            )}

            <ControlPanel
                periodCount={periodCount}
                breakCount={activeBreaks.length}
                isDayActive={isActiveDayEnabled}
                saving={saving}
                loading={loading}
                onPeriodCountChange={setPeriodCount}
                onAddBreak={addBreak}
                onSave={handleSave}
                onDayActiveChange={toggleActiveDay}
            />

            {loading ? (
                <div className="rounded-2xl border border-gray-200 bg-white p-6 text-sm text-gray-500 shadow-sm">
                    Loading timetable...
                </div>
            ) : isActiveDayEnabled ? (
                <>
                    <BreakSection breaks={activeBreaks} onChange={updateBreak} onDelete={deleteBreak} />

                    <div className="mb-4">
                        <h3 className="text-lg font-bold text-gray-950">Periods</h3>
                        <p className="mt-1 text-sm text-gray-500">Teaching periods only. Breaks are managed above.</p>
                    </div>

                    <div className="grid gap-4 lg:grid-cols-2">
                        {activeEntries.map((entry) => (
                            <PeriodCard key={`${entry.day}-${entry.period}`} entry={entry} onChange={updateEntry} />
                        ))}
                    </div>
                </>
            ) : (
                <div className="rounded-2xl border border-dashed border-gray-300 bg-white p-8 text-center shadow-sm">
                    <h3 className="text-lg font-bold text-gray-950">{dayLabels[activeDay]} is inactive</h3>
                    <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-gray-600">
                        Turn this day on when the class has scheduled periods.
                    </p>
                    <button
                        type="button"
                        onClick={() => toggleActiveDay(true)}
                        className="mt-5 min-h-11 rounded-xl bg-gray-950 px-5 text-sm font-bold text-white transition hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-gray-950 focus:ring-offset-2"
                    >
                        Activate day
                    </button>
                </div>
            )}
        </AdminLayout>
    );
}
