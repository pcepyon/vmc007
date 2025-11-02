"""
Pure Python domain entities - infrastructure independent.
These dataclasses represent business concepts without DB coupling.
"""

from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class ResearchFunding:
    """Research funding execution entity."""
    execution_id: str
    department: str
    total_budget: int
    execution_date: date
    execution_amount: int

    def __post_init__(self):
        """Validate business rules."""
        if self.total_budget < 0:
            raise ValueError("Total budget cannot be negative")
        if self.execution_amount < 0:
            raise ValueError("Execution amount cannot be negative")
        if self.execution_amount > self.total_budget:
            raise ValueError("Execution amount cannot exceed total budget")


@dataclass
class Student:
    """Student enrollment entity."""
    student_id: str
    department: str
    grade: int
    program_type: str  # 학사/석사/박사
    enrollment_status: str  # 재학/휴학/졸업

    VALID_PROGRAM_TYPES = ['학사', '석사', '박사']
    VALID_ENROLLMENT_STATUSES = ['재학', '휴학', '졸업']

    def __post_init__(self):
        """Validate business rules."""
        if self.grade < 1 or self.grade > 4:
            raise ValueError("Grade must be between 1 and 4")
        if self.program_type not in self.VALID_PROGRAM_TYPES:
            raise ValueError(f"Invalid program type: {self.program_type}")
        if self.enrollment_status not in self.VALID_ENROLLMENT_STATUSES:
            raise ValueError(f"Invalid enrollment status: {self.enrollment_status}")


@dataclass
class Publication:
    """Publication record entity."""
    publication_id: str
    department: str
    journal_tier: str  # SCIE/KCI/기타
    impact_factor: Optional[float]

    VALID_JOURNAL_TIERS = ['SCIE', 'KCI', '기타']

    def __post_init__(self):
        """Validate business rules."""
        if self.journal_tier not in self.VALID_JOURNAL_TIERS:
            raise ValueError(f"Invalid journal tier: {self.journal_tier}")
        if self.impact_factor is not None and self.impact_factor < 0:
            raise ValueError("Impact factor cannot be negative")


@dataclass
class DepartmentKPI:
    """Department KPI metrics entity."""
    evaluation_year: int
    department: str
    employment_rate: float  # Percentage (0-100)
    tech_transfer_revenue: float  # In 억원

    def __post_init__(self):
        """Validate business rules."""
        if self.evaluation_year < 2000:
            raise ValueError("Evaluation year must be >= 2000")
        if self.employment_rate < 0 or self.employment_rate > 100:
            raise ValueError("Employment rate must be between 0 and 100")
        if self.tech_transfer_revenue < 0:
            raise ValueError("Tech transfer revenue cannot be negative")
