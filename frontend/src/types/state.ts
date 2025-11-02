/**
 * State types for dashboard state management.
 * Following state-management.md specification.
 */

import {
  ResearchFundingData,
  StudentData,
  PublicationData,
  DepartmentKpiData,
} from './domain';

export type LoadingStatus = 'idle' | 'loading' | 'success' | 'error';

export interface DashboardFilters {
  department: string;
  year: string;
  period: string;
  studentStatus: string;
  journalTier: string;
}

export interface FilterOptions {
  departments: string[];
  years: string[];
  periods: string[];
}

export interface DashboardState {
  // Domain State
  researchFundingData: ResearchFundingData | null;
  studentData: StudentData | null;
  publicationData: PublicationData | null;
  departmentKpiData: DepartmentKpiData | null;

  // UI State
  loadingState: {
    researchFunding: LoadingStatus;
    students: LoadingStatus;
    publications: LoadingStatus;
    departmentKpi: LoadingStatus;
    filterOptions: LoadingStatus;
  };

  errorState: {
    researchFunding: Error | null;
    students: Error | null;
    publications: Error | null;
    departmentKpi: Error | null;
    filterOptions: Error | null;
  };

  // Filter State
  filters: DashboardFilters;
  filterOptions: FilterOptions;
}
