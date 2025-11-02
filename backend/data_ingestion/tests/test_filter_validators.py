"""
Unit tests for filter parameter validators.
Following TDD Red-Green-Refactor cycle.
Testing spec.md Section 12 - Security Requirements.
"""

import pytest
from rest_framework.exceptions import ValidationError
from data_ingestion.api.validators import (
    validate_filter_params,
    sanitize_filter_input,
    VALID_DEPARTMENTS,
    VALID_ENROLLMENT_STATUS,
    VALID_JOURNAL_TIERS
)


class TestValidateDepartmentFilter:
    """Test department filter validation"""

    def test_validate_department_filter_with_valid_department(self):
        """Test 1: 유효한 학과 필터 통과"""
        # Arrange
        params = {'department': '컴퓨터공학과'}

        # Act & Assert
        validate_filter_params(params)  # Should not raise

    def test_validate_department_filter_with_all_keyword(self):
        """Test: 'all' 키워드 허용"""
        # Arrange
        params = {'department': 'all'}

        # Act & Assert
        validate_filter_params(params)  # Should not raise

    def test_validate_department_filter_with_invalid_department(self):
        """Test 2: 잘못된 학과 필터 거부"""
        # Arrange
        params = {'department': 'InvalidDept'}

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            validate_filter_params(params)
        assert 'department' in str(exc_info.value)


class TestValidateYearFilter:
    """Test year filter validation"""

    def test_validate_year_filter_with_valid_year(self):
        """Test 3: 유효한 연도 형식 (YYYY) 통과"""
        # Arrange
        params = {'year': '2024'}

        # Act & Assert
        validate_filter_params(params)  # Should not raise

    def test_validate_year_filter_with_invalid_format(self):
        """Test 4: 잘못된 연도 형식 거부"""
        # Arrange
        params = {'year': '24'}  # 2-digit year

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            validate_filter_params(params)
        assert 'year' in str(exc_info.value)

    def test_validate_year_filter_with_latest_keyword(self):
        """Test 5: 'latest' 키워드 허용"""
        # Arrange
        params = {'year': 'latest'}

        # Act & Assert
        validate_filter_params(params)  # Should not raise

    def test_validate_year_filter_with_non_numeric(self):
        """Test: 숫자가 아닌 연도 거부"""
        # Arrange
        params = {'year': 'abcd'}

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            validate_filter_params(params)
        assert 'year' in str(exc_info.value)


class TestValidateEnrollmentStatus:
    """Test enrollment status filter validation"""

    def test_validate_enrollment_status_with_valid_values(self):
        """Test 6: 학적상태 Enum 검증"""
        # Arrange
        valid_statuses = ['재학', '졸업', '휴학', 'all']

        # Act & Assert
        for status in valid_statuses:
            validate_filter_params({'status': status})

    def test_validate_enrollment_status_with_invalid_value(self):
        """Test: 유효하지 않은 학적상태 거부"""
        # Arrange
        params = {'status': '퇴학'}

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            validate_filter_params(params)
        assert 'status' in str(exc_info.value)


class TestValidateJournalTier:
    """Test journal tier filter validation"""

    def test_validate_journal_tier_with_valid_values(self):
        """Test 7: 저널등급 Enum 검증"""
        # Arrange
        valid_tiers = ['SCIE', 'KCI', '기타', 'all']

        # Act & Assert
        for tier in valid_tiers:
            validate_filter_params({'journal_tier': tier})

    def test_validate_journal_tier_with_invalid_value(self):
        """Test: 유효하지 않은 저널등급 거부"""
        # Arrange
        params = {'journal_tier': 'InvalidTier'}

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            validate_filter_params(params)
        assert 'journal_tier' in str(exc_info.value)


class TestValidateFilterParamsEdgeCases:
    """Test edge cases for filter validation"""

    def test_validate_filter_params_with_empty_params(self):
        """Edge Case 1: 빈 파라미터 허용 (기본값 적용)"""
        # Arrange
        params = {}

        # Act & Assert
        validate_filter_params(params)  # Should not raise

    def test_validate_filter_params_with_multiple_valid_filters(self):
        """Test: 다중 필터 동시 검증"""
        # Arrange
        params = {
            'department': '컴퓨터공학과',
            'year': '2024',
            'status': '재학',
            'journal_tier': 'SCIE'
        }

        # Act & Assert
        validate_filter_params(params)  # Should not raise

    def test_validate_filter_params_with_multiple_invalid_filters(self):
        """Test: 다중 필터 중 일부 잘못된 경우"""
        # Arrange
        params = {
            'department': 'InvalidDept',
            'year': 'invalid_year'
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            validate_filter_params(params)
        # Both errors should be in the exception
        error_str = str(exc_info.value)
        assert 'department' in error_str or 'year' in error_str


class TestSanitizeFilterInput:
    """Test input sanitization for security"""

    def test_sanitize_filter_input_reject_sql_injection(self):
        """Edge Case 2: SQL Injection 시도 거부"""
        # Arrange
        malicious_input = "'; DROP TABLE students; --"

        # Act
        sanitized = sanitize_filter_input(malicious_input)

        # Assert
        assert ';' not in sanitized
        assert '--' not in sanitized
        assert 'DROP' not in sanitized
        # After sanitization, it should not match any valid value

    def test_sanitize_filter_input_reject_xss(self):
        """Edge Case 3: XSS 시도 거부"""
        # Arrange
        malicious_input = '<script>alert("XSS")</script>'

        # Act
        sanitized = sanitize_filter_input(malicious_input)

        # Assert
        assert '<' not in sanitized
        assert '>' not in sanitized
        assert 'script' not in sanitized

    def test_sanitize_filter_input_preserves_korean(self):
        """Test: 한글 보존"""
        # Arrange
        korean_input = "컴퓨터공학과"

        # Act
        sanitized = sanitize_filter_input(korean_input)

        # Assert
        assert sanitized == "컴퓨터공학과"

    def test_sanitize_filter_input_preserves_hyphen_underscore(self):
        """Test: 하이픈/언더스코어 보존"""
        # Arrange
        valid_input = "2024-01_data"

        # Act
        sanitized = sanitize_filter_input(valid_input)

        # Assert
        assert sanitized == "2024-01_data"

    def test_sanitize_filter_input_removes_special_chars(self):
        """Test: 특수문자 제거"""
        # Arrange
        input_with_special = "컴퓨터공학과!@#$%^&*()"

        # Act
        sanitized = sanitize_filter_input(input_with_special)

        # Assert
        assert sanitized == "컴퓨터공학과"
        assert '!' not in sanitized
        assert '@' not in sanitized
