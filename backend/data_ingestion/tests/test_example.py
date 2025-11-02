"""
Example unit test to verify pytest-django setup.
Following TDD principles: Fast, Independent, Repeatable, Self-validating, Timely (FIRST).
"""

import pytest


@pytest.mark.unit
class TestPytestSetup:
    """Verify pytest-django environment is correctly configured."""

    def test_pytest_runs_successfully(self):
        """Basic test to verify pytest is working."""
        # Arrange
        expected = 42

        # Act
        result = 40 + 2

        # Assert
        assert result == expected

    def test_fixture_works(self, sample_research_data):
        """Verify fixtures from conftest.py are accessible."""
        # Arrange & Act
        df = sample_research_data

        # Assert
        assert len(df) == 3
        assert '집행ID' in df.columns
        assert df['집행ID'].iloc[0] == 'R001'

    @pytest.mark.parametrize("input_val,expected", [
        (0, 0),
        (100, 100),
        (-10, 0),
        (150, 100),
    ])
    def test_employment_rate_validation(self, input_val, expected):
        """Example of parametrized test for business rule validation."""
        # Arrange & Act: 취업률은 0%~100% 범위로 제한
        result = max(0, min(100, input_val))

        # Assert
        assert result == expected
