"""
Integration tests for Department KPI API (TDD - Red Phase).
Following plan.md Phase 3.4 - API Integration Tests.
"""

from datetime import datetime
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from data_ingestion.infrastructure.models import DepartmentKPI


class DepartmentKPIAPIIntegrationTestCase(TestCase):
    """Integration tests for Department KPI API endpoint."""

    def setUp(self):
        """Set up test fixtures and client."""
        self.client = APIClient()
        self.url = reverse('department-kpi-list')
        self.current_year = datetime.now().year

        # Create test data
        self.create_test_data()

    def create_test_data(self):
        """Create test KPI data in database."""
        # Computer Science Department
        DepartmentKPI.objects.create(
            evaluation_year=2019,
            department='컴퓨터공학과',
            employment_rate=76.2,
            tech_transfer_revenue=8.5
        )
        DepartmentKPI.objects.create(
            evaluation_year=2020,
            department='컴퓨터공학과',
            employment_rate=77.8,
            tech_transfer_revenue=10.2
        )
        DepartmentKPI.objects.create(
            evaluation_year=2021,
            department='컴퓨터공학과',
            employment_rate=79.1,
            tech_transfer_revenue=11.8
        )
        DepartmentKPI.objects.create(
            evaluation_year=2022,
            department='컴퓨터공학과',
            employment_rate=78.5,
            tech_transfer_revenue=12.3
        )
        DepartmentKPI.objects.create(
            evaluation_year=2023,
            department='컴퓨터공학과',
            employment_rate=80.2,
            tech_transfer_revenue=14.7
        )

        # Electronics Department
        DepartmentKPI.objects.create(
            evaluation_year=2020,
            department='전자공학과',
            employment_rate=74.5,
            tech_transfer_revenue=6.2
        )
        DepartmentKPI.objects.create(
            evaluation_year=2021,
            department='전자공학과',
            employment_rate=75.3,
            tech_transfer_revenue=7.1
        )
        DepartmentKPI.objects.create(
            evaluation_year=2022,
            department='전자공학과',
            employment_rate=76.8,
            tech_transfer_revenue=8.5
        )

    def test_get_kpi_data_all_departments_returns_200(self):
        """전체 학과 KPI 조회 성공"""
        # Act
        response = self.client.get(self.url, {'department': 'all', 'start_year': 2019, 'end_year': 2023})

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'success')
        self.assertIn('data', response.data)
        self.assertIn('meta', response.data)

        # Assert: Data contains aggregated results
        data = response.data['data']
        self.assertGreater(len(data), 0)

        # Assert: First data point structure
        first_item = data[0]
        self.assertIn('evaluation_year', first_item)
        self.assertIn('avg_employment_rate', first_item)
        self.assertIn('total_tech_income', first_item)

    def test_get_kpi_data_specific_department_filters_correctly(self):
        """특정 학과 필터링 성공"""
        # Act
        response = self.client.get(self.url, {
            'department': '컴퓨터공학과',
            'start_year': 2020,
            'end_year': 2022
        })

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'success')

        # Assert: Meta shows correct filter
        self.assertEqual(response.data['meta']['department_filter'], '컴퓨터공학과')

        # Assert: Data is filtered correctly (3 years: 2020, 2021, 2022)
        data = response.data['data']
        self.assertEqual(len(data), 3)
        self.assertEqual(data[0]['evaluation_year'], 2020)
        self.assertEqual(data[2]['evaluation_year'], 2022)

    def test_get_kpi_data_year_range_filter(self):
        """년도 범위 필터링 성공"""
        # Act
        response = self.client.get(self.url, {
            'department': 'all',
            'start_year': 2020,
            'end_year': 2022
        })

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'success')

        # Assert: All data points are within range
        data = response.data['data']
        for item in data:
            self.assertGreaterEqual(item['evaluation_year'], 2020)
            self.assertLessEqual(item['evaluation_year'], 2022)

        # Assert: Meta shows correct year range
        self.assertEqual(response.data['meta']['year_range'], '2020-2022')

    def test_invalid_year_range_returns_400(self):
        """잘못된 년도 범위 시 400 에러"""
        # Act: start_year > end_year
        response = self.client.get(self.url, {
            'start_year': 2024,
            'end_year': 2019
        })

        # Assert
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['status'], 'error')
        self.assertEqual(response.data['error_code'], 'INVALID_YEAR_RANGE')

    def test_future_year_returns_400(self):
        """미래 년도 조회 시 400 에러"""
        # Act: end_year is 2 years in future
        response = self.client.get(self.url, {
            'start_year': self.current_year,
            'end_year': self.current_year + 2
        })

        # Assert
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['status'], 'error')
        self.assertEqual(response.data['error_code'], 'FUTURE_YEAR_NOT_ALLOWED')

    def test_year_range_exceeds_20_years_returns_400(self):
        """20년 초과 범위 조회 시 400 에러"""
        # Act: 21 year range
        response = self.client.get(self.url, {
            'start_year': 2000,
            'end_year': 2021
        })

        # Assert
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['status'], 'error')
        self.assertEqual(response.data['error_code'], 'YEAR_RANGE_TOO_LARGE')

    def test_year_before_2000_returns_400(self):
        """2000년 이전 데이터 조회 시 400 에러"""
        # Act: start_year = 1999
        response = self.client.get(self.url, {
            'start_year': 1999,
            'end_year': 2010
        })

        # Assert
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['status'], 'error')
        self.assertEqual(response.data['error_code'], 'YEAR_TOO_OLD')

    def test_no_data_returns_empty_list_with_200(self):
        """데이터 없을 때 빈 리스트 반환 (200 OK)"""
        # Arrange: Query nonexistent department
        response = self.client.get(self.url, {
            'department': '물리학과',
            'start_year': 2020,
            'end_year': 2023
        })

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(len(response.data['data']), 0)
        self.assertEqual(response.data['meta']['total_count'], 0)
        self.assertIsNone(response.data['meta']['overall_avg_employment_rate'])

    def test_default_parameters_applied(self):
        """파라미터 없을 때 기본값 적용"""
        # Act: No query parameters
        response = self.client.get(self.url)

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'success')

        # Assert: Default is 'all' department and last 5 years
        self.assertEqual(response.data['meta']['department_filter'], 'all')

        # Assert: Year range should be current_year - 5 to current_year
        expected_year_range = f'{self.current_year - 5}-{self.current_year}'
        self.assertEqual(response.data['meta']['year_range'], expected_year_range)

    def test_meta_contains_overall_avg_employment_rate(self):
        """메타 정보에 overall_avg_employment_rate 포함"""
        # Act
        response = self.client.get(self.url, {
            'department': 'all',
            'start_year': 2020,
            'end_year': 2022
        })

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertIn('overall_avg_employment_rate', response.data['meta'])

        # Assert: Should be a rounded float
        avg_rate = response.data['meta']['overall_avg_employment_rate']
        self.assertIsNotNone(avg_rate)
        self.assertIsInstance(avg_rate, float)

    def test_data_ordered_by_year_ascending(self):
        """데이터가 년도 오름차순으로 정렬됨"""
        # Act
        response = self.client.get(self.url, {
            'department': '컴퓨터공학과',
            'start_year': 2019,
            'end_year': 2023
        })

        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.data['data']

        # Assert: Years are in ascending order
        years = [item['evaluation_year'] for item in data]
        self.assertEqual(years, sorted(years))
