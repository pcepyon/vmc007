"""
Service layer for research funding business logic.
Following plan.md Phase 2 - Orchestrates repository calls and data formatting.
"""

from typing import Dict, Any
from data_ingestion.infrastructure.repositories import ResearchFundingRepository


class ResearchFundingService:
    """
    Service for research funding dashboard data.
    Responsibility: Business logic orchestration, data formatting, and transformations.
    """

    def __init__(self, repository: ResearchFundingRepository | None = None):
        """
        Initialize service with optional repository injection.

        Args:
            repository: Optional ResearchFundingRepository for dependency injection.
                       If None, creates a new instance (default behavior).
        """
        self.repository = repository or ResearchFundingRepository()

    def get_dashboard_data(
        self,
        department: str = 'all',
        period: str = 'latest'
    ) -> Dict[str, Any]:
        """
        Get formatted dashboard data for research funding.

        Args:
            department: Department filter ('all' or specific department name)
            period: Time period filter ('latest', '1year', '3years')

        Returns:
            Dict with keys:
                - current_balance: int (원)
                - current_balance_formatted: str (억원)
                - trend: list of formatted monthly trend data
        """
        # Fetch raw data from repository
        current_balance = self.repository.get_current_balance(department=department)
        monthly_trend = self.repository.get_monthly_trend(
            department=department,
            period=period
        )

        # Handle None values defensively
        if current_balance is None:
            current_balance = 0
        if monthly_trend is None:
            monthly_trend = []

        # Format data
        return {
            'current_balance': current_balance,
            'current_balance_formatted': self._format_currency(current_balance),
            'trend': [
                {
                    'month': item['month'],
                    'month_formatted': self._format_month(item['month']),
                    'balance': item['balance'],
                    'balance_formatted': self._format_currency(item['balance']),
                    'execution': item['execution'],
                    'execution_formatted': self._format_currency(item['execution'])
                }
                for item in monthly_trend
            ]
        }

    def _format_currency(self, amount: int) -> str:
        """
        Format amount in Korean Won to 억원 (100 million won units).

        Args:
            amount: Amount in won (원)

        Returns:
            Formatted string like "15.3억원"
        """
        billion_units = amount / 100_000_000
        return f"{billion_units:.1f}억원"

    def _format_month(self, month_str: str) -> str:
        """
        Format month string from YYYY-MM to Korean format.

        Args:
            month_str: Month string in 'YYYY-MM' format

        Returns:
            Formatted string like "2024년 1월"
        """
        year, month = month_str.split('-')
        return f"{year}년 {int(month)}월"
