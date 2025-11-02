"""
Unit tests for Django models following TDD principles.
RED Phase: Write tests first, see them fail.
"""

import pytest
from datetime import date
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from data_ingestion.infrastructure.models import (
    ResearchProject,
    Student,
    Publication,
    DepartmentKPI
)


@pytest.mark.django_db
class TestResearchProjectModel:
    """Tests for ResearchProject model."""

    def test_create_research_project_success(self):
        """RED: Test creating a valid research project record."""
        # Arrange & Act
        project = ResearchProject.objects.create(
            execution_id='TEST001',
            department='컴퓨터공학과',
            total_budget=100000000,
            execution_date=date(2024, 1, 15),
            execution_amount=10000000
        )

        # Assert
        assert project.execution_id == 'TEST001'
        assert project.department == '컴퓨터공학과'
        assert project.total_budget == 100000000
        assert project.execution_amount == 10000000
        assert project.created_at is not None
        assert project.updated_at is not None

    def test_execution_id_is_primary_key(self):
        """RED: Test execution_id is unique and cannot be duplicated."""
        # Arrange
        ResearchProject.objects.create(
            execution_id='DUPLICATE001',
            department='전자공학과',
            total_budget=50000000,
            execution_date=date(2024, 2, 1),
            execution_amount=5000000
        )

        # Act & Assert: Duplicate PK should raise IntegrityError
        with pytest.raises(IntegrityError):
            ResearchProject.objects.create(
                execution_id='DUPLICATE001',  # Same PK
                department='전기공학과',
                total_budget=60000000,
                execution_date=date(2024, 2, 2),
                execution_amount=6000000
            )

    def test_not_null_constraints(self):
        """RED: Test NOT NULL constraints on required fields."""
        # Act & Assert: Missing required field should raise IntegrityError
        with pytest.raises(IntegrityError):
            ResearchProject.objects.create(
                execution_id='TEST002',
                department=None,  # NOT NULL violation
                total_budget=100000000,
                execution_date=date(2024, 1, 15),
                execution_amount=10000000
            )

    def test_negative_budget_validation(self):
        """RED: Test that negative values in budget fields are rejected."""
        # Arrange
        project = ResearchProject(
            execution_id='TEST003',
            department='컴퓨터공학과',
            total_budget=-100000,  # Invalid negative
            execution_date=date(2024, 1, 15),
            execution_amount=10000
        )

        # Act & Assert
        with pytest.raises(ValidationError):
            project.full_clean()  # Triggers Django validators


@pytest.mark.django_db
class TestStudentModel:
    """Tests for Student model."""

    def test_create_student_success(self):
        """RED: Test creating a valid student record."""
        # Arrange & Act
        student = Student.objects.create(
            student_id='2024001',
            department='컴퓨터공학과',
            grade=3,
            program_type='학사',
            enrollment_status='재학'
        )

        # Assert
        assert student.student_id == '2024001'
        assert student.department == '컴퓨터공학과'
        assert student.grade == 3
        assert student.program_type == '학사'
        assert student.enrollment_status == '재학'

    def test_student_id_is_primary_key(self):
        """RED: Test student_id uniqueness."""
        # Arrange
        Student.objects.create(
            student_id='2024002',
            department='전자공학과',
            grade=2,
            program_type='학사',
            enrollment_status='재학'
        )

        # Act & Assert
        with pytest.raises(IntegrityError):
            Student.objects.create(
                student_id='2024002',  # Duplicate
                department='전기공학과',
                grade=3,
                program_type='학사',
                enrollment_status='재학'
            )

    def test_grade_range_validation(self):
        """RED: Test grade must be between 1 and 4."""
        # Arrange
        student = Student(
            student_id='2024003',
            department='컴퓨터공학과',
            grade=10,  # Invalid: too high
            program_type='학사',
            enrollment_status='재학'
        )

        # Act & Assert
        with pytest.raises(ValidationError):
            student.full_clean()

    def test_program_type_choices(self):
        """RED: Test program_type only allows specific values."""
        # Arrange
        student = Student(
            student_id='2024004',
            department='컴퓨터공학과',
            grade=3,
            program_type='무효한과정',  # Invalid choice
            enrollment_status='재학'
        )

        # Act & Assert
        with pytest.raises(ValidationError):
            student.full_clean()


@pytest.mark.django_db
class TestPublicationModel:
    """Tests for Publication model."""

    def test_create_publication_success(self):
        """RED: Test creating a valid publication record."""
        # Arrange & Act
        pub = Publication.objects.create(
            paper_id='PUB001',
            department='컴퓨터공학과',
            journal_tier='SCIE',
            impact_factor=3.25
        )

        # Assert
        assert pub.paper_id == 'PUB001'
        assert pub.journal_tier == 'SCIE'
        assert pub.impact_factor == 3.25

    def test_impact_factor_null_allowed(self):
        """RED: Test that impact_factor can be NULL."""
        # Arrange & Act
        pub = Publication.objects.create(
            paper_id='PUB002',
            department='전자공학과',
            journal_tier='KCI',
            impact_factor=None  # Should be allowed
        )

        # Assert
        assert pub.impact_factor is None

    def test_negative_impact_factor_validation(self):
        """RED: Test negative impact_factor is rejected."""
        # Arrange
        pub = Publication(
            paper_id='PUB003',
            department='컴퓨터공학과',
            journal_tier='SCIE',
            impact_factor=-1.5  # Invalid
        )

        # Act & Assert
        with pytest.raises(ValidationError):
            pub.full_clean()


@pytest.mark.django_db
class TestDepartmentKPIModel:
    """Tests for DepartmentKPI model with composite unique constraint."""

    def test_create_department_kpi_success(self):
        """RED: Test creating a valid KPI record."""
        # Arrange & Act
        kpi = DepartmentKPI.objects.create(
            evaluation_year=2023,
            department='컴퓨터공학과',
            employment_rate=78.5,
            tech_transfer_revenue=12.3
        )

        # Assert
        assert kpi.evaluation_year == 2023
        assert kpi.department == '컴퓨터공학과'
        assert kpi.employment_rate == 78.5
        assert kpi.tech_transfer_revenue == 12.3

    def test_composite_unique_constraint(self):
        """RED: Test that (evaluation_year + department) combination is unique."""
        # Arrange
        DepartmentKPI.objects.create(
            evaluation_year=2023,
            department='컴퓨터공학과',
            employment_rate=78.5,
            tech_transfer_revenue=12.3
        )

        # Act & Assert: Same year + department should fail
        with pytest.raises(IntegrityError):
            DepartmentKPI.objects.create(
                evaluation_year=2023,
                department='컴퓨터공학과',  # Duplicate combination
                employment_rate=80.0,
                tech_transfer_revenue=15.0
            )

    def test_employment_rate_range_validation(self):
        """RED: Test employment_rate must be 0-100."""
        # Arrange
        kpi = DepartmentKPI(
            evaluation_year=2023,
            department='컴퓨터공학과',
            employment_rate=150.0,  # Invalid: > 100
            tech_transfer_revenue=12.3
        )

        # Act & Assert
        with pytest.raises(ValidationError):
            kpi.full_clean()

    def test_negative_revenue_validation(self):
        """RED: Test negative tech_transfer_revenue is rejected."""
        # Arrange
        kpi = DepartmentKPI(
            evaluation_year=2023,
            department='컴퓨터공학과',
            employment_rate=78.5,
            tech_transfer_revenue=-5.0  # Invalid
        )

        # Act & Assert
        with pytest.raises(ValidationError):
            kpi.full_clean()

    def test_evaluation_year_minimum_validation(self):
        """RED: Test evaluation_year must be >= 2000."""
        # Arrange
        kpi = DepartmentKPI(
            evaluation_year=1990,  # Invalid: too old
            department='컴퓨터공학과',
            employment_rate=78.5,
            tech_transfer_revenue=12.3
        )

        # Act & Assert
        with pytest.raises(ValidationError):
            kpi.full_clean()


@pytest.mark.django_db
class TestModelIndexes:
    """Tests for database indexes (performance optimization)."""

    def test_research_project_department_index_exists(self):
        """RED: Verify department index exists on ResearchProject."""
        # This test verifies migration was applied correctly
        indexes = [idx.name for idx in ResearchProject._meta.indexes]
        assert 'idx_rp_dept' in indexes

    def test_research_project_execution_date_index_exists(self):
        """RED: Verify execution_date index exists."""
        indexes = [idx.name for idx in ResearchProject._meta.indexes]
        assert any('execution_date' in idx or 'date' in idx for idx in indexes)

    def test_student_department_index_exists(self):
        """RED: Verify department index exists on Student."""
        indexes = [idx.name for idx in Student._meta.indexes]
        assert 'idx_student_dept' in indexes
