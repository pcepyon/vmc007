"""
Unit tests for KPIService (TDD - Red Phase).
Following plan.md Phase 3.3 - Service Layer Tests.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from django.test import TestCase
from data_ingestion.services.kpi_service import KPIService


class KPIServiceTestCase(TestCase):
    """Test suite for KPIService business logic layer."""

    def setUp(self):
        """Set up test fixtures."""
        self.service = KPIService()
        self.current_year = datetime.now().year

    def test_validate_year_range_raises_error_when_start_greater_than_end(self):
        """시작 년도 > 종료 년도 시 ValueError"""
        # Arrange: start_year=2024, end_year=2019
        start_year = 2024
        end_year = 2019

        # Act & Assert: Should raise ValueError
        with self.assertRaises(ValueError) as context:
            self.service._validate_year_range(start_year, end_year)

        # Assert: Error message should be descriptive
        self.assertIn('작거나 같아야 합니다', str(context.exception))

    def test_validate_year_range_raises_error_when_range_exceeds_20_years(self):
        """년도 범위 20년 초과 시 ValueError"""
        # Arrange: 21 year range (2000-2021)
        start_year = 2000
        end_year = 2021

        # Act & Assert: Should raise ValueError
        with self.assertRaises(ValueError) as context:
            self.service._validate_year_range(start_year, end_year)

        # Assert: Error message mentions 20 year limit
        self.assertIn('20년', str(context.exception))

    def test_validate_year_range_raises_error_when_future_year(self):
        """미래 년도 조회 시 ValueError"""
        # Arrange: end_year is 2 years in the future
        start_year = self.current_year
        end_year = self.current_year + 2

        # Act & Assert: Should raise ValueError
        with self.assertRaises(ValueError) as context:
            self.service._validate_year_range(start_year, end_year)

        # Assert: Error message mentions future year restriction
        self.assertIn('초과할 수 없습니다', str(context.exception))

    def test_validate_year_range_raises_error_when_year_before_2000(self):
        """2000년 이전 데이터 조회 시 ValueError"""
        # Arrange: start_year=1999
        start_year = 1999
        end_year = 2010

        # Act & Assert: Should raise ValueError
        with self.assertRaises(ValueError) as context:
            self.service._validate_year_range(start_year, end_year)

        # Assert: Error message mentions 2000 year minimum
        self.assertIn('2000년 이후여야 합니다', str(context.exception))

    def test_validate_year_range_accepts_valid_range(self):
        """유효한 년도 범위는 통과"""
        # Arrange: Valid 5 year range
        start_year = 2019
        end_year = 2023

        # Act & Assert: Should not raise any exception
        try:
            self.service._validate_year_range(start_year, end_year)
        except ValueError:
            self.fail("_validate_year_range raised ValueError for valid range")

    def test_validate_year_range_accepts_single_year(self):
        """단일 년도 (start == end) 허용"""
        # Arrange: Same year for start and end
        start_year = 2023
        end_year = 2023

        # Act & Assert: Should not raise exception
        try:
            self.service._validate_year_range(start_year, end_year)
        except ValueError:
            self.fail("_validate_year_range raised ValueError for single year")

    def test_validate_year_range_accepts_current_year_plus_one(self):
        """현재 년도 + 1까지 허용 (내년 초 데이터 입력용)"""
        # Arrange: end_year = current_year + 1
        start_year = self.current_year
        end_year = self.current_year + 1

        # Act & Assert: Should not raise exception
        try:
            self.service._validate_year_range(start_year, end_year)
        except ValueError:
            self.fail("_validate_year_range raised ValueError for current_year+1")

    @patch('data_ingestion.services.kpi_service.KPIRepository')
    def test_get_kpi_trend_returns_aggregated_data(self, mock_repo_class):
        """학과 KPI 추이 데이터 정상 집계"""
        # Arrange: Mock repository to return QuerySet
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo

        # Create mock QuerySet with aggregate results
        mock_queryset = Mock()
        mock_queryset.values.return_value.annotate.return_value.order_by.return_value = [
            {
                'evaluation_year': 2019,
                'avg_employment_rate': 76.2,
                'total_tech_income': 8.5
            },
            {
                'evaluation_year': 2020,
                'avg_employment_rate': 77.8,
                'total_tech_income': 10.2
            },
            {
                'evaluation_year': 2021,
                'avg_employment_rate': 79.1,
                'total_tech_income': 11.8
            },
        ]

        # Mock aggregate for overall average
        mock_queryset.aggregate.return_value = {'avg': 77.7}

        mock_repo.find_by_department_and_year.return_value = mock_queryset

        # Create new service with mocked repository
        service = KPIService()

        # Act: Call service method
        result = service.get_kpi_trend(
            department='all',
            start_year=2019,
            end_year=2021
        )

        # Assert: Response structure
        self.assertEqual(result['status'], 'success')
        self.assertEqual(len(result['data']), 3)
        self.assertIn('meta', result)

        # Assert: Data content
        self.assertEqual(result['data'][0]['evaluation_year'], 2019)
        self.assertEqual(result['data'][0]['avg_employment_rate'], 76.2)

        # Assert: Meta information
        self.assertEqual(result['meta']['department_filter'], 'all')
        self.assertEqual(result['meta']['year_range'], '2019-2021')
        self.assertEqual(result['meta']['overall_avg_employment_rate'], 77.7)
        self.assertEqual(result['meta']['total_count'], 3)

    @patch('data_ingestion.services.kpi_service.KPIRepository')
    def test_get_kpi_trend_with_specific_department(self, mock_repo_class):
        """특정 학과 필터링 성공"""
        # Arrange
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo

        mock_queryset = Mock()
        mock_queryset.values.return_value.annotate.return_value.order_by.return_value = [
            {
                'evaluation_year': 2020,
                'avg_employment_rate': 78.5,
                'total_tech_income': 12.3
            },
        ]
        mock_queryset.aggregate.return_value = {'avg': 78.5}

        mock_repo.find_by_department_and_year.return_value = mock_queryset

        # Create new service
        service = KPIService()

        # Act
        result = service.get_kpi_trend(
            department='컴퓨터공학과',
            start_year=2020,
            end_year=2023
        )

        # Assert: Department filter is applied
        self.assertEqual(result['meta']['department_filter'], '컴퓨터공학과')

        # Assert: Repository was called with correct department
        mock_repo.find_by_department_and_year.assert_called_once_with(
            department='컴퓨터공학과',
            start_year=2020,
            end_year=2023
        )

    @patch('data_ingestion.services.kpi_service.KPIRepository')
    def test_overall_avg_employment_rate_is_null_when_no_data(self, mock_repo_class):
        """데이터 없을 때 overall_avg_employment_rate = null"""
        # Arrange: Empty queryset
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo

        mock_queryset = Mock()
        mock_queryset.values.return_value.annotate.return_value.order_by.return_value = []
        mock_queryset.aggregate.return_value = {'avg': None}

        mock_repo.find_by_department_and_year.return_value = mock_queryset

        # Create new service
        service = KPIService()

        # Act
        result = service.get_kpi_trend(
            department='물리학과',
            start_year=2020,
            end_year=2023
        )

        # Assert: Empty data
        self.assertEqual(result['data'], [])
        self.assertIsNone(result['meta']['overall_avg_employment_rate'])
        self.assertEqual(result['meta']['total_count'], 0)

    @patch('data_ingestion.services.kpi_service.KPIRepository')
    def test_rounds_avg_employment_rate_to_one_decimal(self, mock_repo_class):
        """평균 취업률 소수점 첫째자리 반올림"""
        # Arrange
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo

        mock_queryset = Mock()
        mock_queryset.values.return_value.annotate.return_value.order_by.return_value = []
        # Average is 78.456 (should round to 78.5)
        mock_queryset.aggregate.return_value = {'avg': 78.456}

        mock_repo.find_by_department_and_year.return_value = mock_queryset

        # Create new service
        service = KPIService()

        # Act
        result = service.get_kpi_trend(
            department='all',
            start_year=2020,
            end_year=2023
        )

        # Assert: Rounded to one decimal place
        self.assertEqual(result['meta']['overall_avg_employment_rate'], 78.5)

    @patch('data_ingestion.services.kpi_service.KPIRepository')
    def test_handles_single_year_data(self, mock_repo_class):
        """단일 년도 데이터만 존재할 때 정상 처리"""
        # Arrange
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo

        mock_queryset = Mock()
        mock_queryset.values.return_value.annotate.return_value.order_by.return_value = [
            {
                'evaluation_year': 2023,
                'avg_employment_rate': 80.2,
                'total_tech_income': 14.7
            },
        ]
        mock_queryset.aggregate.return_value = {'avg': 80.2}

        mock_repo.find_by_department_and_year.return_value = mock_queryset

        # Create new service
        service = KPIService()

        # Act
        result = service.get_kpi_trend(
            department='all',
            start_year=2023,
            end_year=2023
        )

        # Assert: Single data point handled correctly
        self.assertEqual(len(result['data']), 1)
        self.assertEqual(result['meta']['total_count'], 1)
        self.assertEqual(result['meta']['overall_avg_employment_rate'], 80.2)

    def test_get_kpi_trend_validates_year_range(self):
        """get_kpi_trend가 년도 범위 검증을 수행하는지 확인"""
        # Arrange: Invalid year range
        department = 'all'
        start_year = 2024
        end_year = 2019

        # Act & Assert: Should raise ValueError
        with self.assertRaises(ValueError):
            self.service.get_kpi_trend(department, start_year, end_year)
