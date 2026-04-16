import React from 'react';
import Navbar from './Navbar';

const font = "-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'SF Pro Text', 'Helvetica Neue', Arial, sans-serif";

export default function AdminLayout({ children }) {
    return (
        <div className="min-h-screen bg-gray-50 text-gray-950" style={{ fontFamily: font }}>
            <Navbar />
            <main className="w-full p-4 sm:p-6 lg:p-8">{children}</main>
        </div>
    );
}
