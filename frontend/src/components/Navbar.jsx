import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { adminAuth } from '../utils/auth';

const navItems = [
    { label: 'Dashboard', to: '/admin/dashboard' },
    { label: 'Classes', to: '/admin/classes' },
];

function DesktopNavLink({ item }) {
    return (
        <NavLink
            to={item.to}
            className={({ isActive }) => (
                `inline-flex min-h-11 items-center rounded-xl px-3 text-sm font-semibold transition ${
                    isActive ? 'bg-gray-100 text-gray-950' : 'text-gray-600 hover:bg-gray-50 hover:text-gray-950'
                }`
            )}
        >
            {item.label}
        </NavLink>
    );
}

function DrawerNavLink({ item, onClick }) {
    return (
        <NavLink
            to={item.to}
            onClick={onClick}
            className={({ isActive }) => (
                `flex min-h-11 items-center rounded-xl px-4 text-sm font-semibold transition ${
                    isActive ? 'bg-gray-100 text-gray-950' : 'text-gray-700 hover:bg-gray-50 hover:text-gray-950'
                }`
            )}
        >
            {item.label}
        </NavLink>
    );
}

export default function Navbar() {
    const [isDrawerOpen, setIsDrawerOpen] = useState(false);

    const closeDrawer = () => setIsDrawerOpen(false);

    return (
        <>
            <header className="sticky top-0 z-30 border-b border-gray-200 bg-white">
                <div className="hidden min-h-16 items-center justify-between gap-6 px-8 md:flex">
                    <div className="min-w-0">
                        <h1 className="whitespace-nowrap text-xl font-semibold tracking-normal text-gray-950">
                            AttendNet
                        </h1>
                        <p className="truncate text-xs font-medium text-gray-500">{adminAuth.getUsername()}</p>
                    </div>

                    <nav className="flex items-center justify-center gap-2">
                        {navItems.map((item) => (
                            <DesktopNavLink key={item.to} item={item} />
                        ))}
                    </nav>

                    <button
                        type="button"
                        onClick={adminAuth.logout}
                        className="min-h-11 rounded-xl border border-gray-200 bg-white px-4 text-sm font-bold text-gray-700 transition hover:bg-gray-100 hover:text-gray-950 focus:outline-none focus:ring-2 focus:ring-gray-950 focus:ring-offset-2"
                    >
                        Logout
                    </button>
                </div>

                <div className="grid min-h-16 grid-cols-[44px_1fr_44px] items-center gap-3 px-4 md:hidden">
                    <button
                        type="button"
                        onClick={() => setIsDrawerOpen(true)}
                        className="inline-flex min-h-11 min-w-11 items-center justify-center rounded-xl text-gray-800 transition hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-gray-950"
                        aria-label="Open navigation menu"
                    >
                        <span className="text-2xl leading-none">☰</span>
                    </button>

                    <h1 className="truncate whitespace-nowrap text-center text-lg font-semibold tracking-normal text-gray-950">
                        AttendNet
                    </h1>

                    <button
                        type="button"
                        onClick={adminAuth.logout}
                        className="inline-flex min-h-11 min-w-11 items-center justify-center rounded-xl text-gray-700 transition hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-gray-950"
                        aria-label="Logout"
                    >
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                            <path d="M10 6H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                            <path d="M14 16l4-4-4-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                            <path d="M18 12H9" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                        </svg>
                    </button>
                </div>
            </header>

            {isDrawerOpen && (
                <div className="fixed inset-0 z-40 md:hidden">
                    <button
                        type="button"
                        className="absolute inset-0 bg-black/40"
                        onClick={closeDrawer}
                        aria-label="Close navigation menu"
                    />

                    <aside className="absolute left-0 top-0 flex h-full w-80 max-w-[85vw] flex-col border-r border-gray-200 bg-white shadow-xl transition">
                        <div className="flex min-h-16 items-center justify-between gap-4 border-b border-gray-200 px-4">
                            <div className="min-w-0">
                                <h2 className="truncate whitespace-nowrap text-lg font-semibold text-gray-950">
                                    AttendNet
                                </h2>
                                <p className="truncate text-xs font-medium text-gray-500">{adminAuth.getUsername()}</p>
                            </div>

                            <button
                                type="button"
                                onClick={closeDrawer}
                                className="inline-flex min-h-11 min-w-11 items-center justify-center rounded-xl text-2xl text-gray-700 transition hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-gray-950"
                                aria-label="Close navigation menu"
                            >
                                ×
                            </button>
                        </div>

                        <nav className="flex flex-1 flex-col gap-2 p-4">
                            {navItems.map((item) => (
                                <DrawerNavLink key={item.to} item={item} onClick={closeDrawer} />
                            ))}
                        </nav>

                        <div className="border-t border-gray-200 p-4">
                            <button
                                type="button"
                                onClick={adminAuth.logout}
                                className="flex min-h-11 w-full items-center justify-center rounded-xl border border-gray-300 bg-white px-4 text-sm font-bold text-gray-950 transition hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-gray-950 focus:ring-offset-2"
                            >
                                Logout
                            </button>
                        </div>
                    </aside>
                </div>
            )}
        </>
    );
}
