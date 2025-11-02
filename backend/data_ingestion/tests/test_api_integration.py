"""
Integration tests for API endpoints.
Following TDD - testing actual HTTP requests/responses.
"""

import pytest
from unittest.mock import patch, MagicMock
from rest_framework.test import APIClient
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile


@pytest.mark.integration
@pytest.mark.django_db
class TestUploadAPI:
    """Integration tests for upload endpoint."""

    def setup_method(self):
        """Set up API client with admin key."""
        self.client = APIClient()
        self.admin_key = getattr(settings, 'ADMIN_API_KEY', 'test-admin-key-12345')
        self.client.credentials(HTTP_X_ADMIN_KEY=self.admin_key)

    def test_upload_valid_csv_returns_202_with_job_id(self):
        """
        GIVEN a valid CSV file
        WHEN POST /api/upload/
        THEN returns HTTP 202 with job_id
        """
        # Arrange
        csv_content = b'execution_id,department,total_budget,execution_date,execution_amount\nEXEC001,CS,10000000,2024-01-15,1000000'
        file = SimpleUploadedFile('research.csv', csv_content, content_type='text/csv')

        # Act
        response = self.client.post(
            '/api/upload/',
            {'research_funding': file},
            format='multipart'
        )

        # Assert
        assert response.status_code == 202
        assert 'job_id' in response.data
        assert response.data['status'] == 'processing'

    def test_upload_without_api_key_returns_403(self):
        """
        GIVEN no API key in header
        WHEN POST /api/upload/
        THEN returns HTTP 403 Forbidden
        """
        # Arrange: Remove credentials
        self.client.credentials()
        csv_content = b'test,data'
        file = SimpleUploadedFile('test.csv', csv_content, content_type='text/csv')

        # Act
        response = self.client.post(
            '/api/upload/',
            {'research_funding': file},
            format='multipart'
        )

        # Assert
        assert response.status_code == 403

    def test_upload_file_too_large_returns_400(self):
        """
        GIVEN a file larger than 10MB
        WHEN POST /api/upload/
        THEN returns HTTP 400 with error message
        """
        # Arrange: 11MB file
        large_content = b'x' * (11 * 1024 * 1024)
        file = SimpleUploadedFile('large.csv', large_content, content_type='text/csv')

        # Act
        response = self.client.post(
            '/api/upload/',
            {'research_funding': file},
            format='multipart'
        )

        # Assert
        assert response.status_code == 400
        assert 'error' in response.data

    @patch('data_ingestion.api.views.submit_upload_job')
    def test_upload_submits_background_job(self, mock_submit):
        """
        GIVEN a valid file upload
        WHEN POST /api/upload/
        THEN submits job to background processor
        """
        # Arrange
        mock_submit.return_value = 'test-job-uuid'
        csv_content = b'test,data'
        file = SimpleUploadedFile('test.csv', csv_content, content_type='text/csv')

        # Act
        response = self.client.post(
            '/api/upload/',
            {'research_funding': file},
            format='multipart'
        )

        # Assert
        assert response.status_code == 202
        mock_submit.assert_called_once()


# Status API tests are covered in test_upload_api_views.py
