"""
Unit tests for ResearchFundingService.
Following TDD Red-Green-Refactor cycle and plan.md Phase 2.
Using mocks to isolate service logic from repository.
"""

import pytest
from unittest.mock import Mock, MagicMock
from data_ingestion.services.research_funding_service import ResearchFundingService
from data_ingestion.infrastructure.repositories import ResearchFundingRepository


@pytest.mark.unit
class TestResearchFundingService:
    """Test suite for ResearchFundingService business logic."""

    def test_get_dashboard_data_success(self):
        """
        Test Case 1: 대시보드 데이터 조회 성공
        Verify service orchestrates repository calls and formats data
        """
        # Arrange
        mock_repo = Mock(spec=ResearchFundingRepository)
        mock_repo.get_current_balance.return_value = 1530000000
        mock_repo.get_monthly_trend.return_value = [
            {'month': '2024-01', 'balance': 1200000000, 'execution': 150000000},
            {'month': '2024-02', 'balance': 1400000000, 'execution': 120000000},
        ]

        service = ResearchFundingService(repository=mock_repo)

        # Act
        data = service.get_dashboard_data(department='all', period='latest')

        # Assert
        assert data['current_balance'] == 1530000000
        assert data['current_balance_formatted'] == '15.3억원'
        assert len(data['trend']) == 2
        assert data['trend'][0]['month'] == '2024-01'
        assert data['trend'][0]['month_formatted'] == '2024년 1월'
        assert data['trend'][0]['balance_formatted'] == '12.0억원'
        assert data['trend'][0]['execution_formatted'] == '1.5억원'

    def test_format_currency_to_billion_won(self):
        """
        Test Case 2: 억원 변환 정확성
        Business Rule: 1억원 = 100,000,000원
        """
        # Arrange
        service = ResearchFundingService()

        # Act & Assert
        assert service._format_currency(1530000000) == '15.3억원'
        assert service._format_currency(100000000) == '1.0억원'
        assert service._format_currency(0) == '0.0억원'
        assert service._format_currency(50000000) == '0.5억원'

    def test_format_month(self):
        """
        Test Case 3: 월 포맷팅 (YYYY-MM → YYYY년 M월)
        """
        # Arrange
        service = ResearchFundingService()

        # Act & Assert
        assert service._format_month('2024-01') == '2024년 1월'
        assert service._format_month('2024-12') == '2024년 12월'
        assert service._format_month('2023-03') == '2023년 3월'

    def test_get_dashboard_data_no_data(self):
        """
        Test Case 4: 데이터 없을 때 기본값 반환
        Edge Case: Empty database returns zero values
        """
        # Arrange
        mock_repo = Mock(spec=ResearchFundingRepository)
        mock_repo.get_current_balance.return_value = 0
        mock_repo.get_monthly_trend.return_value = []

        service = ResearchFundingService(repository=mock_repo)

        # Act
        data = service.get_dashboard_data(department='all', period='latest')

        # Assert
        assert data['current_balance'] == 0
        assert data['current_balance_formatted'] == '0.0억원'
        assert data['trend'] == []

    def test_service_calls_repository_with_correct_params(self):
        """
        Test Case 5: Service가 Repository를 올바른 파라미터로 호출
        """
        # Arrange
        mock_repo = Mock(spec=ResearchFundingRepository)
        mock_repo.get_current_balance.return_value = 1000000000
        mock_repo.get_monthly_trend.return_value = []

        service = ResearchFundingService(repository=mock_repo)

        # Act
        service.get_dashboard_data(department='컴퓨터공학과', period='1year')

        # Assert
        mock_repo.get_current_balance.assert_called_once_with(department='컴퓨터공학과')
        mock_repo.get_monthly_trend.assert_called_once_with(
            department='컴퓨터공학과',
            period='1year'
        )

    def test_service_handles_repository_returning_none(self):
        """
        Test Case 6: Repository가 None 반환 시 안전 처리
        Defensive programming: handle unexpected None values
        """
        # Arrange
        mock_repo = Mock(spec=ResearchFundingRepository)
        mock_repo.get_current_balance.return_value = None  # Unexpected
        mock_repo.get_monthly_trend.return_value = None  # Unexpected

        service = ResearchFundingService(repository=mock_repo)

        # Act
        data = service.get_dashboard_data(department='all', period='latest')

        # Assert - Service should handle None gracefully
        assert data['current_balance'] == 0  # Convert None to 0
        assert data['trend'] == []  # Convert None to empty list
