"""
Integration tests for Student Dashboard API.
Following plan.md Phase 3 - Integration tests (TDD approach).

Test coverage:
- API endpoint returns 200 with valid parameters
- Department filtering works correctly
- Enrollment status filtering works correctly
- Combined filters work correctly
- Invalid parameters return 400
- Empty database returns 200 with empty list
- Response structure matches spec.md Section 4

TDD Integration: API → Service → Repository → Database
"""

import pytest
from rest_framework.test import APIClient
from rest_framework import status as http_status
from data_ingestion.infrastructure.models import Student


@pytest.fixture
def api_client():
    """API client for making HTTP requests."""
    return APIClient()


@pytest.fixture
def sample_students(db):
    """
    Sample student data for integration testing.

    Creates 3 students:
    - 2 from 컴퓨터공학과 (1 학사 재학, 1 석사 재학)
    - 1 from 전자공학과 (학사 휴학)
    """
    return Student.objects.bulk_create([
        Student(
            student_id='2024001',
            department='컴퓨터공학과',
            grade=1,
            program_type='학사',
            enrollment_status='재학'
        ),
        Student(
            student_id='2024002',
            department='컴퓨터공학과',
            grade=2,
            program_type='석사',
            enrollment_status='재학'
        ),
        Student(
            student_id='2024003',
            department='전자공학과',
            grade=1,
            program_type='학사',
            enrollment_status='휴학'
        ),
    ])


@pytest.mark.django_db
class TestStudentDashboardAPIIntegration:
    """
    Integration tests for Student Dashboard API.
    Tests full stack: API → Service → Repository → Database.
    """

    def test_get_endpoint_returns_200_with_valid_params(self, api_client, sample_students):
        """
        GIVEN: Sample students in database
        WHEN: GET /api/dashboard/students/?department=all&status=재학
        THEN: Returns 200 OK with expected response structure
        """
        # Act
        response = api_client.get('/api/dashboard/students/', {
            'department': 'all',
            'status': '재학'
        })

        # Assert
        assert response.status_code == http_status.HTTP_200_OK

        data = response.json()
        assert 'total_students' in data
        assert 'by_department' in data
        assert 'updated_at' in data

        # Should have 2 재학 students
        assert data['total_students'] == 2

        # Should have data for 2 departments (컴퓨터공학과, 전자공학과 removed due to filter)
        # Actually only 1 department since 전자공학과 student is 휴학
        assert len(data['by_department']) == 1

    def test_get_endpoint_filters_by_department(self, api_client, sample_students):
        """
        GIVEN: Students from multiple departments
        WHEN: GET /api/dashboard/students/?department=컴퓨터공학과&status=all
        THEN: Returns only 컴퓨터공학과 students
        """
        # Act
        response = api_client.get('/api/dashboard/students/', {
            'department': '컴퓨터공학과',
            'status': 'all'
        })

        # Assert
        assert response.status_code == http_status.HTTP_200_OK

        data = response.json()
        assert data['total_students'] == 2

        # Should have only 1 department
        assert len(data['by_department']) == 1
        assert data['by_department'][0]['department'] == '컴퓨터공학과'

    def test_get_endpoint_filters_by_enrollment_status(self, api_client, sample_students):
        """
        GIVEN: Students with different enrollment statuses
        WHEN: GET /api/dashboard/students/?department=all&status=재학
        THEN: Returns only 재학 students
        """
        # Act
        response = api_client.get('/api/dashboard/students/', {
            'department': 'all',
            'status': '재학'
        })

        # Assert
        assert response.status_code == http_status.HTTP_200_OK

        data = response.json()
        # 2 재학 students (both from 컴퓨터공학과)
        assert data['total_students'] == 2

    def test_get_endpoint_invalid_status_returns_400(self, api_client):
        """
        GIVEN: Invalid enrollment status parameter
        WHEN: GET /api/dashboard/students/?status=invalid_status
        THEN: Returns 400 Bad Request with error message
        """
        # Act
        response = api_client.get('/api/dashboard/students/', {
            'status': 'invalid_status'
        })

        # Assert
        assert response.status_code == http_status.HTTP_400_BAD_REQUEST

        data = response.json()
        assert 'error' in data
        assert data['error'] == 'validation_error'

    def test_get_endpoint_nonexistent_department_returns_400(self, api_client, sample_students):
        """
        GIVEN: Request for nonexistent department
        WHEN: GET /api/dashboard/students/?department=존재하지않는학과
        THEN: Returns 400 Bad Request
        """
        # Act
        response = api_client.get('/api/dashboard/students/', {
            'department': '존재하지않는학과',
            'status': '재학'
        })

        # Assert
        assert response.status_code == http_status.HTTP_400_BAD_REQUEST

        data = response.json()
        assert 'error' in data
        assert '존재하지 않는 학과' in data['message']

    def test_get_endpoint_no_data_returns_200_empty_list(self, api_client, db):
        """
        GIVEN: Empty database (no students)
        WHEN: GET /api/dashboard/students/
        THEN: Returns 200 OK with total_students=0 and empty by_department list
        """
        # Act
        response = api_client.get('/api/dashboard/students/')

        # Assert
        assert response.status_code == http_status.HTTP_200_OK

        data = response.json()
        assert data['total_students'] == 0
        assert data['by_department'] == []

    def test_get_endpoint_missing_query_params_uses_defaults(self, api_client, sample_students):
        """
        GIVEN: Request without query parameters
        WHEN: GET /api/dashboard/students/
        THEN: Uses default values (department='all', status='재학')
        """
        # Act
        response = api_client.get('/api/dashboard/students/')

        # Assert
        assert response.status_code == http_status.HTTP_200_OK

        data = response.json()
        # Default status='재학' should return 2 students
        assert data['total_students'] == 2

    def test_response_structure_matches_spec(self, api_client, sample_students):
        """
        GIVEN: Valid request
        WHEN: GET /api/dashboard/students/
        THEN: Response structure matches spec.md Section 4
        """
        # Act
        response = api_client.get('/api/dashboard/students/', {
            'department': '컴퓨터공학과',
            'status': 'all'
        })

        # Assert
        assert response.status_code == http_status.HTTP_200_OK

        data = response.json()

        # Check top-level keys
        assert set(data.keys()) == {'total_students', 'by_department', 'updated_at'}

        # Check by_department structure
        for dept_data in data['by_department']:
            assert 'department' in dept_data
            assert '학사' in dept_data
            assert '석사' in dept_data
            assert '박사' in dept_data
            assert 'total' in dept_data

    def test_aggregation_accuracy(self, api_client, db):
        """
        GIVEN: Known student distribution
        WHEN: GET /api/dashboard/students/?department=all&status=all
        THEN: Aggregation counts are accurate
        """
        # Arrange: Create specific student distribution
        Student.objects.bulk_create([
            Student(student_id='2024101', department='컴퓨터공학과', grade=1,
                   program_type='학사', enrollment_status='재학'),
            Student(student_id='2024102', department='컴퓨터공학과', grade=2,
                   program_type='학사', enrollment_status='재학'),
            Student(student_id='2024103', department='컴퓨터공학과', grade=1,
                   program_type='석사', enrollment_status='재학'),
            Student(student_id='2024104', department='컴퓨터공학과', grade=1,
                   program_type='박사', enrollment_status='재학'),
        ])

        # Act
        response = api_client.get('/api/dashboard/students/', {
            'department': '컴퓨터공학과',
            'status': 'all'
        })

        # Assert
        data = response.json()
        dept_data = data['by_department'][0]

        assert dept_data['학사'] == 2
        assert dept_data['석사'] == 1
        assert dept_data['박사'] == 1
        assert dept_data['total'] == 4
