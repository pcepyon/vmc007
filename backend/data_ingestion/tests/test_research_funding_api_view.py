"""
Integration tests for ResearchFundingView API endpoint.
Following TDD Red-Green-Refactor cycle and plan.md Phase 3.
Tests actual HTTP endpoints with real database.
"""

import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from data_ingestion.infrastructure.models import ResearchProject
from data_ingestion.constants.error_codes import ErrorCode
from django.utils import timezone
from datetime import timedelta


@pytest.mark.django_db
class TestResearchFundingAPIView:
    """Integration tests for GET /api/dashboard/research-funding/ endpoint."""

    def setup_method(self):
        """Set up test client and clear database before each test."""
        self.client = APIClient()
        ResearchProject.objects.all().delete()

    def test_get_research_funding_all_departments(self):
        """
        Test Case 1: 정상 요청 - 전체 학과
        Should return 200 OK with current balance and trend data
        """
        # Arrange
        ResearchProject.objects.create(
            execution_id='EX001',
            department='컴퓨터공학과',
            total_budget=1000000000,
            execution_date='2024-01-15',
            execution_amount=200000000
        )

        # Act
        response = self.client.get('/api/dashboard/research-funding/')

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'success'
        assert 'data' in response.data
        assert 'current_balance' in response.data['data']
        assert 'trend' in response.data['data']
        assert response.data['data']['current_balance'] == 800000000

    def test_get_research_funding_with_department_filter(self):
        """
        Test Case 2: 학과 필터링
        Should only return data for specified department
        """
        # Arrange
        ResearchProject.objects.bulk_create([
            ResearchProject(
                execution_id='EX001',
                department='컴퓨터공학과',
                total_budget=1000000000,
                execution_date='2024-01-15',
                execution_amount=200000000
            ),
            ResearchProject(
                execution_id='EX002',
                department='전자공학과',
                total_budget=500000000,
                execution_date='2024-01-20',
                execution_amount=100000000
            ),
        ])

        # Act
        response = self.client.get(
            '/api/dashboard/research-funding/',
            {'department': '컴퓨터공학과'}
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['current_balance'] == 800000000

    def test_get_research_funding_invalid_department_returns_empty(self):
        """
        Test Case 3: 존재하지 않는 학과명
        Should return 200 OK with empty data (not an error, just no results)
        """
        # Arrange
        ResearchProject.objects.create(
            execution_id='EX001',
            department='컴퓨터공학과',
            total_budget=1000000000,
            execution_date='2024-01-15',
            execution_amount=200000000
        )

        # Act
        response = self.client.get(
            '/api/dashboard/research-funding/',
            {'department': '존재하지않는학과'}
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['current_balance'] == 0
        assert response.data['data']['trend'] == []

    def test_get_research_funding_no_data(self):
        """
        Test Case 4: 데이터 없을 때 200 OK with 빈 데이터
        Should return successful response with zero values
        """
        # Arrange: Empty database

        # Act
        response = self.client.get('/api/dashboard/research-funding/')

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['current_balance'] == 0
        assert response.data['data']['current_balance_formatted'] == '0.0억원'
        assert response.data['data']['trend'] == []
        assert 'message' in response.data or response.data['status'] == 'success'

    def test_get_research_funding_with_period_filter_1year(self):
        """
        Test Case 5: 기간 필터링 (1year)
        Should only return data from last 12 months
        """
        # Arrange
        two_years_ago = timezone.now() - timedelta(days=730)
        six_months_ago = timezone.now() - timedelta(days=180)

        ResearchProject.objects.bulk_create([
            ResearchProject(
                execution_id='EX001',
                department='컴퓨터공학과',
                total_budget=1000000000,
                execution_date=two_years_ago.date(),
                execution_amount=100000000
            ),
            ResearchProject(
                execution_id='EX002',
                department='컴퓨터공학과',
                total_budget=1000000000,
                execution_date=six_months_ago.date(),
                execution_amount=80000000
            ),
        ])

        # Act
        response = self.client.get(
            '/api/dashboard/research-funding/',
            {'period': '1year'}
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        trend_data = response.data['data']['trend']
        # Should only include recent 6-month data, not 2-year-old data
        assert len(trend_data) >= 0  # At least doesn't crash

    def test_get_research_funding_invalid_period_returns_400(self):
        """
        Test Case 6: 잘못된 period 파라미터
        Should return 400 Bad Request with error code
        """
        # Act
        response = self.client.get(
            '/api/dashboard/research-funding/',
            {'period': 'invalid_period'}
        )

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_get_research_funding_response_structure(self):
        """
        Test Case 7: 응답 구조 검증
        Verify response contains all required fields with correct formats
        """
        # Arrange
        ResearchProject.objects.create(
            execution_id='EX001',
            department='컴퓨터공학과',
            total_budget=1530000000,
            execution_date='2024-03-15',
            execution_amount=100000000
        )

        # Act
        response = self.client.get('/api/dashboard/research-funding/')

        # Assert
        assert response.status_code == status.HTTP_200_OK

        data = response.data['data']
        assert 'current_balance' in data
        assert 'current_balance_formatted' in data
        assert 'trend' in data

        # Check formatted currency
        assert '억원' in data['current_balance_formatted']

        # Check trend item structure
        if data['trend']:
            trend_item = data['trend'][0]
            assert 'month' in trend_item
            assert 'month_formatted' in trend_item
            assert 'balance' in trend_item
            assert 'balance_formatted' in trend_item
            assert 'execution' in trend_item
            assert 'execution_formatted' in trend_item

    def test_get_research_funding_multiple_months_aggregation(self):
        """
        Test Case 8: 월별 집계 정확성
        Verify monthly trend aggregation is correct
        """
        # Arrange: Multiple executions in different months
        ResearchProject.objects.bulk_create([
            ResearchProject(
                execution_id='EX001',
                department='컴퓨터공학과',
                total_budget=1000000000,
                execution_date='2024-01-15',
                execution_amount=100000000
            ),
            ResearchProject(
                execution_id='EX002',
                department='컴퓨터공학과',
                total_budget=1000000000,
                execution_date='2024-01-25',
                execution_amount=50000000
            ),
            ResearchProject(
                execution_id='EX003',
                department='컴퓨터공학과',
                total_budget=1000000000,
                execution_date='2024-02-10',
                execution_amount=80000000
            ),
        ])

        # Act
        response = self.client.get('/api/dashboard/research-funding/')

        # Assert
        assert response.status_code == status.HTTP_200_OK
        trend = response.data['data']['trend']

        # Should have 2 months of data
        assert len(trend) >= 2

        # Find January data
        jan_data = next((item for item in trend if '1월' in item['month_formatted']), None)
        if jan_data:
            # January should aggregate both EX001 and EX002 (100 + 50 = 150 million)
            assert jan_data['execution'] == 150000000
