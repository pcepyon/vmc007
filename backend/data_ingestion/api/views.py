"""
DRF ViewSets for CSV upload API endpoints.
Following spec.md Sections 3.3 (Upload) and 3.6 (Status).
"""

import os
import tempfile
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.conf import settings

from data_ingestion.api.permissions import AdminAPIKeyPermission
from data_ingestion.api.serializers import UploadSerializer, JobStatusSerializer
from data_ingestion.services.ingestion_service import submit_upload_job
from data_ingestion.infrastructure.job_status_store import get_job_store

logger = logging.getLogger(__name__)


class UploadViewSet(viewsets.ViewSet):
    """
    ViewSet for file upload operations.

    Endpoints:
    - POST /api/upload/ - Submit files for background processing
    """

    permission_classes = [AdminAPIKeyPermission]

    def create(self, request):
        """
        Handle file upload request.

        Flow:
        1. Validate files (size, format, MIME type)
        2. Save to temporary directory
        3. Submit background job
        4. Return 202 Accepted with job_id

        Returns:
            HTTP 202 Accepted: Job submitted successfully
            HTTP 400 Bad Request: Validation failed
            HTTP 403 Forbidden: Invalid API key
        """
        # Validate uploaded files
        serializer = UploadSerializer(data=request.FILES)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        # Save files to temporary directory
        temp_dir = tempfile.mkdtemp(prefix='upload_')
        file_paths = {}

        try:
            for file_type, uploaded_file in serializer.validated_data.items():
                if uploaded_file:
                    # Save file with original extension
                    file_ext = os.path.splitext(uploaded_file.name)[1]
                    temp_path = os.path.join(temp_dir, f'{file_type}{file_ext}')

                    with open(temp_path, 'wb+') as dest:
                        for chunk in uploaded_file.chunks():
                            dest.write(chunk)

                    file_paths[file_type] = temp_path
                    logger.info(f"Saved {file_type} to {temp_path}")

            # Submit background processing job
            job_id = submit_upload_job(file_paths)

            return Response(
                {
                    'status': 'processing',
                    'job_id': job_id,
                    'message': '파일 업로드가 시작되었습니다. 처리가 완료되면 알려드리겠습니다.',
                    'estimated_time': '약 30초 소요 예상'
                },
                status=status.HTTP_202_ACCEPTED
            )

        except Exception as e:
            logger.exception(f"Error processing upload: {e}")

            # Cleanup temp files on error
            import shutil
            try:
                shutil.rmtree(temp_dir)
            except Exception as cleanup_error:
                logger.warning(f"Failed to cleanup temp dir: {cleanup_error}")

            return Response(
                {
                    'error': 'ERR_SYSTEM_001',
                    'message': '서버 오류가 발생했습니다. 잠시 후 다시 시도하세요.'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class StatusViewSet(viewsets.ViewSet):
    """
    ViewSet for job status queries.

    Endpoints:
    - GET /api/upload/status/{job_id}/ - Get job processing status
    """

    def retrieve(self, request, pk=None):
        """
        Get job processing status.

        Args:
            pk: job_id (UUID)

        Returns:
            HTTP 200 OK: Job status found
            HTTP 404 Not Found: Job ID not found
        """
        job_id = pk
        job_store = get_job_store()
        job_info = job_store.get_job(job_id)

        if job_info is None:
            return Response(
                {
                    'error': 'not_found',
                    'message': '작업 정보를 찾을 수 없습니다.'
                },
                status=status.HTTP_404_NOT_FOUND
            )

        # Convert JobInfo to dict for serialization
        job_data = {
            'job_id': job_info.job_id,
            'status': job_info.status.value,
            'progress': job_info.progress,
            'total': job_info.total
        }

        # Serialize response
        serializer = JobStatusSerializer(data=job_data)
        serializer.is_valid(raise_exception=True)

        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class ResearchFundingView(viewsets.ViewSet):
    """
    ViewSet for Research Funding Dashboard API.

    Following plan.md Phase 3 - API endpoint for research funding data.

    Endpoints:
    - GET /api/dashboard/research-funding/ - Get research funding dashboard data
    """

    def list(self, request):
        """
        Get research funding dashboard data with optional filters.

        Query Parameters:
            department (str, optional): Department filter ('all' or specific department)
            period (str, optional): Time period filter ('latest', '1year', '3years')

        Returns:
            HTTP 200 OK: Success with dashboard data
            HTTP 400 Bad Request: Invalid parameters
            HTTP 500 Internal Server Error: Server error

        Response Example:
            {
                "status": "success",
                "data": {
                    "current_balance": 1530000000,
                    "current_balance_formatted": "15.3억원",
                    "trend": [...]
                }
            }
        """
        from data_ingestion.api.serializers import ResearchFundingQuerySerializer
        from data_ingestion.services.research_funding_service import ResearchFundingService
        from data_ingestion.constants.error_codes import ErrorCode

        # Validate query parameters
        serializer = ResearchFundingQuerySerializer(data=request.query_params)

        if not serializer.is_valid():
            return Response(
                {
                    'status': 'error',
                    'error_code': ErrorCode.INVALID_PERIOD,
                    'message': '유효하지 않은 필터 파라미터입니다.',
                    'details': serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Extract validated parameters
        department = serializer.validated_data.get('department', 'all')
        period = serializer.validated_data.get('period', 'latest')

        try:
            # Call service layer
            service = ResearchFundingService()
            dashboard_data = service.get_dashboard_data(
                department=department,
                period=period
            )

            # Return successful response
            return Response(
                {
                    'status': 'success',
                    'data': dashboard_data
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.error(f"Error fetching research funding data: {e}")
            return Response(
                {
                    'status': 'error',
                    'error_code': ErrorCode.DATABASE_ERROR,
                    'message': '데이터 조회 중 오류가 발생했습니다.'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class StudentDashboardView(viewsets.ViewSet):
    """
    ViewSet for Student Dashboard API.

    Following plan.md Phase 3 - API endpoint for student enrollment data.

    Endpoints:
    - GET /api/dashboard/students/ - Get student dashboard data
    """

    def list(self, request):
        """
        Get student dashboard data with optional filters.

        Query Parameters:
            department (str, optional): Department filter ('all' or specific department)
                Default: 'all'
            status (str, optional): Enrollment status filter ('all', '재학', '휴학', '졸업')
                Default: '재학' (enrolled students only)

        Returns:
            HTTP 200 OK: Success with dashboard data
            HTTP 400 Bad Request: Invalid parameters (e.g., invalid status, nonexistent department)
            HTTP 500 Internal Server Error: Server error

        Response Example:
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

        Error Responses:
            - 400: validation_error - Invalid enrollment status or nonexistent department
            - 500: server_error - Database error or unexpected exception
        """
        from data_ingestion.api.serializers import (
            StudentDashboardQuerySerializer,
            StudentDashboardResponseSerializer
        )
        from data_ingestion.services.student_dashboard_service import StudentDashboardService
        from data_ingestion.constants.error_codes import ErrorCode
        from django.core.exceptions import ValidationError

        # Validate query parameters
        query_serializer = StudentDashboardQuerySerializer(data=request.query_params)

        if not query_serializer.is_valid():
            return Response(
                {
                    'error': 'validation_error',
                    'message': '유효하지 않은 필터 파라미터입니다.',
                    'details': query_serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Extract validated parameters
        department = query_serializer.validated_data.get('department', 'all')
        enrollment_status = query_serializer.validated_data.get('status', '재학')

        try:
            # Call service layer
            service = StudentDashboardService()
            dashboard_data = service.get_student_dashboard_data(
                department=department,
                status=enrollment_status
            )

            # Serialize response
            response_serializer = StudentDashboardResponseSerializer(data=dashboard_data)
            response_serializer.is_valid(raise_exception=True)

            # Return successful response
            return Response(
                response_serializer.validated_data,
                status=status.HTTP_200_OK
            )

        except ValidationError as e:
            # Business logic validation errors (department not found, invalid status)
            return Response(
                {
                    'error': 'validation_error',
                    'message': str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            logger.error(f"Error fetching student dashboard data: {e}")
            return Response(
                {
                    'error': 'server_error',
                    'message': '데이터 조회 중 오류가 발생했습니다.'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PublicationDashboardView(viewsets.ViewSet):
    """
    ViewSet for Publication Dashboard API.

    Following plan.md Phase 1.4 - API endpoint for publication data.

    Endpoints:
    - GET /api/dashboard/publications/ - Get publication dashboard data
    """

    def list(self, request):
        """
        Get publication dashboard data with optional filters.

        Query Parameters:
            department (str, optional): Department filter ('all' or specific department)
            journal_tier (str, optional): Journal tier filter ('all', 'SCIE', 'KCI', '기타')

        Returns:
            HTTP 200 OK: Success with dashboard data
            HTTP 400 Bad Request: Invalid parameters (invalid tier, nonexistent department)
            HTTP 500 Internal Server Error: Server error

        Response Example:
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

        Error Responses:
            - 400: validation_error - Invalid journal tier or nonexistent department
            - 500: server_error - Database error or unexpected exception
        """
        from data_ingestion.api.serializers import (
            PublicationDashboardQuerySerializer,
            PublicationDashboardResponseSerializer
        )
        from data_ingestion.services.publication_service import PublicationService
        from django.core.exceptions import ValidationError

        # Validate query parameters
        query_serializer = PublicationDashboardQuerySerializer(data=request.query_params)

        if not query_serializer.is_valid():
            return Response(
                {
                    'error': 'validation_error',
                    'message': '유효하지 않은 필터 파라미터입니다.',
                    'details': query_serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Extract validated parameters
        department = query_serializer.validated_data.get('department', 'all')
        journal_tier = query_serializer.validated_data.get('journal_tier', 'all')

        try:
            # Call service layer
            service = PublicationService()
            dashboard_data = service.get_distribution(
                department=department,
                journal_tier=journal_tier
            )

            # Serialize response
            response_serializer = PublicationDashboardResponseSerializer(data=dashboard_data)
            response_serializer.is_valid(raise_exception=True)

            # Return successful response
            return Response(
                response_serializer.validated_data,
                status=status.HTTP_200_OK
            )

        except ValidationError as e:
            # Business logic validation errors (department not found, invalid tier)
            return Response(
                {
                    'error': 'validation_error',
                    'message': str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            logger.error(f"Error fetching publication dashboard data: {e}")
            return Response(
                {
                    'error': 'server_error',
                    'message': '데이터 조회 중 오류가 발생했습니다.'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DepartmentKPIView(viewsets.ViewSet):
    """
    ViewSet for Department KPI Dashboard API.

    Following plan.md Phase 3.4 - API endpoint for department KPI trend data.

    Endpoints:
    - GET /api/dashboard/department-kpi/ - Get department KPI trend data
    """

    def list(self, request):
        """
        Get department KPI trend data with optional filters.

        Query Parameters:
            department (str, optional): Department filter ('all' or specific department)
            start_year (int, optional): Start year, default: current_year - 5
            end_year (int, optional): End year, default: current_year

        Returns:
            HTTP 200 OK: Success with dashboard data
            HTTP 400 Bad Request: Invalid parameters (invalid year range, etc.)
            HTTP 500 Internal Server Error: Server error

        Response Example:
            {
                "status": "success",
                "data": [
                    {
                        "evaluation_year": 2019,
                        "avg_employment_rate": 76.2,
                        "total_tech_income": 8.5
                    },
                    ...
                ],
                "meta": {
                    "department_filter": "all",
                    "year_range": "2019-2023",
                    "overall_avg_employment_rate": 78.4,
                    "total_count": 5
                }
            }

        Error Responses:
            - 400: INVALID_YEAR_RANGE - start_year > end_year
            - 400: YEAR_RANGE_TOO_LARGE - year range exceeds 20 years
            - 400: FUTURE_YEAR_NOT_ALLOWED - end_year is too far in future
            - 400: YEAR_TOO_OLD - start_year before 2000
            - 500: DATABASE_ERROR - Database connection or query error
        """
        from data_ingestion.api.serializers import DepartmentKPIQuerySerializer
        from data_ingestion.services.kpi_service import KPIService
        from data_ingestion.constants.error_codes import ErrorCode

        # Validate query parameters
        query_serializer = DepartmentKPIQuerySerializer(data=request.query_params)

        if not query_serializer.is_valid():
            return Response(
                {
                    'status': 'error',
                    'error_code': 'INVALID_YEAR_RANGE',
                    'message': '유효하지 않은 필터 파라미터입니다.',
                    'details': query_serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Extract validated parameters
        department = query_serializer.validated_data.get('department', 'all')
        start_year = query_serializer.validated_data.get('start_year')
        end_year = query_serializer.validated_data.get('end_year')

        try:
            # Call service layer
            service = KPIService()
            dashboard_data = service.get_kpi_trend(
                department=department,
                start_year=start_year,
                end_year=end_year
            )

            # Return successful response
            return Response(
                dashboard_data,
                status=status.HTTP_200_OK
            )

        except ValueError as e:
            # Business logic validation errors
            error_message = str(e)
            error_code = 'INVALID_YEAR_RANGE'

            if '20년' in error_message:
                error_code = 'YEAR_RANGE_TOO_LARGE'
            elif '초과할 수 없습니다' in error_message:
                error_code = 'FUTURE_YEAR_NOT_ALLOWED'
            elif '2000년 이후여야 합니다' in error_message:
                error_code = 'YEAR_TOO_OLD'

            return Response(
                {
                    'status': 'error',
                    'error_code': error_code,
                    'message': error_message
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            logger.error(f"Error fetching department KPI data: {e}")
            return Response(
                {
                    'status': 'error',
                    'error_code': 'DATABASE_ERROR',
                    'message': '데이터 조회 중 오류가 발생했습니다.'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class FilterOptionsView(viewsets.ViewSet):
    """
    ViewSet for Filter Options Metadata API.

    Following spec.md Section 9.5 - Filter Options Metadata API.

    Endpoints:
    - GET /api/dashboard/filter-options/ - Get available filter options
    """

    def list(self, request):
        """
        Get available filter options for dashboard filtering.

        Returns:
            HTTP 200 OK: Success with filter options metadata

        Response Example:
            {
                "departments": ["all", "컴퓨터공학과", "전자공학과", ...],
                "years": ["latest", "2024", "2023", ...],
                "student_statuses": ["all", "재학", "졸업", "휴학"],
                "journal_tiers": ["all", "SCIE", "KCI", "기타"]
            }
        """
        from data_ingestion.api.validators import (
            VALID_DEPARTMENTS,
            VALID_ENROLLMENT_STATUS,
            VALID_JOURNAL_TIERS
        )
        from datetime import datetime

        # Get current year and generate year options
        current_year = datetime.now().year
        year_options = ['latest']
        # Add current year and previous 5 years
        for year in range(current_year, current_year - 6, -1):
            year_options.append(str(year))

        filter_options = {
            'departments': VALID_DEPARTMENTS,
            'years': year_options,
            'student_statuses': VALID_ENROLLMENT_STATUS,
            'journal_tiers': VALID_JOURNAL_TIERS
        }

        return Response(filter_options, status=status.HTTP_200_OK)
