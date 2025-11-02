"""
pytest configuration and fixtures for data_ingestion tests.
Following test-plan.md: minimal setup, unittest.mock for isolation.
"""

import pytest
from unittest.mock import Mock
import pandas as pd


@pytest.fixture
def sample_research_data():
    """Sample research project data for testing."""
    return pd.DataFrame({
        '집행ID': ['R001', 'R002', 'R003'],
        '소속학과': ['컴퓨터공학과', '전기공학과', '컴퓨터공학과'],
        '총연구비': [10000000, 20000000, 15000000],
        '집행일자': ['2024-01-15', '2024-02-20', '2024-03-10'],
        '집행금액': [1000000, 2000000, 1500000]
    })


@pytest.fixture
def sample_student_roster():
    """Sample student roster data for testing."""
    return pd.DataFrame({
        '학번': ['2021001', '2021002', '2022001'],
        '학과': ['컴퓨터공학과', '전기공학과', '컴퓨터공학과'],
        '학년': [4, 4, 3],
        '과정구분': ['학사', '학사', '학사'],
        '학적상태': ['재학', '재학', '휴학']
    })


@pytest.fixture
def sample_publication_list():
    """Sample publication data for testing."""
    return pd.DataFrame({
        '논문ID': ['P001', 'P002', 'P003'],
        '학과': ['컴퓨터공학과', '전기공학과', '컴퓨터공학과'],
        '저널등급': ['SCIE', 'KCI', 'SCIE'],
        'Impact Factor': [3.5, None, 2.8]
    })


@pytest.fixture
def sample_department_kpi():
    """Sample department KPI data for testing."""
    return pd.DataFrame({
        '평가년도': [2023, 2023, 2024],
        '학과': ['컴퓨터공학과', '전기공학과', '컴퓨터공학과'],
        '졸업생 취업률(%)': [85.5, 78.3, 87.2],
        '연간 기술이전 수입액(억원)': [5.2, 3.1, 6.5]
    })
