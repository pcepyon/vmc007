"""
Filter parameter validators for dashboard filtering APIs.
Following spec.md Section 12 - Security Requirements.
Following plan.md Phase 3.1 - Filter Validators implementation.
"""

import re
from rest_framework.exceptions import ValidationError


# Whitelist constants for filter validation
VALID_DEPARTMENTS = [
    'all',
    '컴퓨터공학과',
    '전자공학과',
    '기계공학과',
    '화학공학과',
    '산업공학과',
    '생명공학과',
    '물리학과',
    '수학과',
    '경영학과',
    '경제학과'
]

VALID_ENROLLMENT_STATUS = [
    'all',
    '재학',
    '졸업',
    '휴학'
]

VALID_JOURNAL_TIERS = [
    'all',
    'SCIE',
    'KCI',
    '기타'
]

VALID_PERIODS = [
    'latest',
    '1y',
    '3y'
]


def sanitize_filter_input(value: str) -> str:
    """
    Sanitize filter input to prevent XSS and SQL injection.

    Whitelist: 영문자, 숫자, 한글, 하이픈, 언더스코어만 허용
    SQL 위험 키워드 제거: DROP, SELECT, DELETE, UPDATE, INSERT, --, ;

    Args:
        value: 사용자 입력 필터 값

    Returns:
        살균화된 문자열

    Examples:
        sanitize_filter_input("컴퓨터공학과") -> "컴퓨터공학과"
        sanitize_filter_input("<script>alert('XSS')</script>") -> "alertXSS"
        sanitize_filter_input("'; DROP TABLE students; --") -> ""
    """
    if not isinstance(value, str):
        return str(value)

    # Step 1: Remove SQL dangerous keywords (case-insensitive)
    sql_keywords = ['DROP', 'SELECT', 'DELETE', 'UPDATE', 'INSERT', 'TABLE', 'WHERE', 'UNION', 'EXEC']
    sanitized = value
    for keyword in sql_keywords:
        sanitized = re.sub(rf'\b{keyword}\b', '', sanitized, flags=re.IGNORECASE)

    # Step 2: Remove dangerous character sequences
    dangerous_sequences = ['--', ';', '/*', '*/', '||', '&&']
    for seq in dangerous_sequences:
        sanitized = sanitized.replace(seq, '')

    # Step 3: Remove HTML/JS tags and dangerous keywords
    js_keywords = ['script', 'javascript', 'onerror', 'onload', 'onclick', 'eval']
    for keyword in js_keywords:
        sanitized = re.sub(rf'{keyword}', '', sanitized, flags=re.IGNORECASE)

    # Step 4: Remove all characters except alphanumeric, Korean, hyphen, underscore, spaces
    sanitized = re.sub(r'[^\w가-힣\-_ ]', '', sanitized)

    # Step 5: Clean up multiple spaces and strip
    sanitized = re.sub(r'\s+', ' ', sanitized).strip()

    return sanitized


def validate_filter_params(params: dict) -> None:
    """
    Validate filter parameters against whitelists.

    Validates:
    - department: Must be in VALID_DEPARTMENTS or 'all'
    - year: Must be 'latest' or 4-digit year (YYYY)
    - period: Must be in VALID_PERIODS
    - status: Must be in VALID_ENROLLMENT_STATUS
    - journal_tier: Must be in VALID_JOURNAL_TIERS

    Args:
        params: Dictionary of filter parameters from query string

    Raises:
        ValidationError: If any parameter is invalid

    Examples:
        validate_filter_params({'department': '컴퓨터공학과'})  # OK
        validate_filter_params({'department': 'InvalidDept'})  # Raises ValidationError
    """
    errors = {}

    # Sanitize all string inputs first
    sanitized_params = {}
    for key, value in params.items():
        if isinstance(value, str):
            sanitized_params[key] = sanitize_filter_input(value)
        else:
            sanitized_params[key] = value

    # Validate department
    if 'department' in sanitized_params:
        department = sanitized_params['department']
        if department and department not in VALID_DEPARTMENTS:
            errors['department'] = f'유효하지 않은 학과입니다. 허용된 값: {", ".join(VALID_DEPARTMENTS)}'

    # Validate year
    if 'year' in sanitized_params:
        year = sanitized_params['year']
        if year and year != 'latest':
            # Must be 4-digit year
            if not (year.isdigit() and len(year) == 4):
                errors['year'] = '올바른 연도 형식이 아닙니다. (YYYY 형식 또는 "latest")'

    # Validate period
    if 'period' in sanitized_params:
        period = sanitized_params['period']
        if period and period not in VALID_PERIODS:
            errors['period'] = f'유효하지 않은 기간입니다. 허용된 값: {", ".join(VALID_PERIODS)}'

    # Validate enrollment status
    if 'status' in sanitized_params:
        status = sanitized_params['status']
        if status and status not in VALID_ENROLLMENT_STATUS:
            errors['status'] = f'유효하지 않은 학적상태입니다. 허용된 값: {", ".join(VALID_ENROLLMENT_STATUS)}'

    # Validate journal tier
    if 'journal_tier' in sanitized_params:
        journal_tier = sanitized_params['journal_tier']
        if journal_tier and journal_tier not in VALID_JOURNAL_TIERS:
            errors['journal_tier'] = f'유효하지 않은 저널등급입니다. 허용된 값: {", ".join(VALID_JOURNAL_TIERS)}'

    # Raise ValidationError if any errors found
    if errors:
        raise ValidationError(errors)
