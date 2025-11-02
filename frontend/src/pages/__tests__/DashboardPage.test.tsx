/**
 * Integration tests for DashboardPage.
 */

import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { DashboardPage } from '../DashboardPage';

describe('DashboardPage', () => {
  it('renders dashboard title', () => {
    render(<DashboardPage />);
    expect(screen.getByText('대학교 데이터 대시보드')).toBeInTheDocument();
  });

  it('renders all chart sections with empty states', () => {
    render(<DashboardPage />);
    // Charts render with empty state when no data
    const emptyMessages = screen.getAllByText(/데이터가 없습니다/);
    expect(emptyMessages.length).toBeGreaterThan(0);
  });

  it('renders filter panel', () => {
    render(<DashboardPage />);
    expect(screen.getByLabelText(/학과/)).toBeInTheDocument();
  });
});
