import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import AdminLayout from './AdminLayout';
import { adminAPI } from '../utils/api';

function ClassTile({ classItem }) {
    return (
        <article className="rounded-xl border border-gray-200 bg-white p-5 text-center shadow-sm transition hover:-translate-y-0.5 hover:border-gray-300 hover:shadow-md">
            <h3 className="truncate text-lg font-bold text-gray-950">{classItem.class_name}</h3>
            <p className="mt-2 text-sm font-medium text-gray-500">
                {classItem.period_count} {classItem.period_count === 1 ? 'period' : 'periods'}
            </p>
            <Link
                to={`/admin/timetable/${encodeURIComponent(classItem.class_name)}`}
                className="mt-4 inline-flex min-h-11 w-full items-center justify-center rounded-xl bg-gray-950 px-4 text-sm font-bold text-white transition hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-gray-950 focus:ring-offset-2"
            >
                Edit Timetable
            </Link>
        </article>
    );
}

function EmptyState() {
    return (
        <section className="rounded-xl border border-dashed border-gray-300 bg-white p-8 text-center shadow-sm">
            <h3 className="text-lg font-bold text-gray-950">No classes yet</h3>
            <Link
                to="/admin/classes"
                className="mt-5 inline-flex min-h-11 items-center justify-center rounded-xl bg-gray-950 px-5 text-sm font-bold text-white transition hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-gray-950 focus:ring-offset-2"
            >
                + Add Class
            </Link>
        </section>
    );
}

export default function AdminDashboard() {
    const [classes, setClasses] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        let isMounted = true;

        async function loadClasses() {
            try {
                const response = await adminAPI.getClasses();
                const classesWithPeriods = await Promise.all(
                    response.data.map(async (classItem) => {
                        try {
                            const timetableResponse = await adminAPI.getTimetable(classItem.class_name);
                            const periods = timetableResponse.data
                                .filter((entry) => !entry.is_break)
                                .map((entry) => entry.period);

                            return {
                                ...classItem,
                                period_count: periods.length ? Math.max(...periods) : 0,
                            };
                        } catch (_) {
                            return {
                                ...classItem,
                                period_count: 0,
                            };
                        }
                    })
                );

                if (isMounted) setClasses(classesWithPeriods);
            } finally {
                if (isMounted) setLoading(false);
            }
        }

        loadClasses();

        return () => {
            isMounted = false;
        };
    }, []);

    return (
        <AdminLayout>
            <header className="mb-6 flex items-center justify-between gap-4">
                <h2 className="text-3xl font-bold tracking-normal text-gray-950">Dashboard</h2>
                <Link
                    to="/admin/classes"
                    className="inline-flex min-h-11 shrink-0 items-center justify-center rounded-xl bg-gray-950 px-5 text-sm font-bold text-white transition hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-gray-950 focus:ring-offset-2"
                >
                    + Add Class
                </Link>
            </header>

            {loading ? (
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                    {[1, 2, 3].map((item) => (
                        <div key={item} className="h-40 animate-pulse rounded-xl border border-gray-200 bg-white shadow-sm" />
                    ))}
                </div>
            ) : classes.length === 0 ? (
                <EmptyState />
            ) : (
                <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                    {classes.map((classItem) => (
                        <ClassTile key={classItem.id} classItem={classItem} />
                    ))}
                </section>
            )}
        </AdminLayout>
    );
}
