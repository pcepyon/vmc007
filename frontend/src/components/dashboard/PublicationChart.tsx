/**
 * PublicationChart - displays publication distribution by journal tier.
 * TDD Green Phase.
 */

import React from 'react';
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { PublicationData } from '../../types/domain';

interface PublicationChartProps {
  data: PublicationData | null;
  loading: boolean;
  error: Error | null;
}

const COLORS = {
  SCIE: '#3B82F6',
  KCI: '#10B981',
  기타: '#F59E0B',
};

export const PublicationChart: React.FC<PublicationChartProps> = ({
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

  if (!data || data.distribution.length === 0) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded p-8 text-center text-gray-500">
        <p>데이터가 없습니다</p>
      </div>
    );
  }

  const chartData = data.distribution.map((item) => ({
    name: item.journal_tier,
    value: item.count,
    percentage: item.percentage,
  }));

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h3 className="text-lg font-semibold mb-4">논문 실적</h3>
      <ResponsiveContainer width="100%" height={400}>
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            innerRadius={60}
            outerRadius={120}
            fill="#8884d8"
            dataKey="value"
            label={(entry) => `${entry.name}: ${entry.percentage.toFixed(1)}%`}
          >
            {chartData.map((entry) => (
              <Cell key={`cell-${entry.name}`} fill={COLORS[entry.name as keyof typeof COLORS] || '#999'} />
            ))}
          </Pie>
          <Tooltip />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
};
