"""
Unit tests for ResearchProject model.
Following TDD Red-Green-Refactor cycle and plan.md Phase 1.
"""

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from datetime import date
from data_ingestion.infrastructure.models import ResearchProject


@pytest.mark.unit
@pytest.mark.django_db
class TestResearchProjectModel:
    """Test suite for ResearchProject model validations."""

    def test_create_research_project_with_valid_data(self):
        """
        Test Case 1: 모델 생성 성공
        RED PHASE: Write failing test first
        """
        # Arrange
        data = {
            'execution_id': 'EX001',
            'department': '컴퓨터공학과',
            'total_budget': 1000000000,
            'execution_date': date(2024, 1, 15),
            'execution_amount': 200000000
        }

        # Act
        project = ResearchProject.objects.create(**data)

        # Assert
        assert project.execution_id == 'EX001'
        assert project.department == '컴퓨터공학과'
        assert project.total_budget == 1000000000
        assert project.execution_date == date(2024, 1, 15)
        assert project.execution_amount == 200000000
        assert project.created_at is not None
        assert project.updated_at is not None

    def test_execution_id_must_be_unique(self):
        """
        Test Case 2: execution_id UNIQUE 제약
        Business Rule: 동일한 집행ID는 중복 불가
        """
        # Arrange
        ResearchProject.objects.create(
            execution_id='EX001',
            department='컴퓨터공학과',
            total_budget=1000000000,
            execution_date=date(2024, 1, 15),
            execution_amount=200000000
        )

        # Act & Assert
        with pytest.raises(IntegrityError):
            ResearchProject.objects.create(
                execution_id='EX001',  # Duplicate
                department='전자공학과',
                total_budget=500000000,
                execution_date=date(2024, 2, 10),
                execution_amount=100000000
            )

    def test_negative_total_budget_rejected(self):
        """
        Test Case 3: 음수 총연구비 불허
        Business Rule: total_budget >= 0
        """
        # Arrange & Act
        project = ResearchProject(
            execution_id='EX002',
            department='컴퓨터공학과',
            total_budget=-1000,  # Invalid
            execution_date=date(2024, 1, 15),
            execution_amount=100000
        )

        # Assert
        with pytest.raises(ValidationError) as exc_info:
            project.full_clean()

        assert 'total_budget' in exc_info.value.error_dict

    def test_negative_execution_amount_rejected(self):
        """
        Test Case 4: 음수 집행금액 불허
        Business Rule: execution_amount >= 0
        """
        # Arrange & Act
        project = ResearchProject(
            execution_id='EX003',
            department='컴퓨터공학과',
            total_budget=1000000000,
            execution_date=date(2024, 1, 15),
            execution_amount=-500000  # Invalid
        )

        # Assert
        with pytest.raises(ValidationError) as exc_info:
            project.full_clean()

        assert 'execution_amount' in exc_info.value.error_dict

    def test_required_fields_cannot_be_null(self):
        """
        Test Case 5: 필수 필드 누락 검증
        """
        # Act & Assert - Missing department
        with pytest.raises(ValidationError) as exc_info:
            project = ResearchProject(
                execution_id='EX004',
                total_budget=1000000000,
                execution_date=date(2024, 1, 15),
                execution_amount=200000000
            )
            project.full_clean()

        assert 'department' in exc_info.value.error_dict

    def test_str_representation(self):
        """Test __str__ method returns expected format."""
        # Arrange
        project = ResearchProject.objects.create(
            execution_id='EX005',
            department='컴퓨터공학과',
            total_budget=1000000000,
            execution_date=date(2024, 1, 15),
            execution_amount=200000000
        )

        # Act
        result = str(project)

        # Assert
        assert result == 'EX005 - 컴퓨터공학과'

    def test_updated_at_auto_updates(self):
        """Test updated_at field auto-updates on save."""
        # Arrange
        project = ResearchProject.objects.create(
            execution_id='EX006',
            department='컴퓨터공학과',
            total_budget=1000000000,
            execution_date=date(2024, 1, 15),
            execution_amount=200000000
        )
        initial_updated_at = project.updated_at

        # Act
        project.execution_amount = 300000000
        project.save()
        project.refresh_from_db()

        # Assert
        assert project.updated_at > initial_updated_at
