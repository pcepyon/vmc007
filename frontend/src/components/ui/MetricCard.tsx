/**
 * Generic metric card component for displaying key metrics.
 * Following CLAUDE.md: Generic UI components separated from dashboard logic.
 */

import React from 'react';

export interface MetricCardProps {
  title: string;
  value: number | string;
  unit?: string;
  trend?: 'up' | 'down' | 'neutral';
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  unit = '',
  trend = 'neutral'
}) => {
  return (
    <div className="metric-card" data-testid="metric-card">
      <h3 className="metric-title">{title}</h3>
      <div className="metric-value">
        <span data-testid="metric-value">{value}</span>
        {unit && <span className="metric-unit">{unit}</span>}
      </div>
      {trend !== 'neutral' && (
        <div className="metric-trend" data-testid="metric-trend">
          {trend === 'up' ? '↑' : '↓'}
        </div>
      )}
    </div>
  );
};
