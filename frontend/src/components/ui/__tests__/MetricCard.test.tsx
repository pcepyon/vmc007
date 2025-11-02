/**
 * Unit tests for MetricCard component.
 * Following test-plan.md: Jest + RTL for user behavior-based component testing.
 */

import { render, screen } from '@testing-library/react';
import { MetricCard } from '../MetricCard';

describe('MetricCard', () => {
  it('should render title and value', () => {
    // Arrange & Act
    render(<MetricCard title="Total Students" value={1500} />);

    // Assert
    expect(screen.getByText('Total Students')).toBeInTheDocument();
    expect(screen.getByTestId('metric-value')).toHaveTextContent('1500');
  });

  it('should render with unit when provided', () => {
    // Arrange & Act
    render(
      <MetricCard
        title="Research Funding"
        value={100000000}
        unit="원"
      />
    );

    // Assert
    expect(screen.getByText('원')).toBeInTheDocument();
  });

  it('should render trend indicator when trend is up', () => {
    // Arrange & Act
    render(
      <MetricCard
        title="Publications"
        value={250}
        trend="up"
      />
    );

    // Assert
    expect(screen.getByTestId('metric-trend')).toHaveTextContent('↑');
  });

  it('should render trend indicator when trend is down', () => {
    // Arrange & Act
    render(
      <MetricCard
        title="Publications"
        value={200}
        trend="down"
      />
    );

    // Assert
    expect(screen.getByTestId('metric-trend')).toHaveTextContent('↓');
  });

  it('should not render trend indicator when trend is neutral', () => {
    // Arrange & Act
    render(
      <MetricCard
        title="Publications"
        value={250}
        trend="neutral"
      />
    );

    // Assert
    expect(screen.queryByTestId('metric-trend')).not.toBeInTheDocument();
  });
});
