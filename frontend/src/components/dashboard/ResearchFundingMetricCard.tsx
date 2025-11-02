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
      <div data-testid="metric-loading" className="skeleton-shimmer h-32 rounded-xl">
      </div>
    );
  }

  if (currentBalance === null) {
    return (
      <div className="bg-white p-6 rounded-xl shadow text-center text-gray-400">
        데이터 없음
      </div>
    );
  }

  const balanceInEokWon = (currentBalance / 100000000).toFixed(1);

  return (
    <div className="bg-gradient-blue p-6 rounded-xl shadow-xl hover-lift">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-medium text-blue-100">현재 연구비 잔액</h3>
        <span className="text-4xl" role="img" aria-label="money">💰</span>
      </div>
      <p className="mt-3 text-5xl font-bold text-white">
        {balanceInEokWon}
      </p>
      <p className="text-xl text-blue-50 mt-1">억원</p>
    </div>
  );
};
