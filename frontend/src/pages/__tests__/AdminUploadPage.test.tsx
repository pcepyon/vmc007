/**
 * AdminUploadPage Component Tests
 * Testing the admin upload page integration
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import AdminUploadPage from '../AdminUploadPage';
import * as dataApiClient from '../../api/dataApiClient';

// Mock the API client
jest.mock('../../api/dataApiClient');

describe('AdminUploadPage', () => {
  const mockUploadFiles = dataApiClient.uploadFiles as jest.MockedFunction<typeof dataApiClient.uploadFiles>;
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

  describe('Initial Rendering', () => {
    test('renders page title', () => {
      render(<AdminUploadPage />);

      expect(screen.getByText(/데이터 업로드/i)).toBeInTheDocument();
    });

    test('renders FileUploadForm component', () => {
      render(<AdminUploadPage />);

      expect(screen.getByText(/연구비 집행 데이터/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /업로드 시작/i })).toBeInTheDocument();
    });

    test('does not show status section initially', () => {
      render(<AdminUploadPage />);

      expect(screen.queryByText(/처리 중/i)).not.toBeInTheDocument();
      expect(screen.queryByText(/완료/i)).not.toBeInTheDocument();
    });
  });

  describe('Upload Flow', () => {
    test('shows processing status after upload starts', async () => {
      mockUploadFiles.mockResolvedValue({
        status: 'processing',
        job_id: 'test-job-id',
        message: '파일 업로드가 시작되었습니다.',
      });

      mockGetUploadStatus.mockResolvedValue({
        job_id: 'test-job-id',
        status: 'processing',
        progress: 25,
        files: [
          {
            file_type: 'research_funding',
            status: 'processing',
            progress: 25,
          },
        ],
      });

      render(<AdminUploadPage />);

      // Select and upload file
      const validFile = new File(['data'], 'research.csv', { type: 'text/csv' });
      const input = screen.getAllByLabelText(/파일 선택/i)[0] as HTMLInputElement;
      fireEvent.change(input, { target: { files: [validFile] } });

      const uploadButton = screen.getByRole('button', { name: /업로드 시작/i });
      fireEvent.click(uploadButton);

      await waitFor(() => {
        expect(screen.getByRole('heading', { level: 2, name: /처리 중/i })).toBeInTheDocument();
      });
    });

    test('displays progress information while processing', async () => {
      mockUploadFiles.mockResolvedValue({
        status: 'processing',
        job_id: 'test-job-id',
        message: '파일 업로드가 시작되었습니다.',
      });

      mockGetUploadStatus.mockResolvedValue({
        job_id: 'test-job-id',
        status: 'processing',
        progress: 50,
        files: [
          {
            file_type: 'research_funding',
            status: 'completed',
            rows_processed: 100,
            rows_inserted: 95,
          },
          {
            file_type: 'students',
            status: 'processing',
            progress: 50,
          },
        ],
      });

      render(<AdminUploadPage />);

      const validFile = new File(['data'], 'research.csv', { type: 'text/csv' });
      const input = screen.getAllByLabelText(/파일 선택/i)[0] as HTMLInputElement;
      fireEvent.change(input, { target: { files: [validFile] } });

      const uploadButton = screen.getByRole('button', { name: /업로드 시작/i });
      fireEvent.click(uploadButton);

      await waitFor(() => {
        expect(screen.getByText(/진행률: 50%/i)).toBeInTheDocument();
      });
    });

    test('shows success message when upload completes', async () => {
      mockUploadFiles.mockResolvedValue({
        status: 'processing',
        job_id: 'test-job-id',
        message: '파일 업로드가 시작되었습니다.',
      });

      mockGetUploadStatus.mockResolvedValue({
        job_id: 'test-job-id',
        status: 'completed',
        progress: 100,
        files: [
          {
            file_type: 'research_funding',
            status: 'completed',
            rows_processed: 100,
            rows_inserted: 100,
            rows_skipped: 0,
          },
        ],
        completed_at: '2025-11-02T10:00:00Z',
      });

      render(<AdminUploadPage />);

      const validFile = new File(['data'], 'research.csv', { type: 'text/csv' });
      const input = screen.getAllByLabelText(/파일 선택/i)[0] as HTMLInputElement;
      fireEvent.change(input, { target: { files: [validFile] } });

      const uploadButton = screen.getByRole('button', { name: /업로드 시작/i });
      fireEvent.click(uploadButton);

      await waitFor(() => {
        expect(screen.getByText(/업로드가 완료되었습니다/i)).toBeInTheDocument();
      });
    });

    test('shows failure message when upload fails', async () => {
      mockUploadFiles.mockResolvedValue({
        status: 'processing',
        job_id: 'test-job-id',
        message: '파일 업로드가 시작되었습니다.',
      });

      mockGetUploadStatus.mockResolvedValue({
        job_id: 'test-job-id',
        status: 'failed',
        progress: 30,
        files: [
          {
            file_type: 'research_funding',
            status: 'failed',
            error_message: "필수 컬럼 '학과'가 누락되었습니다.",
            error_details: "3번째 행부터 '학과' 컬럼 값이 비어있습니다.",
          },
        ],
        failed_at: '2025-11-02T10:00:00Z',
      });

      render(<AdminUploadPage />);

      const validFile = new File(['data'], 'research.csv', { type: 'text/csv' });
      const input = screen.getAllByLabelText(/파일 선택/i)[0] as HTMLInputElement;
      fireEvent.change(input, { target: { files: [validFile] } });

      const uploadButton = screen.getByRole('button', { name: /업로드 시작/i });
      fireEvent.click(uploadButton);

      await waitFor(() => {
        expect(screen.getByText(/업로드 중 오류가 발생했습니다/i)).toBeInTheDocument();
      });
    });

    test('shows partial success message', async () => {
      mockUploadFiles.mockResolvedValue({
        status: 'processing',
        job_id: 'test-job-id',
        message: '파일 업로드가 시작되었습니다.',
      });

      mockGetUploadStatus.mockResolvedValue({
        job_id: 'test-job-id',
        status: 'partial_success',
        progress: 100,
        files: [
          {
            file_type: 'research_funding',
            status: 'completed',
            rows_processed: 100,
            rows_inserted: 100,
          },
          {
            file_type: 'students',
            status: 'failed',
            error_message: "필수 컬럼 '학과'가 누락되었습니다.",
          },
        ],
      });

      render(<AdminUploadPage />);

      const validFile = new File(['data'], 'research.csv', { type: 'text/csv' });
      const input = screen.getAllByLabelText(/파일 선택/i)[0] as HTMLInputElement;
      fireEvent.change(input, { target: { files: [validFile] } });

      const uploadButton = screen.getByRole('button', { name: /업로드 시작/i });
      fireEvent.click(uploadButton);

      await waitFor(() => {
        expect(screen.getByText(/부분적으로 완료되었습니다/i)).toBeInTheDocument();
      });
    });
  });

  describe('File Details Display', () => {
    test('shows processing status for each file', async () => {
      mockUploadFiles.mockResolvedValue({
        status: 'processing',
        job_id: 'test-job-id',
        message: '파일 업로드가 시작되었습니다.',
      });

      mockGetUploadStatus.mockResolvedValue({
        job_id: 'test-job-id',
        status: 'processing',
        progress: 50,
        files: [
          {
            file_type: 'research_funding',
            status: 'completed',
            rows_processed: 100,
            rows_inserted: 100,
          },
          {
            file_type: 'students',
            status: 'processing',
            progress: 50,
          },
        ],
      });

      render(<AdminUploadPage />);

      const validFile = new File(['data'], 'research.csv', { type: 'text/csv' });
      const input = screen.getAllByLabelText(/파일 선택/i)[0] as HTMLInputElement;
      fireEvent.change(input, { target: { files: [validFile] } });

      const uploadButton = screen.getByRole('button', { name: /업로드 시작/i });
      fireEvent.click(uploadButton);

      await waitFor(() => {
        expect(screen.getByText(/연구비 집행 데이터/i)).toBeInTheDocument();
        expect(screen.getByText(/학생 현황 데이터/i)).toBeInTheDocument();
      });
    });

    test('shows error details for failed files', async () => {
      mockUploadFiles.mockResolvedValue({
        status: 'processing',
        job_id: 'test-job-id',
        message: '파일 업로드가 시작되었습니다.',
      });

      mockGetUploadStatus.mockResolvedValue({
        job_id: 'test-job-id',
        status: 'failed',
        progress: 50,
        files: [
          {
            file_type: 'students',
            status: 'failed',
            error_message: "필수 컬럼 '학과'가 누락되었습니다.",
            error_details: "3번째 행부터 '학과' 컬럼 값이 비어있습니다.",
          },
        ],
        failed_at: '2025-11-02T10:00:00Z',
      });

      render(<AdminUploadPage />);

      const validFile = new File(['data'], 'research.csv', { type: 'text/csv' });
      const input = screen.getAllByLabelText(/파일 선택/i)[0] as HTMLInputElement;
      fireEvent.change(input, { target: { files: [validFile] } });

      const uploadButton = screen.getByRole('button', { name: /업로드 시작/i });
      fireEvent.click(uploadButton);

      await waitFor(() => {
        const errorElement = screen.queryByText((_content, element) => {
          return element?.textContent === "필수 컬럼 '학과'가 누락되었습니다.";
        });
        expect(errorElement).toBeInTheDocument();
      });
    });
  });

  describe('Action Buttons', () => {
    test('shows "추가 업로드" button after completion', async () => {
      mockUploadFiles.mockResolvedValue({
        status: 'processing',
        job_id: 'test-job-id',
        message: '파일 업로드가 시작되었습니다.',
      });

      mockGetUploadStatus.mockResolvedValue({
        job_id: 'test-job-id',
        status: 'completed',
        progress: 100,
        files: [
          {
            file_type: 'research_funding',
            status: 'completed',
            rows_processed: 100,
            rows_inserted: 100,
          },
        ],
        completed_at: '2025-11-02T10:00:00Z',
      });

      render(<AdminUploadPage />);

      const validFile = new File(['data'], 'research.csv', { type: 'text/csv' });
      const input = screen.getAllByLabelText(/파일 선택/i)[0] as HTMLInputElement;
      fireEvent.change(input, { target: { files: [validFile] } });

      const uploadButton = screen.getByRole('button', { name: /업로드 시작/i });
      fireEvent.click(uploadButton);

      await waitFor(() => {
        expect(screen.getByText(/업로드가 완료되었습니다/i)).toBeInTheDocument();
      });

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /추가 업로드/i })).toBeInTheDocument();
      });
    });

    test('resets page when "추가 업로드" is clicked', async () => {
      mockUploadFiles.mockResolvedValue({
        status: 'processing',
        job_id: 'test-job-id',
        message: '파일 업로드가 시작되었습니다.',
      });

      mockGetUploadStatus.mockResolvedValue({
        job_id: 'test-job-id',
        status: 'completed',
        progress: 100,
        files: [
          {
            file_type: 'research_funding',
            status: 'completed',
            rows_processed: 100,
            rows_inserted: 100,
          },
        ],
        completed_at: '2025-11-02T10:00:00Z',
      });

      render(<AdminUploadPage />);

      const validFile = new File(['data'], 'research.csv', { type: 'text/csv' });
      const input = screen.getAllByLabelText(/파일 선택/i)[0] as HTMLInputElement;
      fireEvent.change(input, { target: { files: [validFile] } });

      const uploadButton = screen.getByRole('button', { name: /업로드 시작/i });
      fireEvent.click(uploadButton);

      await waitFor(() => {
        expect(screen.getByText(/업로드가 완료되었습니다/i)).toBeInTheDocument();
      });

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /추가 업로드/i })).toBeInTheDocument();
      });

      const resetButton = screen.getByRole('button', { name: /추가 업로드/i });
      fireEvent.click(resetButton);

      await waitFor(() => {
        expect(screen.queryByText(/업로드가 완료되었습니다/i)).not.toBeInTheDocument();
      });
    });
  });

  describe('Accessibility', () => {
    test('uses semantic HTML structure', () => {
      render(<AdminUploadPage />);

      expect(screen.getByRole('main')).toBeInTheDocument();
    });

    test('has proper heading hierarchy', () => {
      render(<AdminUploadPage />);

      const heading = screen.getByRole('heading', { level: 1 });
      expect(heading).toHaveTextContent(/데이터 업로드/i);
    });
  });
});
