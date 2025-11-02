/**
 * DashboardPage - Main integration component for all dashboard features.
 * Integrates features 002-006: Research Funding, Students, Publications, KPI, Filtering.
 */

import React, { useState, useEffect } from 'react';
import { ResearchFundingChart } from '../components/dashboard/ResearchFundingChart';
import { ResearchFundingMetricCard } from '../components/dashboard/ResearchFundingMetricCard';
import { StudentChart } from '../components/dashboard/StudentChart';
import { PublicationChart } from '../components/dashboard/PublicationChart';
import { DepartmentKPIChart } from '../components/dashboard/DepartmentKPIChart';
import { FilterPanel } from '../components/dashboard/FilterPanel';
import { DashboardFilters, FilterOptions } from '../types/state';
import {
  ResearchFundingData,
  StudentData,
  PublicationData,
  DepartmentKpiData,
} from '../types/domain';

export const DashboardPage: React.FC = () => {
  // Filter state
  const [filters, setFilters] = useState<DashboardFilters>({
    department: 'all',
    year: 'latest',
    period: '1y',
    studentStatus: 'all',
    journalTier: 'all',
  });

  const [filterOptions] = useState<FilterOptions>({
    departments: ['전체', '컴퓨터공학과', '전자공학과', '기계공학과'],
    years: ['최근 1년', '최근 3년', '2024년', '2023년', '2022년'],
    periods: ['1y', '3y'],
  });

  // Data state (mock data for MVP)
  const [researchFundingData] = useState<ResearchFundingData | null>(null);
  const [studentData] = useState<StudentData | null>(null);
  const [publicationData] = useState<PublicationData | null>(null);
  const [departmentKpiData] = useState<DepartmentKpiData | null>(null);

  const handleFilterChange = (key: keyof DashboardFilters, value: string) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  };

  const handleResetFilters = () => {
    setFilters({
      department: 'all',
      year: 'latest',
      period: '1y',
      studentStatus: 'all',
      journalTier: 'all',
    });
  };

  useEffect(() => {
    // TODO: Fetch dashboard data with filters
    // This will be implemented with actual API calls
  }, [filters]);

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-6">대학교 데이터 대시보드</h1>

      <FilterPanel
        filters={filters}
        filterOptions={filterOptions}
        onFilterChange={handleFilterChange}
        onReset={handleResetFilters}
      />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="lg:col-span-2">
          <ResearchFundingChart data={researchFundingData} loading={false} error={null} />
        </div>

        <div>
          <ResearchFundingMetricCard
            currentBalance={researchFundingData?.current_balance || null}
          />
        </div>

        <div>
          <StudentChart data={studentData} loading={false} error={null} />
        </div>

        <div>
          <PublicationChart data={publicationData} loading={false} error={null} />
        </div>

        <div>
          <DepartmentKPIChart data={departmentKpiData} loading={false} error={null} />
        </div>
      </div>
    </div>
  );
};
