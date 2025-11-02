"""
Unit tests for Service Layer (KPI, Publication, Student).
Testing business logic with mocked repositories.

Following test-plan.md:
- Service/Repo layer (15% unit tests)
- Mock repository dependencies
- Test business rules and validation
"""

import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime
from django.core.exceptions import ValidationError
from django.utils import timezone

from data_ingestion.services.kpi_service import KPIService
from data_ingestion.services.publication_service import PublicationService
from data_ingestion.services.student_dashboard_service import StudentDashboardService


@pytest.mark.unit
class TestKPIService:
    """Test KPIService business logic."""

    def test_validate_year_range_success(self):
        """Valid year range should pass validation."""
        # Arrange
        service = KPIService()
        current_year = datetime.now().year

        # Act & Assert - Should not raise
        service._validate_year_range(2020, 2025)

    def test_validate_year_range_start_greater_than_end_raises_error(self):
        """Start year > end year should raise ValueError."""
        # Arrange
        service = KPIService()

        # Act & Assert
        with pytest.raises(ValueError, match="시작 년도는 종료 년도보다 작거나 같아야 합니다"):
            service._validate_year_range(2025, 2020)

    def test_validate_year_range_exceeds_20_years_raises_error(self):
        """Year range > 20 years should raise ValueError."""
        # Arrange
        service = KPIService()

        # Act & Assert
        with pytest.raises(ValueError, match="년도 범위는 최대 20년까지 조회 가능합니다"):
            service._validate_year_range(2000, 2021)  # 21 years

    def test_validate_year_range_future_year_raises_error(self):
        """Future year beyond current_year + 1 should raise ValueError."""
        # Arrange
        service = KPIService()
        current_year = datetime.now().year

        # Act & Assert
        with pytest.raises(ValueError, match="종료 년도는.*을 초과할 수 없습니다"):
            service._validate_year_range(2020, current_year + 2)

    def test_validate_year_range_before_2000_raises_error(self):
        """Start year before 2000 should raise ValueError."""
        # Arrange
        service = KPIService()

        # Act & Assert
        with pytest.raises(ValueError, match="시작 년도는 2000년 이후여야 합니다"):
            service._validate_year_range(1999, 2000)  # Use valid end year to isolate the check

    def test_get_kpi_trend_calls_repository_with_correct_params(self):
        """get_kpi_trend should call repository with validated parameters."""
        # Arrange
        service = KPIService()
        mock_repo = Mock()
        service.repository = mock_repo

        # Mock queryset
        mock_queryset = Mock()
        mock_queryset.values.return_value.annotate.return_value.order_by.return_value = []
        mock_queryset.aggregate.return_value = {'avg': 85.5}
        mock_repo.find_by_department_and_year.return_value = mock_queryset

        # Act
        result = service.get_kpi_trend('컴퓨터공학과', 2020, 2025)

        # Assert
        mock_repo.find_by_department_and_year.assert_called_once_with(
            department='컴퓨터공학과',
            start_year=2020,
            end_year=2025
        )
        assert result['status'] == 'success'

    def test_get_kpi_trend_formats_response_correctly(self):
        """get_kpi_trend should format response with correct structure."""
        # Arrange
        service = KPIService()
        mock_repo = Mock()
        service.repository = mock_repo

        # Mock queryset
        mock_queryset = Mock()
        mock_trend_data = [
            {'evaluation_year': 2020, 'avg_employment_rate': 80.0, 'total_tech_income': 10.0},
            {'evaluation_year': 2021, 'avg_employment_rate': 85.0, 'total_tech_income': 12.0}
        ]
        mock_queryset.values.return_value.annotate.return_value.order_by.return_value = mock_trend_data
        mock_queryset.aggregate.return_value = {'avg': 82.5}
        mock_repo.find_by_department_and_year.return_value = mock_queryset

        # Act
        result = service.get_kpi_trend('all', 2020, 2021)

        # Assert
        assert result['status'] == 'success'
        assert result['data'] == mock_trend_data
        assert result['meta']['department_filter'] == 'all'
        assert result['meta']['year_range'] == '2020-2021'
        assert result['meta']['overall_avg_employment_rate'] == 82.5
        assert result['meta']['total_count'] == 2


@pytest.mark.unit
class TestPublicationService:
    """Test PublicationService business logic."""

    def test_validate_inputs_invalid_journal_tier_raises_error(self):
        """Invalid journal tier should raise ValidationError."""
        # Arrange
        service = PublicationService()

        # Act & Assert
        with pytest.raises(ValidationError, match="유효하지 않은 저널등급입니다"):
            service._validate_inputs('all', 'INVALID_TIER')

    def test_validate_inputs_valid_journal_tier_passes(self):
        """Valid journal tier should pass validation."""
        # Arrange
        mock_repo = Mock()
        mock_repo.get_all_departments.return_value = []
        service = PublicationService(repository=mock_repo)

        # Act & Assert - Should not raise
        for tier in ['all', 'SCIE', 'KCI', '기타']:
            service._validate_inputs('all', tier)

    def test_validate_inputs_nonexistent_department_raises_error(self):
        """Non-existent department should raise ValidationError."""
        # Arrange
        mock_repo = Mock()
        mock_repo.get_all_departments.return_value = ['컴퓨터공학과', '전자공학과']
        service = PublicationService(repository=mock_repo)

        # Act & Assert
        with pytest.raises(ValidationError, match="존재하지 않는 학과입니다"):
            service._validate_inputs('기계공학과', 'SCIE')

    def test_calculate_avg_impact_factor_with_no_data(self):
        """calculate_avg_impact_factor with no IF data should return None."""
        # Arrange
        service = PublicationService()
        mock_queryset = Mock()
        mock_queryset.filter.return_value.count.return_value = 0

        # Act
        avg_if, papers_with_if = service._calculate_avg_impact_factor(mock_queryset)

        # Assert
        assert avg_if is None
        assert papers_with_if == 0

    def test_calculate_avg_impact_factor_with_valid_data(self):
        """calculate_avg_impact_factor should calculate average correctly."""
        # Arrange
        service = PublicationService()
        mock_queryset = Mock()
        mock_filtered = Mock()
        mock_filtered.count.return_value = 3
        mock_filtered.aggregate.return_value = {'avg': 4.5}
        mock_queryset.filter.return_value = mock_filtered

        # Act
        avg_if, papers_with_if = service._calculate_avg_impact_factor(mock_queryset)

        # Assert
        assert avg_if == 4.5
        assert papers_with_if == 3

    def test_aggregate_by_tier_with_empty_queryset(self):
        """aggregate_by_tier with empty queryset should return empty list."""
        # Arrange
        service = PublicationService()
        mock_queryset = Mock()
        mock_queryset.count.return_value = 0

        # Act
        result = service._aggregate_by_tier(mock_queryset)

        # Assert
        assert result == []

    def test_aggregate_by_tier_calculates_percentages(self):
        """aggregate_by_tier should calculate percentages correctly."""
        # Arrange
        service = PublicationService()
        mock_queryset = Mock()
        mock_queryset.count.return_value = 100

        mock_aggregated = [
            {'journal_tier': 'SCIE', 'count': 60, 'avg_if': 3.5},
            {'journal_tier': 'KCI', 'count': 30, 'avg_if': None},
            {'journal_tier': '기타', 'count': 10, 'avg_if': 1.2}
        ]
        mock_queryset.values.return_value.annotate.return_value.order_by.return_value = mock_aggregated

        # Act
        result = service._aggregate_by_tier(mock_queryset)

        # Assert
        assert len(result) == 3
        assert result[0]['journal_tier'] == 'SCIE'
        assert result[0]['percentage'] == 60.0
        assert result[0]['avg_if'] == 3.5

        assert result[1]['percentage'] == 30.0
        assert result[1]['avg_if'] is None

    def test_get_distribution_returns_formatted_response(self):
        """get_distribution should return properly formatted response."""
        # Arrange
        mock_repo = Mock()
        mock_repo.get_all_departments.return_value = []

        mock_queryset = Mock()
        mock_queryset.count.return_value = 100

        mock_aggregated = [
            {'journal_tier': 'SCIE', 'count': 60, 'avg_if': 3.5}
        ]
        mock_queryset.values.return_value.annotate.return_value.order_by.return_value = mock_aggregated

        mock_filtered = Mock()
        mock_filtered.count.return_value = 50
        mock_filtered.aggregate.return_value = {'avg': 4.0}
        mock_queryset.filter.return_value = mock_filtered

        mock_repo.get_publications_by_filter.return_value = mock_queryset

        service = PublicationService(repository=mock_repo)

        # Act
        result = service.get_distribution('all', 'all')

        # Assert
        assert result['total_papers'] == 100
        assert result['avg_impact_factor'] == 4.0
        assert result['papers_with_if'] == 50
        assert len(result['distribution']) == 1
        assert 'last_updated' in result


@pytest.mark.unit
class TestStudentDashboardService:
    """Test StudentDashboardService business logic."""

    def test_validate_inputs_invalid_status_raises_error(self):
        """Invalid enrollment status should raise ValidationError."""
        # Arrange
        service = StudentDashboardService()

        # Act & Assert
        with pytest.raises(ValidationError, match="유효하지 않은 학적상태"):
            service._validate_inputs('all', '퇴학')

    def test_validate_inputs_valid_statuses_pass(self):
        """Valid enrollment statuses should pass validation."""
        # Arrange
        mock_repo = Mock()
        mock_repo.get_all_departments.return_value = []
        service = StudentDashboardService(repository=mock_repo)

        # Act & Assert - Should not raise
        for status in ['all', '재학', '휴학', '졸업']:
            service._validate_inputs('all', status)

    def test_validate_inputs_nonexistent_department_raises_error(self):
        """Non-existent department should raise ValidationError."""
        # Arrange
        mock_repo = Mock()
        mock_repo.get_all_departments.return_value = ['컴퓨터공학과']
        service = StudentDashboardService(repository=mock_repo)

        # Act & Assert
        with pytest.raises(ValidationError, match="존재하지 않는 학과"):
            service._validate_inputs('기계공학과', '재학')

    def test_aggregate_by_department_returns_correct_structure(self):
        """aggregate_by_department should return correct data structure."""
        # Arrange
        service = StudentDashboardService()

        mock_queryset = Mock()
        mock_aggregated = [
            {'department': '컴퓨터공학과', '학사': 120, '석사': 35, '박사': 12, 'total': 167},
            {'department': '전자공학과', '학사': 100, '석사': 30, '박사': 10, 'total': 140}
        ]
        mock_queryset.values.return_value.annotate.return_value.order_by.return_value = mock_aggregated

        # Act
        result = service._aggregate_by_department(mock_queryset)

        # Assert
        assert len(result) == 2
        assert result[0]['department'] == '컴퓨터공학과'
        assert result[0]['학사'] == 120
        assert result[0]['석사'] == 35
        assert result[0]['박사'] == 12
        assert result[0]['total'] == 167

    def test_get_student_dashboard_data_returns_formatted_response(self):
        """get_student_dashboard_data should return properly formatted response."""
        # Arrange
        mock_repo = Mock()
        mock_repo.get_all_departments.return_value = []

        mock_queryset = Mock()
        mock_queryset.count.return_value = 307

        mock_aggregated = [
            {'department': '컴퓨터공학과', '학사': 120, '석사': 35, '박사': 12, 'total': 167}
        ]
        mock_queryset.values.return_value.annotate.return_value.order_by.return_value = mock_aggregated

        mock_repo.get_students_by_filter.return_value = mock_queryset

        service = StudentDashboardService(repository=mock_repo)

        # Act
        result = service.get_student_dashboard_data('all', '재학')

        # Assert
        assert result['total_students'] == 307
        assert len(result['by_department']) == 1
        assert result['by_department'][0]['department'] == '컴퓨터공학과'
        assert 'updated_at' in result

    def test_get_student_dashboard_data_calls_repository_correctly(self):
        """get_student_dashboard_data should call repository with correct params."""
        # Arrange
        mock_repo = Mock()
        mock_repo.get_all_departments.return_value = ['컴퓨터공학과', '전자공학과']

        mock_queryset = Mock()
        mock_queryset.count.return_value = 0
        mock_queryset.values.return_value.annotate.return_value.order_by.return_value = []

        mock_repo.get_students_by_filter.return_value = mock_queryset

        service = StudentDashboardService(repository=mock_repo)

        # Act
        service.get_student_dashboard_data('컴퓨터공학과', '재학')

        # Assert
        mock_repo.get_students_by_filter.assert_called_once_with('컴퓨터공학과', '재학')

    def test_default_parameters_use_enrolled_students(self):
        """Default parameters should filter for enrolled students."""
        # Arrange
        mock_repo = Mock()
        mock_repo.get_all_departments.return_value = []

        mock_queryset = Mock()
        mock_queryset.count.return_value = 0
        mock_queryset.values.return_value.annotate.return_value.order_by.return_value = []

        mock_repo.get_students_by_filter.return_value = mock_queryset

        service = StudentDashboardService(repository=mock_repo)

        # Act
        service.get_student_dashboard_data()

        # Assert
        mock_repo.get_students_by_filter.assert_called_once_with('all', '재학')
