"""
StudentDashboardService - Business logic for student dashboard.
Following plan.md Phase 2 - Service Layer (Business Logic).

Responsibilities:
- Input validation (department existence, status whitelist)
- Data aggregation by department and program_type
- Business rules enforcement (sorting by total students descending)
- Response data structuring

Following CLAUDE.md architecture: Service layer orchestrates business logic.
"""

from typing import Any, Dict, List
from django.core.exceptions import ValidationError
from django.db.models import Q, Count, QuerySet
from django.utils import timezone
from data_ingestion.infrastructure.repositories import StudentRepository


class StudentDashboardService:
    """
    Service for student dashboard data retrieval and aggregation.

    Business Rules:
    - Default enrollment status filter: '재학' (enrolled students)
    - Department sorting: Descending by total student count
    - Program type aggregation: 학사, 석사, 박사 (0 if none)
    """

    # Whitelist for enrollment status validation
    ALLOWED_STATUSES = ['all', '재학', '휴학', '졸업']

    def __init__(self, repository: StudentRepository = None):
        """
        Initialize service with repository dependency.

        Args:
            repository: StudentRepository instance. If None, creates default instance.
        """
        self.repository = repository or StudentRepository()

    def get_student_dashboard_data(
        self,
        department: str = 'all',
        status: str = '재학'
    ) -> Dict[str, Any]:
        """
        Main service method: Get student dashboard data with filters.

        Args:
            department: Department filter ('all' or specific department name)
            status: Enrollment status filter ('all', '재학', '휴학', '졸업')

        Returns:
            dict with keys:
                - total_students (int): Total count of filtered students
                - by_department (list): List of dicts with department aggregation
                - updated_at (datetime): Current timestamp

        Raises:
            ValidationError: If inputs are invalid

        Business Logic:
        1. Validate inputs (department existence, status whitelist)
        2. Query repository with filters
        3. Aggregate by department and program_type
        4. Return structured response
        """
        # Step 1: Input validation
        self._validate_inputs(department, status)

        # Step 2: Repository query
        students = self.repository.get_students_by_filter(department, status)

        # Step 3: Aggregation
        by_department = self._aggregate_by_department(students)
        total_students = students.count()

        # Step 4: Response structure
        return {
            'total_students': total_students,
            'by_department': by_department,
            'updated_at': timezone.now()
        }

    def _validate_inputs(self, department: str, status: str) -> None:
        """
        Validate input parameters.

        Args:
            department: Department name to validate
            status: Enrollment status to validate

        Raises:
            ValidationError: If inputs are invalid

        Validation Rules:
        - status must be in ALLOWED_STATUSES whitelist
        - department (if not 'all') must exist in database
        """
        # Validate enrollment status (whitelist)
        if status not in self.ALLOWED_STATUSES:
            raise ValidationError(
                f"유효하지 않은 학적상태: {status}. "
                f"허용된 값: {', '.join(self.ALLOWED_STATUSES)}"
            )

        # Validate department existence (if specific department)
        if department != 'all':
            valid_departments = self.repository.get_all_departments()
            if department not in valid_departments:
                raise ValidationError(f"존재하지 않는 학과: {department}")

    def _aggregate_by_department(self, queryset: QuerySet) -> List[Dict[str, Any]]:
        """
        Aggregate students by department and program_type.

        Args:
            queryset: QuerySet of Student objects

        Returns:
            List of dicts with structure:
            [
                {
                    'department': '컴퓨터공학과',
                    '학사': 120,
                    '석사': 35,
                    '박사': 12,
                    'total': 167
                },
                ...
            ]

        Business Rules:
        - Count by program_type (학사, 석사, 박사)
        - Missing program types default to 0
        - Sort by total students descending (spec.md Section 9 - Business Rule 4)

        Implementation:
        - Uses Django ORM annotate with conditional aggregation
        - Single database query for efficiency
        """
        aggregated = queryset.values('department').annotate(
            학사=Count('student_id', filter=Q(program_type='학사')),
            석사=Count('student_id', filter=Q(program_type='석사')),
            박사=Count('student_id', filter=Q(program_type='박사')),
            total=Count('student_id')
        ).order_by('-total')  # Business Rule 4: Descending order by student count

        return list(aggregated)
