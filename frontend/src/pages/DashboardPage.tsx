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
import {
  getResearchFundingData,
  getStudentData,
  getPublicationData,
  getDepartmentKPIData,
  getFilterOptions,
} from '../api/dataApiClient';

export const DashboardPage: React.FC = () => {
  // Filter state
  const [filters, setFilters] = useState<DashboardFilters>({
    department: 'all',
    year: 'latest',
    period: 'latest',
    studentStatus: 'all',
    journalTier: 'all',
  });

  const [filterOptions] = useState<FilterOptions>({
    departments: ['전체', '컴퓨터공학과', '전자공학과', '기계공학과'],
    years: ['최근 1년', '최근 3년', '2024년', '2023년', '2022년'],
    periods: ['latest', '1year', '3years'],
  });

  // Data state
  const [researchFundingData, setResearchFundingData] = useState<ResearchFundingData | null>(null);
  const [studentData, setStudentData] = useState<StudentData | null>(null);
  const [publicationData, setPublicationData] = useState<PublicationData | null>(null);
  const [departmentKpiData, setDepartmentKpiData] = useState<DepartmentKpiData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<Error | null>(null);

  const handleFilterChange = (key: keyof DashboardFilters, value: string) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  };

  const handleResetFilters = () => {
    setFilters({
      department: 'all',
      year: 'latest',
      period: 'latest',
      studentStatus: 'all',
      journalTier: 'all',
    });
  };

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Fetch all dashboard data in parallel
        const [researchFunding, students, publications, kpi] = await Promise.all([
          getResearchFundingData({
            department: filters.department,
            year: filters.year,
            period: filters.period,
          }),
          getStudentData({
            department: filters.department,
            status: filters.studentStatus,
          }),
          getPublicationData({
            department: filters.department,
            tier: filters.journalTier,
          }),
          getDepartmentKPIData({
            department: filters.department,
            year: filters.year,
          }),
        ]);

        // Update state with fetched data
        setResearchFundingData(researchFunding?.data || null);
        setStudentData(students || null);
        setPublicationData(publications || null);
        setDepartmentKpiData(kpi || null);
      } catch (err) {
        console.error('Failed to fetch dashboard data:', err);
        setError(err as Error);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
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
          <ResearchFundingChart data={researchFundingData} loading={loading} error={error} />
        </div>

        <div>
          <ResearchFundingMetricCard
            currentBalance={researchFundingData?.current_balance || null}
          />
        </div>

        <div>
          <StudentChart data={studentData} loading={loading} error={error} />
        </div>

        <div>
          <PublicationChart data={publicationData} loading={loading} error={error} />
        </div>

        <div>
          <DepartmentKPIChart data={departmentKpiData} loading={loading} error={error} />
        </div>
      </div>
    </div>
  );
};
