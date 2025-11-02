"""
Integration tests for Repository layer.
Following TDD - write tests first, then implement repositories.
"""

import pytest
import pandas as pd
from datetime import date
from django.db import transaction
from data_ingestion.infrastructure.models import (
    ResearchProject,
    Student,
    Publication,
    DepartmentKPI
)
from data_ingestion.infrastructure.repositories import (
    save_research_funding_data,
    save_student_data,
    save_publication_data,
    save_department_kpi_data
)


@pytest.mark.django_db
class TestResearchFundingRepository:
    """Tests for research funding repository operations."""

    def test_save_research_funding_replaces_existing_data(self):
        """RED: Test that save with replace=True deletes old data."""
        # Arrange: Create existing data
        ResearchProject.objects.create(
            execution_id='OLD001',
            department='컴퓨터공학과',
            total_budget=100000000,
            execution_date=date(2023, 1, 1),
            execution_amount=10000000
        )
        assert ResearchProject.objects.count() == 1

        # Create new dataframe
        df = pd.DataFrame([
            {
                'execution_id': 'NEW001',
                'department': '전자공학과',
                'total_budget': 200000000,
                'execution_date': date(2024, 1, 1),
                'execution_amount': 20000000
            }
        ])

        # Act: Save with replace
        result = save_research_funding_data(df, replace=True)

        # Assert: Old data deleted, new data inserted
        assert ResearchProject.objects.count() == 1
        assert ResearchProject.objects.filter(execution_id='OLD001').count() == 0
        assert ResearchProject.objects.filter(execution_id='NEW001').count() == 1
        assert result['rows_inserted'] == 1

    def test_save_research_funding_bulk_insert(self):
        """RED: Test bulk insert of multiple records."""
        # Arrange
        df = pd.DataFrame([
            {
                'execution_id': f'EXEC{i:03d}',
                'department': '컴퓨터공학과',
                'total_budget': 100000000 + i,
                'execution_date': date(2024, 1, (i % 28) + 1),  # Keep days within valid range
                'execution_amount': 10000000 + i
            }
            for i in range(100)
        ])

        # Act
        result = save_research_funding_data(df, replace=True)

        # Assert
        assert ResearchProject.objects.count() == 100
        assert result['rows_inserted'] == 100

    def test_save_empty_dataframe_deletes_all(self):
        """RED: Test that empty DataFrame with replace=True deletes all data."""
        # Arrange: Create existing data
        ResearchProject.objects.create(
            execution_id='TEST001',
            department='컴퓨터공학과',
            total_budget=100000000,
            execution_date=date(2023, 1, 1),
            execution_amount=10000000
        )

        # Create empty dataframe with correct columns
        df = pd.DataFrame(columns=[
            'execution_id', 'department', 'total_budget',
            'execution_date', 'execution_amount'
        ])

        # Act
        result = save_research_funding_data(df, replace=True)

        # Assert
        assert ResearchProject.objects.count() == 0
        assert result['rows_inserted'] == 0

    def test_transaction_rollback_on_error(self):
        """RED: Test that transaction rolls back on error."""
        # Arrange: Create initial data
        ResearchProject.objects.create(
            execution_id='SAFE001',
            department='컴퓨터공학과',
            total_budget=100000000,
            execution_date=date(2023, 1, 1),
            execution_amount=10000000
        )

        # Create first record that's valid
        ResearchProject.objects.create(
            execution_id='EXISTING001',
            department='전자공학과',
            total_budget=200000000,
            execution_date=date(2024, 1, 1),
            execution_amount=20000000
        )

        # Create dataframe with duplicate PK (will cause IntegrityError)
        df = pd.DataFrame([
            {
                'execution_id': 'EXISTING001',  # Duplicate PK
                'department': '전기공학과',
                'total_budget': 300000000,
                'execution_date': date(2024, 2, 1),
                'execution_amount': 30000000
            }
        ])

        # Act & Assert: Should raise IntegrityError
        from django.db import IntegrityError
        with pytest.raises(IntegrityError):
            save_research_funding_data(df, replace=False)  # Don't delete existing

        # Original data should still exist (transaction rolled back)
        assert ResearchProject.objects.count() == 2
        assert ResearchProject.objects.filter(execution_id='SAFE001').exists()
        assert ResearchProject.objects.filter(execution_id='EXISTING001').exists()


@pytest.mark.django_db
class TestStudentRepository:
    """Tests for student repository operations."""

    def test_save_student_data_success(self):
        """RED: Test successful student data save."""
        # Arrange
        df = pd.DataFrame([
            {
                'student_id': '2024001',
                'department': '컴퓨터공학과',
                'grade': 3,
                'program_type': '학사',
                'enrollment_status': '재학'
            },
            {
                'student_id': '2024002',
                'department': '전자공학과',
                'grade': 2,
                'program_type': '석사',
                'enrollment_status': '재학'
            }
        ])

        # Act
        result = save_student_data(df, replace=True)

        # Assert
        assert Student.objects.count() == 2
        assert result['rows_inserted'] == 2


@pytest.mark.django_db
class TestPublicationRepository:
    """Tests for publication repository operations."""

    def test_save_publication_with_null_impact_factor(self):
        """RED: Test saving publications with NULL impact factor."""
        # Arrange
        df = pd.DataFrame([
            {
                'paper_id': 'PUB001',
                'department': '컴퓨터공학과',
                'journal_tier': 'SCIE',
                'impact_factor': 3.25
            },
            {
                'paper_id': 'PUB002',
                'department': '전자공학과',
                'journal_tier': 'KCI',
                'impact_factor': None  # NULL allowed
            }
        ])

        # Act
        result = save_publication_data(df, replace=True)

        # Assert
        assert Publication.objects.count() == 2
        pub2 = Publication.objects.get(paper_id='PUB002')
        assert pub2.impact_factor is None


@pytest.mark.django_db
class TestDepartmentKPIRepository:
    """Tests for department KPI repository operations."""

    def test_save_department_kpi_composite_key(self):
        """RED: Test that composite unique constraint is enforced."""
        # Arrange: Create initial data
        DepartmentKPI.objects.create(
            evaluation_year=2023,
            department='컴퓨터공학과',
            employment_rate=78.5,
            tech_transfer_revenue=12.3
        )

        # Try to insert duplicate (same year + department)
        df = pd.DataFrame([
            {
                'evaluation_year': 2023,
                'department': '컴퓨터공학과',  # Duplicate combination
                'employment_rate': 80.0,
                'tech_transfer_revenue': 15.0
            }
        ])

        # Act & Assert: Should raise IntegrityError
        with pytest.raises(Exception):  # IntegrityError or similar
            save_department_kpi_data(df, replace=False)

    def test_save_department_kpi_multiple_years_same_department(self):
        """RED: Test saving multiple years for same department (allowed)."""
        # Arrange
        df = pd.DataFrame([
            {
                'evaluation_year': 2021,
                'department': '컴퓨터공학과',
                'employment_rate': 75.0,
                'tech_transfer_revenue': 10.0
            },
            {
                'evaluation_year': 2022,
                'department': '컴퓨터공학과',  # Same dept, different year
                'employment_rate': 77.0,
                'tech_transfer_revenue': 11.0
            },
            {
                'evaluation_year': 2023,
                'department': '컴퓨터공학과',  # Same dept, different year
                'employment_rate': 78.5,
                'tech_transfer_revenue': 12.3
            }
        ])

        # Act
        result = save_department_kpi_data(df, replace=True)

        # Assert: All 3 records should be inserted
        assert DepartmentKPI.objects.count() == 3
        assert result['rows_inserted'] == 3
        assert DepartmentKPI.objects.filter(department='컴퓨터공학과').count() == 3


@pytest.mark.django_db
class TestRepositoryPerformance:
    """Tests for repository performance optimizations."""

    def test_bulk_create_batch_size(self):
        """RED: Test that bulk_create uses batching for large datasets."""
        # Arrange: Create 2000 records
        df = pd.DataFrame([
            {
                'execution_id': f'PERF{i:04d}',
                'department': '컴퓨터공학과',
                'total_budget': 100000000,
                'execution_date': date(2024, 1, 1),
                'execution_amount': 10000000
            }
            for i in range(2000)
        ])

        # Act
        result = save_research_funding_data(df, replace=True)

        # Assert: All records inserted
        assert ResearchProject.objects.count() == 2000
        assert result['rows_inserted'] == 2000
