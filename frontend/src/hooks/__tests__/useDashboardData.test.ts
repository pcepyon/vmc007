/**
 * Unit tests for useDashboardData hook.
 * Following TDD principles: AAA pattern (Arrange, Act, Assert).
 */

import { renderHook, waitFor } from '@testing-library/react';
import { useDashboardData } from '../useDashboardData';

describe('useDashboardData', () => {
  it('should return loading state initially', () => {
    // Arrange & Act
    const { result } = renderHook(() => useDashboardData());

    // Assert
    expect(result.current.loading).toBe(true);
    expect(result.current.data).toBeNull();
    expect(result.current.error).toBeNull();
  });

  it('should return data after successful fetch', async () => {
    // Arrange & Act
    const { result } = renderHook(() => useDashboardData());

    // Assert
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.data).not.toBeNull();
    expect(result.current.data?.researchFunding).toBe(100000000);
    expect(result.current.data?.studentCount).toBe(1500);
    expect(result.current.data?.publicationCount).toBe(250);
    expect(result.current.error).toBeNull();
  });
});
