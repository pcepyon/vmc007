"""
Service layer for publication business logic.
Following plan.md Phase 1.2 - Orchestrates repository calls and data aggregation.
"""

from typing import Dict, Any
from django.db.models import Count, Avg, Q
from django.utils import timezone
from django.core.exceptions import ValidationError
from data_ingestion.infrastructure.repositories import PublicationRepository


class PublicationService:
    """
    Service for publication dashboard data.
    Responsibility: Business logic orchestration, aggregation, and validation.
    Following spec.md Section 6 - Service Layer architecture.
    """

    # Whitelist for journal tier validation
    ALLOWED_TIERS = ['all', 'SCIE', 'KCI', '기타']

    def __init__(self, repository: PublicationRepository | None = None):
        """
        Initialize service with optional repository injection.

        Args:
            repository: Optional PublicationRepository for dependency injection.
                       If None, creates a new instance (default behavior).
        """
        self.repository = repository or PublicationRepository()

    def get_distribution(
        self,
        department: str = 'all',
        journal_tier: str = 'all'
    ) -> Dict[str, Any]:
        """
        Get publication distribution aggregated by journal tier.

        Following spec.md Section 6.1 - Service Layer responsibilities.

        Args:
            department: Department filter ('all' or specific department name)
            journal_tier: Journal tier filter ('all', 'SCIE', 'KCI', '기타')

        Returns:
            Dict with keys:
                - total_papers: int (total publication count)
                - avg_impact_factor: float | None (overall average IF, NULL if no IF data)
                - papers_with_if: int (count of papers with non-NULL IF)
                - distribution: list of dicts with tier-level aggregations
                - last_updated: datetime (timestamp of data retrieval)

        Raises:
            ValidationError: If department doesn't exist or journal_tier is invalid
        """
        # Step 1: Validate input parameters
        self._validate_inputs(department, journal_tier)

        # Step 2: Fetch filtered data from repository
        queryset = self.repository.get_publications_by_filter(
            department=department,
            journal_tier=journal_tier
        )

        # Step 3: Aggregate data by journal tier
        distribution = self._aggregate_by_tier(queryset)

        # Step 4: Calculate overall statistics
        total_papers = queryset.count()
        avg_if, papers_with_if = self._calculate_avg_impact_factor(queryset)

        # Step 5: Format response
        return {
            'total_papers': total_papers,
            'avg_impact_factor': round(avg_if, 2) if avg_if is not None else None,
            'papers_with_if': papers_with_if,
            'distribution': list(distribution),
            'last_updated': timezone.now()
        }

    def _validate_inputs(self, department: str, journal_tier: str):
        """
        Validate input parameters.

        Following spec.md Section 10.2 - Input validation requirements.

        Args:
            department: Department filter value
            journal_tier: Journal tier filter value

        Raises:
            ValidationError: If validation fails
        """
        # Validate journal tier (whitelist-based)
        if journal_tier not in self.ALLOWED_TIERS:
            raise ValidationError(
                f"유효하지 않은 저널등급입니다. ('SCIE', 'KCI', '기타', 'all' 중 선택)"
            )

        # Validate department (existence check)
        if department != 'all':
            all_departments = self.repository.get_all_departments()
            if department not in all_departments:
                raise ValidationError(
                    f"존재하지 않는 학과입니다: {department}"
                )

    def _aggregate_by_tier(self, queryset):
        """
        Aggregate publications by journal tier.

        Following spec.md Section 7.1 - Django ORM aggregation.

        Business Rules (BR3):
        - Percentages rounded to 1 decimal place
        - Sum of percentages should be 99.9~100.1% (rounding tolerance)

        Args:
            queryset: Filtered QuerySet of Publication objects

        Returns:
            List of dicts with keys: journal_tier, count, percentage, avg_if
        """
        total_count = queryset.count()

        # Handle empty dataset
        if total_count == 0:
            return []

        # Aggregate by journal tier
        aggregated = queryset.values('journal_tier').annotate(
            count=Count('publication_id'),
            avg_if=Avg('impact_factor', filter=Q(impact_factor__isnull=False))
        ).order_by('-count')  # Sort by count descending

        # Calculate percentages
        result = []
        for item in aggregated:
            percentage = round((item['count'] / total_count) * 100, 1)
            result.append({
                'journal_tier': item['journal_tier'],
                'count': item['count'],
                'percentage': percentage,
                'avg_if': round(item['avg_if'], 2) if item['avg_if'] is not None else None
            })

        return result

    def _calculate_avg_impact_factor(self, queryset):
        """
        Calculate average Impact Factor (excluding NULL values).

        Following spec.md Section 3 - Business Rule BR1:
        - IF가 NULL인 논문은 평균 계산에서 제외
        - papers_with_if 카운트도 반환

        Args:
            queryset: Filtered QuerySet of Publication objects

        Returns:
            tuple: (avg_if: float | None, papers_with_if: int)
        """
        # Filter publications with non-NULL impact factor
        publications_with_if = queryset.filter(impact_factor__isnull=False)
        papers_with_if = publications_with_if.count()

        # Return None if no papers have IF
        if papers_with_if == 0:
            return None, 0

        # Calculate average
        avg_if = publications_with_if.aggregate(
            avg=Avg('impact_factor')
        )['avg']

        return avg_if, papers_with_if
