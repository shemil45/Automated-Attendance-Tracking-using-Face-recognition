import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { timetableAPI, attendanceAPI, reportsAPI } from '../utils/api';
import { auth } from '../utils/auth';
import AttendanceSession from './AttendanceSession';

export default function Dashboard() {
    const [todayTimetable, setTodayTimetable] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [currentSession, setCurrentSession] = useState(null);
    const [showReports, setShowReports] = useState(false);
    const [selectedDate, setSelectedDate] = useState('');
    const [sessions, setSessions] = useState([]);

    const navigate = useNavigate();

    const className = auth.getClassName();

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
                period.period
            );
            setCurrentSession(response.data);
        } catch (err) {
            alert('Failed to start session: ' + (err.response?.data?.detail || err.message));
        }
    };

    const handleSessionEnd = () => {
        setCurrentSession(null);
        loadTodayTimetable(); // Reload to update statuses
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
        } catch (err) {
            alert('Failed to load sessions');
        }
    };

    const handleDownloadReport = async (sessionId) => {
        try {
            const response = await reportsAPI.exportSession(sessionId);

            // Create download link
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

    const getStatusBadge = (status) => {
        const badges = {
            not_started: 'bg-gray-500/20 text-gray-700 border-gray-300',
            ongoing: 'bg-yellow-500/20 text-yellow-700 border-yellow-300',
            completed: 'bg-green-500/20 text-green-700 border-green-300',
        };

        const labels = {
            not_started: 'Not Started',
            ongoing: 'Ongoing',
            completed: 'Completed',
        };

        return (
            <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${badges[status]}`}>
                {labels[status]}
            </span>
        );
    };

    const getActionButton = (period) => {
        if (period.status === 'not_started') {
            return (
                <button
                    onClick={() => handleStartSession(period)}
                    className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition font-medium"
                >
                    Start Attendance
                </button>
            );
        } else if (period.status === 'ongoing') {
            return (
                <button
                    onClick={() => handleStartSession(period)}
                    className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition font-medium"
                >
                    Open Session
                </button>
            );
        } else if (period.status === 'completed') {
            return (
                <button
                    onClick={() => handleViewReport(period)}
                    className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition font-medium"
                >
                    View Report
                </button>
            );
        }
    };

    if (currentSession) {
        return <AttendanceSession session={currentSession} onClose={handleSessionEnd} />;
    }

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-50">
                <div className="text-center">
                    <div className="w-16 h-16 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
                    <p className="mt-4 text-gray-600">Loading timetable...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-linear-to-br from-gray-50 to-gray-100">
            {/* Header */}
            <header className="bg-white shadow-sm border-b border-gray-200">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
                    <div className="flex justify-between items-center">
                        <div>
                            <h1 className="text-2xl font-bold text-gray-900">Faculty Portal</h1>
                            <p className="text-sm text-gray-600">Welcome, {className}</p>
                        </div>
                        <div className="flex gap-3">
                            <button
                                onClick={async () => {
                                    if (confirm('Sync students from CSV database?')) {
                                        try {
                                            const res = await import('../utils/api').then(m => m.utilityAPI.syncStudents());
                                            alert(`Synced Successfully!\nAdded: ${res.data.added}\nUpdated: ${res.data.updated}`);
                                        } catch (e) {
                                            alert('Sync Failed');
                                        }
                                    }
                                }}
                                className="px-4 py-2 bg-indigo-100 text-indigo-700 rounded-lg hover:bg-indigo-200 transition font-medium"
                            >
                                Sync DB
                            </button>
                            <button
                                onClick={auth.logout}
                                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition font-medium"
                            >
                                Logout
                            </button>
                        </div>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {/* Today's Timetable Section */}
                <div className="bg-white rounded-2xl shadow-lg border border-gray-200 overflow-hidden mb-8">
                    <div className="bg-linear-to-r from-indigo-600 to-purple-600 px-6 py-4">
                        <h2 className="text-xl font-bold text-white">Today's Schedule</h2>
                        <p className="text-indigo-100 text-sm">
                            {todayTimetable && new Date(todayTimetable.date).toLocaleDateString('en-US', {
                                weekday: 'long',
                                year: 'numeric',
                                month: 'long',
                                day: 'numeric'
                            })}
                        </p>
                    </div>

                    {error && (
                        <div className="bg-red-50 border-l-4 border-red-500 p-4">
                            <p className="text-red-700">{error}</p>
                        </div>
                    )}

                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead className="bg-gray-50 border-b border-gray-200">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Period</th>
                                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Time</th>
                                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Subject</th>
                                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Status</th>
                                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Action</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-200">
                                {todayTimetable?.periods.map((period) => (
                                    <tr key={period.id} className="hover:bg-gray-50 transition">
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <span className="font-semibold text-gray-900">Period {period.period}</span>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                                            {period.start_time} - {period.end_time}
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="text-sm font-medium text-gray-900">{period.subject_name}</div>
                                            <div className="text-xs text-gray-500">{period.subject_code}</div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            {getStatusBadge(period.status)}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            {getActionButton(period)}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>

                {/* Previous Reports Section */}
                <div className="bg-white rounded-2xl shadow-lg border border-gray-200 overflow-hidden">
                    <div className="bg-linear-to-r from-purple-600 to-pink-600 px-6 py-4">
                        <h2 className="text-xl font-bold text-white">Previous Attendance Reports</h2>
                    </div>

                    <div className="p-6">
                        <div className="flex gap-4 items-end mb-6">
                            <div className="flex-1">
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    Select Date
                                </label>
                                <input
                                    type="date"
                                    value={selectedDate}
                                    onChange={(e) => setSelectedDate(e.target.value)}
                                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                                />
                            </div>
                            <button
                                onClick={loadSessionsByDate}
                                disabled={!selectedDate}
                                className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                Load Sessions
                            </button>
                        </div>

                        {sessions.length > 0 && (
                            <div className="space-y-3">
                                {sessions.map((session) => (
                                    <div key={session.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg border border-gray-200">
                                        <div className="flex-1">
                                            <h4 className="font-semibold text-gray-900">
                                                Period {session.period} - {session.subject_name}
                                            </h4>
                                            <p className="text-sm text-gray-600">
                                                {session.start_time} - {session.end_time} | {session.subject_code}
                                            </p>
                                        </div>
                                        <div className="flex gap-2">
                                            <button
                                                onClick={() => navigate(`/report/${session.id}`)}
                                                className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition text-sm font-medium"
                                            >
                                                View
                                            </button>
                                            <button
                                                onClick={() => handleDownloadReport(session.id)}
                                                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition text-sm font-medium"
                                            >
                                                Download Excel
                                            </button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            </main>
        </div>
    );
}
