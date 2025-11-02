"""
Integration tests for filter options metadata API.
Following TDD Red-Green-Refactor cycle.
Testing spec.md Section 9.5 - Filter Options API.
"""

import pytest
from rest_framework.test import APIClient
from django.urls import reverse


@pytest.mark.django_db
class TestFilterOptionsAPI:
    """Test GET /api/dashboard/filter-options/ endpoint"""

    def test_get_filter_options_returns_200(self):
        """Test: Filter options endpoint returns 200 OK"""
        # Arrange
        client = APIClient()
        url = '/api/dashboard/filter-options/'

        # Act
        response = client.get(url)

        # Assert
        assert response.status_code == 200

    def test_get_filter_options_returns_all_filter_types(self):
        """Test: Response includes all filter type arrays"""
        # Arrange
        client = APIClient()
        url = '/api/dashboard/filter-options/'

        # Act
        response = client.get(url)
        data = response.json()

        # Assert
        assert 'departments' in data
        assert 'years' in data
        assert 'student_statuses' in data
        assert 'journal_tiers' in data

    def test_get_filter_options_departments_includes_all_keyword(self):
        """Test: Departments array includes 'all' option"""
        # Arrange
        client = APIClient()
        url = '/api/dashboard/filter-options/'

        # Act
        response = client.get(url)
        data = response.json()

        # Assert
        assert 'all' in data['departments']

    def test_get_filter_options_years_includes_latest_keyword(self):
        """Test: Years array includes 'latest' option"""
        # Arrange
        client = APIClient()
        url = '/api/dashboard/filter-options/'

        # Act
        response = client.get(url)
        data = response.json()

        # Assert
        assert 'latest' in data['years']

    def test_get_filter_options_student_statuses_valid(self):
        """Test: Student statuses array contains valid values"""
        # Arrange
        client = APIClient()
        url = '/api/dashboard/filter-options/'

        # Act
        response = client.get(url)
        data = response.json()

        # Assert
        expected_statuses = ['all', '재학', '졸업', '휴학']
        for status in expected_statuses:
            assert status in data['student_statuses']

    def test_get_filter_options_journal_tiers_valid(self):
        """Test: Journal tiers array contains valid values"""
        # Arrange
        client = APIClient()
        url = '/api/dashboard/filter-options/'

        # Act
        response = client.get(url)
        data = response.json()

        # Assert
        expected_tiers = ['all', 'SCIE', 'KCI', '기타']
        for tier in expected_tiers:
            assert tier in data['journal_tiers']

    def test_get_filter_options_response_structure(self):
        """Test: Response structure matches spec"""
        # Arrange
        client = APIClient()
        url = '/api/dashboard/filter-options/'

        # Act
        response = client.get(url)
        data = response.json()

        # Assert
        assert isinstance(data['departments'], list)
        assert isinstance(data['years'], list)
        assert isinstance(data['student_statuses'], list)
        assert isinstance(data['journal_tiers'], list)

    def test_get_filter_options_no_authentication_required(self):
        """Test: Endpoint accessible without authentication (viewer access)"""
        # Arrange
        client = APIClient()
        url = '/api/dashboard/filter-options/'

        # Act - No authentication headers
        response = client.get(url)

        # Assert
        assert response.status_code == 200
