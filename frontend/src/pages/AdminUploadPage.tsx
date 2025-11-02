/**
 * AdminUploadPage Component
 * Page for admins to upload CSV/Excel files and monitor processing status
 */

import React, { useState } from 'react';
import FileUploadForm from '../components/upload/FileUploadForm';
import useUploadStatus from '../hooks/useUploadStatus';
import { UploadStatusResponse, FileStatus } from '../api/dataApiClient';

const AdminUploadPage: React.FC = () => {
  const [jobId, setJobId] = useState<string | null>(null);
  const { status, isPolling, error: pollingError } = useUploadStatus(jobId);

  /**
   * Handle upload start from FileUploadForm
   */
  const handleUploadStart = (newJobId: string) => {
    setJobId(newJobId);
  };

  /**
   * Reset page to initial state
   */
  const handleReset = () => {
    setJobId(null);
  };

  /**
   * Get file type display name
   */
  const getFileTypeDisplayName = (fileType: string): string => {
    const displayNames: Record<string, string> = {
      research_funding: '연구비 집행 데이터',
      students: '학생 현황 데이터',
      publications: '논문 실적 데이터',
      kpi: '학과 KPI 데이터',
    };
    return displayNames[fileType] || fileType;
  };

  /**
   * Get status display message
   */
  const getStatusMessage = (status: UploadStatusResponse | null): string => {
    if (!status) {
      return '';
    }

    switch (status.status) {
      case 'processing':
        return '처리 중...';
      case 'completed':
        return '업로드가 완료되었습니다!';
      case 'failed':
        return '업로드 중 오류가 발생했습니다.';
      case 'partial_success':
        return '업로드가 부분적으로 완료되었습니다.';
      default:
        return '';
    }
  };

  /**
   * Get status color class
   */
  const getStatusColorClass = (statusValue: string): string => {
    switch (statusValue) {
      case 'processing':
        return 'status-processing';
      case 'completed':
        return 'status-success';
      case 'failed':
        return 'status-error';
      case 'partial_success':
        return 'status-warning';
      default:
        return '';
    }
  };

  /**
   * Calculate total statistics
   */
  const getTotalStats = (files: FileStatus[]): { processed: number; inserted: number } => {
    return files.reduce(
      (acc, file) => ({
        processed: acc.processed + (file.rows_processed || 0),
        inserted: acc.inserted + (file.rows_inserted || 0),
      }),
      { processed: 0, inserted: 0 }
    );
  };

  return (
    <main className="admin-upload-page">
      <h1>데이터 업로드</h1>

      {/* Upload Form - shown when no job is running */}
      {!jobId && (
        <section className="upload-section">
          <FileUploadForm onUploadStart={handleUploadStart} />
        </section>
      )}

      {/* Status Section - shown when job is running or completed */}
      {jobId && status && (
        <section className="status-section">
          <div className={`status-header ${getStatusColorClass(status.status)}`}>
            <h2>{getStatusMessage(status)}</h2>
            <div className="progress-info">
              <span>진행률: {status.progress}%</span>
            </div>
          </div>

          {/* File Details */}
          <div className="file-details">
            {status.files.map((file, index) => (
              <div key={index} className={`file-item ${getStatusColorClass(file.status)}`}>
                <h3>{getFileTypeDisplayName(file.file_type)}</h3>

                {file.status === 'processing' && (
                  <div className="file-status">
                    <span>처리 중... {file.progress || 0}%</span>
                  </div>
                )}

                {file.status === 'completed' && (
                  <div className="file-status">
                    <span>✓ 완료</span>
                    {file.rows_processed !== undefined && (
                      <div className="file-stats">
                        <p>처리된 행: {file.rows_processed}</p>
                        <p>삽입된 행: {file.rows_inserted}</p>
                        {file.rows_skipped !== undefined && file.rows_skipped > 0 && (
                          <p>제외된 행: {file.rows_skipped}</p>
                        )}
                      </div>
                    )}
                  </div>
                )}

                {file.status === 'failed' && (
                  <div className="file-status">
                    <span>✗ 실패</span>
                    {file.error_message && (
                      <div className="file-errors">
                        <p className="error-message">{file.error_message}</p>
                        {file.error_details && <p className="error-details">{file.error_details}</p>}
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Total Statistics - shown on completion */}
          {(status.status === 'completed' || status.status === 'partial_success') && (
            <div className="total-stats">
              <h3>전체 통계</h3>
              {(() => {
                const stats = getTotalStats(status.files);
                return (
                  <>
                    <p>총 처리된 행: {stats.processed}건</p>
                    <p>총 삽입된 행: {stats.inserted}건</p>
                  </>
                );
              })()}
            </div>
          )}

          {/* Polling Error */}
          {pollingError && (
            <div className="polling-error" role="alert">
              {pollingError}
            </div>
          )}

          {/* Action Buttons */}
          {!isPolling && (
            <div className="action-buttons">
              <button onClick={handleReset} className="reset-button">
                추가 업로드
              </button>
            </div>
          )}
        </section>
      )}
    </main>
  );
};

export default AdminUploadPage;
