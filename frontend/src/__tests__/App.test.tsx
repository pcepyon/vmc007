/**
 * App Component Tests
 * Tests routing logic and navigation integration
 */

import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { App } from '../App';
import '@testing-library/jest-dom';

// Mock child components
jest.mock('../pages/DashboardPage', () => ({
  DashboardPage: () => <div data-testid="dashboard-page">Dashboard Page</div>,
}));

jest.mock('../pages/AdminUploadPage', () => ({
  __esModule: true,
  default: () => <div data-testid="admin-upload-page">Admin Upload Page</div>,
}));

jest.mock('../pages/NotFoundPage', () => ({
  NotFoundPage: () => <div data-testid="not-found-page">404 Not Found</div>,
}));

jest.mock('../components/layout/Navigation', () => ({
  Navigation: () => <nav data-testid="navigation">Navigation</nav>,
}));

describe('App Component', () => {
  describe('Routing', () => {
    it('should render Navigation component on all routes', () => {
      render(
        <MemoryRouter initialEntries={['/']}>
          <App />
        </MemoryRouter>
      );

      expect(screen.getByTestId('navigation')).toBeInTheDocument();
    });

    it('should render DashboardPage on root path "/"', () => {
      render(
        <MemoryRouter initialEntries={['/']}>
          <App />
        </MemoryRouter>
      );

      expect(screen.getByTestId('dashboard-page')).toBeInTheDocument();
    });

    it('should render AdminUploadPage on "/admin/upload" path', () => {
      render(
        <MemoryRouter initialEntries={['/admin/upload']}>
          <App />
        </MemoryRouter>
      );

      expect(screen.getByTestId('admin-upload-page')).toBeInTheDocument();
    });

    it('should render NotFoundPage on invalid path', () => {
      render(
        <MemoryRouter initialEntries={['/invalid-path']}>
          <App />
        </MemoryRouter>
      );

      expect(screen.getByTestId('not-found-page')).toBeInTheDocument();
    });

    it('should render NotFoundPage on "/admin" without "/upload"', () => {
      render(
        <MemoryRouter initialEntries={['/admin']}>
          <App />
        </MemoryRouter>
      );

      expect(screen.getByTestId('not-found-page')).toBeInTheDocument();
    });
  });

  describe('Layout', () => {
    it('should have proper layout structure with min-height', () => {
      const { container } = render(
        <MemoryRouter initialEntries={['/']}>
          <App />
        </MemoryRouter>
      );

      const rootDiv = container.firstChild as HTMLElement;
      expect(rootDiv).toHaveClass('min-h-screen');
      expect(rootDiv).toHaveClass('bg-gray-100');
    });
  });
});
