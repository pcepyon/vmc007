/**
 * StudentChart - displays student enrollment by department.
 * TDD Green Phase.
 */

import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { StudentData } from '../../types/domain';

interface StudentChartProps {
  data: StudentData | null;
  loading: boolean;
  error: Error | null;
}

export const StudentChart: React.FC<StudentChartProps> = ({ data, loading, error }) => {
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

  if (!data || data.by_department.length === 0) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded p-8 text-center text-gray-500">
        <p>데이터가 없습니다</p>
      </div>
    );
  }

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h3 className="text-lg font-semibold mb-4">학생 현황</h3>
      <ResponsiveContainer width="100%" height={400}>
        <BarChart data={data.by_department}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="department" />
          <YAxis label={{ value: '학생 수', angle: -90, position: 'insideLeft' }} />
          <Tooltip />
          <Legend />
          <Bar dataKey="학사" stackId="a" fill="#3B82F6" name="학사" />
          <Bar dataKey="석사" stackId="a" fill="#10B981" name="석사" />
          <Bar dataKey="박사" stackId="a" fill="#F59E0B" name="박사" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};
