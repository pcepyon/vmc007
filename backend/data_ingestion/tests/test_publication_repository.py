"""
Unit tests for PublicationRepository.
Following TDD Red-Green-Refactor cycle and plan.md Phase 1.1.

Test Strategy: Unit Tests (AAA Pattern)
Coverage: Data access layer - filtering, aggregation, department list
"""

from django.test import TestCase
from data_ingestion.infrastructure.models import Publication
from data_ingestion.infrastructure.repositories import PublicationRepository


class PublicationRepositoryTestCase(TestCase):
    """
    Unit tests for PublicationRepository.

    Tests cover:
    - Basic filtering (department, journal_tier)
    - Combined filters (AND conditions)
    - Department list retrieval
    - Empty result handling
    """

    def setUp(self):
        """
        Arrange: Set up test data before each test.

        Test dataset:
        - 5 SCIE publications in Computer Science dept (IF: 3.0 - 5.0)
        - 3 KCI publications in Computer Science dept (IF: 1.0 - 1.4)
        - 2 SCIE publications in Electronics dept (IF: 2.5, 2.8)
        - 1 KCI publication in Mechanical dept (IF: None)
        """
        self.repo = PublicationRepository()

        # Computer Science dept - SCIE papers
        for i in range(5):
            Publication.objects.create(
                paper_id=f'CS_SCIE_{i}',
                department='컴퓨터공학과',
                journal_tier='SCIE',
                impact_factor=3.0 + i * 0.5
            )

        # Computer Science dept - KCI papers
        for i in range(3):
            Publication.objects.create(
                paper_id=f'CS_KCI_{i}',
                department='컴퓨터공학과',
                journal_tier='KCI',
                impact_factor=1.0 + i * 0.2
            )

        # Electronics dept - SCIE papers
        Publication.objects.create(
            paper_id='EE_SCIE_1',
            department='전자공학과',
            journal_tier='SCIE',
            impact_factor=2.5
        )
        Publication.objects.create(
            paper_id='EE_SCIE_2',
            department='전자공학과',
            journal_tier='SCIE',
            impact_factor=2.8
        )

        # Mechanical dept - KCI paper (no IF)
        Publication.objects.create(
            paper_id='ME_KCI_1',
            department='기계공학과',
            journal_tier='KCI',
            impact_factor=None
        )

    def test_get_all_publications(self):
        """
        Test: Get all publications without filters.

        GIVEN: 11 publications in database
        WHEN: get_publications_by_filter() called with no filters
        THEN: Returns all 11 publications
        """
        # Act
        queryset = self.repo.get_publications_by_filter()

        # Assert
        self.assertEqual(queryset.count(), 11)

    def test_filter_by_department(self):
        """
        Test: Filter publications by department.

        GIVEN: Multiple departments with publications
        WHEN: Filter by '컴퓨터공학과'
        THEN: Returns only 8 publications from that department
        """
        # Act
        queryset = self.repo.get_publications_by_filter(department='컴퓨터공학과')

        # Assert
        self.assertEqual(queryset.count(), 8)

        # Verify all returned publications are from correct department
        for pub in queryset:
            self.assertEqual(pub.department, '컴퓨터공학과')

    def test_filter_by_journal_tier(self):
        """
        Test: Filter publications by journal tier.

        GIVEN: Publications with SCIE and KCI tiers
        WHEN: Filter by 'SCIE'
        THEN: Returns only 7 SCIE publications
        """
        # Act
        queryset = self.repo.get_publications_by_filter(journal_tier='SCIE')

        # Assert
        self.assertEqual(queryset.count(), 7)

        # Verify all returned publications are SCIE
        for pub in queryset:
            self.assertEqual(pub.journal_tier, 'SCIE')

    def test_filter_by_department_and_tier_combined(self):
        """
        Test: Filter publications by department AND journal tier.

        GIVEN: Publications across multiple departments and tiers
        WHEN: Filter by department='컴퓨터공학과' AND journal_tier='SCIE'
        THEN: Returns only 5 publications matching both conditions
        """
        # Act
        queryset = self.repo.get_publications_by_filter(
            department='컴퓨터공학과',
            journal_tier='SCIE'
        )

        # Assert
        self.assertEqual(queryset.count(), 5)

        # Verify all results match both filters
        for pub in queryset:
            self.assertEqual(pub.department, '컴퓨터공학과')
            self.assertEqual(pub.journal_tier, 'SCIE')

    def test_filter_by_nonexistent_department_returns_empty(self):
        """
        Test: Filter by department that doesn't exist.

        GIVEN: Publications in various departments
        WHEN: Filter by '존재하지않는학과'
        THEN: Returns empty queryset
        """
        # Act
        queryset = self.repo.get_publications_by_filter(department='존재하지않는학과')

        # Assert
        self.assertEqual(queryset.count(), 0)

    def test_get_all_departments(self):
        """
        Test: Get list of all unique departments.

        GIVEN: Publications in 3 departments
        WHEN: get_all_departments() called
        THEN: Returns set of 3 department names
        """
        # Act
        departments = self.repo.get_all_departments()

        # Assert
        self.assertEqual(len(departments), 3)
        self.assertIn('컴퓨터공학과', departments)
        self.assertIn('전자공학과', departments)
        self.assertIn('기계공학과', departments)

    def test_get_all_departments_returns_distinct_values(self):
        """
        Test: Department list contains no duplicates.

        GIVEN: Multiple publications in same departments
        WHEN: get_all_departments() called
        THEN: Each department appears only once
        """
        # Act
        departments = self.repo.get_all_departments()

        # Assert - check uniqueness
        self.assertEqual(len(departments), len(set(departments)))

    def test_filter_with_all_keyword_returns_all_results(self):
        """
        Test: 'all' keyword in filters returns unfiltered results.

        GIVEN: 11 publications total
        WHEN: Filter with department='all' and journal_tier='all'
        THEN: Returns all 11 publications
        """
        # Act
        queryset = self.repo.get_publications_by_filter(
            department='all',
            journal_tier='all'
        )

        # Assert
        self.assertEqual(queryset.count(), 11)

    def test_queryset_is_lazy_evaluated(self):
        """
        Test: Repository returns Django QuerySet (not list).

        GIVEN: Repository method call
        WHEN: get_publications_by_filter() returns
        THEN: Result is a QuerySet (allows further chaining)
        """
        # Act
        result = self.repo.get_publications_by_filter()

        # Assert
        from django.db.models.query import QuerySet
        self.assertIsInstance(result, QuerySet)
