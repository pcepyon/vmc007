/**
 * Unit tests for ResearchFundingMetricCard component.
 * TDD Red Phase: Test-first approach.
 */

import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ResearchFundingMetricCard } from '../ResearchFundingMetricCard';

describe('ResearchFundingMetricCard', () => {
  it('renders successfully with balance data', () => {
    // Arrange
    const currentBalance = 1530000000; // 153억원

    // Act
    const { container } = render(<ResearchFundingMetricCard currentBalance={currentBalance} />);

    // Assert
    expect(container).not.toBeEmptyDOMElement();
    expect(screen.getByText('현재 연구비 잔액')).toBeInTheDocument();
  });

  it('displays loading state', () => {
    // Arrange & Act
    render(<ResearchFundingMetricCard currentBalance={null} loading={true} />);

    // Assert
    expect(screen.getByTestId('metric-loading')).toBeInTheDocument();
  });

  it('displays no data state', () => {
    // Arrange & Act
    render(<ResearchFundingMetricCard currentBalance={null} loading={false} />);

    // Assert
    expect(screen.getByText(/데이터 없음/)).toBeInTheDocument();
  });
});
