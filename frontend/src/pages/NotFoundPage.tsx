/**
 * NotFoundPage Component
 * Displays a 404 error page for invalid routes
 */

import React from 'react';

export const NotFoundPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center p-8">
      <div className="card text-center" style={{ maxWidth: '500px' }}>
        <h1 style={{ fontSize: '4rem', color: '#3b82f6', marginBottom: '1rem' }}>404</h1>
        <h2>페이지를 찾을 수 없습니다</h2>
        <p style={{ color: '#6b7280', marginTop: '1rem', marginBottom: '2rem' }}>
          요청하신 페이지가 존재하지 않거나 이동되었습니다.
        </p>
        <a
          href="/"
          className="btn-primary"
          style={{
            display: 'inline-block',
            textDecoration: 'none',
            padding: '0.75rem 1.5rem',
          }}
        >
          대시보드로 돌아가기
        </a>
      </div>
    </div>
  );
};
