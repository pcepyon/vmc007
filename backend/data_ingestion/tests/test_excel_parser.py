"""
Unit tests for ExcelParser - Core business logic validation.
Following test-plan.md: 70% coverage target, all business rules verified.

Test Strategy: Inside-Out TDD
- Test pure Pandas logic in isolation
- No DB or Django dependencies
- Fast, repeatable, independent tests (FIRST principles)
"""

import pytest
import pandas as pd
from data_ingestion.services.excel_parser import ExcelParser, ValidationError


@pytest.mark.unit
class TestResearchProjectDataParser:
    """Test research project data parsing and validation."""

    def test_parse_valid_research_data(self, sample_research_data):
        """Happy path: Valid research data should parse successfully."""
        # Arrange
        df = sample_research_data

        # Act
        result = ExcelParser.parse_research_project_data(df)

        # Assert
        assert len(result) == 3
        assert result['집행ID'].iloc[0] == 'R001'
        assert result['총연구비'].iloc[0] == 10000000
        assert result['집행금액'].iloc[0] == 1000000

    def test_reject_duplicate_execution_id(self):
        """Business Rule: 집행ID must be unique."""
        # Arrange: Create DataFrame with duplicate IDs
        df = pd.DataFrame({
            '집행ID': ['R001', 'R001', 'R003'],  # Duplicate R001
            '소속학과': ['컴퓨터공학과', '전기공학과', '컴퓨터공학과'],
            '총연구비': [10000000, 20000000, 15000000],
            '집행일자': ['2024-01-15', '2024-02-20', '2024-03-10'],
            '집행금액': [1000000, 2000000, 1500000]
        })

        # Act & Assert
        with pytest.raises(ValidationError, match="Duplicate 집행ID"):
            ExcelParser.parse_research_project_data(df)

    def test_reject_execution_amount_exceeding_total_budget(self):
        """Business Rule: 집행금액 <= 총연구비."""
        # Arrange: 집행금액 > 총연구비
        df = pd.DataFrame({
            '집행ID': ['R001'],
            '소속학과': ['컴퓨터공학과'],
            '총연구비': [10000000],
            '집행일자': ['2024-01-15'],
            '집행금액': [15000000]  # Exceeds budget!
        })

        # Act & Assert
        with pytest.raises(ValidationError, match="exceeds 총연구비"):
            ExcelParser.parse_research_project_data(df)

    def test_reject_negative_budget(self):
        """Business Rule: 총연구비 must be non-negative."""
        # Arrange
        df = pd.DataFrame({
            '집행ID': ['R001'],
            '소속학과': ['컴퓨터공학과'],
            '총연구비': [-10000000],  # Negative!
            '집행일자': ['2024-01-15'],
            '집행금액': [1000000]
        })

        # Act & Assert
        with pytest.raises(ValidationError, match="cannot be negative"):
            ExcelParser.parse_research_project_data(df)

    def test_reject_missing_required_columns(self):
        """Validation: All required columns must be present."""
        # Arrange: Missing '집행금액' column
        df = pd.DataFrame({
            '집행ID': ['R001'],
            '소속학과': ['컴퓨터공학과'],
            '총연구비': [10000000],
            '집행일자': ['2024-01-15'],
            # Missing: 집행금액
        })

        # Act & Assert
        with pytest.raises(ValidationError, match="Missing required columns"):
            ExcelParser.parse_research_project_data(df)


@pytest.mark.unit
class TestStudentRosterParser:
    """Test student roster parsing and validation."""

    def test_parse_valid_student_roster(self, sample_student_roster):
        """Happy path: Valid student data should parse successfully."""
        # Arrange
        df = sample_student_roster

        # Act
        result = ExcelParser.parse_student_roster(df)

        # Assert
        assert len(result) == 3
        assert result['학번'].iloc[0] == '2021001'
        assert result['학과'].iloc[0] == '컴퓨터공학과'

    def test_reject_duplicate_student_id(self):
        """Business Rule: 학번 must be unique."""
        # Arrange: Duplicate student IDs
        df = pd.DataFrame({
            '학번': ['2021001', '2021001', '2022001'],  # Duplicate
            '학과': ['컴퓨터공학과', '전기공학과', '컴퓨터공학과'],
            '학년': [4, 4, 3],
            '과정구분': ['학사', '학사', '학사'],
            '학적상태': ['재학', '재학', '휴학']
        })

        # Act & Assert
        with pytest.raises(ValidationError, match="Duplicate 학번"):
            ExcelParser.parse_student_roster(df)

    def test_reject_invalid_grade_range(self):
        """Business Rule: 학년 must be 1-7."""
        # Arrange: Invalid grade
        df = pd.DataFrame({
            '학번': ['2021001'],
            '학과': ['컴퓨터공학과'],
            '학년': [10],  # Invalid!
            '과정구분': ['학사'],
            '학적상태': ['재학']
        })

        # Act & Assert
        with pytest.raises(ValidationError, match="학년 must be between"):
            ExcelParser.parse_student_roster(df)


@pytest.mark.unit
class TestDepartmentKPIParser:
    """Test department KPI parsing and validation."""

    def test_parse_valid_department_kpi(self, sample_department_kpi):
        """Happy path: Valid KPI data should parse successfully."""
        # Arrange
        df = sample_department_kpi

        # Act
        result = ExcelParser.parse_department_kpi(df)

        # Assert
        assert len(result) == 3
        assert result['평가년도'].iloc[0] == 2023
        assert result['졸업생 취업률(%)'].iloc[0] == 85.5

    @pytest.mark.parametrize("invalid_rate", [
        -10.0,  # Negative
        150.0,  # Over 100%
        -0.1,   # Just below 0
        100.1,  # Just above 100
    ])
    def test_reject_invalid_employment_rate(self, invalid_rate):
        """Business Rule: 취업률 must be 0-100%."""
        # Arrange
        df = pd.DataFrame({
            '평가년도': [2024],
            '학과': ['컴퓨터공학과'],
            '졸업생 취업률(%)': [invalid_rate],
            '연간 기술이전 수입액(억원)': [5.0]
        })

        # Act & Assert
        with pytest.raises(ValidationError, match="must be between 0 and 100"):
            ExcelParser.parse_department_kpi(df)

    def test_reject_negative_tech_transfer_revenue(self):
        """Business Rule: 기술이전 수입액 must be non-negative."""
        # Arrange
        df = pd.DataFrame({
            '평가년도': [2024],
            '학과': ['컴퓨터공학과'],
            '졸업생 취업률(%)': [85.0],
            '연간 기술이전 수입액(억원)': [-5.0]  # Negative!
        })

        # Act & Assert
        with pytest.raises(ValidationError, match="cannot be negative"):
            ExcelParser.parse_department_kpi(df)

    def test_valid_edge_case_employment_rates(self):
        """Edge cases: 0% and 100% employment rates are valid."""
        # Arrange: Test boundary values
        df = pd.DataFrame({
            '평가년도': [2024, 2024],
            '학과': ['학과A', '학과B'],
            '졸업생 취업률(%)': [0.0, 100.0],  # Valid boundaries
            '연간 기술이전 수입액(억원)': [0.0, 10.0]
        })

        # Act
        result = ExcelParser.parse_department_kpi(df)

        # Assert: Should not raise exception
        assert len(result) == 2
        assert result['졸업생 취업률(%)'].iloc[0] == 0.0
        assert result['졸업생 취업률(%)'].iloc[1] == 100.0
