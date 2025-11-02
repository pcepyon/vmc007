"""
Unit tests for ResearchFundingSerializer.
Following TDD Red-Green-Refactor cycle and plan.md Phase 3.
"""

import pytest
from rest_framework.exceptions import ValidationError
from data_ingestion.api.serializers import ResearchFundingQuerySerializer


@pytest.mark.unit
class TestResearchFundingQuerySerializer:
    """Test suite for query parameter validation."""

    def test_default_values(self):
        """
        Test Case 1: 기본값 설정
        When no parameters provided, should use defaults
        """
        # Arrange
        serializer = ResearchFundingQuerySerializer(data={})

        # Act
        is_valid = serializer.is_valid()

        # Assert
        assert is_valid
        assert serializer.validated_data['department'] == 'all'
        assert serializer.validated_data['period'] == 'latest'

    def test_validate_valid_parameters(self):
        """
        Test Case 2: 유효한 파라미터 검증
        Should accept valid department and period values
        """
        # Arrange
        serializer = ResearchFundingQuerySerializer(data={
            'department': '컴퓨터공학과',
            'period': '1year'
        })

        # Act
        is_valid = serializer.is_valid()

        # Assert
        assert is_valid
        assert serializer.validated_data['department'] == '컴퓨터공학과'
        assert serializer.validated_data['period'] == '1year'

    def test_invalid_period_value(self):
        """
        Test Case 3: 잘못된 period 값 검증
        Should reject period values not in allowed choices
        """
        # Arrange
        serializer = ResearchFundingQuerySerializer(data={
            'period': 'invalid_period'
        })

        # Act
        is_valid = serializer.is_valid()

        # Assert
        assert not is_valid
        assert 'period' in serializer.errors

    def test_all_valid_period_choices(self):
        """
        Test Case 4: 모든 유효한 period 값 확인
        Test all allowed period choices
        """
        valid_periods = ['latest', '1year', '3years']

        for period in valid_periods:
            # Arrange
            serializer = ResearchFundingQuerySerializer(data={'period': period})

            # Act
            is_valid = serializer.is_valid()

            # Assert
            assert is_valid, f"Period '{period}' should be valid"
            assert serializer.validated_data['period'] == period

    def test_department_allows_any_string(self):
        """
        Test Case 5: department 필드는 임의의 문자열 허용
        Department validation happens at view level, not serializer
        """
        # Arrange
        test_departments = ['all', '컴퓨터공학과', '전자공학과', '기계공학과']

        for dept in test_departments:
            # Arrange
            serializer = ResearchFundingQuerySerializer(data={'department': dept})

            # Act
            is_valid = serializer.is_valid()

            # Assert
            assert is_valid
            assert serializer.validated_data['department'] == dept
