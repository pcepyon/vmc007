/**
 * Data API Client
 * Handles communication with the backend API for file uploads and status polling
 */

import axios, { AxiosInstance } from 'axios';
import { ENV } from '../config/env';

// Export createApiClient for testing
export const createApiClient = (): AxiosInstance => {
  return axios.create({
    baseURL: ENV.API_BASE_URL,
    timeout: 60000, // 60 seconds for file uploads
  });
};

// Default instance for production use
let apiClient: AxiosInstance | null = null;
const getApiClient = (): AxiosInstance => {
  if (!apiClient) {
    apiClient = createApiClient();
  }
  return apiClient;
};

// Types
export interface UploadFilesInput {
  research_funding?: File;
  students?: File;
  publications?: File;
  kpi?: File;
}

export interface UploadResponse {
  status: 'processing';
  job_id: string;
  message: string;
  estimated_time?: string;
}

export interface FileStatus {
  file_type: string;
  status: 'processing' | 'completed' | 'failed';
  rows_processed?: number;
  rows_inserted?: number;
  rows_skipped?: number;
  errors?: string[];
  error_message?: string;
  error_details?: string;
  progress?: number;
}

export interface UploadStatusResponse {
  job_id: string;
  status: 'processing' | 'completed' | 'failed' | 'partial_success';
  progress: number;
  files: FileStatus[];
  completed_at?: string;
  failed_at?: string;
}

/**
 * Upload CSV/Excel files to the backend
 * @param files Object containing files to upload (keyed by file type)
 * @returns Promise with upload response containing job_id
 */
export async function uploadFiles(files: UploadFilesInput): Promise<UploadResponse> {
  const formData = new FormData();

  // Append files to FormData
  if (files.research_funding) {
    formData.append('research_funding', files.research_funding);
  }
  if (files.students) {
    formData.append('students', files.students);
  }
  if (files.publications) {
    formData.append('publications', files.publications);
  }
  if (files.kpi) {
    formData.append('kpi', files.kpi);
  }

  // Get API key from environment
  const apiKey = ENV.ADMIN_API_KEY;

  // Make POST request
  const response = await getApiClient().post<UploadResponse>('/api/upload/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
      'X-Admin-Key': apiKey,
    },
  });

  return response.data;
}

/**
 * Get upload job status
 * @param jobId Unique job identifier returned from uploadFiles
 * @returns Promise with current upload status
 */
export async function getUploadStatus(jobId: string): Promise<UploadStatusResponse> {
  const response = await getApiClient().get<UploadStatusResponse>(`/api/upload/status/${jobId}/`);
  return response.data;
}

// Export for testing - allows resetting the client
export const __resetApiClient = () => {
  apiClient = null;
};
