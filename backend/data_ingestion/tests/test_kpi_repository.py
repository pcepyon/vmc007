"""
Unit tests for KPIRepository (TDD - Red Phase).
Following plan.md Phase 3.2 - Repository Layer Tests.
"""

import pytest
from datetime import datetime
from django.test import TestCase
from data_ingestion.infrastructure.models import DepartmentKPI
from data_ingestion.infrastructure.repositories import KPIRepository


class KPIRepositoryTestCase(TestCase):
    """Test suite for KPIRepository data access layer."""

    def setUp(self):
        """Set up test data before each test."""
        # Create test data for years 2019-2023 for two departments
        self.test_data = [
            # 컴퓨터공학과
            DepartmentKPI.objects.create(
                evaluation_year=2019,
                department='컴퓨터공학과',
                employment_rate=76.2,
                tech_transfer_revenue=8.5
            ),
            DepartmentKPI.objects.create(
                evaluation_year=2020,
                department='컴퓨터공학과',
                employment_rate=77.8,
                tech_transfer_revenue=10.2
            ),
            DepartmentKPI.objects.create(
                evaluation_year=2021,
                department='컴퓨터공학과',
                employment_rate=79.1,
                tech_transfer_revenue=11.8
            ),
            DepartmentKPI.objects.create(
                evaluation_year=2022,
                department='컴퓨터공학과',
                employment_rate=78.5,
                tech_transfer_revenue=12.3
            ),
            DepartmentKPI.objects.create(
                evaluation_year=2023,
                department='컴퓨터공학과',
                employment_rate=80.2,
                tech_transfer_revenue=14.7
            ),
            # 전자공학과
            DepartmentKPI.objects.create(
                evaluation_year=2020,
                department='전자공학과',
                employment_rate=74.5,
                tech_transfer_revenue=6.2
            ),
            DepartmentKPI.objects.create(
                evaluation_year=2021,
                department='전자공학과',
                employment_rate=75.3,
                tech_transfer_revenue=7.1
            ),
            DepartmentKPI.objects.create(
                evaluation_year=2022,
                department='전자공학과',
                employment_rate=76.8,
                tech_transfer_revenue=8.5
            ),
        ]
        self.repository = KPIRepository()

    def test_find_by_department_and_year_returns_filtered_queryset(self):
        """학과 및 년도 범위로 필터링된 QuerySet 반환"""
        # Act: Get computer science department data from 2020-2022
        queryset = self.repository.find_by_department_and_year(
            department='컴퓨터공학과',
            start_year=2020,
            end_year=2022
        )

        # Assert: Should return 3 records (2020, 2021, 2022)
        self.assertEqual(queryset.count(), 3)

        # Assert: All records should be from computer science department
        for record in queryset:
            self.assertEqual(record.department, '컴퓨터공학과')
            self.assertGreaterEqual(record.evaluation_year, 2020)
            self.assertLessEqual(record.evaluation_year, 2022)

    def test_find_by_department_all_returns_all_departments(self):
        """department='all' 시 모든 학과 반환"""
        # Act: Get all departments for 2020-2022
        queryset = self.repository.find_by_department_and_year(
            department='all',
            start_year=2020,
            end_year=2022
        )

        # Assert: Should return 6 records (3 from each department)
        self.assertEqual(queryset.count(), 6)

        # Assert: Should include both departments
        departments = set(queryset.values_list('department', flat=True))
        self.assertIn('컴퓨터공학과', departments)
        self.assertIn('전자공학과', departments)

    def test_find_by_year_returns_single_year_data(self):
        """특정 년도 데이터만 조회"""
        # Act: Get data for 2022 only
        queryset = self.repository.find_by_year(2022)

        # Assert: Should return 2 records (one from each department)
        self.assertEqual(queryset.count(), 2)

        # Assert: All records should be from 2022
        for record in queryset:
            self.assertEqual(record.evaluation_year, 2022)

    def test_find_all_returns_all_records(self):
        """모든 KPI 데이터 조회"""
        # Act: Get all KPI records
        queryset = self.repository.find_all()

        # Assert: Should return all 8 test records
        self.assertEqual(queryset.count(), 8)

    def test_empty_queryset_when_no_matching_data(self):
        """조건에 맞는 데이터 없을 때 빈 QuerySet 반환"""
        # Act: Query nonexistent department
        queryset = self.repository.find_by_department_and_year(
            department='물리학과',
            start_year=2020,
            end_year=2023
        )

        # Assert: Should return empty queryset
        self.assertEqual(queryset.count(), 0)
        self.assertFalse(queryset.exists())

    def test_empty_queryset_when_year_range_has_no_data(self):
        """년도 범위에 데이터 없을 때 빈 QuerySet 반환"""
        # Act: Query year range with no data (2024-2025)
        queryset = self.repository.find_by_department_and_year(
            department='all',
            start_year=2024,
            end_year=2025
        )

        # Assert: Should return empty queryset
        self.assertEqual(queryset.count(), 0)

    def test_queryset_ordered_by_year(self):
        """QuerySet이 년도순으로 정렬되어 있는지 확인"""
        # Act: Get all data for computer science
        queryset = self.repository.find_by_department_and_year(
            department='컴퓨터공학과',
            start_year=2019,
            end_year=2023
        )

        # Assert: Should be ordered by evaluation_year ascending
        years = list(queryset.values_list('evaluation_year', flat=True))
        self.assertEqual(years, [2019, 2020, 2021, 2022, 2023])

    def test_boundary_conditions_inclusive_range(self):
        """경계 조건: 시작년도와 종료년도가 모두 포함되는지 확인"""
        # Act: Query exact range boundaries
        queryset = self.repository.find_by_department_and_year(
            department='컴퓨터공학과',
            start_year=2019,
            end_year=2019
        )

        # Assert: Should include the boundary year (2019)
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.first().evaluation_year, 2019)

    def test_get_all_departments(self):
        """모든 학과 목록 조회"""
        # Act: Get all unique departments
        departments = self.repository.get_all_departments()

        # Assert: Should return 2 departments
        self.assertEqual(len(departments), 2)
        self.assertIn('컴퓨터공학과', departments)
        self.assertIn('전자공학과', departments)
