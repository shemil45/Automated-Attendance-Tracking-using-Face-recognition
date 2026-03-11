import React, { useState, useEffect, useRef } from 'react';
import { useParams, useLocation, useNavigate } from 'react-router-dom';
import { attendanceAPI } from '../utils/api';

export default function AttendanceSession() {
    const { sessionId } = useParams();
    const location = useLocation();
    const navigate = useNavigate();

    // Session data comes from router state (passed by Dashboard) or fetched by ID
    const [session, setSession] = useState(location.state?.session || null);
    const [students, setStudents] = useState([]);
    const [loading, setLoading] = useState(false);
    const [initialLoading, setInitialLoading] = useState(true);
    const videoRef = useRef(null);
    const canvasRef = useRef(null);
    const streamRef = useRef(null);
    const isActiveRef = useRef(true);    // flipped to false on unmount
    const isSendingRef = useRef(false);   // true while a request is in-flight
    const facesRef = useRef([]);          // latest face list from backend
    const faceNameCacheRef = useRef({}); // name → { cx, cy, lastSeen } — prevents Unknown flicker
    const rafRef = useRef(null);          // rAF handle for draw loop
    const lastFaceUpdateRef = useRef(0); // timestamp of last backend response

    // If session wasn't passed via state (e.g. direct URL / page refresh), fetch it
    useEffect(() => {
        if (!session) {
            attendanceAPI.getSession(sessionId)
                .then(res => setSession(res.data))
                .catch(() => navigate('/dashboard'));
        }
    }, []);

    useEffect(() => {
        if (!session) return;

        isActiveRef.current = true;
        startCamera();
        loadStudents();
        startDrawLoop();

        const updateInterval = setInterval(loadStudents, 1500);
        const frameInterval = setInterval(captureAndSendFrame, 1000);

        return () => {
            isActiveRef.current = false;
            clearInterval(updateInterval);
            clearInterval(frameInterval);
            stopDrawLoop();
            stopCamera();
        };
    }, [session]);

    const startCamera = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { width: 640, height: 480 }  // 640×480 is plenty for face detection and uploads faster
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

    // ── Continuous draw loop (requestAnimationFrame) ─────────────────────────
    // Draws from facesRef so boxes never flicker between API responses.
    const drawFaceBoxes = () => {
        const canvas = canvasRef.current;
        const video = videoRef.current;
        if (!canvas || !video) return;

        // Keep canvas pixel size synced to displayed element size
        if (canvas.width !== video.clientWidth || canvas.height !== video.clientHeight) {
            canvas.width = video.clientWidth || 640;
            canvas.height = video.clientHeight || 360;
        }
        const cw = canvas.width;
        const ch = canvas.height;
        if (!cw || !ch) return;

        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, cw, ch);

        // If no face update in >3s, clear facesRef to hide stale boxes
        if (Date.now() - lastFaceUpdateRef.current > 3000) {
            facesRef.current = [];
        }

        const now = Date.now();
        const CACHE_TTL = 5000; // ms to keep a recognized name "sticky"

        facesRef.current.forEach(({ name, box }) => {
            if (!box) return;
            const { x, y, w, h, fw, fh } = box;

            const scaleX = cw / fw;
            const scaleY = ch / fh;

            // Mirror X — video is CSS-flipped with -scale-x-100
            const drawX = cw - (x + w) * scaleX;
            const drawY = y * scaleY;
            const drawW = w * scaleX;
            const drawH = h * scaleY;
            const faceCx = drawX + drawW / 2;
            const faceCy = drawY + drawH / 2;

            // Resolve name: if backend said null, check name cache for a nearby match
            let resolvedName = name;
            if (!resolvedName) {
                let bestMatch = null;
                let bestDist = Infinity;
                for (const [n, cached] of Object.entries(faceNameCacheRef.current)) {
                    if (now - cached.lastSeen > CACHE_TTL) continue;
                    const dist = Math.hypot(cached.cx - faceCx, cached.cy - faceCy);
                    const threshold = Math.max(drawW, drawH) * 0.8;
                    if (dist < threshold && dist < bestDist) {
                        bestDist = dist;
                        bestMatch = n;
                    }
                }
                resolvedName = bestMatch;
            } else {
                // Update cache with latest position
                faceNameCacheRef.current[resolvedName] = { cx: faceCx, cy: faceCy, lastSeen: now };
            }

            const isKnown = !!resolvedName;
            const color = isKnown ? '#22c55e' : '#ef4444';
            const label = resolvedName || 'Unknown';

            // Draw bounding box
            ctx.strokeStyle = color;
            ctx.lineWidth = 3.5;
            ctx.setLineDash(isKnown ? [] : [6, 4]);
            ctx.strokeRect(drawX, drawY, drawW, drawH);
            ctx.setLineDash([]);

            // Draw label pill
            ctx.font = 'bold 13px Inter, system-ui, sans-serif';
            const textWidth = ctx.measureText(label).width;
            const padX = 8, padY = 5, labelH = 22;
            const labelY = drawY > labelH + 4 ? drawY - labelH - 4 : drawY + drawH + 4;

            ctx.fillStyle = isKnown ? 'rgba(22,163,74,0.88)' : 'rgba(239,68,68,0.88)';
            ctx.beginPath();
            ctx.roundRect(drawX, labelY, textWidth + padX * 2, labelH, 4);
            ctx.fill();

            ctx.fillStyle = '#fff';
            ctx.fillText(label, drawX + padX, labelY + labelH - padY);
        });
    };

    const startDrawLoop = () => {
        const loop = () => {
            if (!isActiveRef.current) return;
            drawFaceBoxes();
            rafRef.current = requestAnimationFrame(loop);
        };
        rafRef.current = requestAnimationFrame(loop);
    };

    const stopDrawLoop = () => {
        if (rafRef.current) {
            cancelAnimationFrame(rafRef.current);
            rafRef.current = null;
        }
    };

    const captureAndSendFrame = async () => {
        if (!isActiveRef.current || isSendingRef.current) return;
        if (!videoRef.current || !streamRef.current) return;

        try {
            const offscreen = document.createElement('canvas');
            offscreen.width = videoRef.current.videoWidth;
            offscreen.height = videoRef.current.videoHeight;
            const ctx = offscreen.getContext('2d');
            ctx.drawImage(videoRef.current, 0, 0);

            offscreen.toBlob(async (blob) => {
                if (!blob || !isActiveRef.current) return;

                isSendingRef.current = true;
                const formData = new FormData();
                formData.append('file', blob, 'frame.jpg');

                try {
                    const res = await attendanceAPI.recognizeFace(session.id, formData);
                    if (res?.data?.faces) {
                        // Update the ref — the rAF loop will pick it up on next paint
                        facesRef.current = res.data.faces;
                        lastFaceUpdateRef.current = Date.now();
                    }
                } catch (err) {
                    console.error('Frame recognition error:', err);
                } finally {
                    isSendingRef.current = false;
                }
            }, 'image/jpeg', 0.8);
        } catch (err) {
            console.error('Capture error:', err);
        }
    };

    const loadStudents = async () => {
        try {
            const response = await attendanceAPI.getSessionStudents(session.id);
            const sorted = [...response.data].sort((a, b) => {
                // No marked_at → goes to the bottom
                if (!a.marked_at && !b.marked_at) return 0;
                if (!a.marked_at) return 1;
                if (!b.marked_at) return -1;
                // Most recently marked → top
                return new Date(b.marked_at) - new Date(a.marked_at);
            });
            setStudents(sorted);
        } catch (err) {
            console.error('Error loading students:', err);
        } finally {
            setInitialLoading(false);
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
            navigate('/dashboard');
        } catch (err) {
            alert('Failed to end session');
            setLoading(false);
        }
    };

    const presentCount = students.filter(s => s.status === 'present').length;
    const absentCount = students.filter(s => s.status === 'absent').length;
    const odCount = students.filter(s => s.status === 'od').length;

    // Show loading screen while fetching session data (e.g. on page refresh)
    if (!session) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-50">
                <div className="text-center">
                    <div className="w-16 h-16 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
                    <p className="mt-4 text-gray-600">Loading session...</p>
                </div>
            </div>
        );
    }

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
                        <div className="flex gap-3">
                            <button
                                onClick={() => { stopCamera(); navigate('/dashboard'); }}
                                className="px-6 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition font-medium"
                            >
                                ← Back
                            </button>
                            <button
                                onClick={handleEndSession}
                                disabled={loading}
                                className="px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition font-medium disabled:opacity-50"
                            >
                                {loading ? 'Ending...' : 'End Session'}
                            </button>
                        </div>
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
                            <div className="bg-gray-50 border-b border-gray-200 px-6 py-4">
                                <h2 className="text-xl font-semibold text-gray-800">Live Camera Feed</h2>
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

                                    {/* Bounding box canvas overlay */}
                                    <canvas
                                        ref={canvasRef}
                                        className="absolute inset-0 w-full h-full pointer-events-none"
                                        style={{ mixBlendMode: 'normal' }}
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
                        <div className="bg-gray-50 border-b border-gray-200 px-6 py-4">
                            <h2 className="text-xl font-semibold text-gray-800">Student Attendance</h2>
                            <p className="text-sm text-gray-500">
                                {initialLoading ? 'Loading...' : `Total: ${students.length} students`}
                            </p>
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
                                    {initialLoading ? (
                                        <tr>
                                            <td colSpan={4} className="px-4 py-8 text-center text-gray-400 text-sm">
                                                Loading students...
                                            </td>
                                        </tr>
                                    ) : students.length === 0 ? (
                                        <tr>
                                            <td colSpan={4} className="px-4 py-8 text-center text-gray-400 text-sm">
                                                No students found in this class.
                                            </td>
                                        </tr>
                                    ) : students.map((student) => (
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
                                                <span className={`px-2 py-1 rounded-full text-xs ${student.marked_by === 'faculty'
                                                    ? 'bg-orange-100 text-orange-700'
                                                    : 'bg-purple-100 text-purple-700'
                                                    }`}>
                                                    {student.marked_by === 'faculty' ? '👤 Faculty' : '🤖 System'}
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
