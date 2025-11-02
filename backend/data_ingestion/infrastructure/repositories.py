"""
Repository layer for data persistence.
Direct Django ORM usage (no abstraction layer for MVP).
"""

import pandas as pd
from typing import Dict, Any
from django.db import transaction
from django.db.models import Sum
from data_ingestion.infrastructure.models import (
    ResearchProject,
    Student,
    Publication,
    DepartmentKPI
)


def save_research_funding_data(dataframe: pd.DataFrame, replace: bool = True) -> Dict[str, Any]:
    """
    Save research funding data to database.

    Args:
        dataframe: Pandas DataFrame with research funding data
        replace: If True, delete all existing data before inserting

    Returns:
        dict with 'rows_inserted' count

    Raises:
        Exception: On database errors (transaction will rollback)
    """
    with transaction.atomic():
        if replace:
            ResearchProject.objects.all().delete()

        if len(dataframe) == 0:
            return {'rows_inserted': 0}

        # Convert DataFrame to list of model instances
        records = [
            ResearchProject(
                execution_id=row['execution_id'],
                department=row['department'],
                total_budget=int(row['total_budget']),
                execution_date=row['execution_date'],
                execution_amount=int(row['execution_amount'])
            )
            for _, row in dataframe.iterrows()
        ]

        # Bulk insert with batching (1000 per batch for performance)
        ResearchProject.objects.bulk_create(records, batch_size=1000)

        return {'rows_inserted': len(records)}


def save_student_data(dataframe: pd.DataFrame, replace: bool = True) -> Dict[str, Any]:
    """
    Save student enrollment data to database.

    Args:
        dataframe: Pandas DataFrame with student data
        replace: If True, delete all existing data before inserting

    Returns:
        dict with 'rows_inserted' count
    """
    with transaction.atomic():
        if replace:
            Student.objects.all().delete()

        if len(dataframe) == 0:
            return {'rows_inserted': 0}

        records = [
            Student(
                student_id=row['student_id'],
                department=row['department'],
                grade=int(row['grade']),
                program_type=row['program_type'],
                enrollment_status=row['enrollment_status']
            )
            for _, row in dataframe.iterrows()
        ]

        Student.objects.bulk_create(records, batch_size=1000)

        return {'rows_inserted': len(records)}


def save_publication_data(dataframe: pd.DataFrame, replace: bool = True) -> Dict[str, Any]:
    """
    Save publication records to database.

    Args:
        dataframe: Pandas DataFrame with publication data
        replace: If True, delete all existing data before inserting

    Returns:
        dict with 'rows_inserted' count
    """
    with transaction.atomic():
        if replace:
            Publication.objects.all().delete()

        if len(dataframe) == 0:
            return {'rows_inserted': 0}

        records = [
            Publication(
                publication_id=row['publication_id'],
                department=row['department'],
                journal_tier=row['journal_tier'],
                impact_factor=row['impact_factor'] if pd.notna(row['impact_factor']) else None
            )
            for _, row in dataframe.iterrows()
        ]

        Publication.objects.bulk_create(records, batch_size=1000)

        return {'rows_inserted': len(records)}


def save_department_kpi_data(dataframe: pd.DataFrame, replace: bool = True) -> Dict[str, Any]:
    """
    Save department KPI metrics to database.

    Args:
        dataframe: Pandas DataFrame with KPI data
        replace: If True, delete all existing data before inserting

    Returns:
        dict with 'rows_inserted' count

    Note:
        Composite unique constraint on (evaluation_year, department).
        If replace=False and duplicate exists, IntegrityError will be raised.
    """
    with transaction.atomic():
        if replace:
            DepartmentKPI.objects.all().delete()

        if len(dataframe) == 0:
            return {'rows_inserted': 0}

        records = [
            DepartmentKPI(
                evaluation_year=int(row['evaluation_year']),
                department=row['department'],
                employment_rate=float(row['employment_rate']),
                tech_transfer_revenue=float(row['tech_transfer_revenue'])
            )
            for _, row in dataframe.iterrows()
        ]

        DepartmentKPI.objects.bulk_create(records, batch_size=1000)

        return {'rows_inserted': len(records)}


class StudentRepository:
    """
    Repository for Student data access.
    Responsibility: Database query operations for student dashboard.
    Following plan.md Phase 1 - Infrastructure Layer (Data Access).
    """

    def get_students_by_filter(self, department: str = 'all', status: str = 'all'):
        """
        Get students filtered by department and enrollment status.

        Args:
            department: Department filter ('all' or specific department name)
            status: Enrollment status filter ('all', '재학', '휴학', '졸업')

        Returns:
            QuerySet of Student objects matching the filters
        """
        queryset = Student.objects.all()

        # Apply department filter
        if department != 'all':
            queryset = queryset.filter(department=department)

        # Apply enrollment status filter
        if status != 'all':
            queryset = queryset.filter(enrollment_status=status)

        return queryset

    def get_all_departments(self) -> list[str]:
        """
        Get list of all unique departments (for dropdown population).

        Returns:
            List of distinct department names (alphabetically sorted)
        """
        departments = Student.objects.values_list('department', flat=True).distinct()
        return list(departments)


class ResearchFundingRepository:
    """
    Repository for ResearchProject data access.
    Responsibility: Database CRUD operations and aggregation queries.
    Following plan.md Phase 1.2 - Direct Django ORM usage (MVP simplification).
    """

    def get_current_balance(self, department: str | None = None) -> int:
        """
        Calculate current balance: SUM(total_budget) - SUM(execution_amount).

        Args:
            department: Optional department filter. If None, calculate for all departments.

        Returns:
            Current balance in Korean Won (원). Returns 0 if no data.
        """
        queryset = ResearchProject.objects.all()

        if department and department != "all":
            queryset = queryset.filter(department=department)

        result = queryset.aggregate(
            total_budget=Sum('total_budget'),
            total_execution=Sum('execution_amount')
        )

        total_budget = result['total_budget'] or 0
        total_execution = result['total_execution'] or 0
        current_balance = total_budget - total_execution

        return current_balance

    def get_monthly_trend(
        self,
        department: str | None = None,
        period: str = 'latest'
    ) -> list[dict[str, Any]]:
        """
        Get monthly execution trend with cumulative balance.

        Args:
            department: Optional department filter
            period: Time period filter ('latest', '1year', '3years')

        Returns:
            List of dicts with keys: month (str), execution (int), balance (int)
        """
        from django.utils import timezone
        from datetime import timedelta
        from django.db.models.functions import TruncMonth

        queryset = ResearchProject.objects.all()

        # Apply department filter
        if department and department != "all":
            queryset = queryset.filter(department=department)

        # Apply period filter
        if period == "1year":
            one_year_ago = timezone.now() - timedelta(days=365)
            queryset = queryset.filter(execution_date__gte=one_year_ago)
        elif period == "3years":
            three_years_ago = timezone.now() - timedelta(days=1095)
            queryset = queryset.filter(execution_date__gte=three_years_ago)

        # Calculate total budget (for balance calculation)
        # MVP simplification: sum all total_budget values
        # Note: This assumes each execution_id has unique total_budget
        total_budget_result = queryset.aggregate(total=Sum('total_budget'))
        total_budget = total_budget_result['total'] or 0

        # Monthly execution aggregation
        trend_data = queryset.annotate(
            month=TruncMonth('execution_date')
        ).values('month').annotate(
            monthly_execution=Sum('execution_amount')
        ).order_by('month')

        # Calculate cumulative balance
        cumulative_execution = 0
        result = []

        for item in trend_data:
            monthly_execution = item['monthly_execution']
            cumulative_execution += monthly_execution

            # Balance = Total Budget - Cumulative Execution
            balance = total_budget - cumulative_execution

            result.append({
                'month': item['month'].strftime('%Y-%m'),
                'balance': balance,
                'execution': monthly_execution
            })

        return result


class PublicationRepository:
    """
    Repository for Publication data access.
    Responsibility: Database query operations for publication dashboard.
    Following plan.md Phase 1.1 - Infrastructure Layer (Data Access).
    """

    def get_publications_by_filter(self, department: str = 'all', journal_tier: str = 'all'):
        """
        Get publications filtered by department and journal tier.

        Args:
            department: Department filter ('all' or specific department name)
            journal_tier: Journal tier filter ('all', 'SCIE', 'KCI', '기타')

        Returns:
            QuerySet of Publication objects matching the filters
        """
        queryset = Publication.objects.all()

        # Apply department filter
        if department != 'all':
            queryset = queryset.filter(department=department)

        # Apply journal tier filter
        if journal_tier != 'all':
            queryset = queryset.filter(journal_tier=journal_tier)

        return queryset

    def get_all_departments(self) -> list[str]:
        """
        Get list of all unique departments (for dropdown population).

        Returns:
            List of distinct department names
        """
        departments = Publication.objects.values_list('department', flat=True).distinct()
        return list(departments)


class KPIRepository:
    """
    Repository for DepartmentKPI data access.
    Responsibility: Database query operations for department KPI dashboard.
    Following plan.md Phase 3.2 - Repository Layer (Data Access).
    """

    def find_by_department_and_year(
        self,
        department: str,
        start_year: int,
        end_year: int
    ):
        """
        Get KPI data filtered by department and year range.

        Args:
            department: Department filter ('all' or specific department name)
            start_year: Start year (inclusive)
            end_year: End year (inclusive)

        Returns:
            QuerySet of DepartmentKPI objects matching the filters,
            ordered by evaluation_year ascending
        """
        # Base query: filter by year range
        queryset = DepartmentKPI.objects.filter(
            evaluation_year__gte=start_year,
            evaluation_year__lte=end_year
        )

        # Apply department filter
        if department != 'all':
            queryset = queryset.filter(department=department)

        # Order by year ascending
        return queryset.order_by('evaluation_year')

    def find_by_year(self, year: int):
        """
        Get KPI data for a specific year.

        Args:
            year: Evaluation year

        Returns:
            QuerySet of DepartmentKPI objects for the specified year
        """
        return DepartmentKPI.objects.filter(evaluation_year=year)

    def find_all(self):
        """
        Get all KPI data.

        Returns:
            QuerySet of all DepartmentKPI objects
        """
        return DepartmentKPI.objects.all()

    def get_all_departments(self) -> list[str]:
        """
        Get list of all unique departments (for dropdown population).

        Returns:
            List of distinct department names
        """
        departments = DepartmentKPI.objects.values_list('department', flat=True).distinct()
        return list(departments)
