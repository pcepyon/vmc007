/**
 * useUploadStatus Hook Tests
 * Testing upload status polling logic
 */

import { renderHook, waitFor } from '@testing-library/react';
import { act } from 'react-dom/test-utils';
import useUploadStatus from '../useUploadStatus';
import * as dataApiClient from '../../api/dataApiClient';

// Mock the API client
jest.mock('../../api/dataApiClient');

describe('useUploadStatus', () => {
  const mockGetUploadStatus = dataApiClient.getUploadStatus as jest.MockedFunction<
    typeof dataApiClient.getUploadStatus
  >;

  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  describe('Initial State', () => {
    test('returns null status initially', () => {
      const { result } = renderHook(() => useUploadStatus(null));

      expect(result.current.status).toBeNull();
      expect(result.current.isPolling).toBe(false);
      expect(result.current.error).toBeNull();
    });

    test('does not poll when jobId is null', () => {
      renderHook(() => useUploadStatus(null));

      act(() => {
        jest.advanceTimersByTime(3000);
      });

      expect(mockGetUploadStatus).not.toHaveBeenCalled();
    });
  });

  describe('Status Polling', () => {
    test('polls status every 3 seconds when jobId is provided', async () => {
      mockGetUploadStatus.mockResolvedValue({
        job_id: 'test-job-id',
        status: 'processing',
        progress: 50,
        files: [],
      });

      renderHook(() => useUploadStatus('test-job-id'));

      // Initial call (immediate)
      await waitFor(() => {
        expect(mockGetUploadStatus).toHaveBeenCalledTimes(1);
      });

      // After 3 seconds
      act(() => {
        jest.advanceTimersByTime(3000);
      });

      await waitFor(() => {
        expect(mockGetUploadStatus).toHaveBeenCalledTimes(2);
      });

      // After another 3 seconds
      act(() => {
        jest.advanceTimersByTime(3000);
      });

      await waitFor(() => {
        expect(mockGetUploadStatus).toHaveBeenCalledTimes(3);
      });
    });

    test('calls API with correct jobId', async () => {
      mockGetUploadStatus.mockResolvedValue({
        job_id: 'test-job-id',
        status: 'processing',
        progress: 50,
        files: [],
      });

      renderHook(() => useUploadStatus('test-job-id'));

      await waitFor(() => {
        expect(mockGetUploadStatus).toHaveBeenCalledWith('test-job-id');
      });
    });

    test('updates status state when API returns data', async () => {
      const mockStatus = {
        job_id: 'test-job-id',
        status: 'processing' as const,
        progress: 75,
        files: [
          {
            file_type: 'research_funding',
            status: 'completed' as const,
            rows_processed: 100,
            rows_inserted: 95,
          },
        ],
      };

      mockGetUploadStatus.mockResolvedValue(mockStatus);

      const { result } = renderHook(() => useUploadStatus('test-job-id'));

      await waitFor(() => {
        expect(result.current.status).toEqual(mockStatus);
      });
    });

    test('sets isPolling to true while polling', async () => {
      mockGetUploadStatus.mockResolvedValue({
        job_id: 'test-job-id',
        status: 'processing',
        progress: 50,
        files: [],
      });

      const { result } = renderHook(() => useUploadStatus('test-job-id'));

      await waitFor(() => {
        expect(result.current.isPolling).toBe(true);
      });
    });
  });

  describe('Polling Termination', () => {
    test('stops polling when status is "completed"', async () => {
      mockGetUploadStatus
        .mockResolvedValueOnce({
          job_id: 'test-job-id',
          status: 'processing',
          progress: 50,
          files: [],
        })
        .mockResolvedValueOnce({
          job_id: 'test-job-id',
          status: 'completed',
          progress: 100,
          files: [],
          completed_at: '2025-11-02T10:00:00Z',
        });

      renderHook(() => useUploadStatus('test-job-id'));

      // First call
      await waitFor(() => {
        expect(mockGetUploadStatus).toHaveBeenCalledTimes(1);
      });

      // Second call after 3 seconds
      act(() => {
        jest.advanceTimersByTime(3000);
      });

      await waitFor(() => {
        expect(mockGetUploadStatus).toHaveBeenCalledTimes(2);
      });

      // Should not call again after completion
      act(() => {
        jest.advanceTimersByTime(3000);
      });

      await waitFor(() => {
        expect(mockGetUploadStatus).toHaveBeenCalledTimes(2); // Still 2
      });
    });

    test('stops polling when status is "failed"', async () => {
      mockGetUploadStatus
        .mockResolvedValueOnce({
          job_id: 'test-job-id',
          status: 'processing',
          progress: 25,
          files: [],
        })
        .mockResolvedValueOnce({
          job_id: 'test-job-id',
          status: 'failed',
          progress: 25,
          files: [],
          failed_at: '2025-11-02T10:00:00Z',
        });

      renderHook(() => useUploadStatus('test-job-id'));

      // First call
      await waitFor(() => {
        expect(mockGetUploadStatus).toHaveBeenCalledTimes(1);
      });

      // Second call
      act(() => {
        jest.advanceTimersByTime(3000);
      });

      await waitFor(() => {
        expect(mockGetUploadStatus).toHaveBeenCalledTimes(2);
      });

      // Should not call again
      act(() => {
        jest.advanceTimersByTime(3000);
      });

      await waitFor(() => {
        expect(mockGetUploadStatus).toHaveBeenCalledTimes(2);
      });
    });

    test('stops polling when status is "partial_success"', async () => {
      mockGetUploadStatus.mockResolvedValue({
        job_id: 'test-job-id',
        status: 'partial_success',
        progress: 100,
        files: [],
      });

      renderHook(() => useUploadStatus('test-job-id'));

      await waitFor(() => {
        expect(mockGetUploadStatus).toHaveBeenCalledTimes(1);
      });

      // Should not poll again
      act(() => {
        jest.advanceTimersByTime(3000);
      });

      await waitFor(() => {
        expect(mockGetUploadStatus).toHaveBeenCalledTimes(1);
      });
    });

    test('sets isPolling to false when polling stops', async () => {
      mockGetUploadStatus.mockResolvedValue({
        job_id: 'test-job-id',
        status: 'completed',
        progress: 100,
        files: [],
        completed_at: '2025-11-02T10:00:00Z',
      });

      const { result } = renderHook(() => useUploadStatus('test-job-id'));

      await waitFor(() => {
        expect(result.current.isPolling).toBe(false);
      });
    });
  });

  describe('Error Handling', () => {
    test('handles API errors gracefully', async () => {
      mockGetUploadStatus.mockRejectedValue(new Error('Network error'));

      const { result } = renderHook(() => useUploadStatus('test-job-id'));

      await waitFor(() => {
        expect(result.current.error).toBe('Network error');
      });
    });

    test('continues polling after recoverable error', async () => {
      mockGetUploadStatus
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce({
          job_id: 'test-job-id',
          status: 'processing',
          progress: 50,
          files: [],
        });

      renderHook(() => useUploadStatus('test-job-id'));

      // First call fails
      await waitFor(() => {
        expect(mockGetUploadStatus).toHaveBeenCalledTimes(1);
      });

      // Second call succeeds
      act(() => {
        jest.advanceTimersByTime(3000);
      });

      await waitFor(() => {
        expect(mockGetUploadStatus).toHaveBeenCalledTimes(2);
      });
    });

    test('stops polling after 3 consecutive errors', async () => {
      mockGetUploadStatus.mockRejectedValue(new Error('Network error'));

      renderHook(() => useUploadStatus('test-job-id'));

      // First error
      await waitFor(() => {
        expect(mockGetUploadStatus).toHaveBeenCalledTimes(1);
      });

      // Second error
      act(() => {
        jest.advanceTimersByTime(3000);
      });
      await waitFor(() => {
        expect(mockGetUploadStatus).toHaveBeenCalledTimes(2);
      });

      // Third error
      act(() => {
        jest.advanceTimersByTime(3000);
      });
      await waitFor(() => {
        expect(mockGetUploadStatus).toHaveBeenCalledTimes(3);
      });

      // Should stop polling
      act(() => {
        jest.advanceTimersByTime(3000);
      });
      await waitFor(() => {
        expect(mockGetUploadStatus).toHaveBeenCalledTimes(3); // Still 3
      });
    });

    test('handles 404 error (job not found)', async () => {
      const error: any = new Error('Not found');
      error.response = { status: 404 };
      mockGetUploadStatus.mockRejectedValue(error);

      const { result } = renderHook(() => useUploadStatus('test-job-id'));

      await waitFor(() => {
        expect(result.current.error).toContain('작업 정보를 찾을 수 없습니다');
      });
    });
  });

  describe('Cleanup', () => {
    test('clears interval on unmount', async () => {
      mockGetUploadStatus.mockResolvedValue({
        job_id: 'test-job-id',
        status: 'processing',
        progress: 50,
        files: [],
      });

      const { unmount } = renderHook(() => useUploadStatus('test-job-id'));

      await waitFor(() => {
        expect(mockGetUploadStatus).toHaveBeenCalledTimes(1);
      });

      unmount();

      // Should not call API after unmount
      act(() => {
        jest.advanceTimersByTime(3000);
      });

      expect(mockGetUploadStatus).toHaveBeenCalledTimes(1);
    });

    test('clears interval when jobId changes to null', async () => {
      mockGetUploadStatus.mockResolvedValue({
        job_id: 'test-job-id',
        status: 'processing',
        progress: 50,
        files: [],
      });

      const { rerender } = renderHook(({ jobId }: { jobId: string | null }) => useUploadStatus(jobId), {
        initialProps: { jobId: 'test-job-id' as string | null },
      });

      await waitFor(() => {
        expect(mockGetUploadStatus).toHaveBeenCalledTimes(1);
      });

      // Change jobId to null
      rerender({ jobId: null });

      // Should not call API anymore
      act(() => {
        jest.advanceTimersByTime(3000);
      });

      expect(mockGetUploadStatus).toHaveBeenCalledTimes(1);
    });
  });
});
