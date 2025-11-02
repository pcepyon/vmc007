"""
Centralized error code registry for data_ingestion API.
Follows plan.md Phase 3 requirement for consistent error handling.
"""


class ErrorCode:
    """
    Central registry for all error codes used in the application.

    Usage:
        from data_ingestion.constants.error_codes import ErrorCode

        if department not in valid_departments:
            return Response({
                'error_code': ErrorCode.INVALID_DEPARTMENT,
                'message': '유효하지 않은 학과명입니다.'
            }, status=400)
    """

    # Input Validation Errors (4xx)
    INVALID_DEPARTMENT = 'INVALID_DEPARTMENT'
    INVALID_PERIOD = 'INVALID_PERIOD'
    INVALID_DATE_RANGE = 'INVALID_DATE_RANGE'
    INVALID_DATE_FORMAT = 'INVALID_DATE_FORMAT'

    # Data Errors (2xx with message or 404)
    NO_DATA_AVAILABLE = 'NO_DATA_AVAILABLE'

    # Server Errors (5xx)
    DATABASE_ERROR = 'DATABASE_ERROR'
    INTERNAL_SERVER_ERROR = 'INTERNAL_SERVER_ERROR'
