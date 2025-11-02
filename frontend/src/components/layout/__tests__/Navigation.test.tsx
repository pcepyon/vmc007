/**
 * Navigation Component Tests
 * Tests navigation links, active states, and admin mode visibility
 */

import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { Navigation } from '../Navigation';
import * as env from '../../../config/env';
import '@testing-library/jest-dom';

// Mock getAdminMode function
jest.mock('../../../config/env', () => ({
  getAdminMode: jest.fn(),
}));

describe('Navigation Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Basic Rendering', () => {
    it('should render navigation bar with logo', () => {
      (env.getAdminMode as jest.Mock).mockReturnValue(false);

      render(
        <MemoryRouter>
          <Navigation />
        </MemoryRouter>
      );

      expect(screen.getByText('대학교 데이터 대시보드')).toBeInTheDocument();
    });

    it('should always show dashboard link', () => {
      (env.getAdminMode as jest.Mock).mockReturnValue(false);

      render(
        <MemoryRouter>
          <Navigation />
        </MemoryRouter>
      );

      expect(screen.getByText('대시보드')).toBeInTheDocument();
    });
  });

  describe('Admin Mode', () => {
    it('should show upload link when admin mode is enabled', () => {
      (env.getAdminMode as jest.Mock).mockReturnValue(true);

      render(
        <MemoryRouter>
          <Navigation />
        </MemoryRouter>
      );

      expect(screen.getByText('데이터 업로드')).toBeInTheDocument();
    });

    it('should NOT show upload link when admin mode is disabled', () => {
      (env.getAdminMode as jest.Mock).mockReturnValue(false);

      render(
        <MemoryRouter>
          <Navigation />
        </MemoryRouter>
      );

      expect(screen.queryByText('데이터 업로드')).not.toBeInTheDocument();
    });
  });

  describe('Active Link Highlighting', () => {
    it('should highlight dashboard link when on root path', () => {
      (env.getAdminMode as jest.Mock).mockReturnValue(false);

      render(
        <MemoryRouter initialEntries={['/']}>
          <Navigation />
        </MemoryRouter>
      );

      const dashboardLink = screen.getByText('대시보드');
      expect(dashboardLink).toHaveClass('active');
    });

    it('should highlight upload link when on admin upload path', () => {
      (env.getAdminMode as jest.Mock).mockReturnValue(true);

      render(
        <MemoryRouter initialEntries={['/admin/upload']}>
          <Navigation />
        </MemoryRouter>
      );

      const uploadLink = screen.getByText('데이터 업로드');
      expect(uploadLink).toHaveClass('active');
    });

    it('should NOT highlight dashboard link when on admin upload path', () => {
      (env.getAdminMode as jest.Mock).mockReturnValue(true);

      render(
        <MemoryRouter initialEntries={['/admin/upload']}>
          <Navigation />
        </MemoryRouter>
      );

      const dashboardLink = screen.getByText('대시보드');
      expect(dashboardLink).not.toHaveClass('active');
    });
  });

  describe('Navigation Links', () => {
    it('should have correct href for dashboard link', () => {
      (env.getAdminMode as jest.Mock).mockReturnValue(false);

      render(
        <MemoryRouter>
          <Navigation />
        </MemoryRouter>
      );

      const dashboardLink = screen.getByText('대시보드').closest('a');
      expect(dashboardLink).toHaveAttribute('href', '/');
    });

    it('should have correct href for upload link when admin mode is enabled', () => {
      (env.getAdminMode as jest.Mock).mockReturnValue(true);

      render(
        <MemoryRouter>
          <Navigation />
        </MemoryRouter>
      );

      const uploadLink = screen.getByText('데이터 업로드').closest('a');
      expect(uploadLink).toHaveAttribute('href', '/admin/upload');
    });

    it('should have logo link to root path', () => {
      (env.getAdminMode as jest.Mock).mockReturnValue(false);

      render(
        <MemoryRouter>
          <Navigation />
        </MemoryRouter>
      );

      const logoLink = screen.getByText('대학교 데이터 대시보드').closest('a');
      expect(logoLink).toHaveAttribute('href', '/');
    });
  });
});
