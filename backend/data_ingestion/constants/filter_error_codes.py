"""
Standardized error codes and response formatting for dashboard filtering APIs.
Following spec.md Section 13 - Error Code Specification.
Following plan.md Phase 3.3.1 - Error Response Specification.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any


class FilterErrorCode:
    """
    Standard error codes for dashboard filtering APIs.
    Used as contract between frontend and backend.
    """
    # Validation errors (400)
    INVALID_PARAMETER = 'invalid_parameter'
    INVALID_YEAR_FORMAT = 'invalid_year_format'
    INVALID_DEPARTMENT = 'invalid_department'
    INVALID_STATUS = 'invalid_status'
    INVALID_JOURNAL_TIER = 'invalid_journal_tier'

    # Server errors (500)
    SERVER_ERROR = 'server_error'

    # Rate limiting (429)
    RATE_LIMIT_EXCEEDED = 'rate_limit_exceeded'


def format_error_response(
    error_code: str,
    message: str,
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Format standardized error response.

    Response structure follows spec.md Section 13.1:
    {
        "error": "error_code",
        "message": "사용자 친화적 메시지 (한글)",
        "details": {...},  # Optional
        "timestamp": "2025-11-02T10:30:00Z",
        "request_id": "a1b2c3d4"
    }

    Args:
        error_code: Error code from FilterErrorCode class
        message: User-friendly Korean message
        details: Optional additional error details

    Returns:
        dict: Standardized error response

    Examples:
        >>> format_error_response(
        ...     FilterErrorCode.INVALID_PARAMETER,
        ...     "유효하지 않은 학과입니다.",
        ...     {"field": "department", "value": "InvalidDept"}
        ... )
        {
            "error": "invalid_parameter",
            "message": "유효하지 않은 학과입니다.",
            "details": {"field": "department", "value": "InvalidDept"},
            "timestamp": "2025-11-02T14:35:22Z",
            "request_id": "a1b2c3d4"
        }
    """
    response = {
        "error": error_code,
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        "request_id": str(uuid.uuid4())[:8]  # First 8 characters of UUID
    }

    if details is not None:
        response["details"] = details

    return response
