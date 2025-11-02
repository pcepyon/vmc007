/**
 * Unit tests for StudentChart component.
 * TDD Red Phase.
 */

import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { StudentChart } from '../StudentChart';
import { StudentData } from '../../../types/domain';

describe('StudentChart', () => {
  const mockData: StudentData = {
    total_students: 1234,
    by_department: [
      { department: '컴퓨터공학과', 학사: 120, 석사: 35, 박사: 12, total: 167 },
      { department: '전자공학과', 학사: 150, 석사: 40, 박사: 10, total: 200 },
    ],
    updated_at: '2024-11-02T10:00:00Z',
  };

  it('renders stacked bar chart with department data', () => {
    render(<StudentChart data={mockData} loading={false} error={null} />);
    expect(screen.getByText('학생 현황')).toBeInTheDocument();
  });

  it('displays loading state', () => {
    render(<StudentChart data={null} loading={true} error={null} />);
    expect(screen.getByTestId('loading-skeleton')).toBeInTheDocument();
  });

  it('displays error state', () => {
    const error = new Error('Failed to fetch');
    render(<StudentChart data={null} loading={false} error={error} />);
    expect(screen.getByText(/Failed to fetch/)).toBeInTheDocument();
  });

  it('displays empty state', () => {
    render(<StudentChart data={null} loading={false} error={null} />);
    expect(screen.getByText(/데이터가 없습니다/)).toBeInTheDocument();
  });
});
