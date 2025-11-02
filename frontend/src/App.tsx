/**
 * App Component
 * Main application component with routing configuration
 */

import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { Navigation } from './components/layout/Navigation';
import { DashboardPage } from './pages/DashboardPage';
import AdminUploadPage from './pages/AdminUploadPage';
import { NotFoundPage } from './pages/NotFoundPage';

export const App: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-100">
      <Navigation />
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/admin/upload" element={<AdminUploadPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </div>
  );
};
