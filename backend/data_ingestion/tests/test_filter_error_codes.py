"""
Unit tests for standardized filter error codes and responses.
Following TDD Red-Green-Refactor cycle.
Testing spec.md Section 13 - Error Code Specification.
"""

import pytest
from datetime import datetime
from data_ingestion.constants.filter_error_codes import (
    FilterErrorCode,
    format_error_response
)


class TestErrorCodeConstants:
    """Test error code constants are defined"""

    def test_filter_error_code_constants_exist(self):
        """Test: All error codes are defined"""
        # Assert
        assert hasattr(FilterErrorCode, 'INVALID_PARAMETER')
        assert hasattr(FilterErrorCode, 'INVALID_YEAR_FORMAT')
        assert hasattr(FilterErrorCode, 'INVALID_DEPARTMENT')
        assert hasattr(FilterErrorCode, 'INVALID_STATUS')
        assert hasattr(FilterErrorCode, 'INVALID_JOURNAL_TIER')
        assert hasattr(FilterErrorCode, 'SERVER_ERROR')
        assert hasattr(FilterErrorCode, 'RATE_LIMIT_EXCEEDED')

    def test_error_code_values_are_strings(self):
        """Test: Error codes are string constants"""
        # Assert
        assert FilterErrorCode.INVALID_PARAMETER == 'invalid_parameter'
        assert FilterErrorCode.SERVER_ERROR == 'server_error'
        assert FilterErrorCode.RATE_LIMIT_EXCEEDED == 'rate_limit_exceeded'


class TestFormatErrorResponse:
    """Test error response formatting"""

    def test_format_error_response_basic(self):
        """Test 1: 에러 응답 포맷 검증"""
        # Arrange
        error_code = FilterErrorCode.INVALID_PARAMETER
        message = "유효하지 않은 파라미터입니다."

        # Act
        response = format_error_response(error_code, message)

        # Assert
        assert response['error'] == 'invalid_parameter'
        assert response['message'] == message
        assert 'timestamp' in response
        assert 'request_id' in response

    def test_format_error_response_with_details(self):
        """Test 2: 에러 응답에 details 포함"""
        # Arrange
        error_code = FilterErrorCode.INVALID_PARAMETER
        message = "필터 검증 실패"
        details = {"field": "year", "value": "invalid", "reason": "형식 오류"}

        # Act
        response = format_error_response(error_code, message, details)

        # Assert
        assert response['details'] == details
        assert response['details']['field'] == 'year'
        assert response['details']['value'] == 'invalid'

    def test_format_error_response_timestamp_format(self):
        """Test 3: timestamp가 ISO 8601 형식"""
        # Arrange & Act
        response = format_error_response(FilterErrorCode.SERVER_ERROR, "서버 오류")

        # Assert
        assert response['timestamp'].endswith('Z')
        # Verify it's valid ISO 8601 format
        datetime.fromisoformat(response['timestamp'].replace('Z', '+00:00'))  # Should not raise

    def test_format_error_response_unique_request_id(self):
        """Test 4: request_id가 고유함"""
        # Arrange & Act
        response1 = format_error_response(FilterErrorCode.SERVER_ERROR, "오류 1")
        response2 = format_error_response(FilterErrorCode.SERVER_ERROR, "오류 2")

        # Assert
        assert response1['request_id'] != response2['request_id']
        # Request IDs should be 8-character strings (truncated UUIDs)
        assert len(response1['request_id']) == 8
        assert len(response2['request_id']) == 8

    def test_format_error_response_without_details(self):
        """Test: details가 없을 때 필드 미포함"""
        # Arrange & Act
        response = format_error_response(FilterErrorCode.SERVER_ERROR, "서버 오류")

        # Assert
        assert 'details' not in response

    def test_format_error_response_all_error_codes(self):
        """Test: 모든 에러 코드가 정상 작동"""
        # Arrange
        error_codes = [
            (FilterErrorCode.INVALID_PARAMETER, "Invalid parameter"),
            (FilterErrorCode.INVALID_YEAR_FORMAT, "Invalid year"),
            (FilterErrorCode.INVALID_DEPARTMENT, "Invalid department"),
            (FilterErrorCode.INVALID_STATUS, "Invalid status"),
            (FilterErrorCode.INVALID_JOURNAL_TIER, "Invalid tier"),
            (FilterErrorCode.SERVER_ERROR, "Server error"),
            (FilterErrorCode.RATE_LIMIT_EXCEEDED, "Rate limit")
        ]

        # Act & Assert
        for error_code, message in error_codes:
            response = format_error_response(error_code, message)
            assert response['error'] == error_code
            assert response['message'] == message
            assert 'timestamp' in response
            assert 'request_id' in response


class TestErrorResponseStructure:
    """Test error response structure matches spec.md Section 13"""

    def test_error_response_has_required_fields(self):
        """Test: 에러 응답에 필수 필드 포함"""
        # Arrange & Act
        response = format_error_response(
            FilterErrorCode.INVALID_PARAMETER,
            "유효하지 않은 파라미터",
            {"field": "department", "value": "invalid"}
        )

        # Assert - Required fields
        assert 'error' in response
        assert 'message' in response
        assert 'timestamp' in response
        assert 'request_id' in response

        # Assert - Optional fields when provided
        assert 'details' in response

    def test_error_response_field_types(self):
        """Test: 에러 응답 필드 타입 검증"""
        # Arrange & Act
        response = format_error_response(
            FilterErrorCode.INVALID_PARAMETER,
            "메시지",
            {"key": "value"}
        )

        # Assert
        assert isinstance(response['error'], str)
        assert isinstance(response['message'], str)
        assert isinstance(response['timestamp'], str)
        assert isinstance(response['request_id'], str)
        assert isinstance(response['details'], dict)

    def test_error_response_message_korean(self):
        """Test: 에러 메시지는 한글"""
        # Arrange & Act
        response = format_error_response(
            FilterErrorCode.INVALID_PARAMETER,
            "유효하지 않은 필터 값입니다."
        )

        # Assert
        assert '유효하지 않은' in response['message']

    def test_error_response_details_structure(self):
        """Test: details 필드 구조 검증"""
        # Arrange
        details = {
            "field": "department",
            "value": "InvalidDept",
            "valid_values": ["컴퓨터공학과", "전자공학과"]
        }

        # Act
        response = format_error_response(
            FilterErrorCode.INVALID_DEPARTMENT,
            "유효하지 않은 학과입니다.",
            details
        )

        # Assert
        assert response['details']['field'] == 'department'
        assert response['details']['value'] == 'InvalidDept'
        assert isinstance(response['details']['valid_values'], list)
