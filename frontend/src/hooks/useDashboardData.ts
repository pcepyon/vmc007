/**
 * Custom hook for fetching dashboard data.
 * Following CLAUDE.md: UI library agnostic data handling logic.
 */

import { useState, useEffect } from 'react';

export interface DashboardData {
  researchFunding: number;
  studentCount: number;
  publicationCount: number;
}

/**
 * Fetches dashboard data from the API.
 * @returns Dashboard data state with loading and error states
 */
export const useDashboardData = () => {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        // API call will be implemented later
        // For now, return mock data
        const mockData: DashboardData = {
          researchFunding: 100000000,
          studentCount: 1500,
          publicationCount: 250,
        };
        setData(mockData);
        setError(null);
      } catch (err) {
        setError(err as Error);
        setData(null);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return { data, loading, error };
};
