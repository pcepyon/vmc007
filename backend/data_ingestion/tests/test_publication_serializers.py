"""
Unit tests for Publication Serializers.
Following TDD Red-Green-Refactor cycle and plan.md Phase 1.3.

Test Strategy: Unit Tests (AAA Pattern)
Coverage: Serialization validation, field presence, data format
"""

from django.test import TestCase
from django.utils import timezone
from data_ingestion.api.serializers import (
    PublicationDashboardQuerySerializer,
    PublicationDashboardResponseSerializer
)


class PublicationDashboardQuerySerializerTestCase(TestCase):
    """
    Unit tests for PublicationDashboardQuerySerializer.

    Tests cover:
    - Valid parameter combinations
    - Default values
    - Invalid journal tier validation
    - Field constraints
    """

    def test_valid_query_parameters(self):
        """
        Test: Valid query parameters accepted.

        GIVEN: Valid department and journal_tier
        WHEN: Serializer validates data
        THEN: is_valid() returns True
        """
        # Arrange
        data = {
            'department': '컴퓨터공학과',
            'journal_tier': 'SCIE'
        }

        # Act
        serializer = PublicationDashboardQuerySerializer(data=data)

        # Assert
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['department'], '컴퓨터공학과')
        self.assertEqual(serializer.validated_data['journal_tier'], 'SCIE')

    def test_defaults_applied_when_fields_missing(self):
        """
        Test: Default values for optional fields.

        GIVEN: Empty data dict
        WHEN: Serializer validates
        THEN: Defaults are 'all' for both fields
        """
        # Arrange
        data = {}

        # Act
        serializer = PublicationDashboardQuerySerializer(data=data)

        # Assert
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['department'], 'all')
        self.assertEqual(serializer.validated_data['journal_tier'], 'all')

    def test_all_keyword_accepted_for_department(self):
        """
        Test: 'all' is valid department value.

        GIVEN: department='all'
        WHEN: Serializer validates
        THEN: is_valid() returns True
        """
        # Arrange
        data = {'department': 'all'}

        # Act
        serializer = PublicationDashboardQuerySerializer(data=data)

        # Assert
        self.assertTrue(serializer.is_valid())

    def test_invalid_journal_tier_rejected(self):
        """
        Test: Invalid journal tier value rejected.

        GIVEN: journal_tier='INVALID'
        WHEN: Serializer validates
        THEN: is_valid() returns False with error
        """
        # Arrange
        data = {'journal_tier': 'INVALID'}

        # Act
        serializer = PublicationDashboardQuerySerializer(data=data)

        # Assert
        self.assertFalse(serializer.is_valid())
        self.assertIn('journal_tier', serializer.errors)

    def test_all_valid_journal_tiers_accepted(self):
        """
        Test: All allowed journal tiers accepted.

        GIVEN: Each valid tier value
        WHEN: Serializer validates
        THEN: All are accepted
        """
        valid_tiers = ['all', 'SCIE', 'KCI', '기타']

        for tier in valid_tiers:
            with self.subTest(tier=tier):
                # Arrange
                data = {'journal_tier': tier}

                # Act
                serializer = PublicationDashboardQuerySerializer(data=data)

                # Assert
                self.assertTrue(serializer.is_valid(), f"Tier '{tier}' should be valid")


class PublicationDashboardResponseSerializerTestCase(TestCase):
    """
    Unit tests for PublicationDashboardResponseSerializer.

    Tests cover:
    - Valid response data structure
    - Required field validation
    - Data type validation
    - NULL handling for avg_impact_factor
    """

    def test_valid_response_data_serialization(self):
        """
        Test: Valid response data serialized correctly.

        GIVEN: Complete response data dict
        WHEN: Serializer validates
        THEN: is_valid() returns True
        """
        # Arrange
        data = {
            'total_papers': 156,
            'avg_impact_factor': 2.3,
            'papers_with_if': 145,
            'distribution': [
                {
                    'journal_tier': 'SCIE',
                    'count': 89,
                    'percentage': 57.1,
                    'avg_if': 3.2
                },
                {
                    'journal_tier': 'KCI',
                    'count': 67,
                    'percentage': 42.9,
                    'avg_if': 1.1
                }
            ],
            'last_updated': timezone.now()
        }

        # Act
        serializer = PublicationDashboardResponseSerializer(data=data)

        # Assert
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_avg_impact_factor_can_be_null(self):
        """
        Test: avg_impact_factor accepts NULL.

        GIVEN: avg_impact_factor is None
        WHEN: Serializer validates
        THEN: is_valid() returns True
        """
        # Arrange
        data = {
            'total_papers': 10,
            'avg_impact_factor': None,
            'papers_with_if': 0,
            'distribution': [],
            'last_updated': timezone.now()
        }

        # Act
        serializer = PublicationDashboardResponseSerializer(data=data)

        # Assert
        self.assertTrue(serializer.is_valid())
        self.assertIsNone(serializer.validated_data['avg_impact_factor'])

    def test_missing_required_field_raises_error(self):
        """
        Test: Missing required field rejected.

        GIVEN: total_papers field missing
        WHEN: Serializer validates
        THEN: is_valid() returns False with error
        """
        # Arrange
        data = {
            'avg_impact_factor': 2.3,
            'papers_with_if': 100,
            'distribution': [],
            'last_updated': timezone.now()
        }

        # Act
        serializer = PublicationDashboardResponseSerializer(data=data)

        # Assert
        self.assertFalse(serializer.is_valid())
        self.assertIn('total_papers', serializer.errors)

    def test_empty_distribution_list_accepted(self):
        """
        Test: Empty distribution list is valid.

        GIVEN: distribution = []
        WHEN: Serializer validates
        THEN: is_valid() returns True
        """
        # Arrange
        data = {
            'total_papers': 0,
            'avg_impact_factor': None,
            'papers_with_if': 0,
            'distribution': [],
            'last_updated': timezone.now()
        }

        # Act
        serializer = PublicationDashboardResponseSerializer(data=data)

        # Assert
        self.assertTrue(serializer.is_valid())

    def test_last_updated_timestamp_validation(self):
        """
        Test: last_updated field validates as datetime.

        GIVEN: Valid datetime object
        WHEN: Serializer validates
        THEN: is_valid() returns True
        """
        # Arrange
        now = timezone.now()
        data = {
            'total_papers': 50,
            'avg_impact_factor': 2.5,
            'papers_with_if': 50,
            'distribution': [],
            'last_updated': now
        }

        # Act
        serializer = PublicationDashboardResponseSerializer(data=data)

        # Assert
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['last_updated'], now)

    def test_distribution_item_structure(self):
        """
        Test: Distribution items have correct structure.

        GIVEN: Distribution with all required fields
        WHEN: Serializer validates
        THEN: All fields present in validated data
        """
        # Arrange
        data = {
            'total_papers': 100,
            'avg_impact_factor': 2.0,
            'papers_with_if': 95,
            'distribution': [
                {
                    'journal_tier': 'SCIE',
                    'count': 60,
                    'percentage': 60.0,
                    'avg_if': 3.0
                }
            ],
            'last_updated': timezone.now()
        }

        # Act
        serializer = PublicationDashboardResponseSerializer(data=data)

        # Assert
        self.assertTrue(serializer.is_valid())
        dist_item = serializer.validated_data['distribution'][0]
        self.assertIn('journal_tier', dist_item)
        self.assertIn('count', dist_item)
        self.assertIn('percentage', dist_item)
        self.assertIn('avg_if', dist_item)
