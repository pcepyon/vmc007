/**
 * FileUploadForm Component Tests
 * Testing file upload UI, validation, and API integration
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import FileUploadForm from '../FileUploadForm';
import * as dataApiClient from '../../../api/dataApiClient';

// Mock the API client
jest.mock('../../../api/dataApiClient');

describe('FileUploadForm', () => {
  const mockUploadFiles = dataApiClient.uploadFiles as jest.MockedFunction<typeof dataApiClient.uploadFiles>;

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    test('renders upload form with 4 file type sections', () => {
      render(<FileUploadForm onUploadStart={jest.fn()} />);

      expect(screen.getByText(/연구비 집행 데이터/i)).toBeInTheDocument();
      expect(screen.getByText(/학생 현황 데이터/i)).toBeInTheDocument();
      expect(screen.getByText(/논문 실적 데이터/i)).toBeInTheDocument();
      expect(screen.getByText(/학과 KPI 데이터/i)).toBeInTheDocument();
    });

    test('renders upload button as disabled initially', () => {
      render(<FileUploadForm onUploadStart={jest.fn()} />);

      const uploadButton = screen.getByRole('button', { name: /업로드 시작/i });
      expect(uploadButton).toBeDisabled();
    });

    test('displays file format and size restrictions', () => {
      render(<FileUploadForm onUploadStart={jest.fn()} />);

      expect(screen.getByText(/CSV, XLSX, XLS/i)).toBeInTheDocument();
      expect(screen.getByText(/최대 10MB/i)).toBeInTheDocument();
    });
  });

  describe('Client-side Validation', () => {
    test('shows error for file exceeding 10MB', () => {
      render(<FileUploadForm onUploadStart={jest.fn()} />);

      // Create a file larger than 10MB
      const largeFile = new File(['x'.repeat(11 * 1024 * 1024)], 'large.csv', { type: 'text/csv' });
      const input = screen.getAllByLabelText(/파일 선택/i)[0] as HTMLInputElement;

      fireEvent.change(input, { target: { files: [largeFile] } });

      expect(screen.getByText(/파일 크기가 10MB를 초과합니다/i)).toBeInTheDocument();
    });

    test('shows error for invalid file extension', () => {
      render(<FileUploadForm onUploadStart={jest.fn()} />);

      const invalidFile = new File(['data'], 'test.txt', { type: 'text/plain' });
      const input = screen.getAllByLabelText(/파일 선택/i)[0] as HTMLInputElement;

      fireEvent.change(input, { target: { files: [invalidFile] } });

      expect(screen.getByText(/지원되지 않는 파일 형식입니다/i)).toBeInTheDocument();
    });

    test('shows error for empty file (0 bytes)', () => {
      render(<FileUploadForm onUploadStart={jest.fn()} />);

      const emptyFile = new File([], 'empty.csv', { type: 'text/csv' });
      const input = screen.getAllByLabelText(/파일 선택/i)[0] as HTMLInputElement;

      fireEvent.change(input, { target: { files: [emptyFile] } });

      expect(screen.getByText(/빈 파일입니다/i)).toBeInTheDocument();
    });

    test('accepts valid CSV file', () => {
      render(<FileUploadForm onUploadStart={jest.fn()} />);

      const validFile = new File(['data'], 'test.csv', { type: 'text/csv' });
      const input = screen.getAllByLabelText(/파일 선택/i)[0] as HTMLInputElement;

      fireEvent.change(input, { target: { files: [validFile] } });

      expect(screen.queryByText(/파일 크기가 10MB를 초과합니다/i)).not.toBeInTheDocument();
      expect(screen.getByText(/test.csv/i)).toBeInTheDocument();
    });

    test('enables upload button when at least one valid file is selected', () => {
      render(<FileUploadForm onUploadStart={jest.fn()} />);

      const validFile = new File(['data'], 'test.csv', { type: 'text/csv' });
      const input = screen.getAllByLabelText(/파일 선택/i)[0] as HTMLInputElement;

      fireEvent.change(input, { target: { files: [validFile] } });

      const uploadButton = screen.getByRole('button', { name: /업로드 시작/i });
      expect(uploadButton).not.toBeDisabled();
    });
  });

  describe('File Upload', () => {
    test('calls API with selected files when upload button is clicked', async () => {
      mockUploadFiles.mockResolvedValue({
        status: 'processing',
        job_id: 'test-job-id',
        message: '파일 업로드가 시작되었습니다.',
      });

      const mockOnUploadStart = jest.fn();
      render(<FileUploadForm onUploadStart={mockOnUploadStart} />);

      // Select a file
      const validFile = new File(['data'], 'research.csv', { type: 'text/csv' });
      const input = screen.getAllByLabelText(/파일 선택/i)[0] as HTMLInputElement;
      fireEvent.change(input, { target: { files: [validFile] } });

      // Click upload button
      const uploadButton = screen.getByRole('button', { name: /업로드 시작/i });
      fireEvent.click(uploadButton);

      await waitFor(() => {
        expect(mockUploadFiles).toHaveBeenCalledWith(
          expect.objectContaining({
            research_funding: validFile,
          })
        );
      });

      expect(mockOnUploadStart).toHaveBeenCalledWith('test-job-id');
    });

    test('disables upload button during upload', async () => {
      mockUploadFiles.mockImplementation(() => new Promise(() => {})); // Never resolves

      render(<FileUploadForm onUploadStart={jest.fn()} />);

      const validFile = new File(['data'], 'research.csv', { type: 'text/csv' });
      const input = screen.getAllByLabelText(/파일 선택/i)[0] as HTMLInputElement;
      fireEvent.change(input, { target: { files: [validFile] } });

      const uploadButton = screen.getByRole('button', { name: /업로드 시작/i });
      fireEvent.click(uploadButton);

      await waitFor(() => {
        expect(uploadButton).toBeDisabled();
      });
    });

    test('shows error message when upload fails', async () => {
      mockUploadFiles.mockRejectedValue(new Error('Network error'));

      render(<FileUploadForm onUploadStart={jest.fn()} />);

      const validFile = new File(['data'], 'research.csv', { type: 'text/csv' });
      const input = screen.getAllByLabelText(/파일 선택/i)[0] as HTMLInputElement;
      fireEvent.change(input, { target: { files: [validFile] } });

      const uploadButton = screen.getByRole('button', { name: /업로드 시작/i });
      fireEvent.click(uploadButton);

      await waitFor(() => {
        expect(screen.getByText(/업로드 중 오류가 발생했습니다/i)).toBeInTheDocument();
      });
    });

    test('shows 403 error message for unauthorized access', async () => {
      const error: any = new Error('Forbidden');
      error.response = { status: 403 };
      mockUploadFiles.mockRejectedValue(error);

      render(<FileUploadForm onUploadStart={jest.fn()} />);

      const validFile = new File(['data'], 'research.csv', { type: 'text/csv' });
      const input = screen.getAllByLabelText(/파일 선택/i)[0] as HTMLInputElement;
      fireEvent.change(input, { target: { files: [validFile] } });

      const uploadButton = screen.getByRole('button', { name: /업로드 시작/i });
      fireEvent.click(uploadButton);

      await waitFor(() => {
        expect(screen.getByText(/관리자 권한이 없습니다/i)).toBeInTheDocument();
      });
    });
  });

  describe('Multiple File Upload', () => {
    test('allows uploading all 4 file types simultaneously', async () => {
      mockUploadFiles.mockResolvedValue({
        status: 'processing',
        job_id: 'test-job-id',
        message: '파일 업로드가 시작되었습니다.',
      });

      const mockOnUploadStart = jest.fn();
      render(<FileUploadForm onUploadStart={mockOnUploadStart} />);

      const files = {
        research: new File(['data1'], 'research.csv', { type: 'text/csv' }),
        students: new File(['data2'], 'students.csv', { type: 'text/csv' }),
        publications: new File(['data3'], 'publications.csv', { type: 'text/csv' }),
        kpi: new File(['data4'], 'kpi.csv', { type: 'text/csv' }),
      };

      const inputs = screen.getAllByLabelText(/파일 선택/i) as HTMLInputElement[];
      fireEvent.change(inputs[0], { target: { files: [files.research] } });
      fireEvent.change(inputs[1], { target: { files: [files.students] } });
      fireEvent.change(inputs[2], { target: { files: [files.publications] } });
      fireEvent.change(inputs[3], { target: { files: [files.kpi] } });

      const uploadButton = screen.getByRole('button', { name: /업로드 시작/i });
      fireEvent.click(uploadButton);

      await waitFor(() => {
        expect(mockUploadFiles).toHaveBeenCalledWith({
          research_funding: files.research,
          students: files.students,
          publications: files.publications,
          kpi: files.kpi,
        });
      });
    });
  });

  describe('Accessibility', () => {
    test('has proper ARIA labels for file inputs', () => {
      render(<FileUploadForm onUploadStart={jest.fn()} />);

      const inputs = screen.getAllByLabelText(/파일 선택/i);
      expect(inputs).toHaveLength(4);

      inputs.forEach((input) => {
        expect(input).toHaveAttribute('type', 'file');
      });
    });

    test('has accessible upload button', () => {
      render(<FileUploadForm onUploadStart={jest.fn()} />);

      const uploadButton = screen.getByRole('button', { name: /업로드 시작/i });
      expect(uploadButton).toBeInTheDocument();
    });
  });
});
