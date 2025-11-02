/**
 * Domain types for dashboard data structures.
 * Following state-management.md specification.
 */

export interface ResearchFundingData {
  current_balance: number;
  year_over_year_change: number;
  year_over_year_percentage: number;
  trend: ResearchFundingTrendItem[];
  last_updated: string;
}

export interface ResearchFundingTrendItem {
  month: string; // 'YYYY-MM'
  balance: number;
  execution: number;
}

export interface StudentData {
  total_students: number;
  by_department: StudentDepartmentItem[];
  updated_at: string;
}

export interface StudentDepartmentItem {
  department: string;
  학사: number;
  석사: number;
  박사: number;
  total: number;
}

export interface PublicationData {
  total_papers: number;
  avg_impact_factor: number | null;
  papers_with_if: number;
  distribution: PublicationDistributionItem[];
  last_updated: string;
}

export interface PublicationDistributionItem {
  journal_tier: 'SCIE' | 'KCI' | '기타';
  count: number;
  percentage: number;
  avg_if: number | null;
}

export interface DepartmentKpiData {
  trend: DepartmentKpiTrendItem[];
  overall_avg_employment_rate: number | null;
  overall_total_tech_income: number | null;
  total_count: number;
}

export interface DepartmentKpiTrendItem {
  evaluation_year: number;
  avg_employment_rate: number;
  total_tech_income: number;
}
