"""
DRF Serializers for file upload API.
Following spec.md Section 4: API specifications and validation rules.
"""

import magic
from rest_framework import serializers
from django.conf import settings


class UploadSerializer(serializers.Serializer):
    """
    Serializer for file upload requests.

    Validates:
    - File size <= 10MB
    - File type: CSV or Excel (.csv, .xlsx, .xls)
    - MIME type validation (security)

    Accepted file types (form field names):
    - research_funding
    - students
    - publications
    - kpi
    """

    research_funding = serializers.FileField(required=False, allow_null=True)
    students = serializers.FileField(required=False, allow_null=True)
    publications = serializers.FileField(required=False, allow_null=True)
    kpi = serializers.FileField(required=False, allow_null=True)

    # Constants
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes
    ALLOWED_EXTENSIONS = ['.csv', '.xlsx', '.xls']
    ALLOWED_MIME_TYPES = [
        'text/csv',
        'text/plain',  # CSV may be detected as plain text
        'application/vnd.ms-excel',  # .xls
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'  # .xlsx
    ]

    def validate(self, attrs):
        """
        Validate uploaded files.

        Checks performed:
        1. At least one file uploaded
        2. File size <= 10MB
        3. File extension in whitelist
        4. MIME type validation (security: prevent malicious files)

        Raises:
            ValidationError: If any validation fails
        """
        # Filter out None values
        files = {k: v for k, v in attrs.items() if v is not None}

        if not files:
            raise serializers.ValidationError({
                'error': 'ERR_FILE_001',
                'message': '최소 1개 이상의 파일을 업로드해야 합니다.'
            })

        # Validate each file
        for file_type, uploaded_file in files.items():
            # Check file size
            if uploaded_file.size > self.MAX_FILE_SIZE:
                size_mb = uploaded_file.size / (1024 * 1024)
                raise serializers.ValidationError({
                    'error': 'ERR_FILE_002',
                    'file': file_type,
                    'message': f'파일 크기가 10MB를 초과합니다. (현재: {size_mb:.1f} MB)'
                })

            # Check file extension
            file_name = uploaded_file.name.lower()
            if not any(file_name.endswith(ext) for ext in self.ALLOWED_EXTENSIONS):
                raise serializers.ValidationError({
                    'error': 'ERR_FILE_001',
                    'file': file_type,
                    'message': f'지원되지 않는 파일 형식입니다. CSV 또는 Excel 파일을 선택하세요. ({uploaded_file.name})'
                })

            # MIME type validation (security check)
            try:
                # Read first 2048 bytes to determine MIME type
                uploaded_file.seek(0)
                file_head = uploaded_file.read(2048)
                uploaded_file.seek(0)  # Reset file pointer

                mime_type = magic.from_buffer(file_head, mime=True)

                if mime_type not in self.ALLOWED_MIME_TYPES:
                    raise serializers.ValidationError({
                        'error': 'ERR_FILE_001',
                        'file': file_type,
                        'message': f'허용되지 않은 파일 형식입니다: {mime_type}'
                    })

            except Exception as e:
                # If python-magic fails, log warning but allow (fallback to extension check)
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"MIME type validation failed for {file_type}: {e}")

        return files


class JobStatusSerializer(serializers.Serializer):
    """
    Serializer for job status responses.

    Response structure follows spec.md Section 4.2.
    """

    job_id = serializers.UUIDField()
    status = serializers.ChoiceField(choices=['processing', 'completed', 'failed', 'partial_success'])
    progress = serializers.IntegerField(min_value=0, max_value=100)
    files = serializers.ListField(required=False)
    error_message = serializers.CharField(required=False)
    completed_at = serializers.DateTimeField(required=False)
    failed_at = serializers.DateTimeField(required=False)


class ResearchFundingQuerySerializer(serializers.Serializer):
    """
    Serializer for Research Funding API query parameters.

    Following plan.md Phase 3 - Validates department and period filters.

    Query Parameters:
        department: str - Department filter ('all' or specific department name)
        period: str - Time period filter ('latest', '1year', '3years')

    Defaults:
        department: 'all'
        period: 'latest'
    """

    department = serializers.CharField(
        default='all',
        required=False,
        help_text="Department filter ('all' or specific department name)"
    )

    period = serializers.ChoiceField(
        choices=['latest', '1year', '3years'],
        default='latest',
        required=False,
        help_text="Time period filter"
    )


class StudentDashboardQuerySerializer(serializers.Serializer):
    """
    Serializer for Student Dashboard API query parameters.

    Following plan.md Phase 3 - Validates department and enrollment status filters.

    Query Parameters:
        department: str - Department filter ('all' or specific department name)
        status: str - Enrollment status filter ('all', '재학', '휴학', '졸업')

    Defaults:
        department: 'all'
        status: '재학' (enrolled students only)
    """

    department = serializers.CharField(
        default='all',
        required=False,
        help_text="Department filter ('all' or specific department name)"
    )

    status = serializers.ChoiceField(
        choices=['all', '재학', '휴학', '졸업'],
        default='재학',
        required=False,
        help_text="Enrollment status filter"
    )


class StudentDashboardResponseSerializer(serializers.Serializer):
    """
    Serializer for Student Dashboard API response.

    Following spec.md Section 4 - API Response Format.

    Response structure:
    {
        "total_students": 1234,
        "by_department": [
            {
                "department": "컴퓨터공학과",
                "학사": 120,
                "석사": 35,
                "박사": 12,
                "total": 167
            },
            ...
        ],
        "updated_at": "2025-11-02T14:35:22Z"
    }
    """

    total_students = serializers.IntegerField(
        help_text="Total number of filtered students"
    )

    by_department = serializers.ListField(
        child=serializers.DictField(),
        help_text="List of department aggregations with program type counts"
    )

    updated_at = serializers.DateTimeField(
        help_text="Timestamp of data retrieval"
    )


class PublicationDashboardQuerySerializer(serializers.Serializer):
    """
    Serializer for Publication Dashboard API query parameters.

    Following plan.md Phase 1.3 - Validates department and journal_tier filters.

    Query Parameters:
        department: str - Department filter ('all' or specific department name)
        journal_tier: str - Journal tier filter ('all', 'SCIE', 'KCI', '기타')

    Defaults:
        department: 'all'
        journal_tier: 'all'
    """

    department = serializers.CharField(
        default='all',
        required=False,
        help_text="Department filter ('all' or specific department name)"
    )

    journal_tier = serializers.ChoiceField(
        choices=['all', 'SCIE', 'KCI', '기타'],
        default='all',
        required=False,
        help_text="Journal tier filter"
    )


class PublicationDashboardResponseSerializer(serializers.Serializer):
    """
    Serializer for Publication Dashboard API response.

    Following spec.md Section 4 - API Response Format.

    Response structure:
    {
        "total_papers": 156,
        "avg_impact_factor": 2.3,
        "papers_with_if": 145,
        "distribution": [
            {
                "journal_tier": "SCIE",
                "count": 89,
                "percentage": 57.1,
                "avg_if": 3.2
            },
            ...
        ],
        "last_updated": "2025-11-02T14:35:22Z"
    }
    """

    total_papers = serializers.IntegerField(
        help_text="Total number of filtered publications"
    )

    avg_impact_factor = serializers.FloatField(
        allow_null=True,
        help_text="Average Impact Factor (NULL if no IF data)"
    )

    papers_with_if = serializers.IntegerField(
        help_text="Count of papers with non-NULL Impact Factor"
    )

    distribution = serializers.ListField(
        child=serializers.DictField(),
        help_text="List of journal tier aggregations"
    )

    last_updated = serializers.DateTimeField(
        help_text="Timestamp of data retrieval"
    )


class DepartmentKPIQuerySerializer(serializers.Serializer):
    """
    Serializer for Department KPI API query parameters.

    Following plan.md Phase 3.4 - Validates department and year range filters.

    Query Parameters:
        department: str - Department filter ('all' or specific department name)
        start_year: int - Start year (inclusive), default: current_year - 5
        end_year: int - End year (inclusive), default: current_year

    Business Rules (validated in Service Layer):
        - start_year <= end_year
        - Year range <= 20 years
        - end_year <= current_year + 1
        - start_year >= 2000
    """

    department = serializers.CharField(
        default='all',
        required=False,
        help_text="Department filter ('all' or specific department name)"
    )

    start_year = serializers.IntegerField(
        required=False,
        min_value=1900,  # Allow any reasonable year, validation in service
        max_value=2100,
        help_text="Start year for KPI data (inclusive)"
    )

    end_year = serializers.IntegerField(
        required=False,
        min_value=1900,  # Allow any reasonable year, validation in service
        max_value=2100,
        help_text="End year for KPI data (inclusive)"
    )

    def validate(self, attrs):
        """
        Add default values for start_year and end_year if not provided.

        Note: Business logic validation (year range, future dates) is handled
        in KPIService._validate_year_range() to keep serializer thin.
        """
        from datetime import datetime
        current_year = datetime.now().year

        # Set default values if not provided
        if 'start_year' not in attrs or attrs['start_year'] is None:
            attrs['start_year'] = current_year - 5

        if 'end_year' not in attrs or attrs['end_year'] is None:
            attrs['end_year'] = current_year

        # Basic validation: start <= end (lightweight check)
        if attrs['start_year'] > attrs['end_year']:
            raise serializers.ValidationError(
                '시작 년도는 종료 년도보다 작거나 같아야 합니다.'
            )

        return attrs
