"""
Unit tests for StudentDashboardService.
Following plan.md Phase 2 - Service Layer tests (TDD RED phase).

Test coverage:
- Input validation (department existence, status whitelist)
- Data aggregation logic (_aggregate_by_department)
- Business rules (sorting by total descending)
- Edge cases: no data, missing program types, invalid inputs

TDD Cycle: RED → GREEN → REFACTOR
Uses mocked StudentRepository for isolated unit testing
"""

import pytest
from unittest.mock import Mock, MagicMock
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime
from data_ingestion.infrastructure.models import Student
from data_ingestion.services.student_dashboard_service import StudentDashboardService


@pytest.fixture
def mock_repository():
    """
    Mock StudentRepository for isolated service testing.
    Returns a mock object with configurable return values.
    """
    return Mock()


@pytest.mark.django_db
class TestStudentDashboardServiceValidation:
    """
    Test input validation logic.
    Service must validate department existence and status whitelist.
    """

    def test_validate_inputs_valid_parameters(self, mock_repository):
        """
        GIVEN: Valid department='컴퓨터공학과', status='재학'
        WHEN: Calling _validate_inputs()
        THEN: No ValidationError raised
        """
        # Arrange
        mock_repository.get_all_departments.return_value = ['컴퓨터공학과', '전자공학과']
        service = StudentDashboardService(mock_repository)

        # Act & Assert (should not raise)
        try:
            service._validate_inputs(department='컴퓨터공학과', status='재학')
        except ValidationError:
            pytest.fail("ValidationError should not be raised for valid inputs")

    def test_validate_inputs_all_department_and_all_status(self, mock_repository):
        """
        GIVEN: department='all', status='all'
        WHEN: Calling _validate_inputs()
        THEN: No ValidationError raised (valid default values)
        """
        # Arrange
        service = StudentDashboardService(mock_repository)

        # Act & Assert
        try:
            service._validate_inputs(department='all', status='all')
        except ValidationError:
            pytest.fail("ValidationError should not be raised for 'all' values")

    def test_validate_inputs_invalid_status_raises_error(self, mock_repository):
        """
        GIVEN: status='invalid_status' (not in whitelist)
        WHEN: Calling _validate_inputs()
        THEN: ValidationError raised with appropriate message
        """
        # Arrange
        service = StudentDashboardService(mock_repository)

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            service._validate_inputs(department='all', status='invalid_status')

        assert '유효하지 않은 학적상태' in str(exc_info.value)

    def test_validate_inputs_nonexistent_department_raises_error(self, mock_repository):
        """
        GIVEN: department='존재하지않는학과' (not in database)
        WHEN: Calling _validate_inputs()
        THEN: ValidationError raised
        """
        # Arrange
        mock_repository.get_all_departments.return_value = ['컴퓨터공학과', '전자공학과']
        service = StudentDashboardService(mock_repository)

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            service._validate_inputs(department='존재하지않는학과', status='재학')

        assert '존재하지 않는 학과' in str(exc_info.value)

    def test_validate_inputs_all_allowed_statuses(self, mock_repository):
        """
        GIVEN: All allowed status values ('재학', '휴학', '졸업', 'all')
        WHEN: Calling _validate_inputs() with each
        THEN: No ValidationError raised for any
        """
        # Arrange
        mock_repository.get_all_departments.return_value = ['컴퓨터공학과']
        service = StudentDashboardService(mock_repository)

        allowed_statuses = ['재학', '휴학', '졸업', 'all']

        # Act & Assert
        for status in allowed_statuses:
            try:
                service._validate_inputs(department='all', status=status)
            except ValidationError:
                pytest.fail(f"ValidationError should not be raised for status='{status}'")


@pytest.mark.django_db
class TestStudentDashboardServiceAggregation:
    """
    Test business logic and data aggregation.
    Service must correctly aggregate students by department and program_type.
    """

    def test_aggregate_by_department_groups_by_program_type(self, db):
        """
        GIVEN: 컴퓨터공학과 students (학사 2명, 석사 1명)
        WHEN: Calling _aggregate_by_department()
        THEN: Returns list with correct counts: {'department': '컴퓨터공학과', '학사': 2, '석사': 1, '박사': 0, 'total': 3}
        """
        # Arrange
        Student.objects.bulk_create([
            Student(student_id='2024001', department='컴퓨터공학과', grade=1,
                   program_type='학사', enrollment_status='재학'),
            Student(student_id='2024002', department='컴퓨터공학과', grade=2,
                   program_type='학사', enrollment_status='재학'),
            Student(student_id='2024003', department='컴퓨터공학과', grade=1,
                   program_type='석사', enrollment_status='재학'),
        ])
        mock_repo = Mock()
        service = StudentDashboardService(mock_repo)
        queryset = Student.objects.filter(department='컴퓨터공학과')

        # Act
        result = service._aggregate_by_department(queryset)

        # Assert
        assert len(result) == 1
        dept_data = result[0]
        assert dept_data['department'] == '컴퓨터공학과'
        assert dept_data['학사'] == 2
        assert dept_data['석사'] == 1
        assert dept_data['박사'] == 0
        assert dept_data['total'] == 3

    def test_aggregate_by_department_orders_by_total_desc(self, db):
        """
        GIVEN: 전자공학과(10명), 컴퓨터공학과(20명)
        WHEN: Calling _aggregate_by_department()
        THEN: Returns list with 컴퓨터공학과 first (descending order by total)
        """
        # Arrange
        # Create 20 students for 컴퓨터공학과
        comp_students = [
            Student(student_id=f'CS{i:04d}', department='컴퓨터공학과',
                   grade=1, program_type='학사', enrollment_status='재학')
            for i in range(20)
        ]
        # Create 10 students for 전자공학과
        elec_students = [
            Student(student_id=f'EE{i:04d}', department='전자공학과',
                   grade=1, program_type='학사', enrollment_status='재학')
            for i in range(10)
        ]
        Student.objects.bulk_create(comp_students + elec_students)

        mock_repo = Mock()
        service = StudentDashboardService(mock_repo)
        queryset = Student.objects.all()

        # Act
        result = service._aggregate_by_department(queryset)

        # Assert
        assert len(result) == 2
        # First item should be 컴퓨터공학과 (highest total)
        assert result[0]['department'] == '컴퓨터공학과'
        assert result[0]['total'] == 20
        # Second item should be 전자공학과
        assert result[1]['department'] == '전자공학과'
        assert result[1]['total'] == 10

    def test_aggregate_handles_missing_program_types(self, db):
        """
        GIVEN: Department with only 학사 students (no 석사 or 박사)
        WHEN: Calling _aggregate_by_department()
        THEN: Returns {'학사': N, '석사': 0, '박사': 0}
        """
        # Arrange
        Student.objects.bulk_create([
            Student(student_id='2024001', department='기계공학과', grade=1,
                   program_type='학사', enrollment_status='재학'),
            Student(student_id='2024002', department='기계공학과', grade=2,
                   program_type='학사', enrollment_status='재학'),
        ])
        mock_repo = Mock()
        service = StudentDashboardService(mock_repo)
        queryset = Student.objects.filter(department='기계공학과')

        # Act
        result = service._aggregate_by_department(queryset)

        # Assert
        assert len(result) == 1
        dept_data = result[0]
        assert dept_data['학사'] == 2
        assert dept_data['석사'] == 0
        assert dept_data['박사'] == 0


@pytest.mark.django_db
class TestStudentDashboardServiceMainFlow:
    """
    Test main service method get_student_dashboard_data().
    Integration of validation + repository query + aggregation.
    """

    def test_get_student_dashboard_data_all_students(self, db):
        """
        GIVEN: Multiple students in database
        WHEN: Calling get_student_dashboard_data('all', '재학')
        THEN: Returns dict with total_students, by_department, updated_at
        """
        # Arrange
        Student.objects.bulk_create([
            Student(student_id='2024001', department='컴퓨터공학과', grade=1,
                   program_type='학사', enrollment_status='재학'),
            Student(student_id='2024002', department='전자공학과', grade=1,
                   program_type='석사', enrollment_status='재학'),
        ])
        from data_ingestion.infrastructure.repositories import StudentRepository
        repo = StudentRepository()
        service = StudentDashboardService(repo)

        # Act
        result = service.get_student_dashboard_data(department='all', status='재학')

        # Assert
        assert 'total_students' in result
        assert 'by_department' in result
        assert 'updated_at' in result
        assert result['total_students'] == 2
        assert len(result['by_department']) == 2
        assert isinstance(result['updated_at'], datetime)

    def test_get_student_dashboard_data_filtered_by_department(self, db):
        """
        GIVEN: Students from multiple departments
        WHEN: Filtering by specific department
        THEN: Returns only data for that department
        """
        # Arrange
        Student.objects.bulk_create([
            Student(student_id='2024001', department='컴퓨터공학과', grade=1,
                   program_type='학사', enrollment_status='재학'),
            Student(student_id='2024002', department='컴퓨터공학과', grade=2,
                   program_type='석사', enrollment_status='재학'),
            Student(student_id='2024003', department='전자공학과', grade=1,
                   program_type='학사', enrollment_status='재학'),
        ])
        from data_ingestion.infrastructure.repositories import StudentRepository
        repo = StudentRepository()
        service = StudentDashboardService(repo)

        # Act
        result = service.get_student_dashboard_data(department='컴퓨터공학과', status='all')

        # Assert
        assert result['total_students'] == 2
        assert len(result['by_department']) == 1
        assert result['by_department'][0]['department'] == '컴퓨터공학과'

    # Edge Cases

    def test_get_student_dashboard_data_no_students(self, mock_repository):
        """
        GIVEN: Empty database (no students)
        WHEN: Calling get_student_dashboard_data()
        THEN: Returns total_students=0, by_department=[]
        """
        # Arrange
        mock_repository.get_students_by_filter.return_value = Student.objects.none()
        service = StudentDashboardService(mock_repository)

        # Act
        result = service.get_student_dashboard_data(department='all', status='재학')

        # Assert
        assert result['total_students'] == 0
        assert result['by_department'] == []

    def test_get_student_dashboard_data_invalid_input_raises_error(self, mock_repository):
        """
        GIVEN: Invalid status parameter
        WHEN: Calling get_student_dashboard_data()
        THEN: ValidationError raised before repository access
        """
        # Arrange
        service = StudentDashboardService(mock_repository)

        # Act & Assert
        with pytest.raises(ValidationError):
            service.get_student_dashboard_data(department='all', status='invalid')

        # Verify repository was never called
        mock_repository.get_students_by_filter.assert_not_called()
