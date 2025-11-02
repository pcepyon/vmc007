/**
 * useUploadStatus Hook
 * Polls upload job status every 3 seconds until completion or failure
 */

import { useState, useEffect, useRef } from 'react';
import { getUploadStatus, UploadStatusResponse } from '../api/dataApiClient';

interface UseUploadStatusReturn {
  status: UploadStatusResponse | null;
  isPolling: boolean;
  error: string | null;
}

const POLLING_INTERVAL = 3000; // 3 seconds
const MAX_CONSECUTIVE_ERRORS = 3;

/**
 * Hook for polling upload status
 * @param jobId - Job ID to poll (null to disable polling)
 * @returns Current status, polling state, and error
 */
function useUploadStatus(jobId: string | null): UseUploadStatusReturn {
  const [status, setStatus] = useState<UploadStatusResponse | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const consecutiveErrorsRef = useRef(0);

  useEffect(() => {
    // Clear any existing interval
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }

    // Don't poll if no jobId
    if (!jobId) {
      setIsPolling(false);
      return;
    }

    // Reset state
    consecutiveErrorsRef.current = 0;
    setIsPolling(true);
    setError(null);

    /**
     * Fetch status from API
     */
    const fetchStatus = async () => {
      try {
        const response = await getUploadStatus(jobId);
        setStatus(response);
        setError(null);
        consecutiveErrorsRef.current = 0;

        // Stop polling if job is complete
        if (
          response.status === 'completed' ||
          response.status === 'failed' ||
          response.status === 'partial_success'
        ) {
          if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
          }
          setIsPolling(false);
        }
      } catch (err: any) {
        consecutiveErrorsRef.current += 1;

        // Handle specific error cases
        if (err.response?.status === 404) {
          setError('작업 정보를 찾을 수 없습니다. 페이지를 새로고침하거나 다시 업로드하세요.');
        } else {
          setError(err.message || '상태 조회 중 오류가 발생했습니다.');
        }

        // Stop polling after 3 consecutive errors
        if (consecutiveErrorsRef.current >= MAX_CONSECUTIVE_ERRORS) {
          if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
          }
          setIsPolling(false);
        }
      }
    };

    // Initial fetch
    fetchStatus();

    // Set up polling interval
    intervalRef.current = setInterval(fetchStatus, POLLING_INTERVAL);

    // Cleanup on unmount or jobId change
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      setIsPolling(false);
    };
  }, [jobId]);

  return {
    status,
    isPolling,
    error,
  };
}

export default useUploadStatus;
