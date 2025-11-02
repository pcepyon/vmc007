/**
 * FilterPanel - dashboard filtering UI component.
 * TDD Green Phase.
 */

import React from 'react';
import { DashboardFilters, FilterOptions } from '../../types/state';

interface FilterPanelProps {
  filters: DashboardFilters;
  filterOptions: FilterOptions;
  onFilterChange: (key: keyof DashboardFilters, value: string) => void;
  onReset: () => void;
  loading?: boolean;
}

export const FilterPanel: React.FC<FilterPanelProps> = ({
  filters,
  filterOptions,
  onFilterChange,
  onReset,
  loading = false,
}) => {
  if (loading) {
    return (
      <div className="bg-white p-4 rounded-lg shadow">
        <p className="text-gray-500">필터 로딩 중...</p>
      </div>
    );
  }

  return (
    <div className="bg-white p-6 rounded-xl shadow-xl mb-6">
      <h3 className="text-lg font-semibold mb-4 text-gray-900">필터</h3>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label htmlFor="department-filter" className="block text-sm font-medium text-gray-700 mb-1">
            학과
          </label>
          <select
            id="department-filter"
            value={filters.department}
            onChange={(e) => onFilterChange('department', e.target.value)}
            className="w-full border border-gray-300 rounded-md px-3 py-2 hover-lift"
            style={{transition: 'all 0.2s'}}
          >
            {filterOptions.departments.map((dept) => (
              <option key={dept} value={dept}>
                {dept}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="year-filter" className="block text-sm font-medium text-gray-700 mb-1">
            기간
          </label>
          <select
            id="year-filter"
            value={filters.year}
            onChange={(e) => onFilterChange('year', e.target.value)}
            className="w-full border border-gray-300 rounded-md px-3 py-2 hover-lift"
            style={{transition: 'all 0.2s'}}
          >
            {filterOptions.years.map((year) => (
              <option key={year} value={year}>
                {year}
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-end">
          <button
            onClick={onReset}
            className="w-full bg-gradient-blue text-white font-medium py-2 px-4 rounded-md hover-lift"
          >
            필터 초기화
          </button>
        </div>
      </div>
    </div>
  );
};
