/**
 * ResearchFundingChart component - displays monthly research funding trend.
 * Following CLAUDE.md: Recharts-based chart component.
 * TDD Green Phase: Implementing to pass tests.
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
import { ResearchFundingData } from '../../types/domain';

interface ResearchFundingChartProps {
  data: ResearchFundingData | null;
  loading: boolean;
  error: Error | null;
}

export const ResearchFundingChart: React.FC<ResearchFundingChartProps> = ({
  data,
  loading,
  error,
}) => {
  // Loading state
  if (loading) {
    return (
      <div
        data-testid="loading-skeleton"
        className="skeleton-shimmer h-96 rounded-xl"
      >
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded p-4 text-red-700">
        <p className="font-semibold">데이터 로딩 실패</p>
        <p className="text-sm">{error.message}</p>
      </div>
    );
  }

  // Empty state
  if (!data || data.trend.length === 0) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded p-8 text-center text-gray-500">
        <p>데이터가 없습니다</p>
        <p className="text-sm mt-2">연구비 집행 데이터를 업로드하세요</p>
      </div>
    );
  }

  // Transform data for Recharts
  const chartData = data.trend.map((item) => ({
    month: item.month,
    집행금액: item.execution / 100000000, // Convert to 억원
    잔액: item.balance / 100000000,
  }));

  return (
    <div data-testid="research-funding-chart" className="bg-white p-6 rounded-xl shadow-xl hover-scale">
      <h3 className="text-lg font-semibold mb-4 text-gray-900">연구비 집행 추이</h3>

      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" opacity={0.5} />
          <XAxis
            dataKey="month"
            label={{ value: '월', position: 'insideBottom', offset: -5 }}
            tick={{ fontSize: 12 }}
          />
          <YAxis
            label={{ value: '금액 (억원)', angle: -90, position: 'insideLeft' }}
            tick={{ fontSize: 12 }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#fff',
              border: 'none',
              borderRadius: '0.5rem',
              boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)'
            }}
          />
          <Legend />
          <Line
            type="monotone"
            dataKey="집행금액"
            stroke="#3B82F6"
            strokeWidth={3}
            dot={{ r: 5, fill: '#3B82F6' }}
            activeDot={{ r: 7 }}
            name="집행금액 (억원)"
          />
          <Line
            type="monotone"
            dataKey="잔액"
            stroke="#10B981"
            strokeWidth={3}
            dot={{ r: 5, fill: '#10B981' }}
            activeDot={{ r: 7 }}
            name="잔액 (억원)"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};
