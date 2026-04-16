import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import AdminLayout from './AdminLayout';
import { adminAPI } from '../utils/api';

function EyeIcon({ hidden }) {
    return hidden ? (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <path d="M3 3l18 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
            <path d="M10.6 10.6A2 2 0 0012 14a2 2 0 001.4-.6M8.1 5.6A9.8 9.8 0 0112 5c5 0 8.3 4.1 9.3 5.6.3.4.3.9 0 1.3-.5.8-1.7 2.2-3.4 3.4M6.2 6.9a14.7 14.7 0 00-3.5 3.7c-.3.4-.3.9 0 1.3C3.7 13.4 7 17.5 12 17.5c1.3 0 2.5-.3 3.6-.8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
    ) : (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <path d="M2.7 10.6C3.7 9.1 7 5 12 5s8.3 4.1 9.3 5.6c.3.4.3.9 0 1.3C20.3 13.4 17 17.5 12 17.5s-8.3-4.1-9.3-5.6c-.3-.4-.3-.9 0-1.3z" stroke="currentColor" strokeWidth="2" strokeLinejoin="round" />
            <path d="M12 14a2 2 0 100-4 2 2 0 000 4z" stroke="currentColor" strokeWidth="2" />
        </svg>
    );
}

function PasswordField({ id, label, value, onChange, placeholder, visible, onToggle, required = false }) {
    return (
        <label htmlFor={id} className="block">
            <span className="text-sm font-semibold text-gray-800">{label}</span>
            <div className="relative mt-2">
                <input
                    id={id}
                    type={visible ? 'text' : 'password'}
                    value={value}
                    onChange={(event) => onChange(event.target.value)}
                    placeholder={placeholder}
                    minLength={6}
                    required={required}
                    className="min-h-11 w-full rounded-xl border border-gray-200 bg-gray-50 px-3 pr-12 text-sm text-gray-950 outline-none transition placeholder:text-gray-400 focus:border-gray-950 focus:bg-white focus:ring-2 focus:ring-gray-200"
                />
                <button
                    type="button"
                    onClick={onToggle}
                    className="absolute right-2 top-1/2 inline-flex min-h-9 min-w-9 -translate-y-1/2 items-center justify-center rounded-lg text-gray-500 transition hover:bg-gray-100 hover:text-gray-950 focus:outline-none focus:ring-2 focus:ring-gray-950"
                    aria-label={visible ? 'Hide password' : 'Show password'}
                >
                    <EyeIcon hidden={!visible} />
                </button>
            </div>
        </label>
    );
}

function CreateClassCard({
    className,
    password,
    passwordVisible,
    onClassNameChange,
    onPasswordChange,
    onPasswordToggle,
    onSubmit,
}) {
    return (
        <section className="mb-6 rounded-xl border border-gray-200 bg-white p-4 shadow-sm sm:p-5">
            <div className="mb-5">
                <h3 className="text-lg font-bold text-gray-950">Create Class</h3>
                <p className="mt-1 text-sm text-gray-500">Add a class login for the timetable portal.</p>
            </div>

            <form onSubmit={onSubmit} autoComplete="off" className="grid gap-4 lg:grid-cols-2">
                <label htmlFor="class-name" className="block">
                    <span className="text-sm font-semibold text-gray-800">Class Name</span>
                    <input
                        id="class-name"
                        value={className}
                        onChange={(event) => onClassNameChange(event.target.value)}
                        autoComplete="off"
                        required
                        className="mt-2 min-h-11 w-full rounded-xl border border-gray-200 bg-gray-50 px-3 text-sm text-gray-950 outline-none transition placeholder:text-gray-400 focus:border-gray-950 focus:bg-white focus:ring-2 focus:ring-gray-200"
                    />
                </label>

                <PasswordField
                    id="class-password"
                    label="Password"
                    value={password}
                    onChange={onPasswordChange}
                    placeholder="Minimum 6 characters"
                    visible={passwordVisible}
                    onToggle={onPasswordToggle}
                    required
                />

                <div className="flex justify-end lg:col-span-2">
                    <button
                        type="submit"
                        className="min-h-11 w-full rounded-xl bg-gray-950 px-5 text-sm font-bold text-white transition hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-gray-950 focus:ring-offset-2 sm:w-auto"
                    >
                        Create Class
                    </button>
                </div>
            </form>
        </section>
    );
}

function ClassCard({
    classItem,
    isPasswordOpen,
    passwordDraft,
    passwordVisible,
    onTogglePasswordPanel,
    onPasswordDraftChange,
    onPasswordVisibilityToggle,
    onPasswordUpdate,
    onDelete,
}) {
    return (
        <article className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm transition hover:border-gray-300 hover:shadow-md sm:p-5">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <div>
                    <h3 className="text-lg font-bold text-gray-950">{classItem.class_name}</h3>
                    <p className="mt-1 text-sm text-gray-500">Class login and timetable access</p>
                </div>

                <div className="flex flex-col gap-2 sm:flex-row">
                    <Link
                        to={`/admin/timetable/${encodeURIComponent(classItem.class_name)}`}
                        className="inline-flex min-h-11 items-center justify-center rounded-xl bg-gray-950 px-4 text-sm font-bold text-white transition hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-gray-950 focus:ring-offset-2"
                    >
                        Edit Timetable
                    </Link>
                    <button
                        type="button"
                        onClick={onTogglePasswordPanel}
                        className="inline-flex min-h-11 items-center justify-center rounded-xl border border-gray-200 bg-white px-4 text-sm font-bold text-gray-800 transition hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-gray-950 focus:ring-offset-2"
                    >
                        {isPasswordOpen ? 'Hide Password' : 'View Password'}
                    </button>
                    <button
                        type="button"
                        onClick={onDelete}
                        className="inline-flex min-h-11 items-center justify-center rounded-xl border border-gray-200 bg-white px-4 text-sm font-bold text-gray-700 transition hover:border-gray-400 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-gray-950 focus:ring-offset-2"
                    >
                        Delete
                    </button>
                </div>
            </div>

            {isPasswordOpen && (
                <form onSubmit={onPasswordUpdate} className="mt-4 rounded-xl border border-gray-200 bg-gray-50 p-4">
                    <p className="mb-3 text-sm text-gray-600">
                        Passwords are stored securely and cannot be read back. Set a new password here.
                    </p>
                    <div className="grid gap-3 sm:grid-cols-[1fr_auto] sm:items-end">
                        <PasswordField
                            id={`password-${classItem.id}`}
                            label="New Password"
                            value={passwordDraft}
                            onChange={onPasswordDraftChange}
                            placeholder="Enter new password"
                            visible={passwordVisible}
                            onToggle={onPasswordVisibilityToggle}
                        />
                        <button
                            type="submit"
                            className="min-h-11 rounded-xl bg-gray-950 px-5 text-sm font-bold text-white transition hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-gray-950 focus:ring-offset-2"
                        >
                            Update
                        </button>
                    </div>
                </form>
            )}
        </article>
    );
}

export default function ClassManagement() {
    const [classes, setClasses] = useState([]);
    const [className, setClassName] = useState('');
    const [password, setPassword] = useState('');
    const [passwordVisible, setPasswordVisible] = useState(false);
    const [openPasswordClassId, setOpenPasswordClassId] = useState(null);
    const [passwordDrafts, setPasswordDrafts] = useState({});
    const [visiblePasswordDrafts, setVisiblePasswordDrafts] = useState({});
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
            setPasswordVisible(false);
            setMessage('Class created');
            loadClasses();
        } catch (err) {
            setError(err.response?.data?.detail || 'Could not create class');
        }
    };

    const handlePasswordUpdate = async (event, classItem) => {
        event.preventDefault();
        const nextPassword = passwordDrafts[classItem.id] || '';
        if (!nextPassword) return;

        try {
            await adminAPI.updateClass(classItem.id, { password: nextPassword });
            setPasswordDrafts((current) => ({ ...current, [classItem.id]: '' }));
            setOpenPasswordClassId(null);
            setMessage('Password updated');
            setError('');
        } catch (err) {
            setError(err.response?.data?.detail || 'Could not update password');
            setMessage('');
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
            setMessage('');
        }
    };

    return (
        <AdminLayout>
            <header className="mb-6">
                <h2 className="text-3xl font-bold tracking-normal text-gray-950">Class Management</h2>
                <p className="mt-2 text-sm leading-6 text-gray-600">
                    Create class accounts and manage timetable access.
                </p>
            </header>

            {(message || error) && (
                <div className={`mb-5 rounded-xl border px-4 py-3 text-sm font-medium ${
                    error
                        ? 'border-gray-300 bg-white text-gray-950'
                        : 'border-gray-200 bg-gray-100 text-gray-800'
                }`}>
                    {error || message}
                </div>
            )}

            <CreateClassCard
                className={className}
                password={password}
                passwordVisible={passwordVisible}
                onClassNameChange={setClassName}
                onPasswordChange={setPassword}
                onPasswordToggle={() => setPasswordVisible((visible) => !visible)}
                onSubmit={handleCreate}
            />

            <section className="space-y-3">
                <div className="flex items-center justify-between gap-4">
                    <h3 className="text-lg font-bold text-gray-950">Existing Classes</h3>
                    <span className="text-sm font-medium text-gray-500">{classes.length} total</span>
                </div>

                {classes.length === 0 ? (
                    <div className="rounded-xl border border-dashed border-gray-300 bg-white p-6 text-center text-sm text-gray-500 shadow-sm">
                        No classes yet.
                    </div>
                ) : (
                    <div className="grid gap-3">
                        {classes.map((classItem) => (
                            <ClassCard
                                key={classItem.id}
                                classItem={classItem}
                                isPasswordOpen={openPasswordClassId === classItem.id}
                                passwordDraft={passwordDrafts[classItem.id] || ''}
                                passwordVisible={Boolean(visiblePasswordDrafts[classItem.id])}
                                onTogglePasswordPanel={() => setOpenPasswordClassId((current) => (
                                    current === classItem.id ? null : classItem.id
                                ))}
                                onPasswordDraftChange={(value) => setPasswordDrafts((current) => ({
                                    ...current,
                                    [classItem.id]: value,
                                }))}
                                onPasswordVisibilityToggle={() => setVisiblePasswordDrafts((current) => ({
                                    ...current,
                                    [classItem.id]: !current[classItem.id],
                                }))}
                                onPasswordUpdate={(event) => handlePasswordUpdate(event, classItem)}
                                onDelete={() => handleDelete(classItem)}
                            />
                        ))}
                    </div>
                )}
            </section>
        </AdminLayout>
    );
}
