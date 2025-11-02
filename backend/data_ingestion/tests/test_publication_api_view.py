"""
Integration tests for Publication API View.
Following TDD Red-Green-Refactor cycle and plan.md Phase 1.4.

Test Strategy: Integration Tests (API endpoint)
Coverage: HTTP requests/responses, error handling, filter application
"""

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from data_ingestion.infrastructure.models import Publication


class PublicationAPIViewTestCase(TestCase):
    """
    Integration tests for Publication Dashboard API endpoint.

    Tests cover:
    - Successful GET requests with various filters
    - Error responses (400, 404, 500)
    - Query parameter validation
    - Response structure
    """

    def setUp(self):
        """
        Arrange: Set up test client and sample data.

        Test dataset:
        - 2 SCIE papers in Computer Science (IF: 3.5, 4.0)
        - 1 KCI paper in Computer Science (IF: 1.2)
        - 1 SCIE paper in Electronics (IF: 2.0)
        """
        self.client = APIClient()

        # Computer Science - SCIE
        Publication.objects.create(
            publication_id='CS_P1',
            department='컴퓨터공학과',
            journal_tier='SCIE',
            impact_factor=3.5
        )
        Publication.objects.create(
            publication_id='CS_P2',
            department='컴퓨터공학과',
            journal_tier='SCIE',
            impact_factor=4.0
        )

        # Computer Science - KCI
        Publication.objects.create(
            publication_id='CS_P3',
            department='컴퓨터공학과',
            journal_tier='KCI',
            impact_factor=1.2
        )

        # Electronics - SCIE
        Publication.objects.create(
            publication_id='EE_P1',
            department='전자공학과',
            journal_tier='SCIE',
            impact_factor=2.0
        )

    def test_get_publications_distribution_success(self):
        """
        Test: GET /api/dashboard/publications/ returns 200 OK.

        GIVEN: API endpoint exists
        WHEN: GET request without filters
        THEN: Returns 200 with complete data
        """
        # Act
        response = self.client.get('/api/dashboard/publications/')

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        # Verify response structure
        self.assertIn('total_papers', data)
        self.assertIn('avg_impact_factor', data)
        self.assertIn('papers_with_if', data)
        self.assertIn('distribution', data)
        self.assertIn('last_updated', data)

        # Verify data values
        self.assertEqual(data['total_papers'], 4)
        self.assertIsNotNone(data['avg_impact_factor'])
        self.assertEqual(len(data['distribution']), 2)  # SCIE and KCI

    def test_filter_by_department_query_param(self):
        """
        Test: Department filter via query parameter.

        GIVEN: Publications in multiple departments
        WHEN: GET with department='컴퓨터공학과'
        THEN: Returns only Computer Science publications (3 papers)
        """
        # Act
        response = self.client.get('/api/dashboard/publications/', {
            'department': '컴퓨터공학과'
        })

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['total_papers'], 3)

    def test_filter_by_journal_tier_query_param(self):
        """
        Test: Journal tier filter via query parameter.

        GIVEN: SCIE and KCI publications
        WHEN: GET with journal_tier='SCIE'
        THEN: Returns only SCIE publications (3 papers)
        """
        # Act
        response = self.client.get('/api/dashboard/publications/', {
            'journal_tier': 'SCIE'
        })

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['total_papers'], 3)
        self.assertEqual(len(data['distribution']), 1)
        self.assertEqual(data['distribution'][0]['journal_tier'], 'SCIE')

    def test_combined_filters_apply_correctly(self):
        """
        Test: Multiple filters applied together (AND condition).

        GIVEN: Publications across departments and tiers
        WHEN: GET with department='컴퓨터공학과' AND journal_tier='SCIE'
        THEN: Returns Computer Science SCIE papers only (2 papers)
        """
        # Act
        response = self.client.get('/api/dashboard/publications/', {
            'department': '컴퓨터공학과',
            'journal_tier': 'SCIE'
        })

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['total_papers'], 2)

    def test_invalid_department_returns_400(self):
        """
        Test: Nonexistent department returns 400 Bad Request.

        GIVEN: Valid departments in DB
        WHEN: GET with nonexistent department
        THEN: Returns 400 with error code
        """
        # Act
        response = self.client.get('/api/dashboard/publications/', {
            'department': '존재하지않는학과'
        })

        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        error = response.json()
        self.assertIn('error', error)

    def test_invalid_journal_tier_returns_400(self):
        """
        Test: Invalid journal tier returns 400 Bad Request.

        GIVEN: Valid tiers are SCIE, KCI, 기타, all
        WHEN: GET with invalid tier 'INVALID'
        THEN: Returns 400 with error code
        """
        # Act
        response = self.client.get('/api/dashboard/publications/', {
            'journal_tier': 'INVALID'
        })

        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        error = response.json()
        self.assertIn('error', error)

    def test_no_data_returns_empty_distribution(self):
        """
        Test: Empty database returns valid response with zero values.

        GIVEN: No publications in database
        WHEN: GET request
        THEN: Returns 200 with total_papers=0
        """
        # Arrange: Delete all publications
        Publication.objects.all().delete()

        # Act
        response = self.client.get('/api/dashboard/publications/')

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['total_papers'], 0)
        self.assertEqual(len(data['distribution']), 0)
        self.assertIsNone(data['avg_impact_factor'])

    def test_filter_result_empty_returns_400_for_nonexistent_department(self):
        """
        Test: Filter with nonexistent department returns 400.

        GIVEN: Department doesn't exist in DB at all
        WHEN: GET with nonexistent department filter
        THEN: Returns 400 Bad Request (department validation)
        """
        # Act
        response = self.client.get('/api/dashboard/publications/', {
            'department': '존재하지않는학과'
        })

        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_response_includes_last_updated_timestamp(self):
        """
        Test: Response includes last_updated timestamp.

        GIVEN: Valid request
        WHEN: GET request succeeds
        THEN: Response contains 'last_updated' ISO 8601 timestamp
        """
        # Act
        response = self.client.get('/api/dashboard/publications/')

        # Assert
        data = response.json()
        self.assertIn('last_updated', data)
        self.assertIsNotNone(data['last_updated'])

        # Verify ISO 8601 format (basic check)
        from datetime import datetime
        datetime.fromisoformat(data['last_updated'].replace('Z', '+00:00'))

    def test_distribution_items_have_required_fields(self):
        """
        Test: Each distribution item contains all required fields.

        GIVEN: Valid request with results
        WHEN: GET request succeeds
        THEN: Each distribution item has journal_tier, count, percentage, avg_if
        """
        # Act
        response = self.client.get('/api/dashboard/publications/')

        # Assert
        data = response.json()
        for item in data['distribution']:
            self.assertIn('journal_tier', item)
            self.assertIn('count', item)
            self.assertIn('percentage', item)
            self.assertIn('avg_if', item)

    def test_avg_if_calculated_correctly_in_response(self):
        """
        Test: Average Impact Factor calculation in API response.

        GIVEN: 4 papers with IF: 3.5, 4.0, 1.2, 2.0
        WHEN: GET request
        THEN: avg_impact_factor = (3.5 + 4.0 + 1.2 + 2.0) / 4 = 2.675
        """
        # Act
        response = self.client.get('/api/dashboard/publications/')

        # Assert
        data = response.json()
        expected_avg = (3.5 + 4.0 + 1.2 + 2.0) / 4
        self.assertAlmostEqual(data['avg_impact_factor'], expected_avg, places=2)

    def test_percentage_calculation_in_distribution(self):
        """
        Test: Percentage calculation in distribution items.

        GIVEN: 3 SCIE papers, 1 KCI paper (total 4)
        WHEN: GET request
        THEN: SCIE = 75%, KCI = 25%
        """
        # Act
        response = self.client.get('/api/dashboard/publications/')

        # Assert
        data = response.json()
        distribution = {item['journal_tier']: item for item in data['distribution']}

        self.assertAlmostEqual(distribution['SCIE']['percentage'], 75.0, places=1)
        self.assertAlmostEqual(distribution['KCI']['percentage'], 25.0, places=1)

    def test_null_impact_factor_excluded_from_avg(self):
        """
        Test: NULL Impact Factors excluded from average calculation.

        GIVEN: Paper with NULL impact_factor
        WHEN: GET request
        THEN: avg_impact_factor calculated from non-NULL values only
        """
        # Arrange: Add paper without IF
        Publication.objects.create(
            publication_id='NO_IF',
            department='컴퓨터공학과',
            journal_tier='SCIE',
            impact_factor=None
        )

        # Act
        response = self.client.get('/api/dashboard/publications/')

        # Assert
        data = response.json()
        self.assertEqual(data['total_papers'], 5)
        self.assertEqual(data['papers_with_if'], 4)
        # Average should still be calculated from 4 papers with IF
        expected_avg = (3.5 + 4.0 + 1.2 + 2.0) / 4
        self.assertAlmostEqual(data['avg_impact_factor'], expected_avg, places=2)
