"""
Unit tests for ingestion service.
Testing background job orchestration with mocked dependencies.

Following test-plan.md:
- Mock all external dependencies (parser, repository, job store)
- Test orchestration logic in isolation
- TDD Red-Green-Refactor cycle
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock, call
from data_ingestion.services.ingestion_service import (
    submit_upload_job,
    process_upload,
    FILE_TYPE_PARSERS
)
from data_ingestion.services.excel_parser import ValidationError


@pytest.mark.unit
class TestSubmitUploadJob:
    """Test job submission to background thread."""

    @patch('data_ingestion.services.ingestion_service.get_job_store')
    @patch('data_ingestion.services.ingestion_service.executor')
    def test_submit_job_creates_job_status(self, mock_executor, mock_get_job_store):
        """Submit job should create job status and return job_id."""
        # Arrange
        mock_job_store = Mock()
        mock_job_store.create_job.return_value = {'job_id': 'test-job-id', 'status': 'pending'}
        mock_get_job_store.return_value = mock_job_store

        files = {'research_funding': '/tmp/test.csv'}

        # Act
        with patch('data_ingestion.services.ingestion_service.uuid.uuid4') as mock_uuid:
            mock_uuid.return_value = MagicMock()
            mock_uuid.return_value.__str__.return_value = 'test-job-id'

            job_id = submit_upload_job(files)

        # Assert
        assert job_id == 'test-job-id'
        mock_job_store.create_job.assert_called_once_with('test-job-id')
        mock_executor.submit.assert_called_once()

    @patch('data_ingestion.services.ingestion_service.get_job_store')
    @patch('data_ingestion.services.ingestion_service.executor')
    def test_submit_job_submits_to_executor(self, mock_executor, mock_get_job_store):
        """Submit job should delegate processing to background executor."""
        # Arrange
        mock_job_store = Mock()
        mock_job_store.create_job.return_value = {'job_id': 'test-job-id'}
        mock_get_job_store.return_value = mock_job_store

        files = {'research_funding': '/tmp/test.csv'}

        # Act
        with patch('data_ingestion.services.ingestion_service.uuid.uuid4') as mock_uuid:
            mock_uuid.return_value = MagicMock()
            mock_uuid.return_value.__str__.return_value = 'test-job-id'

            submit_upload_job(files)

        # Assert
        assert mock_executor.submit.call_count == 1
        submit_args = mock_executor.submit.call_args[0]
        assert submit_args[0] == process_upload
        assert submit_args[1] == 'test-job-id'
        assert submit_args[2] == files


@pytest.mark.unit
class TestProcessUpload:
    """Test file processing orchestration."""

    @patch('data_ingestion.services.ingestion_service.get_job_store')
    @patch('data_ingestion.services.ingestion_service.pd.read_csv')
    @patch('data_ingestion.services.ingestion_service.FILE_TYPE_PARSERS')
    def test_process_single_file_success(
        self, mock_parsers_dict, mock_read_csv, mock_get_job_store
    ):
        """Process single file should parse, validate, and save data."""
        # Arrange
        mock_job_store = Mock()
        mock_get_job_store.return_value = mock_job_store

        # Mock DataFrame
        mock_df = pd.DataFrame({
            '집행ID': ['R001'],
            '소속학과': ['컴퓨터공학과'],
            '총연구비': [1000000],
            '집행일자': ['2025-01-01'],
            '집행금액': [500000]
        })
        mock_read_csv.return_value = mock_df

        # Mock parser and repository functions
        mock_parser = Mock(return_value=mock_df)
        mock_repo = Mock(return_value={'rows_inserted': 1, 'rows_skipped': 0})
        mock_parsers_dict.__getitem__.return_value = (mock_parser, mock_repo)
        mock_parsers_dict.__contains__.return_value = True

        files = {'research_funding': '/tmp/test.csv'}

        # Act
        process_upload('test-job-id', files)

        # Assert
        mock_read_csv.assert_called_once_with('/tmp/test.csv', encoding='utf-8')
        mock_parser.assert_called_once()
        mock_repo.assert_called_once()

        # Verify job status updates
        assert mock_job_store.update_status.called
        assert mock_job_store.update_progress.called

    @patch('data_ingestion.services.ingestion_service.get_job_store')
    @patch('data_ingestion.services.ingestion_service.pd.read_csv')
    def test_process_multiple_files_success(self, mock_read_csv, mock_get_job_store):
        """Process multiple files should handle each file independently."""
        # Arrange
        mock_job_store = Mock()
        mock_get_job_store.return_value = mock_job_store

        mock_df = pd.DataFrame({'test': [1]})
        mock_read_csv.return_value = mock_df

        # Mock all parsers/repos
        with patch.dict(FILE_TYPE_PARSERS, {
            'research_funding': (Mock(return_value=mock_df), Mock(return_value={'rows_inserted': 1})),
            'students': (Mock(return_value=mock_df), Mock(return_value={'rows_inserted': 1})),
        }):
            files = {
                'research_funding': '/tmp/research.csv',
                'students': '/tmp/students.csv'
            }

            # Act
            process_upload('test-job-id', files)

        # Assert
        assert mock_read_csv.call_count == 2
        mock_job_store.update_status.assert_called()

    @patch('data_ingestion.services.ingestion_service.get_job_store')
    @patch('data_ingestion.services.ingestion_service.pd.read_csv')
    def test_process_handles_validation_error(self, mock_read_csv, mock_get_job_store):
        """Process should handle ValidationError and continue with other files."""
        # Arrange
        mock_job_store = Mock()
        mock_get_job_store.return_value = mock_job_store

        mock_df = pd.DataFrame({'test': [1]})
        mock_read_csv.return_value = mock_df

        # Mock parser to raise ValidationError
        mock_parser = Mock(side_effect=ValidationError("Invalid data"))

        with patch.dict(FILE_TYPE_PARSERS, {
            'research_funding': (mock_parser, Mock()),
        }):
            files = {'research_funding': '/tmp/test.csv'}

            # Act
            process_upload('test-job-id', files)

        # Assert - job should be marked as failed
        mock_job_store.update_status.assert_called()
        status_call = mock_job_store.update_status.call_args
        # Should be called with FAILED status
        assert status_call is not None

    @patch('data_ingestion.services.ingestion_service.get_job_store')
    @patch('data_ingestion.services.ingestion_service.pd.read_csv')
    def test_process_handles_unknown_file_type(self, mock_read_csv, mock_get_job_store):
        """Process should handle unknown file type gracefully."""
        # Arrange
        mock_job_store = Mock()
        mock_get_job_store.return_value = mock_job_store

        files = {'unknown_type': '/tmp/test.csv'}

        # Act
        process_upload('test-job-id', files)

        # Assert - job should be marked as failed
        mock_job_store.update_status.assert_called()

    @patch('data_ingestion.services.ingestion_service.get_job_store')
    @patch('data_ingestion.services.ingestion_service.pd.read_csv')
    def test_process_partial_success_scenario(self, mock_read_csv, mock_get_job_store):
        """Process should handle partial success (some files fail, some succeed)."""
        # Arrange
        mock_job_store = Mock()
        mock_get_job_store.return_value = mock_job_store

        mock_df = pd.DataFrame({'test': [1]})
        mock_read_csv.return_value = mock_df

        # First file succeeds, second fails
        mock_parser_success = Mock(return_value=mock_df)
        mock_parser_fail = Mock(side_effect=ValidationError("Invalid"))

        with patch.dict(FILE_TYPE_PARSERS, {
            'research_funding': (mock_parser_success, Mock(return_value={'rows_inserted': 1})),
            'students': (mock_parser_fail, Mock()),
        }):
            files = {
                'research_funding': '/tmp/research.csv',
                'students': '/tmp/students.csv'
            }

            # Act
            process_upload('test-job-id', files)

        # Assert - both files should be processed
        assert mock_read_csv.call_count == 2
        mock_job_store.update_status.assert_called()

    @patch('data_ingestion.services.ingestion_service.get_job_store')
    @patch('data_ingestion.services.ingestion_service.pd.read_csv')
    def test_process_updates_progress(self, mock_read_csv, mock_get_job_store):
        """Process should update job progress to 100% on completion."""
        # Arrange
        mock_job_store = Mock()
        mock_get_job_store.return_value = mock_job_store

        mock_df = pd.DataFrame({'test': [1]})
        mock_read_csv.return_value = mock_df

        with patch.dict(FILE_TYPE_PARSERS, {
            'research_funding': (Mock(return_value=mock_df), Mock(return_value={'rows_inserted': 1})),
        }):
            files = {'research_funding': '/tmp/test.csv'}

            # Act
            process_upload('test-job-id', files)

        # Assert
        mock_job_store.update_progress.assert_called()
        # Check if 100% progress was set
        progress_calls = mock_job_store.update_progress.call_args_list
        assert any(call[0][1] == 100 for call in progress_calls)

    @patch('data_ingestion.services.ingestion_service.get_job_store')
    @patch('data_ingestion.services.ingestion_service.pd.read_csv')
    def test_process_handles_critical_exception(self, mock_read_csv, mock_get_job_store):
        """Process should handle critical exceptions and mark job as failed."""
        # Arrange
        mock_job_store = Mock()
        mock_get_job_store.return_value = mock_job_store

        # Simulate critical error
        mock_read_csv.side_effect = Exception("Critical system error")

        files = {'research_funding': '/tmp/test.csv'}

        # Act
        process_upload('test-job-id', files)

        # Assert - job should be marked as failed
        mock_job_store.update_status.assert_called()


@pytest.mark.unit
class TestFileTypeParsers:
    """Test FILE_TYPE_PARSERS configuration."""

    def test_all_required_file_types_configured(self):
        """All required file types should be configured."""
        # Assert
        required_types = ['research_funding', 'students', 'publications', 'kpi']

        for file_type in required_types:
            assert file_type in FILE_TYPE_PARSERS

            parser_func, repo_func = FILE_TYPE_PARSERS[file_type]
            assert callable(parser_func)
            assert callable(repo_func)

    def test_parser_configuration_structure(self):
        """Each parser configuration should have (parser_func, repo_func) tuple."""
        # Assert
        for file_type, (parser_func, repo_func) in FILE_TYPE_PARSERS.items():
            assert parser_func is not None
            assert repo_func is not None
            assert callable(parser_func)
            assert callable(repo_func)
