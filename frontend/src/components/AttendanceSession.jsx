import React, { useState, useEffect, useRef } from 'react';
import { attendanceAPI } from '../utils/api';

export default function AttendanceSession({ session, onClose }) {
    const [students, setStudents] = useState([]);
    const [loading, setLoading] = useState(false);
    const [sessionData, setSessionData] = useState(session);
    const videoRef = useRef(null);
    const streamRef = useRef(null);

    useEffect(() => {
        startCamera();
        loadStudents();

        // Poll for updates every 3 seconds
        const updateInterval = setInterval(loadStudents, 3000);

        // Frame capture loop (send frame every 1 second)
        const frameInterval = setInterval(captureAndSendFrame, 1000);

        return () => {
            clearInterval(updateInterval);
            clearInterval(frameInterval);
            stopCamera();
        };
    }, []);

    const startCamera = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { width: 1280, height: 720 }
            });

            if (videoRef.current) {
                videoRef.current.srcObject = stream;
                streamRef.current = stream;
            }
        } catch (err) {
            console.error('Error accessing camera:', err);
            alert('Failed to access camera. Please grant camera permissions.');
        }
    };

    const stopCamera = () => {
        if (streamRef.current) {
            streamRef.current.getTracks().forEach(track => track.stop());
        }
    };

    const captureAndSendFrame = async () => {
        if (!videoRef.current || !streamRef.current) return;

        try {
            const canvas = document.createElement('canvas');
            canvas.width = videoRef.current.videoWidth;
            canvas.height = videoRef.current.videoHeight;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(videoRef.current, 0, 0);

            canvas.toBlob(async (blob) => {
                if (!blob) return;

                const formData = new FormData();
                formData.append('file', blob, 'frame.jpg');

                try {
                    await attendanceAPI.recognizeFace(session.id, formData);
                    // We don't need to do anything with the response because 
                    // the loadStudents polling will pick up any changes
                } catch (err) {
                    // Silent fail for individual frames to avoid spamming alerts
                    console.error('Frame recognition error:', err);
                }
            }, 'image/jpeg', 0.8);
        } catch (err) {
            console.error('Capture error:', err);
        }
    };

    const loadStudents = async () => {
        try {
            const response = await attendanceAPI.getSessionStudents(session.id);
            setStudents(response.data);
        } catch (err) {
            console.error('Error loading students:', err);
        }
    };

    const handleStatusChange = async (regNo, newStatus) => {
        try {
            await attendanceAPI.manualOverride(session.id, regNo, newStatus);
            loadStudents(); // Reload to get updated data
        } catch (err) {
            alert('Failed to update attendance');
        }
    };

    const handleEndSession = async () => {
        if (!confirm('Are you sure you want to end this session? All unmarked students will be marked absent.')) {
            return;
        }

        setLoading(true);
        try {
            await attendanceAPI.endSession(session.id);
            stopCamera();
            onClose();
        } catch (err) {
            alert('Failed to end session');
            setLoading(false);
        }
    };

    const presentCount = students.filter(s => s.status === 'present').length;
    const absentCount = students.filter(s => s.status === 'absent').length;
    const odCount = students.filter(s => s.status === 'od').length;

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Header */}
            <header className="bg-white shadow-sm border-b border-gray-200">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
                    <div className="flex justify-between items-center">
                        <div>
                            <h1 className="text-2xl font-bold text-gray-900">Attendance Session</h1>
                            <p className="text-sm text-gray-600">
                                Period {session.period} - {session.subject_name} ({session.subject_code})
                            </p>
                            <p className="text-xs text-gray-500">
                                {session.start_time} - {session.end_time}
                            </p>
                        </div>
                        <button
                            onClick={handleEndSession}
                            disabled={loading}
                            className="px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition font-medium disabled:opacity-50"
                        >
                            {loading ? 'Ending...' : 'End Session'}
                        </button>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    {/* Left Column - Camera Feed */}
                    <div className="space-y-6">
                        {/* Camera View */}
                        <div className="bg-white rounded-2xl shadow-lg border border-gray-200 overflow-hidden">
                            <div className="bg-linear-to-r from-indigo-600 to-purple-600 px-6 py-4">
                                <h2 className="text-xl font-bold text-white">Live Camera Feed</h2>
                            </div>

                            <div className="p-4">
                                <div className="relative bg-black rounded-xl overflow-hidden aspect-video">
                                    <video
                                        ref={videoRef}
                                        autoPlay
                                        playsInline
                                        muted
                                        className="w-full h-full object-cover transform -scale-x-100"
                                    />

                                    {/* Overlay Info */}
                                    <div className="absolute top-4 left-4 bg-black/60 backdrop-blur-sm px-4 py-2 rounded-lg">
                                        <p className="text-white text-sm font-medium">
                                            <span className="inline-block w-2 h-2 bg-red-500 rounded-full animate-pulse mr-2"></span>
                                            Recording
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Stats Cards */}
                        <div className="grid grid-cols-3 gap-4">
                            <div className="bg-green-50 border-2 border-green-200 rounded-xl p-4">
                                <p className="text-sm text-green-600 font-medium">Present</p>
                                <p className="text-3xl font-bold text-green-700">{presentCount}</p>
                            </div>
                            <div className="bg-red-50 border-2 border-red-200 rounded-xl p-4">
                                <p className="text-sm text-red-600 font-medium">Absent</p>
                                <p className="text-3xl font-bold text-red-700">{absentCount}</p>
                            </div>
                            <div className="bg-blue-50 border-2 border-blue-200 rounded-xl p-4">
                                <p className="text-sm text-blue-600 font-medium">OD</p>
                                <p className="text-3xl font-bold text-blue-700">{odCount}</p>
                            </div>
                        </div>
                    </div>

                    {/* Right Column - Student List */}
                    <div className="bg-white rounded-2xl shadow-lg border border-gray-200 overflow-hidden">
                        <div className="bg-linear-to-r from-purple-600 to-pink-600 px-6 py-4">
                            <h2 className="text-xl font-bold text-white">Student Attendance</h2>
                            <p className="text-sm text-purple-100">Total: {students.length} students</p>
                        </div>

                        <div className="overflow-y-auto" style={{ maxHeight: '70vh' }}>
                            <table className="w-full">
                                <thead className="bg-gray-50 border-b border-gray-200 sticky top-0">
                                    <tr>
                                        <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Reg No</th>
                                        <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Name</th>
                                        <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Status</th>
                                        <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Marked By</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-200">
                                    {students.map((student) => (
                                        <tr key={student.reg_no} className="hover:bg-gray-50 transition">
                                            <td className="px-4 py-3 text-sm font-medium text-gray-900">
                                                {student.reg_no}
                                            </td>
                                            <td className="px-4 py-3 text-sm text-gray-700">
                                                {student.name}
                                            </td>
                                            <td className="px-4 py-3">
                                                <select
                                                    value={student.status}
                                                    onChange={(e) => handleStatusChange(student.reg_no, e.target.value)}
                                                    className={`px-3 py-1 rounded-full text-xs font-semibold border-2 focus:outline-none focus:ring-2 focus:ring-offset-1 ${student.status === 'present'
                                                        ? 'bg-green-100 text-green-700 border-green-300 focus:ring-green-500'
                                                        : student.status === 'absent'
                                                            ? 'bg-red-100 text-red-700 border-red-300 focus:ring-red-500'
                                                            : 'bg-blue-100 text-blue-700 border-blue-300 focus:ring-blue-500'
                                                        }`}
                                                >
                                                    <option value="present">Present</option>
                                                    <option value="absent">Absent</option>
                                                    <option value="od">OD</option>
                                                </select>
                                            </td>
                                            <td className="px-4 py-3">
                                                <span className={`px-2 py-1 rounded-full text-xs ${student.marked_by === 'system'
                                                    ? 'bg-purple-100 text-purple-700'
                                                    : 'bg-orange-100 text-orange-700'
                                                    }`}>
                                                    {student.marked_by === 'system' ? '🤖 System' : '👤 Faculty'}
                                                </span>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}
