/**
 * FileUploadForm Component
 * Handles file selection, client-side validation, and upload initiation
 */

import React, { useState, useCallback } from 'react';
import { uploadFiles, UploadFilesInput } from '../../api/dataApiClient';

interface FileUploadFormProps {
  onUploadStart: (jobId: string) => void;
}

interface FileWithError {
  file: File | null;
  error: string | null;
}

interface FileState {
  research_funding: FileWithError;
  students: FileWithError;
  publications: FileWithError;
  kpi: FileWithError;
}

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB in bytes
const ALLOWED_EXTENSIONS = ['.csv', '.xlsx', '.xls'];

const FileUploadForm: React.FC<FileUploadFormProps> = ({ onUploadStart }) => {
  const [files, setFiles] = useState<FileState>({
    research_funding: { file: null, error: null },
    students: { file: null, error: null },
    publications: { file: null, error: null },
    kpi: { file: null, error: null },
  });

  const [uploadError, setUploadError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  /**
   * Validate a single file
   */
  const validateFile = (file: File | null): string | null => {
    if (!file) {
      return null;
    }

    // Check if file is empty
    if (file.size === 0) {
      return '빈 파일입니다. 데이터가 포함된 파일을 선택하세요.';
    }

    // Check file size
    if (file.size > MAX_FILE_SIZE) {
      return `파일 크기가 10MB를 초과합니다. (현재: ${(file.size / 1024 / 1024).toFixed(1)} MB)`;
    }

    // Check file extension
    const fileName = file.name.toLowerCase();
    const hasValidExtension = ALLOWED_EXTENSIONS.some((ext) => fileName.endsWith(ext));
    if (!hasValidExtension) {
      return '지원되지 않는 파일 형식입니다. CSV 또는 Excel 파일을 선택하세요.';
    }

    return null;
  };

  /**
   * Handle file selection for a specific file type
   */
  const handleFileChange = useCallback(
    (fileType: keyof FileState, event: React.ChangeEvent<HTMLInputElement>) => {
      const selectedFile = event.target.files?.[0] || null;
      const error = validateFile(selectedFile);

      setFiles((prev) => ({
        ...prev,
        [fileType]: {
          file: selectedFile,
          error,
        },
      }));

      // Clear upload error when user selects a new file
      setUploadError(null);
    },
    []
  );

  /**
   * Check if upload button should be enabled
   */
  const canUpload = (): boolean => {
    // At least one file must be selected
    const hasAnyFile = Object.values(files).some((f) => f.file !== null);
    if (!hasAnyFile) {
      return false;
    }

    // No validation errors
    const hasErrors = Object.values(files).some((f) => f.error !== null);
    if (hasErrors) {
      return false;
    }

    // Not currently uploading
    return !isUploading;
  };

  /**
   * Handle upload button click
   */
  const handleUpload = async () => {
    setIsUploading(true);
    setUploadError(null);

    try {
      // Build upload input from selected files
      const uploadInput: UploadFilesInput = {};
      if (files.research_funding.file) {
        uploadInput.research_funding = files.research_funding.file;
      }
      if (files.students.file) {
        uploadInput.students = files.students.file;
      }
      if (files.publications.file) {
        uploadInput.publications = files.publications.file;
      }
      if (files.kpi.file) {
        uploadInput.kpi = files.kpi.file;
      }

      // Call API
      const response = await uploadFiles(uploadInput);

      // Notify parent component
      onUploadStart(response.job_id);
    } catch (error: any) {
      // Handle specific error cases
      if (error.response?.status === 403) {
        setUploadError('관리자 권한이 없습니다. 접근이 거부되었습니다.');
      } else if (error.response?.status === 400) {
        setUploadError('파일 검증에 실패했습니다. 파일 형식과 내용을 확인하세요.');
      } else {
        setUploadError('업로드 중 오류가 발생했습니다. 잠시 후 다시 시도하세요.');
      }
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="file-upload-form">
      <div className="file-upload-info">
        <p>
          <strong>지원 형식:</strong> CSV, XLSX, XLS
        </p>
        <p>
          <strong>최대 크기:</strong> 최대 10MB
        </p>
      </div>

      <div className="file-sections">
        {/* Research Funding */}
        <FileSection
          title="연구비 집행 데이터"
          fileType="research_funding"
          file={files.research_funding.file}
          error={files.research_funding.error}
          onChange={(e) => handleFileChange('research_funding', e)}
        />

        {/* Students */}
        <FileSection
          title="학생 현황 데이터"
          fileType="students"
          file={files.students.file}
          error={files.students.error}
          onChange={(e) => handleFileChange('students', e)}
        />

        {/* Publications */}
        <FileSection
          title="논문 실적 데이터"
          fileType="publications"
          file={files.publications.file}
          error={files.publications.error}
          onChange={(e) => handleFileChange('publications', e)}
        />

        {/* KPI */}
        <FileSection
          title="학과 KPI 데이터"
          fileType="kpi"
          file={files.kpi.file}
          error={files.kpi.error}
          onChange={(e) => handleFileChange('kpi', e)}
        />
      </div>

      {uploadError && (
        <div className="upload-error" role="alert">
          {uploadError}
        </div>
      )}

      <button
        onClick={handleUpload}
        disabled={!canUpload()}
        className="upload-button"
        aria-label="업로드 시작"
      >
        {isUploading ? '업로드 중...' : '업로드 시작'}
      </button>
    </div>
  );
};

/**
 * File Section Component
 * Displays file input and validation for a single file type
 */
interface FileSectionProps {
  title: string;
  fileType: string;
  file: File | null;
  error: string | null;
  onChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
}

const FileSection: React.FC<FileSectionProps> = ({ title, fileType, file, error, onChange }) => {
  return (
    <div className="file-section">
      <h3>{title}</h3>
      <div className="file-input-wrapper">
        <label htmlFor={`file-input-${fileType}`} className="file-input-label">
          파일 선택
        </label>
        <input
          id={`file-input-${fileType}`}
          type="file"
          accept=".csv,.xlsx,.xls"
          onChange={onChange}
          aria-label={`${title} 파일 선택`}
        />
      </div>

      {file && !error && (
        <div className="file-info">
          <span className="file-name">{file.name}</span>
          <span className="file-size">({(file.size / 1024).toFixed(1)} KB)</span>
        </div>
      )}

      {error && (
        <div className="file-error" role="alert">
          {error}
        </div>
      )}
    </div>
  );
};

export default FileUploadForm;
