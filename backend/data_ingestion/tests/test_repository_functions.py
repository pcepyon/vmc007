"""
Integration tests for repository save functions.
Testing database persistence with Django ORM.

Following test-plan.md:
- Integration tests (20%)
- DB access allowed with @pytest.mark.django_db
- Test all save_*_data functions
"""

import pytest
import pandas as pd
from data_ingestion.infrastructure.repositories import (
    save_research_funding_data,
    save_student_data,
    save_publication_data,
    save_department_kpi_data
)
from data_ingestion.infrastructure.models import (
    ResearchProject,
    Student,
    Publication,
    DepartmentKPI
)


@pytest.mark.integration
@pytest.mark.django_db
class TestSaveResearchFundingData:
    """Test save_research_funding_data repository function."""

    def test_save_research_funding_success(self):
        """Save research funding data should insert records to database."""
        # Arrange
        df = pd.DataFrame({
            'execution_id': ['R001', 'R002'],
            'department': ['컴퓨터공학과', '전자공학과'],
            'total_budget': [1000000, 2000000],
            'execution_date': ['2025-01-01', '2025-01-02'],
            'execution_amount': [500000, 1000000]
        })

        # Act
        result = save_research_funding_data(df, replace=True)

        # Assert
        assert result['rows_inserted'] == 2
        assert ResearchProject.objects.count() == 2

        # Verify data
        project1 = ResearchProject.objects.get(execution_id='R001')
        assert project1.department == '컴퓨터공학과'
        assert project1.total_budget == 1000000

    def test_save_empty_dataframe_returns_zero(self):
        """Save empty DataFrame should return 0 rows inserted."""
        # Arrange
        df = pd.DataFrame(columns=['execution_id', 'department', 'total_budget', 'execution_date', 'execution_amount'])

        # Act
        result = save_research_funding_data(df, replace=True)

        # Assert
        assert result['rows_inserted'] == 0
        assert ResearchProject.objects.count() == 0

    def test_save_with_replace_true_deletes_existing_data(self):
        """Save with replace=True should delete all existing records."""
        # Arrange - Create existing record
        ResearchProject.objects.create(
            execution_id='OLD001',
            department='기계공학과',
            total_budget=5000000,
            execution_date='2024-12-31',
            execution_amount=2500000
        )
        assert ResearchProject.objects.count() == 1

        df = pd.DataFrame({
            'execution_id': ['R001'],
            'department': ['컴퓨터공학과'],
            'total_budget': [1000000],
            'execution_date': ['2025-01-01'],
            'execution_amount': [500000]
        })

        # Act
        result = save_research_funding_data(df, replace=True)

        # Assert
        assert result['rows_inserted'] == 1
        assert ResearchProject.objects.count() == 1
        assert not ResearchProject.objects.filter(execution_id='OLD001').exists()

    def test_save_bulk_creates_with_batch_size(self):
        """Save should use bulk_create for performance."""
        # Arrange - Create large dataset
        df = pd.DataFrame({
            'execution_id': [f'R{i:04d}' for i in range(100)],
            'department': ['컴퓨터공학과'] * 100,
            'total_budget': [1000000] * 100,
            'execution_date': ['2025-01-01'] * 100,
            'execution_amount': [500000] * 100
        })

        # Act
        result = save_research_funding_data(df, replace=True)

        # Assert
        assert result['rows_inserted'] == 100
        assert ResearchProject.objects.count() == 100


@pytest.mark.integration
@pytest.mark.django_db
class TestSaveStudentData:
    """Test save_student_data repository function."""

    def test_save_student_data_success(self):
        """Save student data should insert records to database."""
        # Arrange
        df = pd.DataFrame({
            'student_id': ['2025001', '2025002'],
            'department': ['컴퓨터공학과', '전자공학과'],
            'grade': [2, 1],
            'program_type': ['학사', '석사'],
            'enrollment_status': ['재학', '재학']
        })

        # Act
        result = save_student_data(df, replace=True)

        # Assert
        assert result['rows_inserted'] == 2
        assert Student.objects.count() == 2

        # Verify data
        student1 = Student.objects.get(student_id='2025001')
        assert student1.department == '컴퓨터공학과'
        assert student1.grade == 2
        assert student1.program_type == '학사'

    def test_save_empty_student_dataframe(self):
        """Save empty student DataFrame should return 0."""
        # Arrange
        df = pd.DataFrame(columns=['student_id', 'department', 'grade', 'program_type', 'enrollment_status'])

        # Act
        result = save_student_data(df, replace=True)

        # Assert
        assert result['rows_inserted'] == 0
        assert Student.objects.count() == 0

    def test_save_students_with_replace_deletes_existing(self):
        """Save students with replace=True should delete existing records."""
        # Arrange
        Student.objects.create(
            student_id='OLD001',
            department='기계공학과',
            grade=4,
            program_type='학사',
            enrollment_status='졸업'
        )

        df = pd.DataFrame({
            'student_id': ['2025001'],
            'department': ['컴퓨터공학과'],
            'grade': [1],
            'program_type': ['학사'],
            'enrollment_status': ['재학']
        })

        # Act
        result = save_student_data(df, replace=True)

        # Assert
        assert result['rows_inserted'] == 1
        assert Student.objects.count() == 1
        assert not Student.objects.filter(student_id='OLD001').exists()

    def test_save_students_handles_all_program_types(self):
        """Save should handle all valid program types."""
        # Arrange
        df = pd.DataFrame({
            'student_id': ['2025001', '2025002', '2025003'],
            'department': ['컴퓨터공학과'] * 3,
            'grade': [1, 1, 1],
            'program_type': ['학사', '석사', '박사'],
            'enrollment_status': ['재학'] * 3
        })

        # Act
        result = save_student_data(df, replace=True)

        # Assert
        assert result['rows_inserted'] == 3
        assert Student.objects.filter(program_type='학사').count() == 1
        assert Student.objects.filter(program_type='석사').count() == 1
        assert Student.objects.filter(program_type='박사').count() == 1


@pytest.mark.integration
@pytest.mark.django_db
class TestSavePublicationData:
    """Test save_publication_data repository function."""

    def test_save_publication_data_success(self):
        """Save publication data should insert records to database."""
        # Arrange
        df = pd.DataFrame({
            'publication_id': ['P001', 'P002'],
            'department': ['컴퓨터공학과', '전자공학과'],
            'journal_tier': ['SCIE', 'KCI'],
            'impact_factor': [3.5, None]
        })

        # Act
        result = save_publication_data(df, replace=True)

        # Assert
        assert result['rows_inserted'] == 2
        assert Publication.objects.count() == 2

        # Verify data
        pub1 = Publication.objects.get(publication_id='P001')
        assert pub1.journal_tier == 'SCIE'
        assert pub1.impact_factor == 3.5

        pub2 = Publication.objects.get(publication_id='P002')
        assert pub2.impact_factor is None

    def test_save_publication_handles_null_impact_factor(self):
        """Save should handle null/NaN impact factor values."""
        # Arrange
        df = pd.DataFrame({
            'publication_id': ['P001', 'P002', 'P003'],
            'department': ['컴퓨터공학과'] * 3,
            'journal_tier': ['SCIE', 'KCI', '기타'],
            'impact_factor': [3.5, pd.NA, None]
        })

        # Act
        result = save_publication_data(df, replace=True)

        # Assert
        assert result['rows_inserted'] == 3
        pub1 = Publication.objects.get(publication_id='P001')
        assert pub1.impact_factor == 3.5

        pub2 = Publication.objects.get(publication_id='P002')
        assert pub2.impact_factor is None

    def test_save_empty_publication_dataframe(self):
        """Save empty publication DataFrame should return 0."""
        # Arrange
        df = pd.DataFrame(columns=['publication_id', 'department', 'journal_tier', 'impact_factor'])

        # Act
        result = save_publication_data(df, replace=True)

        # Assert
        assert result['rows_inserted'] == 0
        assert Publication.objects.count() == 0

    def test_save_publications_with_replace_deletes_existing(self):
        """Save publications with replace=True should delete existing records."""
        # Arrange
        Publication.objects.create(
            publication_id='OLD001',
            department='기계공학과',
            journal_tier='SCIE',
            impact_factor=2.0
        )

        df = pd.DataFrame({
            'publication_id': ['P001'],
            'department': ['컴퓨터공학과'],
            'journal_tier': ['KCI'],
            'impact_factor': [None]
        })

        # Act
        result = save_publication_data(df, replace=True)

        # Assert
        assert result['rows_inserted'] == 1
        assert Publication.objects.count() == 1
        assert not Publication.objects.filter(publication_id='OLD001').exists()


@pytest.mark.integration
@pytest.mark.django_db
class TestSaveDepartmentKPIData:
    """Test save_department_kpi_data repository function."""

    def test_save_kpi_data_success(self):
        """Save KPI data should insert records to database."""
        # Arrange
        df = pd.DataFrame({
            'evaluation_year': [2025, 2024],
            'department': ['컴퓨터공학과', '전자공학과'],
            'employment_rate': [85.5, 90.0],
            'tech_transfer_revenue': [12.3, 8.5]
        })

        # Act
        result = save_department_kpi_data(df, replace=True)

        # Assert
        assert result['rows_inserted'] == 2
        assert DepartmentKPI.objects.count() == 2

        # Verify data
        kpi1 = DepartmentKPI.objects.get(evaluation_year=2025, department='컴퓨터공학과')
        assert kpi1.employment_rate == 85.5
        assert kpi1.tech_transfer_revenue == 12.3

    def test_save_empty_kpi_dataframe(self):
        """Save empty KPI DataFrame should return 0."""
        # Arrange
        df = pd.DataFrame(columns=['evaluation_year', 'department', 'employment_rate', 'tech_transfer_revenue'])

        # Act
        result = save_department_kpi_data(df, replace=True)

        # Assert
        assert result['rows_inserted'] == 0
        assert DepartmentKPI.objects.count() == 0

    def test_save_kpi_with_replace_deletes_existing(self):
        """Save KPI with replace=True should delete existing records."""
        # Arrange
        DepartmentKPI.objects.create(
            evaluation_year=2023,
            department='기계공학과',
            employment_rate=80.0,
            tech_transfer_revenue=5.0
        )

        df = pd.DataFrame({
            'evaluation_year': [2025],
            'department': ['컴퓨터공학과'],
            'employment_rate': [85.5],
            'tech_transfer_revenue': [12.3]
        })

        # Act
        result = save_department_kpi_data(df, replace=True)

        # Assert
        assert result['rows_inserted'] == 1
        assert DepartmentKPI.objects.count() == 1
        assert not DepartmentKPI.objects.filter(evaluation_year=2023).exists()

    def test_save_kpi_handles_float_conversion(self):
        """Save KPI should properly convert numeric types."""
        # Arrange
        df = pd.DataFrame({
            'evaluation_year': [2025],
            'department': ['컴퓨터공학과'],
            'employment_rate': [85.5],
            'tech_transfer_revenue': [12.3]
        })

        # Act
        result = save_department_kpi_data(df, replace=True)

        # Assert
        assert result['rows_inserted'] == 1
        kpi = DepartmentKPI.objects.first()
        assert isinstance(kpi.evaluation_year, int)
        assert isinstance(kpi.employment_rate, float)
        assert isinstance(kpi.tech_transfer_revenue, float)

    def test_save_multiple_years_same_department(self):
        """Save should handle multiple years for same department."""
        # Arrange
        df = pd.DataFrame({
            'evaluation_year': [2025, 2024, 2023],
            'department': ['컴퓨터공학과'] * 3,
            'employment_rate': [85.5, 80.0, 75.0],
            'tech_transfer_revenue': [12.3, 10.0, 8.0]
        })

        # Act
        result = save_department_kpi_data(df, replace=True)

        # Assert
        assert result['rows_inserted'] == 3
        assert DepartmentKPI.objects.filter(department='컴퓨터공학과').count() == 3
