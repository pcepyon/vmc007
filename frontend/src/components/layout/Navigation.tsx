/**
 * Navigation Component
 * Top navigation bar with links to dashboard and admin upload
 */

import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { getAdminMode } from '../../config/env';

export const Navigation: React.FC = () => {
  const location = useLocation();
  const isAdminMode = getAdminMode();

  const isActive = (path: string): boolean => {
    return location.pathname === path;
  };

  return (
    <nav
      style={{
        backgroundColor: '#ffffff',
        borderBottom: '1px solid #e5e7eb',
        padding: '1rem 2rem',
        marginBottom: '2rem',
      }}
    >
      <div className="container" style={{ display: 'flex', alignItems: 'center', gap: '2rem' }}>
        <div style={{ flex: 1 }}>
          <Link
            to="/"
            style={{
              fontSize: '1.25rem',
              fontWeight: '700',
              color: '#1f2937',
              textDecoration: 'none',
            }}
          >
            대학교 데이터 대시보드
          </Link>
        </div>

        <div style={{ display: 'flex', gap: '1rem' }}>
          <Link
            to="/"
            className={`nav-link ${isActive('/') ? 'active' : ''}`}
            style={{
              textDecoration: 'none',
            }}
          >
            대시보드
          </Link>

          {isAdminMode && (
            <Link
              to="/admin/upload"
              className={`nav-link ${isActive('/admin/upload') ? 'active' : ''}`}
              style={{
                textDecoration: 'none',
              }}
            >
              데이터 업로드
            </Link>
          )}
        </div>
      </div>
    </nav>
  );
};
