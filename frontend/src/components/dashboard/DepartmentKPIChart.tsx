/**
 * DepartmentKPIChart - displays dual-axis line chart for KPI trends.
 * TDD Green Phase.
 */

import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { DepartmentKpiData } from '../../types/domain';

interface DepartmentKPIChartProps {
  data: DepartmentKpiData | null;
  loading: boolean;
  error: Error | null;
}

export const DepartmentKPIChart: React.FC<DepartmentKPIChartProps> = ({
  data,
  loading,
  error,
}) => {
  if (loading) {
    return (
      <div data-testid="loading-skeleton" className="animate-pulse bg-gray-200 h-64 rounded">
        Loading...
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded p-4 text-red-700">
        <p className="font-semibold">데이터 로딩 실패</p>
        <p className="text-sm">{error.message}</p>
      </div>
    );
  }

  if (!data || data.trend.length === 0) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded p-8 text-center text-gray-500">
        <p>데이터가 없습니다</p>
      </div>
    );
  }

  const chartData = data.trend.map((item) => ({
    year: item.evaluation_year,
    취업률: item.avg_employment_rate,
    기술이전: item.total_tech_income,
  }));

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h3 className="text-lg font-semibold mb-4">학과 KPI 추이</h3>
      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="year" label={{ value: '년도', position: 'insideBottom', offset: -5 }} />
          <YAxis
            yAxisId="left"
            label={{ value: '취업률 (%)', angle: -90, position: 'insideLeft' }}
            domain={[0, 100]}
          />
          <YAxis
            yAxisId="right"
            orientation="right"
            label={{ value: '기술이전 (억원)', angle: 90, position: 'insideRight' }}
          />
          <Tooltip />
          <Legend />
          <Line
            yAxisId="left"
            type="monotone"
            dataKey="취업률"
            stroke="#3B82F6"
            strokeWidth={2}
            dot={{ r: 4 }}
            name="평균 취업률 (%)"
          />
          <Line
            yAxisId="right"
            type="monotone"
            dataKey="기술이전"
            stroke="#F59E0B"
            strokeWidth={2}
            strokeDasharray="5 5"
            dot={{ r: 4 }}
            name="기술이전 수입 (억원)"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};
