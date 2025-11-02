/**
 * API Client Tests
 * Testing uploadFiles and getUploadStatus functions
 * Following TDD principles - these tests are written BEFORE implementation
 */

import axios from 'axios';
import { uploadFiles, getUploadStatus, __resetApiClient } from '../dataApiClient';

// Mock axios
jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

// Mock axios instance
const mockAxiosInstance = {
  post: jest.fn(),
  get: jest.fn(),
};

describe('dataApiClient', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    __resetApiClient();
    // Mock axios.create to return our mock instance
    mockedAxios.create = jest.fn(() => mockAxiosInstance as any);
  });

  describe('uploadFiles', () => {
    it('should upload files with correct FormData and headers', async () => {
      // Arrange
      const mockFiles = {
        research_funding: new File(['research data'], 'research.csv', { type: 'text/csv' }),
        students: new File(['student data'], 'students.csv', { type: 'text/csv' }),
      };
      const mockResponse = {
        data: {
          status: 'processing',
          job_id: 'test-job-id-123',
          message: '파일 업로드가 시작되었습니다.',
        },
      };
      mockAxiosInstance.post.mockResolvedValue(mockResponse);

      // Act
      const result = await uploadFiles(mockFiles);

      // Assert
      expect(mockAxiosInstance.post).toHaveBeenCalledTimes(1);
      expect(mockAxiosInstance.post).toHaveBeenCalledWith(
        '/api/upload/',
        expect.any(FormData),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Content-Type': 'multipart/form-data',
            'X-Admin-Key': expect.any(String),
          }),
        })
      );
      expect(result).toEqual(mockResponse.data);
    });

    it('should include API key from environment variable', async () => {
      // Arrange
      const mockFiles = {
        research_funding: new File(['data'], 'test.csv', { type: 'text/csv' }),
      };
      const mockResponse = { data: { status: 'processing', job_id: 'test-id' } };
      mockAxiosInstance.post.mockResolvedValue(mockResponse);

      // Act
      await uploadFiles(mockFiles);

      // Assert
      const callArgs = mockAxiosInstance.post.mock.calls[0];
      const headers = callArgs[2]?.headers;
      expect(headers['X-Admin-Key']).toBeDefined();
    });

    it('should handle upload errors gracefully', async () => {
      // Arrange
      const mockFiles = {
        research_funding: new File(['data'], 'test.csv', { type: 'text/csv' }),
      };
      const mockError = {
        response: {
          status: 403,
          data: { error: 'forbidden', message: '관리자 권한이 없습니다.' },
        },
      };
      mockAxiosInstance.post.mockRejectedValue(mockError);

      // Act & Assert
      await expect(uploadFiles(mockFiles)).rejects.toEqual(mockError);
    });
  });

  describe('getUploadStatus', () => {
    it('should fetch upload status by job ID', async () => {
      // Arrange
      const jobId = 'test-job-id-456';
      const mockResponse = {
        data: {
          job_id: jobId,
          status: 'completed',
          progress: 100,
          files: [
            {
              file_type: 'research_funding',
              status: 'completed',
              rows_inserted: 1498,
            },
          ],
        },
      };
      mockAxiosInstance.get.mockResolvedValue(mockResponse);

      // Act
      const result = await getUploadStatus(jobId);

      // Assert
      expect(mockAxiosInstance.get).toHaveBeenCalledTimes(1);
      expect(mockAxiosInstance.get).toHaveBeenCalledWith(`/api/upload/status/${jobId}/`);
      expect(result).toEqual(mockResponse.data);
    });

    it('should handle 404 errors when job ID not found', async () => {
      // Arrange
      const jobId = 'invalid-job-id';
      const mockError = {
        response: {
          status: 404,
          data: { error: 'not_found', message: '작업 정보를 찾을 수 없습니다.' },
        },
      };
      mockAxiosInstance.get.mockRejectedValue(mockError);

      // Act & Assert
      await expect(getUploadStatus(jobId)).rejects.toEqual(mockError);
    });

    it('should handle network errors', async () => {
      // Arrange
      const jobId = 'test-job-id';
      const mockError = new Error('Network Error');
      mockAxiosInstance.get.mockRejectedValue(mockError);

      // Act & Assert
      await expect(getUploadStatus(jobId)).rejects.toThrow('Network Error');
    });
  });
});
