"""
Unit tests for ResearchFundingRepository.
Following TDD Red-Green-Refactor cycle and plan.md Phase 1.2.
"""

import pytest
from datetime import date, timedelta
from django.utils import timezone
from data_ingestion.infrastructure.models import ResearchProject
from data_ingestion.infrastructure.repositories import ResearchFundingRepository


@pytest.mark.unit
@pytest.mark.django_db
class TestResearchFundingRepository:
    """Test suite for ResearchFundingRepository data access methods."""

    def test_get_current_balance_all_departments(self):
        """
        Test Case 1: 전체 학과 현재 잔액 계산
        Business Rule: current_balance = SUM(total_budget) - SUM(execution_amount)
        """
        # Arrange
        ResearchProject.objects.create(
            execution_id='EX001',
            department='컴퓨터공학과',
            total_budget=1000000000,
            execution_date=date(2024, 1, 15),
            execution_amount=200000000
        )
        ResearchProject.objects.create(
            execution_id='EX002',
            department='전자공학과',
            total_budget=500000000,
            execution_date=date(2024, 2, 10),
            execution_amount=100000000
        )
        repo = ResearchFundingRepository()

        # Act
        balance = repo.get_current_balance(department=None)

        # Assert
        expected = (1000000000 + 500000000) - (200000000 + 100000000)
        assert balance == expected  # 1200000000

    def test_get_current_balance_specific_department(self):
        """
        Test Case 2: 특정 학과 잔액 계산
        Filter: department='컴퓨터공학과'
        """
        # Arrange
        ResearchProject.objects.create(
            execution_id='EX001',
            department='컴퓨터공학과',
            total_budget=1000000000,
            execution_date=date(2024, 1, 15),
            execution_amount=200000000
        )
        ResearchProject.objects.create(
            execution_id='EX002',
            department='전자공학과',
            total_budget=500000000,
            execution_date=date(2024, 2, 10),
            execution_amount=100000000
        )
        repo = ResearchFundingRepository()

        # Act
        balance = repo.get_current_balance(department='컴퓨터공학과')

        # Assert
        assert balance == 800000000  # 1000000000 - 200000000

    def test_get_current_balance_no_data_returns_zero(self):
        """
        Test Case 3: 데이터 없을 때 0 반환
        Edge Case: Empty database
        """
        # Arrange
        repo = ResearchFundingRepository()

        # Act
        balance = repo.get_current_balance()

        # Assert
        assert balance == 0

    def test_get_monthly_trend_basic(self):
        """
        Test Case 4: 월별 집행 추이 집계
        Aggregation: GROUP BY month, SUM(execution_amount)
        """
        # Arrange
        ResearchProject.objects.bulk_create([
            ResearchProject(
                execution_id='EX001',
                department='컴퓨터공학과',
                total_budget=1000000000,
                execution_date=date(2024, 1, 15),
                execution_amount=100000000
            ),
            ResearchProject(
                execution_id='EX002',
                department='컴퓨터공학과',
                total_budget=1000000000,
                execution_date=date(2024, 1, 25),
                execution_amount=50000000
            ),
            ResearchProject(
                execution_id='EX003',
                department='컴퓨터공학과',
                total_budget=1000000000,
                execution_date=date(2024, 2, 10),
                execution_amount=80000000
            ),
        ])
        repo = ResearchFundingRepository()

        # Act
        trend = repo.get_monthly_trend(department=None, period='latest')

        # Assert
        assert len(trend) == 2  # 2024-01, 2024-02
        assert trend[0]['month'] == '2024-01'
        assert trend[0]['execution'] == 150000000  # 100M + 50M
        assert trend[1]['month'] == '2024-02'
        assert trend[1]['execution'] == 80000000

    def test_get_monthly_trend_with_1year_period(self):
        """
        Test Case 5: 기간 필터 적용 (1년)
        Filter: execution_date >= 1 year ago
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
        repo = ResearchFundingRepository()

        # Act
        trend = repo.get_monthly_trend(period='1year')

        # Assert
        assert len(trend) == 1  # 최근 1년 데이터만
        assert trend[0]['execution'] == 80000000

    def test_get_monthly_trend_department_filter(self):
        """
        Test Case 6: 학과 필터 적용
        Filter: department='컴퓨터공학과'
        """
        # Arrange
        ResearchProject.objects.bulk_create([
            ResearchProject(
                execution_id='EX001',
                department='컴퓨터공학과',
                total_budget=1000000000,
                execution_date=date(2024, 1, 15),
                execution_amount=100000000
            ),
            ResearchProject(
                execution_id='EX002',
                department='전자공학과',
                total_budget=500000000,
                execution_date=date(2024, 1, 20),
                execution_amount=50000000
            ),
        ])
        repo = ResearchFundingRepository()

        # Act
        trend = repo.get_monthly_trend(department='컴퓨터공학과', period='latest')

        # Assert
        assert len(trend) == 1
        assert trend[0]['month'] == '2024-01'
        assert trend[0]['execution'] == 100000000  # Only 컴퓨터공학과

    def test_get_monthly_trend_empty_data(self):
        """
        Test Case 7: 빈 데이터베이스에서 빈 배열 반환
        """
        # Arrange
        repo = ResearchFundingRepository()

        # Act
        trend = repo.get_monthly_trend()

        # Assert
        assert trend == []

    def test_get_monthly_trend_calculates_cumulative_balance(self):
        """
        Test Case 8: 월별 누적 잔액 계산 검증
        Business Rule: balance = total_budget - cumulative_execution

        Note: MVP simplification - each execution_id has its own total_budget entry,
        so total_budget sums all entries (not grouped by project).
        """
        # Arrange
        ResearchProject.objects.bulk_create([
            ResearchProject(
                execution_id='EX001',
                department='컴퓨터공학과',
                total_budget=1000000000,  # Project A total budget
                execution_date=date(2024, 1, 15),
                execution_amount=100000000
            ),
            ResearchProject(
                execution_id='EX002',
                department='컴퓨터공학과',
                total_budget=1000000000,  # Same project A, but MVP sums both
                execution_date=date(2024, 2, 10),
                execution_amount=50000000
            ),
        ])
        repo = ResearchFundingRepository()

        # Act
        trend = repo.get_monthly_trend(department=None, period='latest')

        # Assert
        # MVP: total_budget = 1000M + 1000M = 2000M (sum of all entries)
        # Month 1: balance = 2000M - 100M = 1900M
        # Month 2: balance = 2000M - (100M + 50M) = 1850M
        assert trend[0]['balance'] == 1900000000
        assert trend[1]['balance'] == 1850000000
