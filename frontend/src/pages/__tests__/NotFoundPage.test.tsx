/**
 * NotFoundPage Component Tests
 * Tests 404 error page rendering and link
 */

import { render, screen } from '@testing-library/react';
import { NotFoundPage } from '../NotFoundPage';
import '@testing-library/jest-dom';

describe('NotFoundPage Component', () => {
  describe('Rendering', () => {
    it('should render 404 heading', () => {
      render(<NotFoundPage />);

      expect(screen.getByText('404')).toBeInTheDocument();
    });

    it('should render error message', () => {
      render(<NotFoundPage />);

      expect(screen.getByText('페이지를 찾을 수 없습니다')).toBeInTheDocument();
    });

    it('should render description text', () => {
      render(<NotFoundPage />);

      expect(
        screen.getByText('요청하신 페이지가 존재하지 않거나 이동되었습니다.')
      ).toBeInTheDocument();
    });

    it('should render link to dashboard', () => {
      render(<NotFoundPage />);

      const link = screen.getByText('대시보드로 돌아가기');
      expect(link).toBeInTheDocument();
      expect(link.closest('a')).toHaveAttribute('href', '/');
    });
  });

  describe('Layout', () => {
    it('should have centered layout with proper styling', () => {
      const { container } = render(<NotFoundPage />);

      const rootDiv = container.firstChild as HTMLElement;
      expect(rootDiv).toHaveClass('min-h-screen');
      expect(rootDiv).toHaveClass('bg-gray-100');
    });
  });
});
