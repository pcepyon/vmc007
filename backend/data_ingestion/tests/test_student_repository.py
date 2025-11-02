"""
Unit tests for StudentRepository.
Following plan.md Phase 1 - Infrastructure Layer tests (TDD RED phase).

Test coverage:
- get_students_by_filter() with various filter combinations
- get_all_departments() for dropdown population
- Edge cases: nonexistent department, empty DB

TDD Cycle: RED → GREEN → REFACTOR
"""

import pytest
from data_ingestion.infrastructure.models import Student
from data_ingestion.infrastructure.repositories import StudentRepository


@pytest.fixture
def sample_students(db):
    """
    Test data fixture: Various students across departments, programs, and statuses.

    Creates 4 students:
    - 2 from 컴퓨터공학과 (1 학사 재학, 1 석사 재학)
    - 1 from 전자공학과 (학사 휴학)
    - 1 from 전자공학과 (학사 졸업)
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
        Student(
            student_id='2024004',
            department='전자공학과',
            grade=3,
            program_type='학사',
            enrollment_status='졸업'
        ),
    ])


@pytest.mark.django_db
class TestStudentRepository:
    """
    StudentRepository unit tests following AAA pattern.
    Each test verifies one specific behavior.
    """

    def test_get_students_by_filter_all_departments_all_status(self, sample_students):
        """
        GIVEN: 4 students in database
        WHEN: Filtering with department='all', status='all'
        THEN: Returns all 4 students
        """
        # Arrange
        repo = StudentRepository()

        # Act
        result = repo.get_students_by_filter(department='all', status='all')

        # Assert
        assert result.count() == 4, "Should return all 4 students"

    def test_get_students_by_filter_specific_department(self, sample_students):
        """
        GIVEN: 4 students (2 from 컴퓨터공학과, 2 from 전자공학과)
        WHEN: Filtering by department='컴퓨터공학과', status='all'
        THEN: Returns only 2 students from 컴퓨터공학과
        """
        # Arrange
        repo = StudentRepository()

        # Act
        result = repo.get_students_by_filter(department='컴퓨터공학과', status='all')

        # Assert
        assert result.count() == 2
        for student in result:
            assert student.department == '컴퓨터공학과'

    def test_get_students_by_filter_enrollment_status_only(self, sample_students):
        """
        GIVEN: 4 students (2 재학, 1 휴학, 1 졸업)
        WHEN: Filtering by department='all', status='재학'
        THEN: Returns only 2 재학 students
        """
        # Arrange
        repo = StudentRepository()

        # Act
        result = repo.get_students_by_filter(department='all', status='재학')

        # Assert
        assert result.count() == 2
        for student in result:
            assert student.enrollment_status == '재학'

    def test_get_students_by_filter_combined_filters(self, sample_students):
        """
        GIVEN: 4 students
        WHEN: Filtering by department='컴퓨터공학과', status='재학'
        THEN: Returns 2 students (both from 컴퓨터공학과 and 재학)
        """
        # Arrange
        repo = StudentRepository()

        # Act
        result = repo.get_students_by_filter(department='컴퓨터공학과', status='재학')

        # Assert
        assert result.count() == 2
        for student in result:
            assert student.department == '컴퓨터공학과'
            assert student.enrollment_status == '재학'

    def test_get_students_by_filter_only_enrollment_status_휴학(self, sample_students):
        """
        GIVEN: 4 students (1 휴학)
        WHEN: Filtering by department='all', status='휴학'
        THEN: Returns 1 student
        """
        # Arrange
        repo = StudentRepository()

        # Act
        result = repo.get_students_by_filter(department='all', status='휴학')

        # Assert
        assert result.count() == 1
        assert result.first().enrollment_status == '휴학'
        assert result.first().department == '전자공학과'

    def test_get_all_departments_returns_distinct_list(self, sample_students):
        """
        GIVEN: 4 students from 2 departments (2 from each)
        WHEN: Calling get_all_departments()
        THEN: Returns list with 2 unique department names (no duplicates)
        """
        # Arrange
        repo = StudentRepository()

        # Act
        result = repo.get_all_departments()

        # Assert
        assert len(result) == 2
        assert '컴퓨터공학과' in result
        assert '전자공학과' in result

    # Edge Cases

    def test_filter_nonexistent_department_returns_empty_queryset(self, sample_students):
        """
        GIVEN: 4 students (none from '기계공학과')
        WHEN: Filtering by department='기계공학과', status='all'
        THEN: Returns empty QuerySet (count == 0)
        """
        # Arrange
        repo = StudentRepository()

        # Act
        result = repo.get_students_by_filter(department='기계공학과', status='all')

        # Assert
        assert result.count() == 0, "Should return empty QuerySet for nonexistent department"

    def test_get_all_departments_empty_db(self, db):
        """
        GIVEN: Empty students table (no data)
        WHEN: Calling get_all_departments()
        THEN: Returns empty list
        """
        # Arrange
        repo = StudentRepository()

        # Act
        result = repo.get_all_departments()

        # Assert
        assert len(result) == 0, "Should return empty list when no students exist"

    def test_get_students_by_filter_empty_db(self, db):
        """
        GIVEN: Empty students table
        WHEN: Filtering by any criteria
        THEN: Returns empty QuerySet
        """
        # Arrange
        repo = StudentRepository()

        # Act
        result = repo.get_students_by_filter(department='all', status='all')

        # Assert
        assert result.count() == 0

    def test_get_students_by_filter_multiple_same_department(self, db):
        """
        GIVEN: 3 students all from same department
        WHEN: Filtering by that department
        THEN: Returns all 3 students
        """
        # Arrange
        Student.objects.bulk_create([
            Student(
                student_id='2024101',
                department='기계공학과',
                grade=1,
                program_type='학사',
                enrollment_status='재학'
            ),
            Student(
                student_id='2024102',
                department='기계공학과',
                grade=2,
                program_type='석사',
                enrollment_status='재학'
            ),
            Student(
                student_id='2024103',
                department='기계공학과',
                grade=3,
                program_type='박사',
                enrollment_status='재학'
            ),
        ])
        repo = StudentRepository()

        # Act
        result = repo.get_students_by_filter(department='기계공학과', status='all')

        # Assert
        assert result.count() == 3
