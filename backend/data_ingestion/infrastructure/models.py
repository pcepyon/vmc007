"""
Django models for CSV data ingestion.
Following spec.md section 5.2 - CSV to Django Model mapping.
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class ResearchProject(models.Model):
    """
    Research funding execution data model.
    Maps to research_project_data.csv
    """
    execution_id = models.CharField(
        max_length=100,
        primary_key=True,
        verbose_name='집행ID'
    )
    department = models.CharField(
        max_length=100,
        verbose_name='소속학과'
    )
    total_budget = models.BigIntegerField(
        validators=[MinValueValidator(0)],
        verbose_name='총연구비'
    )
    execution_date = models.DateField(
        verbose_name='집행일자'
    )
    execution_amount = models.BigIntegerField(
        validators=[MinValueValidator(0)],
        verbose_name='집행금액'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'research_projects'
        indexes = [
            models.Index(fields=['department'], name='idx_rp_dept'),
            models.Index(fields=['execution_date'], name='idx_rp_date'),
        ]
        verbose_name = 'Research Project'
        verbose_name_plural = 'Research Projects'

    def __str__(self):
        return f"{self.execution_id} - {self.department}"


class Student(models.Model):
    """
    Student enrollment data model.
    Maps to student_roster.csv
    """
    PROGRAM_TYPE_CHOICES = [
        ('학사', '학사'),
        ('석사', '석사'),
        ('박사', '박사'),
    ]

    ENROLLMENT_STATUS_CHOICES = [
        ('재학', '재학'),
        ('휴학', '휴학'),
        ('졸업', '졸업'),
    ]

    student_id = models.CharField(
        max_length=20,
        primary_key=True,
        verbose_name='학번'
    )
    department = models.CharField(
        max_length=100,
        verbose_name='학과'
    )
    grade = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(4)],
        verbose_name='학년'
    )
    program_type = models.CharField(
        max_length=20,
        choices=PROGRAM_TYPE_CHOICES,
        verbose_name='과정구분'
    )
    enrollment_status = models.CharField(
        max_length=20,
        choices=ENROLLMENT_STATUS_CHOICES,
        verbose_name='학적상태'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'students'
        indexes = [
            models.Index(fields=['department'], name='idx_student_dept'),
        ]
        verbose_name = 'Student'
        verbose_name_plural = 'Students'

    def __str__(self):
        return f"{self.student_id} - {self.department}"


class Publication(models.Model):
    """
    Publication records data model.
    Maps to publication_list.csv
    """
    JOURNAL_TIER_CHOICES = [
        ('SCIE', 'SCIE'),
        ('KCI', 'KCI'),
        ('기타', '기타'),
    ]

    publication_id = models.CharField(
        max_length=100,
        primary_key=True,
        verbose_name='논문ID'
    )
    department = models.CharField(
        max_length=100,
        verbose_name='학과'
    )
    journal_tier = models.CharField(
        max_length=20,
        choices=JOURNAL_TIER_CHOICES,
        verbose_name='저널등급'
    )
    impact_factor = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name='Impact Factor'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'publications'
        indexes = [
            models.Index(fields=['department'], name='idx_pub_dept'),
        ]
        verbose_name = 'Publication'
        verbose_name_plural = 'Publications'

    def __str__(self):
        return f"{self.publication_id} - {self.department}"


class DepartmentKPI(models.Model):
    """
    Department KPI metrics data model.
    Maps to department_kpi.csv
    Composite unique constraint on (evaluation_year, department)
    """
    evaluation_year = models.IntegerField(
        validators=[MinValueValidator(2000)],
        verbose_name='평가년도'
    )
    department = models.CharField(
        max_length=100,
        verbose_name='학과'
    )
    employment_rate = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='졸업생 취업률(%)'
    )
    tech_transfer_revenue = models.FloatField(
        validators=[MinValueValidator(0)],
        verbose_name='연간 기술이전 수입액(억원)'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'department_kpis'
        constraints = [
            models.UniqueConstraint(
                fields=['evaluation_year', 'department'],
                name='unique_year_department_kpi'
            )
        ]
        indexes = [
            models.Index(fields=['evaluation_year'], name='idx_kpi_year'),
            models.Index(fields=['department'], name='idx_kpi_dept'),
        ]
        verbose_name = 'Department KPI'
        verbose_name_plural = 'Department KPIs'

    def __str__(self):
        return f"{self.evaluation_year} - {self.department}"
