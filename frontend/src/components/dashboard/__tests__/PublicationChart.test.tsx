/**
 * Unit tests for PublicationChart component.
 * TDD Red Phase.
 */

import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { PublicationChart } from '../PublicationChart';
import { PublicationData } from '../../../types/domain';

describe('PublicationChart', () => {
  const mockData: PublicationData = {
    total_papers: 156,
    avg_impact_factor: 2.3,
    papers_with_if: 89,
    distribution: [
      { journal_tier: 'SCIE', count: 89, percentage: 57.1, avg_if: 3.2 },
      { journal_tier: 'KCI', count: 67, percentage: 42.9, avg_if: null },
    ],
    last_updated: '2024-11-02T10:00:00Z',
  };

  it('renders pie chart with journal tier distribution', () => {
    render(<PublicationChart data={mockData} loading={false} error={null} />);
    expect(screen.getByText('논문 실적')).toBeInTheDocument();
  });

  it('displays loading state', () => {
    render(<PublicationChart data={null} loading={true} error={null} />);
    expect(screen.getByTestId('loading-skeleton')).toBeInTheDocument();
  });

  it('displays error state', () => {
    const error = new Error('Failed');
    render(<PublicationChart data={null} loading={false} error={error} />);
    expect(screen.getByText(/Failed/)).toBeInTheDocument();
  });

  it('displays empty state', () => {
    render(<PublicationChart data={null} loading={false} error={null} />);
    expect(screen.getByText(/데이터가 없습니다/)).toBeInTheDocument();
  });
});
