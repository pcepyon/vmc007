/**
 * Unit tests for FilterPanel component.
 * TDD Red Phase.
 */

import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { FilterPanel } from '../FilterPanel';
import { DashboardFilters, FilterOptions } from '../../../types/state';

describe('FilterPanel', () => {
  const mockFilters: DashboardFilters = {
    department: 'all',
    year: 'latest',
    period: '1y',
    studentStatus: 'all',
    journalTier: 'all',
  };

  const mockFilterOptions: FilterOptions = {
    departments: ['전체', '컴퓨터공학과', '전자공학과'],
    years: ['최근 1년', '2024년', '2023년'],
    periods: ['1y', '3y'],
  };

  const mockOnFilterChange = jest.fn();
  const mockOnReset = jest.fn();

  it('renders filter dropdowns', () => {
    render(
      <FilterPanel
        filters={mockFilters}
        filterOptions={mockFilterOptions}
        onFilterChange={mockOnFilterChange}
        onReset={mockOnReset}
      />
    );

    expect(screen.getByLabelText(/학과/)).toBeInTheDocument();
  });

  it('displays loading state when filter options are loading', () => {
    render(
      <FilterPanel
        filters={mockFilters}
        filterOptions={{ departments: [], years: [], periods: [] }}
        onFilterChange={mockOnFilterChange}
        onReset={mockOnReset}
        loading={true}
      />
    );

    expect(screen.getByText(/필터 로딩 중/)).toBeInTheDocument();
  });
});
