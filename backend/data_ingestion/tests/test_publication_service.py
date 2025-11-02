"""
Unit tests for PublicationService.
Following TDD Red-Green-Refactor cycle and plan.md Phase 1.2.

Test Strategy: Unit Tests (AAA Pattern)
Coverage: Business logic - aggregation, percentage calculation, input validation
"""

from django.test import TestCase
from django.core.exceptions import ValidationError
from data_ingestion.infrastructure.models import Publication
from data_ingestion.services.publication_service import PublicationService


class PublicationServiceTestCase(TestCase):
    """
    Unit tests for PublicationService business logic.

    Tests cover:
    - Distribution calculation with percentages
    - Average Impact Factor calculation (NULL handling)
    - Filter parameter validation
    - Empty dataset handling
    - Edge cases (single paper, all NULL IF)
    """

    def setUp(self):
        """
        Arrange: Set up test data and service instance.

        Test dataset:
        - 3 SCIE papers (IF: 3.0, 4.0, 5.0) in Computer Science
        - 2 KCI papers (IF: 1.0, 1.5) in Computer Science
        """
        self.service = PublicationService()

        # SCIE papers (3)
        Publication.objects.create(
            paper_id='S1',
            department='컴퓨터공학과',
            journal_tier='SCIE',
            impact_factor=3.0
        )
        Publication.objects.create(
            paper_id='S2',
            department='컴퓨터공학과',
            journal_tier='SCIE',
            impact_factor=4.0
        )
        Publication.objects.create(
            paper_id='S3',
            department='컴퓨터공학과',
            journal_tier='SCIE',
            impact_factor=5.0
        )

        # KCI papers (2)
        Publication.objects.create(
            paper_id='K1',
            department='컴퓨터공학과',
            journal_tier='KCI',
            impact_factor=1.0
        )
        Publication.objects.create(
            paper_id='K2',
            department='컴퓨터공학과',
            journal_tier='KCI',
            impact_factor=1.5
        )

    def test_get_distribution_calculates_total_papers_correctly(self):
        """
        Test: Total papers count.

        GIVEN: 5 publications in database
        WHEN: get_distribution() called
        THEN: total_papers = 5
        """
        # Act
        result = self.service.get_distribution()

        # Assert
        self.assertEqual(result['total_papers'], 5)

    def test_get_distribution_calculates_percentages_correctly(self):
        """
        Test: Journal tier percentages calculation.

        GIVEN: 5 total papers (3 SCIE, 2 KCI)
        WHEN: get_distribution() called
        THEN: SCIE = 60%, KCI = 40%
        """
        # Act
        result = self.service.get_distribution()

        # Assert
        distribution = {item['journal_tier']: item for item in result['distribution']}
        self.assertAlmostEqual(distribution['SCIE']['percentage'], 60.0, places=1)
        self.assertAlmostEqual(distribution['KCI']['percentage'], 40.0, places=1)

    def test_get_distribution_calculates_overall_avg_if_correctly(self):
        """
        Test: Overall average Impact Factor calculation.

        GIVEN: 5 papers with IF: 3.0, 4.0, 5.0, 1.0, 1.5
        WHEN: get_distribution() called
        THEN: avg_impact_factor = (3+4+5+1+1.5)/5 = 2.9
        """
        # Act
        result = self.service.get_distribution()

        # Assert
        self.assertAlmostEqual(result['avg_impact_factor'], 2.9, places=2)
        self.assertEqual(result['papers_with_if'], 5)

    def test_get_distribution_calculates_tier_avg_if_correctly(self):
        """
        Test: Per-tier average Impact Factor calculation.

        GIVEN: SCIE papers (3, 4, 5), KCI papers (1, 1.5)
        WHEN: get_distribution() called
        THEN: SCIE avg = 4.0, KCI avg = 1.25
        """
        # Act
        result = self.service.get_distribution()

        # Assert
        distribution = {item['journal_tier']: item for item in result['distribution']}
        self.assertAlmostEqual(distribution['SCIE']['avg_if'], 4.0, places=2)
        self.assertAlmostEqual(distribution['KCI']['avg_if'], 1.25, places=2)

    def test_avg_if_excludes_null_values(self):
        """
        Test: NULL Impact Factor exclusion from average.

        GIVEN: 5 papers with IF + 1 paper with NULL IF
        WHEN: get_distribution() called
        THEN: avg_impact_factor calculated from 5 papers only
        """
        # Arrange: Add paper without IF
        Publication.objects.create(
            paper_id='N1',
            department='컴퓨터공학과',
            journal_tier='SCIE',
            impact_factor=None
        )

        # Act
        result = self.service.get_distribution()

        # Assert
        self.assertEqual(result['total_papers'], 6)
        self.assertEqual(result['papers_with_if'], 5)
        self.assertAlmostEqual(result['avg_impact_factor'], 2.9, places=2)

    def test_all_null_if_returns_none_for_avg(self):
        """
        Test: All papers with NULL IF.

        GIVEN: All papers have impact_factor = NULL
        WHEN: get_distribution() called
        THEN: avg_impact_factor = None, papers_with_if = 0
        """
        # Arrange: Set all IF to NULL
        Publication.objects.update(impact_factor=None)

        # Act
        result = self.service.get_distribution()

        # Assert
        self.assertIsNone(result['avg_impact_factor'])
        self.assertEqual(result['papers_with_if'], 0)

    def test_filter_by_department_applies_correctly(self):
        """
        Test: Department filter application.

        GIVEN: Papers in multiple departments
        WHEN: get_distribution(department='컴퓨터공학과') called
        THEN: Only Computer Science papers counted
        """
        # Arrange: Add paper from different department
        Publication.objects.create(
            paper_id='E1',
            department='전자공학과',
            journal_tier='SCIE',
            impact_factor=2.0
        )

        # Act
        result = self.service.get_distribution(department='컴퓨터공학과')

        # Assert
        self.assertEqual(result['total_papers'], 5)  # Excludes Electronics dept

    def test_filter_by_journal_tier_applies_correctly(self):
        """
        Test: Journal tier filter application.

        GIVEN: SCIE and KCI papers
        WHEN: get_distribution(journal_tier='SCIE') called
        THEN: Only SCIE papers counted
        """
        # Act
        result = self.service.get_distribution(journal_tier='SCIE')

        # Assert
        self.assertEqual(result['total_papers'], 3)
        self.assertEqual(len(result['distribution']), 1)
        self.assertEqual(result['distribution'][0]['journal_tier'], 'SCIE')

    def test_invalid_journal_tier_raises_validation_error(self):
        """
        Test: Invalid journal tier rejection.

        GIVEN: Service instance
        WHEN: get_distribution(journal_tier='INVALID') called
        THEN: ValidationError raised
        """
        # Act & Assert
        with self.assertRaises(ValidationError) as ctx:
            self.service.get_distribution(journal_tier='INVALID')

        self.assertIn('유효하지 않은 저널등급', str(ctx.exception))

    def test_invalid_department_raises_validation_error(self):
        """
        Test: Nonexistent department rejection.

        GIVEN: Departments exist in DB
        WHEN: get_distribution(department='존재하지않는학과') called
        THEN: ValidationError raised
        """
        # Act & Assert
        with self.assertRaises(ValidationError) as ctx:
            self.service.get_distribution(department='존재하지않는학과')

        self.assertIn('존재하지 않는 학과', str(ctx.exception))

    def test_empty_dataset_returns_zero_values(self):
        """
        Test: Empty database handling.

        GIVEN: No publications in database
        WHEN: get_distribution() called
        THEN: total_papers = 0, distribution = [], avg_if = None
        """
        # Arrange: Delete all publications
        Publication.objects.all().delete()

        # Act
        result = self.service.get_distribution()

        # Assert
        self.assertEqual(result['total_papers'], 0)
        self.assertEqual(len(result['distribution']), 0)
        self.assertIsNone(result['avg_impact_factor'])

    def test_single_paper_displays_100_percent(self):
        """
        Test: Single paper percentage.

        GIVEN: Only 1 publication in database
        WHEN: get_distribution() called
        THEN: percentage = 100.0
        """
        # Arrange: Keep only 1 paper
        Publication.objects.all().delete()
        Publication.objects.create(
            paper_id='ONLY_ONE',
            department='컴퓨터공학과',
            journal_tier='SCIE',
            impact_factor=3.0
        )

        # Act
        result = self.service.get_distribution()

        # Assert
        self.assertEqual(result['total_papers'], 1)
        self.assertEqual(result['distribution'][0]['percentage'], 100.0)

    def test_percentage_sum_is_100(self):
        """
        Test: Sum of percentages equals 100% (within rounding error).

        GIVEN: Multiple journal tiers
        WHEN: get_distribution() called
        THEN: Sum of percentages = 100.0 ± 0.1
        """
        # Act
        result = self.service.get_distribution()

        # Assert
        total_percentage = sum(item['percentage'] for item in result['distribution'])
        self.assertAlmostEqual(total_percentage, 100.0, delta=0.1)

    def test_distribution_sorted_by_count_descending(self):
        """
        Test: Distribution items sorted by count (descending).

        GIVEN: SCIE (3 papers), KCI (2 papers)
        WHEN: get_distribution() called
        THEN: First item is SCIE, second is KCI
        """
        # Act
        result = self.service.get_distribution()

        # Assert
        self.assertEqual(result['distribution'][0]['journal_tier'], 'SCIE')
        self.assertEqual(result['distribution'][1]['journal_tier'], 'KCI')

    def test_response_includes_last_updated_timestamp(self):
        """
        Test: Response includes last_updated field.

        GIVEN: Service instance
        WHEN: get_distribution() called
        THEN: Response contains 'last_updated' timestamp
        """
        # Act
        result = self.service.get_distribution()

        # Assert
        self.assertIn('last_updated', result)
        self.assertIsNotNone(result['last_updated'])
