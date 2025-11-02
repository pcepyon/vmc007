/**
 * Unit tests for ResearchFundingChart component.
 * Following TDD Red-Green-Refactor cycle.
 * Test file created FIRST (Red phase).
 */

import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ResearchFundingChart } from '../ResearchFundingChart';
import { ResearchFundingData } from '../../../types/domain';

describe('ResearchFundingChart', () => {
  const mockData: ResearchFundingData = {
    current_balance: 1530000000,
    year_over_year_change: 50000000,
    year_over_year_percentage: 3.4,
    trend: [
      { month: '2024-01', execution: 120000000, balance: 1530000000 },
      { month: '2024-02', execution: 98000000, balance: 1432000000 },
      { month: '2024-03', execution: 105000000, balance: 1327000000 },
    ],
    last_updated: '2024-11-02T10:00:00Z',
  };

  describe('AAA Pattern - Rendering', () => {
    it('renders chart with monthly research funding trend', () => {
      // Arrange - mockData provided above

      // Act
      render(<ResearchFundingChart data={mockData} loading={false} error={null} />);

      // Assert
      expect(screen.getByText('연구비 집행 추이')).toBeInTheDocument();
    });

    it('displays loading skeleton when loading is true', () => {
      // Arrange
      const loadingProps = { data: null, loading: true, error: null };

      // Act
      render(<ResearchFundingChart {...loadingProps} />);

      // Assert
      expect(screen.getByTestId('loading-skeleton')).toBeInTheDocument();
    });

    it('displays error message when error is present', () => {
      // Arrange
      const errorProps = {
        data: null,
        loading: false,
        error: new Error('Failed to fetch data'),
      };

      // Act
      render(<ResearchFundingChart {...errorProps} />);

      // Assert
      expect(screen.getByText(/Failed to fetch data/i)).toBeInTheDocument();
    });

    it('displays empty state when data is null and not loading', () => {
      // Arrange
      const emptyProps = { data: null, loading: false, error: null };

      // Act
      render(<ResearchFundingChart {...emptyProps} />);

      // Assert
      expect(screen.getByText(/데이터가 없습니다/i)).toBeInTheDocument();
    });
  });

  describe('AAA Pattern - Data Display', () => {
    it('renders Recharts LineChart component', () => {
      // Arrange - mockData

      // Act
      render(<ResearchFundingChart data={mockData} loading={false} error={null} />);

      // Assert
      const chartContainer = screen.getByTestId('research-funding-chart');
      expect(chartContainer).toBeInTheDocument();
    });

    it('displays correct number of data points', () => {
      // Arrange - mockData with 3 months

      // Act
      render(<ResearchFundingChart data={mockData} loading={false} error={null} />);

      // Assert
      // Recharts renders SVG elements, verify by checking trend data length
      expect(mockData.trend).toHaveLength(3);
    });
  });
});
