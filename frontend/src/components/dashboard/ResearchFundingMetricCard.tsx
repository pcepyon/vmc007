/**
 * ResearchFundingMetricCard - displays current research funding balance.
 * TDD Green Phase: Implementation.
 */

import React from 'react';

interface ResearchFundingMetricCardProps {
  currentBalance: number | null;
  loading?: boolean;
}

export const ResearchFundingMetricCard: React.FC<ResearchFundingMetricCardProps> = ({
  currentBalance,
  loading = false,
}) => {
  if (loading) {
    return (
      <div data-testid="metric-loading" className="animate-pulse bg-gray-200 h-24 rounded">
        Loading...
      </div>
    );
  }

  if (currentBalance === null) {
    return (
      <div className="bg-white p-6 rounded-lg shadow text-center text-gray-400">
        데이터 없음
      </div>
    );
  }

  const balanceInEokWon = (currentBalance / 100000000).toFixed(1);

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h3 className="text-sm font-medium text-gray-500">현재 연구비 잔액</h3>
      <p className="mt-2 text-3xl font-semibold text-gray-900">
        {balanceInEokWon} <span className="text-lg text-gray-600">억원</span>
      </p>
    </div>
  );
};
