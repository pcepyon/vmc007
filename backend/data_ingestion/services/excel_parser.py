"""
Excel data parser using Pandas.
Following CLAUDE.md: Infrastructure-agnostic Pandas transformations (highly testable).

Core responsibility: Parse, clean, and validate CSV/Excel data from Ecount exports.
This module contains PURE Pandas logic with NO Django/DB dependencies.
"""

import pandas as pd
from typing import Dict, List, Tuple
from datetime import datetime


class ValidationError(Exception):
    """Raised when data validation fails."""
    pass


class ExcelParser:
    """
    Pure Pandas-based parser for Ecount Excel exports.

    Following test-plan.md requirements:
    - 70%+ code coverage target
    - All business rules validated:
      * 집행금액 <= 총연구비
      * 취업률 0%~100%
      * PK duplicate handling
    """

    @staticmethod
    def parse_research_project_data(df: pd.DataFrame) -> pd.DataFrame:
        """
        Parse and validate research project data.

        Required columns:
        - 집행ID (String, PK)
        - 소속학과 (String)
        - 총연구비 (Int/Float)
        - 집행일자 (Date)
        - 집행금액 (Int/Float)

        Business Rules:
        1. 집행ID must be unique
        2. 집행금액 <= 총연구비
        3. All monetary values must be non-negative

        Args:
            df: Raw DataFrame from Excel/CSV

        Returns:
            Cleaned and validated DataFrame

        Raises:
            ValidationError: If validation fails
        """
        # Validation: Required columns
        required_cols = ['집행ID', '소속학과', '총연구비', '집행일자', '집행금액']
        missing_cols = set(required_cols) - set(df.columns)
        if missing_cols:
            raise ValidationError(f"Missing required columns: {missing_cols}")

        # Clean: Remove rows with missing critical data
        df = df.dropna(subset=['집행ID', '총연구비', '집행금액'])

        # Validate: PK uniqueness
        if df['집행ID'].duplicated().any():
            duplicates = df[df['집행ID'].duplicated()]['집행ID'].tolist()
            raise ValidationError(f"Duplicate 집행ID found: {duplicates}")

        # Convert: Data types
        df['총연구비'] = pd.to_numeric(df['총연구비'], errors='coerce')
        df['집행금액'] = pd.to_numeric(df['집행금액'], errors='coerce')
        df['집행일자'] = pd.to_datetime(df['집행일자'], errors='coerce')

        # Validate: Non-negative monetary values
        if (df['총연구비'] < 0).any():
            raise ValidationError("총연구비 cannot be negative")
        if (df['집행금액'] < 0).any():
            raise ValidationError("집행금액 cannot be negative")

        # Validate: Business rule - 집행금액 <= 총연구비
        invalid_rows = df[df['집행금액'] > df['총연구비']]
        if not invalid_rows.empty:
            invalid_ids = invalid_rows['집행ID'].tolist()
            raise ValidationError(
                f"집행금액 exceeds 총연구비 for IDs: {invalid_ids}"
            )

        return df

    @staticmethod
    def parse_student_roster(df: pd.DataFrame) -> pd.DataFrame:
        """
        Parse and validate student roster data.

        Required columns:
        - 학번 (String, PK)
        - 학과 (String)
        - 학년 (Int)
        - 과정구분 (String: 학사/석사/박사)
        - 학적상태 (String: 재학/휴학/졸업)

        Args:
            df: Raw DataFrame from Excel/CSV

        Returns:
            Cleaned and validated DataFrame

        Raises:
            ValidationError: If validation fails
        """
        # Validation: Required columns
        required_cols = ['학번', '학과', '학년', '과정구분', '학적상태']
        missing_cols = set(required_cols) - set(df.columns)
        if missing_cols:
            raise ValidationError(f"Missing required columns: {missing_cols}")

        # Clean: Remove rows with missing critical data
        df = df.dropna(subset=['학번'])

        # Validate: PK uniqueness
        if df['학번'].duplicated().any():
            duplicates = df[df['학번'].duplicated()]['학번'].tolist()
            raise ValidationError(f"Duplicate 학번 found: {duplicates}")

        # Convert: Data types
        df['학년'] = pd.to_numeric(df['학년'], errors='coerce')

        # Validate: 학년 range (1-7 for 학사~박사)
        if (df['학년'] < 1).any() or (df['학년'] > 7).any():
            raise ValidationError("학년 must be between 1 and 7")

        return df

    @staticmethod
    def parse_department_kpi(df: pd.DataFrame) -> pd.DataFrame:
        """
        Parse and validate department KPI data.

        Required columns:
        - 평가년도 (Int)
        - 학과 (String)
        - 졸업생 취업률(%) (Float)
        - 연간 기술이전 수입액(억원) (Float)

        Business Rules:
        1. 취업률 must be 0%~100%
        2. 기술이전 수입액 must be non-negative

        Args:
            df: Raw DataFrame from Excel/CSV

        Returns:
            Cleaned and validated DataFrame

        Raises:
            ValidationError: If validation fails
        """
        # Validation: Required columns
        required_cols = ['평가년도', '학과', '졸업생 취업률(%)', '연간 기술이전 수입액(억원)']
        missing_cols = set(required_cols) - set(df.columns)
        if missing_cols:
            raise ValidationError(f"Missing required columns: {missing_cols}")

        # Clean: Remove rows with missing critical data
        df = df.dropna(subset=['평가년도', '학과'])

        # Convert: Data types
        df['평가년도'] = pd.to_numeric(df['평가년도'], errors='coerce').astype(int)
        df['졸업생 취업률(%)'] = pd.to_numeric(df['졸업생 취업률(%)'], errors='coerce')
        df['연간 기술이전 수입액(억원)'] = pd.to_numeric(df['연간 기술이전 수입액(억원)'], errors='coerce')

        # Validate: 취업률 range (0-100%)
        employment_rate = df['졸업생 취업률(%)']
        if (employment_rate < 0).any() or (employment_rate > 100).any():
            raise ValidationError("졸업생 취업률(%) must be between 0 and 100")

        # Validate: Non-negative tech transfer revenue
        tech_revenue = df['연간 기술이전 수입액(억원)']
        if (tech_revenue < 0).any():
            raise ValidationError("연간 기술이전 수입액 cannot be negative")

        return df

    @staticmethod
    def parse_publication_list(df: pd.DataFrame) -> pd.DataFrame:
        """
        Parse and validate publication list data.

        Required columns:
        - 논문ID (String, PK)
        - 학과 (String)
        - 저널등급 (String: SCIE/KCI/기타)
        - Impact Factor (Float, nullable)

        Business Rules:
        1. 논문ID must be unique
        2. Impact Factor must be non-negative or NULL

        Args:
            df: Raw DataFrame from Excel/CSV

        Returns:
            Cleaned and validated DataFrame

        Raises:
            ValidationError: If validation fails
        """
        # Validation: Required columns
        required_cols = ['논문ID', '학과', '저널등급', 'Impact Factor']
        missing_cols = set(required_cols) - set(df.columns)
        if missing_cols:
            raise ValidationError(f"Missing required columns: {missing_cols}")

        # Clean: Remove rows with missing critical data (but Impact Factor can be NULL)
        df = df.dropna(subset=['논문ID', '학과'])

        # Validate: PK uniqueness
        if df['논문ID'].duplicated().any():
            duplicates = df[df['논문ID'].duplicated()]['논문ID'].tolist()
            raise ValidationError(f"Duplicate 논문ID found: {duplicates}")

        # Convert: Data types (Impact Factor can be NULL)
        df['Impact Factor'] = pd.to_numeric(df['Impact Factor'], errors='coerce')

        # Validate: Non-negative Impact Factor (excluding NaN)
        if df['Impact Factor'].notna().any():
            if (df['Impact Factor'].dropna() < 0).any():
                raise ValidationError("Impact Factor cannot be negative")

        return df
