"""
KPIService - Business logic for department KPI dashboard.
Following plan.md Phase 3.3 - Service Layer (Business Logic).
"""

from datetime import datetime
from typing import Dict, List, Any
from django.db.models import Avg, Sum
from data_ingestion.infrastructure.repositories import KPIRepository


class KPIService:
    """
    Service class for department KPI data aggregation and business logic.

    Responsibilities:
    - Year range validation (business rules)
    - KPI data aggregation
    - Response formatting
    """

    def __init__(self):
        """Initialize service with repository dependency."""
        self.repository = KPIRepository()

    def get_kpi_trend(
        self,
        department: str,
        start_year: int,
        end_year: int
    ) -> Dict[str, Any]:
        """
        Get department KPI trend data with aggregation.

        Args:
            department: Department filter ('all' or specific department name)
            start_year: Start year (inclusive)
            end_year: End year (inclusive)

        Returns:
            Dictionary with 'status', 'data', and 'meta' keys

        Raises:
            ValueError: If year range validation fails
        """
        # 1. Validate year range (business rules)
        self._validate_year_range(start_year, end_year)

        # 2. Fetch data from repository
        queryset = self.repository.find_by_department_and_year(
            department=department,
            start_year=start_year,
            end_year=end_year
        )

        # 3. Aggregate by year
        trend_data = queryset.values('evaluation_year').annotate(
            avg_employment_rate=Avg('employment_rate'),
            total_tech_income=Sum('tech_transfer_revenue')
        ).order_by('evaluation_year')

        # 4. Calculate overall average employment rate
        overall_avg = queryset.aggregate(avg=Avg('employment_rate'))['avg']

        # Round to one decimal place if not None
        if overall_avg is not None:
            overall_avg = round(overall_avg, 1)

        # 5. Format response
        return {
            'status': 'success',
            'data': list(trend_data),
            'meta': {
                'department_filter': department,
                'year_range': f'{start_year}-{end_year}',
                'overall_avg_employment_rate': overall_avg,
                'total_count': len(trend_data)
            }
        }

    def _validate_year_range(self, start_year: int, end_year: int) -> None:
        """
        Validate year range according to business rules.

        Business Rules:
        1. start_year <= end_year
        2. Year range cannot exceed 20 years
        3. end_year cannot be more than current_year + 1
        4. start_year must be >= 2000

        Args:
            start_year: Start year
            end_year: End year

        Raises:
            ValueError: If any business rule is violated
        """
        current_year = datetime.now().year

        # Rule 1: start_year <= end_year
        if start_year > end_year:
            raise ValueError('시작 년도는 종료 년도보다 작거나 같아야 합니다.')

        # Rule 2: Year range <= 20 years
        if end_year - start_year > 20:
            raise ValueError('년도 범위는 최대 20년까지 조회 가능합니다.')

        # Rule 3: No future years (allow current_year + 1 for early next year data)
        if end_year > current_year + 1:
            raise ValueError(f'종료 년도는 {current_year + 1}을 초과할 수 없습니다.')

        # Rule 4: Minimum year is 2000
        if start_year < 2000:
            raise ValueError('시작 년도는 2000년 이후여야 합니다.')
