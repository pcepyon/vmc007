/**
 * Unit tests for DepartmentKPIChart component.
 * TDD Red Phase.
 */

import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { DepartmentKPIChart } from '../DepartmentKPIChart';
import { DepartmentKpiData } from '../../../types/domain';

describe('DepartmentKPIChart', () => {
  const mockData: DepartmentKpiData = {
    trend: [
      { evaluation_year: 2021, avg_employment_rate: 76.2, total_tech_income: 85 },
      { evaluation_year: 2022, avg_employment_rate: 78.5, total_tech_income: 102 },
      { evaluation_year: 2023, avg_employment_rate: 80.2, total_tech_income: 147 },
    ],
    overall_avg_employment_rate: 78.3,
    overall_total_tech_income: 334,
    total_count: 3,
  };

  it('renders dual-axis line chart with KPI trend', () => {
    render(<DepartmentKPIChart data={mockData} loading={false} error={null} />);
    expect(screen.getByText('학과 KPI 추이')).toBeInTheDocument();
  });

  it('displays loading state', () => {
    render(<DepartmentKPIChart data={null} loading={true} error={null} />);
    expect(screen.getByTestId('loading-skeleton')).toBeInTheDocument();
  });

  it('displays error state', () => {
    const error = new Error('Failed');
    render(<DepartmentKPIChart data={null} loading={false} error={error} />);
    expect(screen.getByText(/Failed/)).toBeInTheDocument();
  });

  it('displays empty state', () => {
    render(<DepartmentKPIChart data={null} loading={false} error={null} />);
    expect(screen.getByText(/데이터가 없습니다/)).toBeInTheDocument();
  });
});
