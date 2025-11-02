"""
Unit tests for domain entities.
Testing business rule validation in pure Python dataclasses.

Following test-plan.md: Core Logic (70% coverage), TDD Red-Green-Refactor.
"""

import pytest
from datetime import date
from data_ingestion.domain.entities import (
    ResearchFunding,
    Student,
    Publication,
    DepartmentKPI
)


@pytest.mark.unit
class TestResearchFundingEntity:
    """Test ResearchFunding entity business rules."""

    def test_create_valid_research_funding(self):
        """Valid research funding creation should succeed."""
        # Arrange & Act
        funding = ResearchFunding(
            execution_id='R001',
            department='컴퓨터공학과',
            total_budget=1000000,
            execution_date=date(2025, 1, 1),
            execution_amount=500000
        )

        # Assert
        assert funding.execution_id == 'R001'
        assert funding.department == '컴퓨터공학과'
        assert funding.total_budget == 1000000
        assert funding.execution_amount == 500000

    def test_reject_negative_total_budget(self):
        """Negative total budget should raise ValueError."""
        # Act & Assert
        with pytest.raises(ValueError, match="Total budget cannot be negative"):
            ResearchFunding(
                execution_id='R001',
                department='컴퓨터공학과',
                total_budget=-1000000,
                execution_date=date(2025, 1, 1),
                execution_amount=500000
            )

    def test_reject_negative_execution_amount(self):
        """Negative execution amount should raise ValueError."""
        # Act & Assert
        with pytest.raises(ValueError, match="Execution amount cannot be negative"):
            ResearchFunding(
                execution_id='R001',
                department='컴퓨터공학과',
                total_budget=1000000,
                execution_date=date(2025, 1, 1),
                execution_amount=-500000
            )

    def test_reject_execution_exceeding_budget(self):
        """Execution amount exceeding total budget should raise ValueError."""
        # Act & Assert
        with pytest.raises(ValueError, match="Execution amount cannot exceed total budget"):
            ResearchFunding(
                execution_id='R001',
                department='컴퓨터공학과',
                total_budget=1000000,
                execution_date=date(2025, 1, 1),
                execution_amount=2000000  # Exceeds budget
            )

    def test_allow_zero_amounts(self):
        """Zero amounts should be allowed."""
        # Act
        funding = ResearchFunding(
            execution_id='R001',
            department='컴퓨터공학과',
            total_budget=0,
            execution_date=date(2025, 1, 1),
            execution_amount=0
        )

        # Assert
        assert funding.total_budget == 0
        assert funding.execution_amount == 0

    def test_allow_execution_equal_to_budget(self):
        """Execution amount equal to total budget should be allowed."""
        # Act
        funding = ResearchFunding(
            execution_id='R001',
            department='컴퓨터공학과',
            total_budget=1000000,
            execution_date=date(2025, 1, 1),
            execution_amount=1000000  # Exactly equals budget
        )

        # Assert
        assert funding.execution_amount == funding.total_budget


@pytest.mark.unit
class TestStudentEntity:
    """Test Student entity business rules."""

    def test_create_valid_undergraduate_student(self):
        """Valid undergraduate student creation should succeed."""
        # Act
        student = Student(
            student_id='2025001',
            department='컴퓨터공학과',
            grade=2,
            program_type='학사',
            enrollment_status='재학'
        )

        # Assert
        assert student.student_id == '2025001'
        assert student.grade == 2
        assert student.program_type == '학사'
        assert student.enrollment_status == '재학'

    def test_create_valid_graduate_student(self):
        """Valid graduate student creation should succeed."""
        # Act
        student = Student(
            student_id='2025002',
            department='전자공학과',
            grade=1,
            program_type='석사',
            enrollment_status='재학'
        )

        # Assert
        assert student.program_type == '석사'

    def test_create_doctoral_student(self):
        """Valid doctoral student creation should succeed."""
        # Act
        student = Student(
            student_id='2025003',
            department='기계공학과',
            grade=3,
            program_type='박사',
            enrollment_status='휴학'
        )

        # Assert
        assert student.program_type == '박사'
        assert student.enrollment_status == '휴학'

    def test_reject_invalid_grade_zero(self):
        """Grade 0 should raise ValueError."""
        # Act & Assert
        with pytest.raises(ValueError, match="Grade must be between 1 and 4"):
            Student(
                student_id='2025001',
                department='컴퓨터공학과',
                grade=0,
                program_type='학사',
                enrollment_status='재학'
            )

    def test_reject_invalid_grade_five(self):
        """Grade 5 should raise ValueError."""
        # Act & Assert
        with pytest.raises(ValueError, match="Grade must be between 1 and 4"):
            Student(
                student_id='2025001',
                department='컴퓨터공학과',
                grade=5,
                program_type='학사',
                enrollment_status='재학'
            )

    def test_reject_invalid_program_type(self):
        """Invalid program type should raise ValueError."""
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid program type"):
            Student(
                student_id='2025001',
                department='컴퓨터공학과',
                grade=2,
                program_type='학부',  # Invalid
                enrollment_status='재학'
            )

    def test_reject_invalid_enrollment_status(self):
        """Invalid enrollment status should raise ValueError."""
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid enrollment status"):
            Student(
                student_id='2025001',
                department='컴퓨터공학과',
                grade=2,
                program_type='학사',
                enrollment_status='퇴학'  # Invalid
            )

    def test_allow_all_valid_program_types(self):
        """All valid program types should be accepted."""
        # Act & Assert
        for program_type in ['학사', '석사', '박사']:
            student = Student(
                student_id='2025001',
                department='컴퓨터공학과',
                grade=1,
                program_type=program_type,
                enrollment_status='재학'
            )
            assert student.program_type == program_type

    def test_allow_all_valid_enrollment_statuses(self):
        """All valid enrollment statuses should be accepted."""
        # Act & Assert
        for enrollment_status in ['재학', '휴학', '졸업']:
            student = Student(
                student_id='2025001',
                department='컴퓨터공학과',
                grade=1,
                program_type='학사',
                enrollment_status=enrollment_status
            )
            assert student.enrollment_status == enrollment_status

    def test_allow_grade_boundaries(self):
        """Grade boundaries (1 and 4) should be allowed."""
        # Act - Grade 1
        student1 = Student(
            student_id='2025001',
            department='컴퓨터공학과',
            grade=1,
            program_type='학사',
            enrollment_status='재학'
        )

        # Act - Grade 4
        student4 = Student(
            student_id='2025002',
            department='컴퓨터공학과',
            grade=4,
            program_type='학사',
            enrollment_status='졸업'
        )

        # Assert
        assert student1.grade == 1
        assert student4.grade == 4


@pytest.mark.unit
class TestPublicationEntity:
    """Test Publication entity business rules."""

    def test_create_valid_scie_publication(self):
        """Valid SCIE publication creation should succeed."""
        # Act
        pub = Publication(
            publication_id='P001',
            department='컴퓨터공학과',
            journal_tier='SCIE',
            impact_factor=3.5
        )

        # Assert
        assert pub.publication_id == 'P001'
        assert pub.journal_tier == 'SCIE'
        assert pub.impact_factor == 3.5

    def test_create_valid_kci_publication(self):
        """Valid KCI publication creation should succeed."""
        # Act
        pub = Publication(
            publication_id='P002',
            department='전자공학과',
            journal_tier='KCI',
            impact_factor=None
        )

        # Assert
        assert pub.journal_tier == 'KCI'
        assert pub.impact_factor is None

    def test_create_valid_other_publication(self):
        """Valid '기타' publication creation should succeed."""
        # Act
        pub = Publication(
            publication_id='P003',
            department='기계공학과',
            journal_tier='기타',
            impact_factor=None
        )

        # Assert
        assert pub.journal_tier == '기타'

    def test_reject_invalid_journal_tier(self):
        """Invalid journal tier should raise ValueError."""
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid journal tier"):
            Publication(
                publication_id='P001',
                department='컴퓨터공학과',
                journal_tier='SSCI',  # Invalid
                impact_factor=2.0
            )

    def test_reject_negative_impact_factor(self):
        """Negative impact factor should raise ValueError."""
        # Act & Assert
        with pytest.raises(ValueError, match="Impact factor cannot be negative"):
            Publication(
                publication_id='P001',
                department='컴퓨터공학과',
                journal_tier='SCIE',
                impact_factor=-1.5
            )

    def test_allow_zero_impact_factor(self):
        """Zero impact factor should be allowed."""
        # Act
        pub = Publication(
            publication_id='P001',
            department='컴퓨터공학과',
            journal_tier='SCIE',
            impact_factor=0.0
        )

        # Assert
        assert pub.impact_factor == 0.0

    def test_allow_none_impact_factor(self):
        """None impact factor should be allowed."""
        # Act
        pub = Publication(
            publication_id='P001',
            department='컴퓨터공학과',
            journal_tier='KCI',
            impact_factor=None
        )

        # Assert
        assert pub.impact_factor is None

    def test_allow_all_valid_journal_tiers(self):
        """All valid journal tiers should be accepted."""
        # Act & Assert
        for tier in ['SCIE', 'KCI', '기타']:
            pub = Publication(
                publication_id='P001',
                department='컴퓨터공학과',
                journal_tier=tier,
                impact_factor=None
            )
            assert pub.journal_tier == tier


@pytest.mark.unit
class TestDepartmentKPIEntity:
    """Test DepartmentKPI entity business rules."""

    def test_create_valid_department_kpi(self):
        """Valid department KPI creation should succeed."""
        # Act
        kpi = DepartmentKPI(
            evaluation_year=2025,
            department='컴퓨터공학과',
            employment_rate=85.5,
            tech_transfer_revenue=12.3
        )

        # Assert
        assert kpi.evaluation_year == 2025
        assert kpi.department == '컴퓨터공학과'
        assert kpi.employment_rate == 85.5
        assert kpi.tech_transfer_revenue == 12.3

    def test_reject_old_evaluation_year(self):
        """Evaluation year before 2000 should raise ValueError."""
        # Act & Assert
        with pytest.raises(ValueError, match="Evaluation year must be >= 2000"):
            DepartmentKPI(
                evaluation_year=1999,
                department='컴퓨터공학과',
                employment_rate=85.5,
                tech_transfer_revenue=12.3
            )

    def test_allow_year_2000(self):
        """Evaluation year 2000 should be allowed."""
        # Act
        kpi = DepartmentKPI(
            evaluation_year=2000,
            department='컴퓨터공학과',
            employment_rate=85.5,
            tech_transfer_revenue=12.3
        )

        # Assert
        assert kpi.evaluation_year == 2000

    def test_reject_negative_employment_rate(self):
        """Negative employment rate should raise ValueError."""
        # Act & Assert
        with pytest.raises(ValueError, match="Employment rate must be between 0 and 100"):
            DepartmentKPI(
                evaluation_year=2025,
                department='컴퓨터공학과',
                employment_rate=-1.0,
                tech_transfer_revenue=12.3
            )

    def test_reject_employment_rate_over_100(self):
        """Employment rate over 100 should raise ValueError."""
        # Act & Assert
        with pytest.raises(ValueError, match="Employment rate must be between 0 and 100"):
            DepartmentKPI(
                evaluation_year=2025,
                department='컴퓨터공학과',
                employment_rate=100.1,
                tech_transfer_revenue=12.3
            )

    def test_allow_employment_rate_boundaries(self):
        """Employment rate boundaries (0 and 100) should be allowed."""
        # Act - 0%
        kpi_zero = DepartmentKPI(
            evaluation_year=2025,
            department='컴퓨터공학과',
            employment_rate=0.0,
            tech_transfer_revenue=12.3
        )

        # Act - 100%
        kpi_hundred = DepartmentKPI(
            evaluation_year=2025,
            department='전자공학과',
            employment_rate=100.0,
            tech_transfer_revenue=12.3
        )

        # Assert
        assert kpi_zero.employment_rate == 0.0
        assert kpi_hundred.employment_rate == 100.0

    def test_reject_negative_tech_transfer_revenue(self):
        """Negative tech transfer revenue should raise ValueError."""
        # Act & Assert
        with pytest.raises(ValueError, match="Tech transfer revenue cannot be negative"):
            DepartmentKPI(
                evaluation_year=2025,
                department='컴퓨터공학과',
                employment_rate=85.5,
                tech_transfer_revenue=-5.0
            )

    def test_allow_zero_tech_transfer_revenue(self):
        """Zero tech transfer revenue should be allowed."""
        # Act
        kpi = DepartmentKPI(
            evaluation_year=2025,
            department='컴퓨터공학과',
            employment_rate=85.5,
            tech_transfer_revenue=0.0
        )

        # Assert
        assert kpi.tech_transfer_revenue == 0.0

    def test_allow_large_tech_transfer_revenue(self):
        """Large tech transfer revenue values should be allowed."""
        # Act
        kpi = DepartmentKPI(
            evaluation_year=2025,
            department='컴퓨터공학과',
            employment_rate=85.5,
            tech_transfer_revenue=999.99
        )

        # Assert
        assert kpi.tech_transfer_revenue == 999.99
