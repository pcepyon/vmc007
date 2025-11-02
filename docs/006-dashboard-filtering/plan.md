# Dashboard Filtering Implementation Plan

## 1. 개요

대시보드 필터링 기능을 TDD 원칙에 따라 구현하기 위한 모듈화 설계 문서입니다. MVP 목표에 맞춰 **간결하면서도 확장 가능한 구조**를 유지하며, Red-Green-Refactor 사이클을 통해 점진적으로 구현합니다.

### 1.1 핵심 모듈 목록

**Backend (Django):**
- `api/validators.py` - 필터 파라미터 검증 로직 + 보안 검증 (CSRF, XSS, SQL Injection)
- **`api/error_codes.py`** - 표준화된 에러 코드 및 응답 포맷 (신규)
- `services/filtering_service.py` - 필터링 비즈니스 로직 및 집계
- **`utils/filter_helpers.py`** - 재사용 가능한 유틸리티 함수 (신규)
- `infrastructure/repositories.py` - Django ORM 쿼리 (기존 확장)
- `api/views.py` - 필터링 API 엔드포인트 (기존 확장)

**Frontend (React):**
- `hooks/useDashboardFilter.js` - 필터 상태 관리 및 디바운싱
- `hooks/useFilterOptions.js` - 필터 옵션 메타데이터 관리
- `hooks/useDashboardData.js` - 필터 기반 데이터 조회 (기존 확장)
- **`utils/filterHelpers.js`** - 재사용 가능한 유틸리티 함수 (신규)
- `components/dashboard/FilterPanel.jsx` - 필터 UI 컴포넌트
- `components/dashboard/EmptyState.jsx` - 필터 결과 없음 UI
- **`components/ui/ErrorToast.jsx`** - 에러 토스트 알림 컴포넌트 (신규)
- **`components/dashboard/ChartErrorCard.jsx`** - 차트 영역 에러 카드 컴포넌트 (신규)

**E2E Tests:**
- **`tests/e2e/dashboard-filtering.spec.js`** - Playwright E2E 테스트 (신규)

### 1.2 TDD 적용 범위

**Unit Tests (70%):**
- 필터 파라미터 검증 로직 (validators.py)
- 필터 조건 구성 로직 (filtering_service.py)
- React Hook 상태 관리 (useDashboardFilter.js)
- 디바운싱 로직

**Integration Tests (20%):**
- 필터링 API 엔드포인트 전체 플로우
- 병렬 API 호출 로직 (Promise.all)

**Acceptance Tests (10%):**
- 사용자 필터 선택 → 차트 업데이트 E2E 시나리오
- 필터 초기화 플로우

---

## 2. Architecture Diagram

```mermaid
graph TB
    subgraph Frontend
        A[FilterPanel.jsx] --> B[useDashboardFilter]
        A --> C[useFilterOptions]
        B --> D[useDashboardData]
        C --> E[dataApiClient]
        D --> E
    end

    subgraph Backend
        E --> F[views.py]
        F --> G[validators.py]
        F --> H[filtering_service.py]
        H --> I[repositories.py]
        I --> J[(Supabase)]
    end

    subgraph State Flow
        B -.300ms debounce.-> D
        D -.Promise.all.-> E
    end

    style B fill:#e1f5ff
    style H fill:#fff4e1
    style G fill:#ffe1e1
```

**데이터 흐름:**
1. 사용자가 `FilterPanel`에서 필터 선택
2. `useDashboardFilter`가 상태 업데이트 + 300ms 디바운싱
3. `useDashboardData`가 4개 API를 병렬 호출 (Promise.all)
4. Backend `views.py`가 요청 수신
5. `validators.py`로 파라미터 검증
6. `filtering_service.py`로 비즈니스 로직 위임
7. `repositories.py`로 Django ORM 쿼리 실행
8. 집계된 데이터를 JSON으로 응답
9. Frontend에서 차트 리렌더링

---

## 3. Implementation Plan

### 3.1 Backend - Filter Validators (api/validators.py)

**Location:** `backend/data_ingestion/api/validators.py` (신규 생성)

**Responsibility:**
- 필터 파라미터의 Whitelist 검증
- 타입 및 범위 검증
- 보안 취약점 방어 (SQL Injection, XSS)

**Test Strategy:** Unit Tests

**Test Scenarios (Red Phase):**

```python
# Test 1: 유효한 학과 필터 통과
def test_validate_department_filter_with_valid_department():
    # Arrange
    params = {'department': '컴퓨터공학과'}

    # Act & Assert
    validate_filter_params(params)  # Should not raise

# Test 2: 잘못된 학과 필터 거부
def test_validate_department_filter_with_invalid_department():
    # Arrange
    params = {'department': 'InvalidDept'}

    # Act & Assert
    with pytest.raises(ValidationError) as exc_info:
        validate_filter_params(params)
    assert 'department' in exc_info.value.detail

# Test 3: 유효한 연도 형식 (YYYY) 통과
def test_validate_year_filter_with_valid_year():
    # Arrange
    params = {'year': '2024'}

    # Act & Assert
    validate_filter_params(params)  # Should not raise

# Test 4: 잘못된 연도 형식 거부
def test_validate_year_filter_with_invalid_format():
    # Arrange
    params = {'year': '24'}  # 2-digit year

    # Act & Assert
    with pytest.raises(ValidationError) as exc_info:
        validate_filter_params(params)
    assert 'year' in exc_info.value.detail

# Test 5: 'latest' 키워드 허용
def test_validate_year_filter_with_latest_keyword():
    # Arrange
    params = {'year': 'latest'}

    # Act & Assert
    validate_filter_params(params)  # Should not raise

# Test 6: 학적상태 Enum 검증
def test_validate_enrollment_status_with_valid_values():
    # Arrange
    valid_statuses = ['재학', '졸업', '휴학', 'all']

    # Act & Assert
    for status in valid_statuses:
        validate_filter_params({'studentStatus': status})

# Test 7: 저널등급 Enum 검증
def test_validate_journal_tier_with_valid_values():
    # Arrange
    valid_tiers = ['SCIE', 'KCI', 'all']

    # Act & Assert
    for tier in valid_tiers:
        validate_filter_params({'journalTier': tier})

# Edge Case 1: 빈 파라미터 허용 (기본값 적용)
def test_validate_filter_params_with_empty_params():
    # Arrange
    params = {}

    # Act & Assert
    validate_filter_params(params)  # Should not raise

# Edge Case 2: SQL Injection 시도 거부
def test_validate_filter_params_reject_sql_injection():
    # Arrange
    params = {'department': "'; DROP TABLE students; --"}

    # Act & Assert
    with pytest.raises(ValidationError):
        validate_filter_params(params)

# Edge Case 3: XSS 시도 거부
def test_validate_filter_params_reject_xss():
    # Arrange
    params = {'department': '<script>alert("XSS")</script>'}

    # Act & Assert
    with pytest.raises(ValidationError):
        validate_filter_params(params)
```

**Implementation Order (TDD Cycle):**
1. Test 1 작성 → Fail (Red)
2. Whitelist 기반 학과 검증 로직 구현 → Pass (Green)
3. Test 2-7 순차 작성 및 구현
4. Edge Case 1-3 작성 및 구현
5. Refactor: 검증 로직을 함수로 분리 (DRY)

**Dependencies:**
- `rest_framework.exceptions.ValidationError`
- 학과/상태/등급 Whitelist 상수

---

### 3.1.1 Security Validation Requirements

**Location:** Integrated into `api/validators.py` and `api/views.py`

**Responsibility:**
- CSRF 토큰 검증
- 입력값 살균화 (Sanitization)
- SQL Injection 및 XSS 방어
- Rate Limiting

**Test Strategy:** Unit Tests + Integration Tests

**Security Specifications:**

```python
# REQUIRED: CSRF Protection
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator

@method_decorator(csrf_protect, name='dispatch')
class FilteredDashboardView(APIView):
    """
    CSRF 보호가 활성화된 대시보드 필터링 뷰
    """
    pass

# REQUIRED: Input Sanitization
import re

def sanitize_filter_input(value: str) -> str:
    """
    필터 입력값에서 위험한 문자 제거.
    Whitelist: 영문자, 숫자, 한글, 하이픈, 언더스코어

    Args:
        value: 사용자 입력 필터 값

    Returns:
        살균화된 문자열

    Examples:
        sanitize_filter_input("컴퓨터공학과") -> "컴퓨터공학과"
        sanitize_filter_input("<script>alert('XSS')</script>") -> "scriptalertXSSscript"
    """
    return re.sub(r'[^\w가-힣\-_]', '', value)

# REQUIRED: Rate Limiting (MVP: Simple)
# settings.py
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '10/minute',
        'user': '30/minute',
    }
}
```

**Test Scenarios (Red Phase):**

```python
# Test 1: CSRF 토큰 없이 요청 시 거부
def test_filter_api_requires_csrf_token():
    # Arrange
    client = APIClient(enforce_csrf_checks=True)
    url = '/api/dashboard/research-funding/'
    params = {'department': '컴퓨터공학과'}

    # Act
    response = client.get(url, params)

    # Assert
    assert response.status_code == 403  # CSRF token missing

# Test 2: CSRF 토큰이 있으면 허용
def test_filter_api_accepts_valid_csrf_token():
    # Arrange
    client = APIClient(enforce_csrf_checks=True)
    url = '/api/dashboard/research-funding/'

    # Get CSRF token
    csrf_token = client.get('/api/csrf-token/').cookies['csrftoken'].value

    # Act
    response = client.get(url, {'department': '컴퓨터공학과'}, HTTP_X_CSRFTOKEN=csrf_token)

    # Assert
    assert response.status_code == 200

# Test 3: Rate Limiting - 11번째 요청 거부
def test_filter_api_rate_limit():
    # Arrange
    client = APIClient()
    url = '/api/dashboard/research-funding/'

    # Act: Make 11 requests rapidly
    responses = []
    for _ in range(11):
        responses.append(client.get(url))

    # Assert
    assert responses[-1].status_code == 429  # Too many requests
    assert 'Retry-After' in responses[-1].headers

# Test 4: 입력값 살균화 - XSS 차단
def test_sanitize_filter_input_removes_xss():
    # Arrange
    malicious_input = "<script>alert('XSS')</script>"

    # Act
    sanitized = sanitize_filter_input(malicious_input)

    # Assert
    assert '<' not in sanitized
    assert '>' not in sanitized
    assert 'script' not in sanitized

# Test 5: 입력값 살균화 - SQL Injection 차단
def test_sanitize_filter_input_removes_sql_injection():
    # Arrange
    malicious_input = "'; DROP TABLE students; --"

    # Act
    sanitized = sanitize_filter_input(malicious_input)

    # Assert
    assert ';' not in sanitized
    assert '--' not in sanitized
    assert 'DROP' not in sanitized

# Test 6: 입력값 살균화 - 한글 보존
def test_sanitize_filter_input_preserves_korean():
    # Arrange
    korean_input = "컴퓨터공학과"

    # Act
    sanitized = sanitize_filter_input(korean_input)

    # Assert
    assert sanitized == "컴퓨터공학과"

# Test 7: 입력값 살균화 - 하이픈/언더스코어 보존
def test_sanitize_filter_input_preserves_hyphen_underscore():
    # Arrange
    valid_input = "2024-01_data"

    # Act
    sanitized = sanitize_filter_input(valid_input)

    # Assert
    assert sanitized == "2024-01_data"
```

**Implementation Order (TDD Cycle):**
1. Test 1-2 작성 → CSRF 보호 미들웨어 설정
2. Test 3 작성 → DRF Throttling 설정
3. Test 4-7 작성 → sanitize_filter_input 함수 구현
4. Refactor: 살균화 로직을 validator에 통합

**Dependencies:**
- `django.views.decorators.csrf`
- `rest_framework.throttling`
- Python `re` module

---

### 3.2 Backend - Filtering Service (services/filtering_service.py)

**Location:** `backend/data_ingestion/services/filtering_service.py` (신규 생성)

**Responsibility:**
- 필터 조건에 따른 동적 쿼리 조건 구성
- 집계 로직 실행 (잔액, 추이, 학생 수 등)
- 비즈니스 규칙 적용 (AND 조건 결합)

**Test Strategy:** Unit Tests

**Test Scenarios (Red Phase):**

```python
# Test 1: 학과 필터 적용 시 WHERE 절 생성
def test_build_filter_conditions_with_department():
    # Arrange
    filters = {'department': '컴퓨터공학과', 'year': 'latest'}

    # Act
    conditions = FilteringService._build_filter_conditions(filters)

    # Assert
    assert conditions['department'] == '컴퓨터공학과'
    assert 'execution_date__gte' in conditions

# Test 2: 연도 필터 (YYYY) 적용
def test_build_filter_conditions_with_year():
    # Arrange
    filters = {'year': '2024'}

    # Act
    conditions = FilteringService._build_filter_conditions(filters)

    # Assert
    assert conditions['execution_date__year'] == 2024

# Test 3: 'latest' 키워드는 최근 1년 범위로 변환
def test_build_filter_conditions_with_latest_keyword():
    # Arrange
    filters = {'year': 'latest'}

    # Act
    conditions = FilteringService._build_filter_conditions(filters)

    # Assert
    assert 'execution_date__gte' in conditions
    # 날짜가 현재 - 365일인지 검증

# Test 4: 다중 필터 AND 조건 결합
def test_build_filter_conditions_with_multiple_filters():
    # Arrange
    filters = {'department': '컴퓨터공학과', 'year': '2024', 'studentStatus': '재학'}

    # Act
    conditions = FilteringService._build_filter_conditions(filters)

    # Assert
    assert conditions['department'] == '컴퓨터공학과'
    assert conditions['execution_date__year'] == 2024
    assert conditions['enrollment_status'] == '재학'

# Test 5: 'all' 값은 필터 조건에서 제외
def test_build_filter_conditions_exclude_all_keyword():
    # Arrange
    filters = {'department': 'all', 'year': 'latest'}

    # Act
    conditions = FilteringService._build_filter_conditions(filters)

    # Assert
    assert 'department' not in conditions

# Test 6: 연구비 잔액 계산 (총연구비 - 집행금액)
def test_calculate_research_balance(research_projects_fixture):
    # Arrange
    queryset = ResearchProject.objects.filter(department='컴퓨터공학과')

    # Act
    balance = FilteringService._calculate_balance(queryset)

    # Assert
    expected_balance = sum(p.total_budget for p in queryset) - sum(p.execution_amount for p in queryset)
    assert balance == expected_balance

# Test 7: 월별 집행 추이 집계
def test_calculate_monthly_trend(research_projects_fixture):
    # Arrange
    queryset = ResearchProject.objects.filter(department='컴퓨터공학과')

    # Act
    trend = FilteringService._calculate_monthly_trend(queryset)

    # Assert
    assert isinstance(trend, list)
    assert all('month' in item and 'execution_amount' in item for item in trend)

# Test 8: 학과별 학생 수 집계 (과정별 breakdown)
def test_calculate_student_breakdown(students_fixture):
    # Arrange
    queryset = Student.objects.filter(department='컴퓨터공학과', enrollment_status='재학')

    # Act
    breakdown = FilteringService._calculate_student_breakdown(queryset)

    # Assert
    assert '학사' in breakdown
    assert '석사' in breakdown
    assert isinstance(breakdown['학사'], int)

# Edge Case 1: 빈 쿼리셋 처리
def test_calculate_balance_with_empty_queryset():
    # Arrange
    queryset = ResearchProject.objects.none()

    # Act
    balance = FilteringService._calculate_balance(queryset)

    # Assert
    assert balance == 0

# Edge Case 2: NULL Impact Factor 처리
def test_calculate_avg_impact_factor_with_nulls(publications_fixture):
    # Arrange
    queryset = Publication.objects.filter(journal_tier='KCI')  # IF가 NULL일 수 있음

    # Act
    avg_if = FilteringService._calculate_avg_impact_factor(queryset)

    # Assert
    # NULL 제외하고 평균 계산되어야 함
    assert avg_if is not None or queryset.filter(impact_factor__isnull=False).count() == 0
```

**Implementation Order (TDD Cycle):**
1. Test 1-2 작성 → 필터 조건 구성 로직 구현
2. Test 3-5 작성 → 특수 키워드 처리
3. Test 6-8 작성 → 집계 로직 구현
4. Edge Cases → 엣지 케이스 처리
5. Refactor: 집계 함수들을 별도 메서드로 분리

**Dependencies:**
- `infrastructure.repositories.ResearchProjectRepository`
- Django ORM aggregation (Sum, Avg, Count)

---

### 3.3 Backend - API Views (api/views.py 확장)

**Location:** `backend/data_ingestion/api/views.py` (기존 확장)

**Responsibility:**
- 쿼리 파라미터 파싱
- Validator 호출
- Service Layer 위임 (Thin Controller)
- 에러 응답 표준화

**Test Strategy:** Integration Tests

**Test Scenarios (Red Phase):**

```python
# Test 1: GET /api/dashboard/research-funding/?department=컴퓨터공학과
def test_research_funding_filter_by_department(api_client, research_projects_fixture):
    # Arrange
    url = '/api/dashboard/research-funding/'
    params = {'department': '컴퓨터공학과'}

    # Act
    response = api_client.get(url, params)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert 'current_balance' in data
    assert 'trend' in data

# Test 2: GET /api/dashboard/students/?status=재학
def test_students_filter_by_enrollment_status(api_client, students_fixture):
    # Arrange
    url = '/api/dashboard/students/'
    params = {'status': '재학'}

    # Act
    response = api_client.get(url, params)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data['total_students'] > 0

# Test 3: 다중 필터 조합 (학과 + 연도)
def test_research_funding_filter_by_department_and_year(api_client, research_projects_fixture):
    # Arrange
    url = '/api/dashboard/research-funding/'
    params = {'department': '컴퓨터공학과', 'year': '2024'}

    # Act
    response = api_client.get(url, params)

    # Assert
    assert response.status_code == 200
    # 응답 데이터가 필터 조건을 만족하는지 검증

# Test 4: 잘못된 필터 값 → 400 Bad Request
def test_research_funding_filter_with_invalid_department(api_client):
    # Arrange
    url = '/api/dashboard/research-funding/'
    params = {'department': 'InvalidDept'}

    # Act
    response = api_client.get(url, params)

    # Assert
    assert response.status_code == 400
    data = response.json()
    assert data['error'] == 'invalid_parameter'
    assert 'department' in data['details']

# Test 5: 필터 결과 없음 → 빈 배열 반환
def test_research_funding_filter_with_no_results(api_client):
    # Arrange
    url = '/api/dashboard/research-funding/'
    params = {'department': '존재하지않는학과', 'year': '2024'}

    # Act
    response = api_client.get(url, params)

    # Assert
    assert response.status_code == 200  # 빈 결과도 성공 응답
    data = response.json()
    assert data['current_balance'] == 0
    assert data['trend'] == []

# Test 6: GET /api/dashboard/filter-options/ - 필터 옵션 메타데이터
def test_get_filter_options(api_client, research_projects_fixture, students_fixture):
    # Arrange
    url = '/api/dashboard/filter-options/'

    # Act
    response = api_client.get(url)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert 'departments' in data
    assert 'years' in data
    assert 'student_statuses' in data
    assert 'journal_tiers' in data
    assert '컴퓨터공학과' in data['departments']

# Edge Case 1: 파라미터 없이 호출 시 기본값 적용
def test_research_funding_filter_without_params(api_client, research_projects_fixture):
    # Arrange
    url = '/api/dashboard/research-funding/'

    # Act
    response = api_client.get(url)

    # Assert
    assert response.status_code == 200
    # 기본값(department=all, year=latest) 적용됨

# Edge Case 2: 서버 에러 시 500 응답
def test_research_funding_filter_with_server_error(api_client, mocker):
    # Arrange
    url = '/api/dashboard/research-funding/'
    mocker.patch('services.filtering_service.FilteringService.get_research_funding', side_effect=Exception('DB Error'))

    # Act
    response = api_client.get(url)

    # Assert
    assert response.status_code == 500
    data = response.json()
    assert data['error'] == 'server_error'
```

**Implementation Order (TDD Cycle):**
1. Test 1 작성 → research_funding_view 필터 기능 추가
2. Test 2-3 작성 → 다른 엔드포인트에 필터 기능 추가
3. Test 4-5 작성 → 에러 핸들링 추가
4. Test 6 작성 → filter-options API 구현
5. Edge Cases → 엣지 케이스 처리
6. Refactor: 에러 응답 포맷을 공통 함수로 추출

**Dependencies:**
- `api.validators.validate_filter_params`
- `services.filtering_service.FilteringService`
- DRF Serializers (기존)

---

### 3.3.1 Error Response Specification

**Location:** `backend/data_ingestion/api/error_codes.py` (신규 생성)

**Responsibility:**
- 표준화된 에러 코드 정의
- 일관된 에러 응답 포맷 제공
- 프론트엔드와 에러 코드 계약 명시

**Error Code Definitions:**

```python
# api/error_codes.py (NEW FILE)

class FilterErrorCode:
    """
    대시보드 필터링 API의 표준 에러 코드.
    프론트엔드와 계약(Contract)으로 사용.
    """
    VALIDATION_ERROR = 'validation_error'
    INVALID_PARAMETER = 'invalid_parameter'
    SERVER_ERROR = 'server_error'
    RATE_LIMIT_EXCEEDED = 'rate_limit_exceeded'
    NO_DATA_FOUND = 'no_data_found'
    CSRF_ERROR = 'csrf_error'

# Standard Error Response Format
# {
#   "error": "invalid_parameter",  # Error code from FilterErrorCode
#   "message": "유효하지 않은 파라미터입니다.",  # User-friendly Korean message
#   "details": {
#     "field": "department",
#     "value": "InvalidDept",
#     "valid_values": ["전체 학과", "컴퓨터공학과", "전자공학과"]
#   },
#   "timestamp": "2025-11-02T14:35:22Z",
#   "request_id": "a1b2c3d4"  # For debugging
# }


def format_error_response(error_code: str, message: str, details: dict = None) -> dict:
    """
    표준화된 에러 응답 생성.

    Args:
        error_code: FilterErrorCode 클래스의 에러 코드
        message: 사용자에게 표시할 한글 메시지
        details: 추가 상세 정보 (선택적)

    Returns:
        표준 포맷의 에러 응답 딕셔너리

    Examples:
        format_error_response(
            FilterErrorCode.INVALID_PARAMETER,
            "유효하지 않은 학과입니다.",
            {"field": "department", "value": "InvalidDept"}
        )
    """
    import uuid
    from datetime import datetime

    response = {
        "error": error_code,
        "message": message,
        "timestamp": datetime.utcnow().isoformat() + 'Z',
        "request_id": str(uuid.uuid4())[:8]
    }

    if details:
        response["details"] = details

    return response
```

**Test Strategy:** Unit Tests

**Test Scenarios (Red Phase):**

```python
# Test 1: 에러 응답 포맷 검증
def test_format_error_response_basic():
    # Arrange
    error_code = FilterErrorCode.INVALID_PARAMETER
    message = "유효하지 않은 파라미터입니다."

    # Act
    response = format_error_response(error_code, message)

    # Assert
    assert response['error'] == 'invalid_parameter'
    assert response['message'] == message
    assert 'timestamp' in response
    assert 'request_id' in response

# Test 2: 에러 응답에 details 포함
def test_format_error_response_with_details():
    # Arrange
    error_code = FilterErrorCode.VALIDATION_ERROR
    message = "필터 검증 실패"
    details = {"field": "year", "value": "invalid", "reason": "형식 오류"}

    # Act
    response = format_error_response(error_code, message, details)

    # Assert
    assert response['details'] == details
    assert response['details']['field'] == 'year'

# Test 3: timestamp가 ISO 8601 형식
def test_format_error_response_timestamp_format():
    # Arrange & Act
    response = format_error_response(FilterErrorCode.SERVER_ERROR, "서버 오류")

    # Assert
    assert response['timestamp'].endswith('Z')
    # ISO 8601 형식 검증
    from datetime import datetime
    datetime.fromisoformat(response['timestamp'].replace('Z', '+00:00'))  # Should not raise

# Test 4: request_id가 고유함
def test_format_error_response_unique_request_id():
    # Arrange & Act
    response1 = format_error_response(FilterErrorCode.SERVER_ERROR, "오류 1")
    response2 = format_error_response(FilterErrorCode.SERVER_ERROR, "오류 2")

    # Assert
    assert response1['request_id'] != response2['request_id']

# Integration Test: API가 표준 에러 응답 반환
def test_filter_api_returns_standard_error_format(api_client):
    # Arrange
    url = '/api/dashboard/research-funding/'
    params = {'department': 'InvalidDept'}

    # Act
    response = api_client.get(url, params)

    # Assert
    assert response.status_code == 400
    data = response.json()
    assert data['error'] == FilterErrorCode.INVALID_PARAMETER
    assert 'message' in data
    assert 'details' in data
    assert 'timestamp' in data
    assert 'request_id' in data
    assert data['details']['field'] == 'department'

# Integration Test: Rate Limit 초과 시 에러 코드
def test_filter_api_rate_limit_error_code(api_client):
    # Arrange
    url = '/api/dashboard/research-funding/'

    # Act: 11번 요청
    for _ in range(10):
        api_client.get(url)

    response = api_client.get(url)

    # Assert
    assert response.status_code == 429
    data = response.json()
    assert data['error'] == FilterErrorCode.RATE_LIMIT_EXCEEDED
    assert '잠시 후 다시 시도' in data['message']

# Integration Test: 서버 에러 시 에러 코드
def test_filter_api_server_error_code(api_client, mocker):
    # Arrange
    url = '/api/dashboard/research-funding/'
    mocker.patch('services.filtering_service.FilteringService.get_research_funding', side_effect=Exception('DB Error'))

    # Act
    response = api_client.get(url)

    # Assert
    assert response.status_code == 500
    data = response.json()
    assert data['error'] == FilterErrorCode.SERVER_ERROR
    assert '일시적인 오류' in data['message']
    assert 'request_id' in data  # 디버깅용
```

**Error Code Usage in views.py:**

```python
# api/views.py
from .error_codes import FilterErrorCode, format_error_response
from rest_framework.response import Response
from rest_framework import status

class ResearchFundingView(APIView):
    def get(self, request):
        try:
            # Validation
            validate_filter_params(request.query_params)

            # Service logic
            data = FilteringService.get_research_funding(request.query_params)

            return Response(data, status=status.HTTP_200_OK)

        except ValidationError as e:
            return Response(
                format_error_response(
                    FilterErrorCode.VALIDATION_ERROR,
                    "필터 파라미터 검증에 실패했습니다.",
                    {"validation_errors": e.detail}
                ),
                status=status.HTTP_400_BAD_REQUEST
            )

        except ValueError as e:
            return Response(
                format_error_response(
                    FilterErrorCode.INVALID_PARAMETER,
                    str(e),
                    {"parameter": request.query_params}
                ),
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            logger.error(f"Unexpected error in filtering: {str(e)}", exc_info=True)
            return Response(
                format_error_response(
                    FilterErrorCode.SERVER_ERROR,
                    "일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
                    None  # 보안을 위해 내부 에러 상세 정보는 숨김
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
```

**Implementation Order (TDD Cycle):**
1. Test 1-4 작성 → format_error_response 함수 구현
2. Integration Tests 작성 → views.py에 에러 핸들링 추가
3. Refactor: 에러 메시지를 constants.py로 분리

**Dependencies:**
- Python `uuid` module
- Python `datetime` module
- DRF `Response`, `status`

---

### 3.4 Frontend - Filter State Hook (hooks/useDashboardFilter.js)

**Location:** `frontend/src/hooks/useDashboardFilter.js` (신규 생성)

**Responsibility:**
- 필터 상태 관리 (React State)
- 디바운싱 로직 (300ms)
- 필터 변경/초기화 핸들러

**Test Strategy:** Unit Tests

**Test Scenarios (Red Phase):**

```javascript
// Test 1: 초기 상태 값 확인
test('useDashboardFilter should initialize with default filter values', () => {
  // Arrange & Act
  const { result } = renderHook(() => useDashboardFilter());

  // Assert
  expect(result.current.filters.department).toBe('all');
  expect(result.current.filters.year).toBe('latest');
  expect(result.current.filters.studentStatus).toBe('all');
  expect(result.current.filters.journalTier).toBe('all');
  expect(result.current.isFilterApplied).toBe(false);
});

// Test 2: 필터 변경 시 state 업데이트
test('handleFilterChange should update filter state', () => {
  // Arrange
  const { result } = renderHook(() => useDashboardFilter());

  // Act
  act(() => {
    result.current.handleFilterChange('department', '컴퓨터공학과');
  });

  // Assert
  expect(result.current.filters.department).toBe('컴퓨터공학과');
});

// Test 3: 디바운싱 - 300ms 이전에는 isFilterApplied가 false
test('handleFilterChange should debounce for 300ms', async () => {
  // Arrange
  jest.useFakeTimers();
  const { result } = renderHook(() => useDashboardFilter());

  // Act
  act(() => {
    result.current.handleFilterChange('department', '컴퓨터공학과');
    jest.advanceTimersByTime(299);
  });

  // Assert
  expect(result.current.isFilterApplied).toBe(false);

  // Cleanup
  jest.useRealTimers();
});

// Test 4: 디바운싱 - 300ms 후에 isFilterApplied가 true
test('handleFilterChange should set isFilterApplied to true after 300ms', async () => {
  // Arrange
  jest.useFakeTimers();
  const { result } = renderHook(() => useDashboardFilter());

  // Act
  act(() => {
    result.current.handleFilterChange('department', '컴퓨터공학과');
    jest.advanceTimersByTime(300);
  });

  // Assert
  expect(result.current.isFilterApplied).toBe(true);

  // Cleanup
  jest.useRealTimers();
});

// Test 5: 빠른 연속 변경 시 마지막 값만 적용 (디바운싱)
test('handleFilterChange should debounce rapid changes', async () => {
  // Arrange
  jest.useFakeTimers();
  const { result } = renderHook(() => useDashboardFilter());

  // Act
  act(() => {
    result.current.handleFilterChange('department', '컴퓨터공학과');
    jest.advanceTimersByTime(100);
    result.current.handleFilterChange('department', '전자공학과');
    jest.advanceTimersByTime(100);
    result.current.handleFilterChange('department', '기계공학과');
    jest.advanceTimersByTime(300);
  });

  // Assert
  expect(result.current.filters.department).toBe('기계공학과');
  expect(result.current.isFilterApplied).toBe(true);

  // Cleanup
  jest.useRealTimers();
});

// Test 6: 필터 초기화
test('handleResetFilters should reset all filters to default', () => {
  // Arrange
  const { result } = renderHook(() => useDashboardFilter());

  act(() => {
    result.current.handleFilterChange('department', '컴퓨터공학과');
    result.current.handleFilterChange('year', '2024');
  });

  // Act
  act(() => {
    result.current.handleResetFilters();
  });

  // Assert
  expect(result.current.filters.department).toBe('all');
  expect(result.current.filters.year).toBe('latest');
  expect(result.current.isFilterApplied).toBe(false);
});

// Test 7: Cleanup on unmount - 디바운스 타이머 정리
test('should cleanup debounce timer on unmount', () => {
  // Arrange
  jest.useFakeTimers();
  const clearTimeoutSpy = jest.spyOn(global, 'clearTimeout');
  const { result, unmount } = renderHook(() => useDashboardFilter());

  // Act
  act(() => {
    result.current.handleFilterChange('department', '컴퓨터공학과');
  });

  unmount();

  // Assert
  expect(clearTimeoutSpy).toHaveBeenCalled();

  // Cleanup
  jest.useRealTimers();
  clearTimeoutSpy.mockRestore();
});
```

**Implementation Order (TDD Cycle):**
1. Test 1 작성 → 기본 Hook 구조 및 초기값 설정
2. Test 2 작성 → handleFilterChange 구현
3. Test 3-5 작성 → 디바운싱 로직 구현 (useRef + setTimeout)
4. Test 6 작성 → handleResetFilters 구현
5. Test 7 작성 → useEffect cleanup 추가
6. Refactor: 디바운스 로직을 커스텀 Hook으로 분리 고려

**Dependencies:**
- React (useState, useRef, useEffect, useCallback)

---

### 3.5 Frontend - Filter Options Hook (hooks/useFilterOptions.js)

**Location:** `frontend/src/hooks/useFilterOptions.js` (신규 생성)

**Responsibility:**
- 필터 옵션 메타데이터 로딩 (학과 목록, 연도 목록 등)
- API 실패 시 Fallback 기본값 제공
- 로딩 상태 관리

**Test Strategy:** Unit Tests

**Test Scenarios (Red Phase):**

```javascript
// Test 1: 성공 시 필터 옵션 로드
test('useFilterOptions should fetch and set filter options', async () => {
  // Arrange
  const mockOptions = {
    departments: ['전체 학과', '컴퓨터공학과', '전자공학과'],
    years: ['최근 1년', '2024년', '2023년'],
    student_statuses: ['전체', '재학', '졸업'],
    journal_tiers: ['SCIE', 'KCI']
  };

  jest.spyOn(dataApiClient, 'get').mockResolvedValue({ data: mockOptions });

  // Act
  const { result, waitForNextUpdate } = renderHook(() => useFilterOptions());
  await waitForNextUpdate();

  // Assert
  expect(result.current.options).toEqual(mockOptions);
  expect(result.current.isLoading).toBe(false);
});

// Test 2: API 실패 시 기본값 유지
test('useFilterOptions should use default options on API failure', async () => {
  // Arrange
  jest.spyOn(dataApiClient, 'get').mockRejectedValue(new Error('Network error'));
  jest.spyOn(console, 'warn').mockImplementation(() => {});

  // Act
  const { result, waitForNextUpdate } = renderHook(() => useFilterOptions());
  await waitForNextUpdate();

  // Assert
  expect(result.current.options.departments).toContain('전체 학과');
  expect(result.current.isLoading).toBe(false);
  expect(console.warn).toHaveBeenCalled();

  // Cleanup
  console.warn.mockRestore();
});

// Test 3: 초기 로딩 상태 확인
test('useFilterOptions should start with isLoading true', () => {
  // Arrange & Act
  const { result } = renderHook(() => useFilterOptions());

  // Assert
  expect(result.current.isLoading).toBe(true);
});

// Test 4: API 호출은 마운트 시 1회만
test('useFilterOptions should fetch options only once on mount', async () => {
  // Arrange
  const getSpy = jest.spyOn(dataApiClient, 'get').mockResolvedValue({ data: {} });

  // Act
  const { rerender, waitForNextUpdate } = renderHook(() => useFilterOptions());
  await waitForNextUpdate();

  rerender();
  rerender();

  // Assert
  expect(getSpy).toHaveBeenCalledTimes(1);

  // Cleanup
  getSpy.mockRestore();
});
```

**Implementation Order (TDD Cycle):**
1. Test 1 작성 → API 호출 및 성공 케이스 구현
2. Test 2 작성 → 에러 핸들링 및 Fallback
3. Test 3-4 작성 → 로딩 상태 및 useEffect 의존성 관리
4. Refactor: 기본값 상수를 별도 파일로 분리

**Dependencies:**
- `api/dataApiClient.js`
- React (useState, useEffect)

---

### 3.6 Frontend - Data Fetching Hook (hooks/useDashboardData.js 확장)

**Location:** `frontend/src/hooks/useDashboardData.js` (기존 확장)

**Responsibility:**
- 필터 파라미터를 포함한 API 호출
- 4개 API 병렬 호출 (Promise.all)
- 로딩 및 에러 상태 관리

**Test Strategy:** Integration Tests

**Test Scenarios (Red Phase):**

```javascript
// Test 1: 필터 변경 시 API 재호출
test('useDashboardData should refetch when filters change', async () => {
  // Arrange
  const getSpy = jest.spyOn(dataApiClient, 'get').mockResolvedValue({ data: {} });
  const initialFilters = { department: 'all', year: 'latest' };

  // Act
  const { result, rerender, waitForNextUpdate } = renderHook(
    ({ filters }) => useDashboardData(filters),
    { initialProps: { filters: initialFilters } }
  );

  await waitForNextUpdate();

  const newFilters = { department: '컴퓨터공학과', year: '2024' };
  rerender({ filters: newFilters });

  await waitForNextUpdate();

  // Assert
  expect(getSpy).toHaveBeenCalledTimes(8);  // 초기 4회 + 재호출 4회
  expect(getSpy).toHaveBeenCalledWith('/api/dashboard/research-funding/', { params: newFilters });

  // Cleanup
  getSpy.mockRestore();
});

// Test 2: Promise.all로 4개 API 병렬 호출
test('useDashboardData should fetch all APIs in parallel', async () => {
  // Arrange
  const mockResponses = [
    { data: { current_balance: 1530000000 } },
    { data: { total_students: 1234 } },
    { data: { total_papers: 156 } },
    { data: { trend: [] } }
  ];

  const getSpy = jest.spyOn(dataApiClient, 'get')
    .mockImplementation((url) => {
      if (url.includes('research-funding')) return Promise.resolve(mockResponses[0]);
      if (url.includes('students')) return Promise.resolve(mockResponses[1]);
      if (url.includes('publications')) return Promise.resolve(mockResponses[2]);
      if (url.includes('department-kpi')) return Promise.resolve(mockResponses[3]);
    });

  // Act
  const { result, waitForNextUpdate } = renderHook(() =>
    useDashboardData({ department: 'all', year: 'latest' })
  );

  await waitForNextUpdate();

  // Assert
  expect(result.current.data.researchFunding).toEqual(mockResponses[0].data);
  expect(result.current.data.students).toEqual(mockResponses[1].data);
  expect(result.current.data.publications).toEqual(mockResponses[2].data);
  expect(result.current.data.departmentKpi).toEqual(mockResponses[3].data);

  // Cleanup
  getSpy.mockRestore();
});

// Test 3: API 에러 시 에러 상태 설정
test('useDashboardData should set error state on API failure', async () => {
  // Arrange
  const error = new Error('Network error');
  jest.spyOn(dataApiClient, 'get').mockRejectedValue(error);
  jest.spyOn(console, 'error').mockImplementation(() => {});

  // Act
  const { result, waitForNextUpdate } = renderHook(() =>
    useDashboardData({ department: 'all', year: 'latest' })
  );

  await waitForNextUpdate();

  // Assert
  expect(result.current.error).toBe(error);
  expect(result.current.isLoading).toBe(false);

  // Cleanup
  console.error.mockRestore();
});

// Test 4: 로딩 상태 관리
test('useDashboardData should manage loading state correctly', async () => {
  // Arrange
  jest.spyOn(dataApiClient, 'get').mockResolvedValue({ data: {} });

  // Act
  const { result, waitForNextUpdate } = renderHook(() =>
    useDashboardData({ department: 'all', year: 'latest' })
  );

  // Assert - 초기 로딩
  expect(result.current.isLoading).toBe(true);

  await waitForNextUpdate();

  // Assert - 로딩 완료
  expect(result.current.isLoading).toBe(false);
});
```

**Implementation Order (TDD Cycle):**
1. Test 1 작성 → filters를 useEffect 의존성에 추가
2. Test 2 작성 → Promise.all 병렬 호출 구현
3. Test 3-4 작성 → 에러 및 로딩 상태 관리
4. Refactor: API 호출 로직을 별도 함수로 추출

**Dependencies:**
- `api/dataApiClient.js`
- React (useState, useEffect)

---

### 3.7 Frontend - Filter Panel Component (components/dashboard/FilterPanel.jsx)

**Location:** `frontend/src/components/dashboard/FilterPanel.jsx` (신규 생성)

**Responsibility:**
- 필터 UI 렌더링 (드롭다운, 라디오, 체크박스)
- 사용자 입력 이벤트 핸들링
- 필터 초기화 버튼

**Test Strategy:** Unit Tests (Presentation Layer는 최소 테스트)

**Test Scenarios (Red Phase):**

```javascript
// Test 1: 필터 드롭다운 렌더링
test('FilterPanel should render department dropdown', () => {
  // Arrange
  const mockProps = {
    filters: { department: 'all' },
    onFilterChange: jest.fn(),
    onReset: jest.fn(),
    isApplied: false
  };

  // Act
  render(<FilterPanel {...mockProps} />);

  // Assert
  expect(screen.getByTestId('department-filter')).toBeInTheDocument();
});

// Test 2: 드롭다운 선택 시 onFilterChange 호출
test('FilterPanel should call onFilterChange when dropdown value changes', () => {
  // Arrange
  const mockOnFilterChange = jest.fn();
  const mockProps = {
    filters: { department: 'all' },
    onFilterChange: mockOnFilterChange,
    onReset: jest.fn(),
    isApplied: false
  };

  // Act
  render(<FilterPanel {...mockProps} />);
  const dropdown = screen.getByTestId('department-filter');

  fireEvent.change(dropdown, { target: { value: '컴퓨터공학과' } });

  // Assert
  expect(mockOnFilterChange).toHaveBeenCalledWith('department', '컴퓨터공학과');
});

// Test 3: 필터 초기화 버튼 클릭 시 onReset 호출
test('FilterPanel should call onReset when reset button is clicked', () => {
  // Arrange
  const mockOnReset = jest.fn();
  const mockProps = {
    filters: { department: '컴퓨터공학과' },
    onFilterChange: jest.fn(),
    onReset: mockOnReset,
    isApplied: true
  };

  // Act
  render(<FilterPanel {...mockProps} />);
  const resetButton = screen.getByText('전체 보기');

  fireEvent.click(resetButton);

  // Assert
  expect(mockOnReset).toHaveBeenCalled();
});

// Test 4: isApplied=true일 때 초기화 버튼 활성화
test('FilterPanel should enable reset button when filters are applied', () => {
  // Arrange
  const mockProps = {
    filters: { department: '컴퓨터공학과' },
    onFilterChange: jest.fn(),
    onReset: jest.fn(),
    isApplied: true
  };

  // Act
  render(<FilterPanel {...mockProps} />);
  const resetButton = screen.getByText('전체 보기');

  // Assert
  expect(resetButton).not.toBeDisabled();
});

// Test 5: isApplied=false일 때 초기화 버튼 비활성화
test('FilterPanel should disable reset button when no filters are applied', () => {
  // Arrange
  const mockProps = {
    filters: { department: 'all' },
    onFilterChange: jest.fn(),
    onReset: jest.fn(),
    isApplied: false
  };

  // Act
  render(<FilterPanel {...mockProps} />);
  const resetButton = screen.getByText('전체 보기');

  // Assert
  expect(resetButton).toBeDisabled();
});
```

**Implementation Order (TDD Cycle):**
1. Test 1 작성 → 기본 컴포넌트 구조 및 드롭다운 렌더링
2. Test 2 작성 → onChange 이벤트 핸들러 연결
3. Test 3-5 작성 → 초기화 버튼 구현
4. Refactor: 드롭다운을 재사용 가능한 컴포넌트로 분리

**Dependencies:**
- React
- UI 라이브러리 (선택적)

**QA Sheet (Presentation Layer):**

수동 테스트 항목:
- [ ] 드롭다운 클릭 시 옵션 목록이 표시됨
- [ ] 옵션 선택 시 드롭다운에 선택 값이 반영됨
- [ ] 필터 초기화 버튼 클릭 시 모든 드롭다운이 기본값으로 변경됨
- [ ] 필터 적용 시 "전체 보기" 버튼이 활성화되고 색상이 변경됨
- [ ] 키보드 네비게이션 (Tab, Enter)이 정상 작동함
- [ ] 모바일 화면에서도 드롭다운이 정상 표시됨

---

### 3.8 Frontend - Empty State Component (components/dashboard/EmptyState.jsx)

**Location:** `frontend/src/components/dashboard/EmptyState.jsx` (신규 생성)

**Responsibility:**
- 필터 결과 없음 UI 표시
- 필터 초기화 추천 메시지

**Test Strategy:** Unit Tests

**Test Scenarios (Red Phase):**

```javascript
// Test 1: 빈 상태 메시지 렌더링
test('EmptyState should render empty message', () => {
  // Arrange & Act
  render(<EmptyState onReset={jest.fn()} />);

  // Assert
  expect(screen.getByText(/선택한 조건에 해당하는 데이터가 없습니다/i)).toBeInTheDocument();
});

// Test 2: 필터 초기화 버튼 클릭 시 onReset 호출
test('EmptyState should call onReset when reset button is clicked', () => {
  // Arrange
  const mockOnReset = jest.fn();

  // Act
  render(<EmptyState onReset={mockOnReset} />);
  const resetButton = screen.getByText('전체 보기');

  fireEvent.click(resetButton);

  // Assert
  expect(mockOnReset).toHaveBeenCalled();
});

// Test 3: 추천 메시지 표시
test('EmptyState should render recommendation message', () => {
  // Arrange & Act
  render(<EmptyState onReset={jest.fn()} />);

  // Assert
  expect(screen.getByText(/다른 필터 조건을 선택하거나/i)).toBeInTheDocument();
});
```

**Implementation Order (TDD Cycle):**
1. Test 1 작성 → 기본 메시지 렌더링
2. Test 2 작성 → 초기화 버튼 연결
3. Test 3 작성 → 추천 메시지 추가
4. Refactor: CSS 스타일링 추가

**Dependencies:**
- React

**QA Sheet (Presentation Layer):**

수동 테스트 항목:
- [ ] 빈 상태 일러스트레이션이 표시됨
- [ ] 메시지가 중앙 정렬되어 있음
- [ ] 초기화 버튼이 강조 표시됨 (파란색 테두리)
- [ ] 다크 모드에서도 가독성이 유지됨

---

### 3.9 Frontend - Error Display Components

**Location:**
- `frontend/src/components/ui/ErrorToast.jsx` (신규 생성)
- `frontend/src/components/dashboard/ChartErrorCard.jsx` (신규 생성)

**Responsibility:**
- API 에러를 사용자에게 시각적으로 표시
- 에러 토스트 알림 (transient errors)
- 차트 영역 에러 카드 (persistent errors)
- 재시도 버튼 제공

**Test Strategy:** Unit Tests + QA Sheet

#### 3.9.1 ErrorToast Component

**Responsibility:**
- 일시적 에러를 화면 우측 하단에 토스트로 표시
- 5초 후 자동 닫힘
- 닫기 버튼 제공
- 다중 에러 스택 지원

**Test Scenarios (Red Phase):**

```javascript
// Test 1: 에러 메시지 표시
test('ErrorToast should display error message', () => {
  // Arrange
  const message = "네트워크 오류가 발생했습니다";

  // Act
  render(<ErrorToast message={message} onClose={jest.fn()} />);

  // Assert
  expect(screen.getByText(message)).toBeInTheDocument();
});

// Test 2: 5초 후 자동 닫힘
test('ErrorToast should auto-dismiss after 5 seconds', () => {
  // Arrange
  jest.useFakeTimers();
  const mockOnClose = jest.fn();

  // Act
  render(<ErrorToast message="Test Error" onClose={mockOnClose} />);
  jest.advanceTimersByTime(5000);

  // Assert
  expect(mockOnClose).toHaveBeenCalled();

  // Cleanup
  jest.useRealTimers();
});

// Test 3: 닫기 버튼 클릭 시 즉시 닫힘
test('ErrorToast should close immediately when close button clicked', () => {
  // Arrange
  const mockOnClose = jest.fn();
  render(<ErrorToast message="Test Error" onClose={mockOnClose} />);

  // Act
  const closeButton = screen.getByTestId('toast-close-button');
  fireEvent.click(closeButton);

  // Assert
  expect(mockOnClose).toHaveBeenCalled();
});

// Test 4: 에러 타입에 따른 아이콘 표시
test('ErrorToast should display error icon for error type', () => {
  // Arrange & Act
  render(<ErrorToast message="Error" type="error" onClose={jest.fn()} />);

  // Assert
  const icon = screen.getByTestId('toast-error-icon');
  expect(icon).toBeInTheDocument();
});

// Test 5: 경고 타입 토스트
test('ErrorToast should display warning icon for warning type', () => {
  // Arrange & Act
  render(<ErrorToast message="Warning" type="warning" onClose={jest.fn()} />);

  // Assert
  const icon = screen.getByTestId('toast-warning-icon');
  expect(icon).toBeInTheDocument();
});
```

**Component Specification:**

```jsx
// components/ui/ErrorToast.jsx

/**
 * ErrorToast Component
 *
 * Props:
 * - message: string (required) - 표시할 에러 메시지
 * - type: 'error' | 'warning' | 'info' (default: 'error')
 * - onClose: function (required) - 닫힘 핸들러
 * - duration: number (default: 5000ms) - 자동 닫힘 시간
 *
 * Position: fixed, bottom-right (우측 하단)
 * Z-index: 9999
 */

export default function ErrorToast({ message, type = 'error', onClose, duration = 5000 }) {
  // Auto-dismiss after duration
  // Close button handler
  // Icon rendering based on type
}
```

**Implementation Order (TDD Cycle):**
1. Test 1 작성 → 기본 메시지 렌더링
2. Test 2 작성 → useEffect로 자동 닫힘 구현
3. Test 3 작성 → 닫기 버튼 핸들러
4. Test 4-5 작성 → 타입별 아이콘 렌더링
5. Refactor: CSS 스타일링 추가

---

#### 3.9.2 ChartErrorCard Component

**Responsibility:**
- 차트 영역에서 데이터 로딩 실패 시 에러 카드 표시
- 재시도 버튼 제공
- request_id 표시 (디버깅용)

**Test Scenarios (Red Phase):**

```javascript
// Test 1: 에러 메시지 표시
test('ChartErrorCard should display error message', () => {
  // Arrange
  const message = "데이터를 불러올 수 없습니다";

  // Act
  render(<ChartErrorCard message={message} onRetry={jest.fn()} />);

  // Assert
  expect(screen.getByText(/데이터를 불러올 수 없습니다/i)).toBeInTheDocument();
});

// Test 2: 재시도 버튼 클릭 시 onRetry 호출
test('ChartErrorCard should call onRetry when retry button clicked', () => {
  // Arrange
  const mockOnRetry = jest.fn();
  render(<ChartErrorCard message="Error" onRetry={mockOnRetry} />);

  // Act
  const retryButton = screen.getByText('재시도');
  fireEvent.click(retryButton);

  // Assert
  expect(mockOnRetry).toHaveBeenCalled();
});

// Test 3: request_id 표시 (옵션)
test('ChartErrorCard should display request_id when provided', () => {
  // Arrange
  const requestId = 'a1b2c3d4';

  // Act
  render(<ChartErrorCard message="Error" onRetry={jest.fn()} requestId={requestId} />);

  // Assert
  expect(screen.getByText(/a1b2c3d4/i)).toBeInTheDocument();
});

// Test 4: request_id 없을 때 숨김
test('ChartErrorCard should not display request_id section when not provided', () => {
  // Arrange & Act
  render(<ChartErrorCard message="Error" onRetry={jest.fn()} />);

  // Assert
  expect(screen.queryByText(/요청 ID/i)).not.toBeInTheDocument();
});

// Test 5: 에러 아이콘 표시
test('ChartErrorCard should display error icon', () => {
  // Arrange & Act
  render(<ChartErrorCard message="Error" onRetry={jest.fn()} />);

  // Assert
  const icon = screen.getByTestId('chart-error-icon');
  expect(icon).toBeInTheDocument();
});
```

**Component Specification:**

```jsx
// components/dashboard/ChartErrorCard.jsx

/**
 * ChartErrorCard Component
 *
 * Props:
 * - message: string (required) - 표시할 에러 메시지
 * - onRetry: function (required) - 재시도 버튼 핸들러
 * - requestId: string (optional) - 디버깅용 request ID
 *
 * Layout: 차트 영역 전체를 차지하는 카드
 * Background: 연한 빨간색 (#FFF5F5)
 * Border: 1px solid #FEB2B2
 */

export default function ChartErrorCard({ message, onRetry, requestId }) {
  // Error icon
  // Error message
  // Retry button
  // Conditional request_id display
}
```

**Implementation Order (TDD Cycle):**
1. Test 1 작성 → 기본 메시지 렌더링
2. Test 2 작성 → 재시도 버튼 핸들러
3. Test 3-4 작성 → requestId 조건부 렌더링
4. Test 5 작성 → 에러 아이콘 추가
5. Refactor: CSS 스타일링 및 접근성 개선

---

#### 3.9.3 Error Handling Integration

**useDashboardData.js에 에러 처리 통합:**

```javascript
// hooks/useDashboardData.js (확장)

import { useState, useEffect } from 'react';
import dataApiClient from '../api/dataApiClient';

export function useDashboardData(filters) {
  const [data, setData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const [researchFunding, students, publications, departmentKpi] = await Promise.all([
        dataApiClient.get('/api/dashboard/research-funding/', { params: filters }),
        dataApiClient.get('/api/dashboard/students/', { params: filters }),
        dataApiClient.get('/api/dashboard/publications/', { params: filters }),
        dataApiClient.get('/api/dashboard/department-kpi/', { params: filters }),
      ]);

      setData({
        researchFunding: researchFunding.data,
        students: students.data,
        publications: publications.data,
        departmentKpi: departmentKpi.data,
      });
    } catch (err) {
      // 백엔드의 표준 에러 응답 파싱
      const errorResponse = err.response?.data || {};
      setError({
        message: errorResponse.message || '데이터를 불러오는 중 오류가 발생했습니다',
        code: errorResponse.error || 'unknown_error',
        requestId: errorResponse.request_id,
      });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [filters]);

  return { data, isLoading, error, refetch: fetchData };
}
```

**Dashboard Page에서 에러 표시:**

```jsx
// pages/Dashboard.jsx (확장)

import ErrorToast from '../components/ui/ErrorToast';
import ChartErrorCard from '../components/dashboard/ChartErrorCard';

export function Dashboard() {
  const { filters, handleFilterChange, handleResetFilters } = useDashboardFilter();
  const { data, isLoading, error, refetch } = useDashboardData(filters);
  const [showErrorToast, setShowErrorToast] = useState(false);

  // 에러 발생 시 토스트 표시
  useEffect(() => {
    if (error) {
      setShowErrorToast(true);
    }
  }, [error]);

  return (
    <div>
      <FilterPanel filters={filters} onChange={handleFilterChange} />

      {error ? (
        <ChartErrorCard
          message={error.message}
          onRetry={refetch}
          requestId={error.requestId}
        />
      ) : (
        <Charts data={data} isLoading={isLoading} />
      )}

      {showErrorToast && error && (
        <ErrorToast
          message={error.message}
          onClose={() => setShowErrorToast(false)}
        />
      )}
    </div>
  );
}
```

**Test for Integration:**

```javascript
// Test: 에러 발생 시 ErrorToast와 ChartErrorCard 모두 표시
test('Dashboard should display both ErrorToast and ChartErrorCard on error', async () => {
  // Arrange
  const error = { message: '네트워크 오류', code: 'server_error', requestId: 'abc123' };
  jest.spyOn(dataApiClient, 'get').mockRejectedValue({ response: { data: error } });

  // Act
  render(<Dashboard />);
  await waitFor(() => expect(screen.getByText(/네트워크 오류/i)).toBeInTheDocument());

  // Assert
  expect(screen.getByTestId('error-toast')).toBeInTheDocument();
  expect(screen.getByTestId('chart-error-card')).toBeInTheDocument();
  expect(screen.getByText('재시도')).toBeInTheDocument();
});
```

**QA Sheet (Presentation Layer):**

수동 테스트 항목:
- [ ] API 에러 발생 시 화면 우측 하단에 에러 토스트가 표시됨
- [ ] 에러 토스트가 5초 후 자동으로 사라짐
- [ ] 에러 토스트의 닫기 버튼(X) 클릭 시 즉시 사라짐
- [ ] 차트 영역에 ChartErrorCard가 표시됨
- [ ] ChartErrorCard의 "재시도" 버튼 클릭 시 API 재호출됨
- [ ] 재시도 성공 시 ChartErrorCard가 사라지고 차트가 표시됨
- [ ] request_id가 ChartErrorCard 하단에 작게 표시됨
- [ ] 에러 메시지가 한글로 명확히 표시됨
- [ ] Rate Limit 에러 시 "잠시 후 다시 시도해주세요" 메시지 표시
- [ ] 다중 에러 발생 시 토스트가 스택 형태로 쌓임
- [ ] 모바일 화면에서도 에러 UI가 정상 표시됨

**Dependencies:**
- React (useState, useEffect)
- CSS 스타일링

---

### 3.10 Acceptance Tests (E2E with Playwright)

**Location:** `tests/e2e/dashboard-filtering.spec.js` (신규 생성)

**Responsibility:**
- 사용자 관점의 전체 플로우 검증
- 필터 적용 → 차트 업데이트 시나리오
- 에러 핸들링 시나리오
- 성능 벤치마크
- 크로스 브라우저 테스트

**Test Strategy:** E2E Tests (Acceptance Tests - 10%)

**Test Scenarios:**

```javascript
// tests/e2e/dashboard-filtering.spec.js

import { test, expect } from '@playwright/test';

// Scenario 1: Happy Path - 학과 필터 적용
test('User filters dashboard by department', async ({ page }) => {
  // Arrange
  await page.goto('http://localhost:3000/dashboard');
  await page.waitForSelector('[data-testid="research-funding-chart"]');

  // Act
  await page.selectOption('[data-testid="department-filter"]', '컴퓨터공학과');
  await page.waitForTimeout(300);  // Debounce
  await page.waitForResponse(response =>
    response.url().includes('/api/dashboard/research-funding/') &&
    response.status() === 200
  );

  // Assert
  const chartTitle = await page.textContent('[data-testid="chart-title"]');
  expect(chartTitle).toContain('컴퓨터공학과');

  // Screenshot
  await page.screenshot({ path: 'screenshots/filter-by-department.png' });
});

// Scenario 2: 다중 필터 조합
test('User applies multiple filters (department + year)', async ({ page }) => {
  // Arrange
  await page.goto('http://localhost:3000/dashboard');
  await page.waitForSelector('[data-testid="department-filter"]');

  // Act
  await page.selectOption('[data-testid="department-filter"]', '컴퓨터공학과');
  await page.selectOption('[data-testid="year-filter"]', '2024');
  await page.waitForTimeout(300);
  await page.waitForResponse(response =>
    response.url().includes('department=컴퓨터공학과') &&
    response.url().includes('year=2024')
  );

  // Assert
  const url = page.url();
  expect(url).toContain('department=컴퓨터공학과');
  expect(url).toContain('year=2024');

  // Screenshot
  await page.screenshot({ path: 'screenshots/multiple-filters.png' });
});

// Scenario 3: 필터 초기화
test('User resets filters to default', async ({ page }) => {
  // Arrange
  await page.goto('http://localhost:3000/dashboard');
  await page.selectOption('[data-testid="department-filter"]', '컴퓨터공학과');
  await page.waitForTimeout(300);

  // Act
  await page.click('[data-testid="reset-filters-button"]');
  await page.waitForResponse(response =>
    response.url().includes('/api/dashboard/research-funding/') &&
    response.status() === 200
  );

  // Assert
  const dropdownValue = await page.inputValue('[data-testid="department-filter"]');
  expect(dropdownValue).toBe('all');

  const resetButton = await page.locator('[data-testid="reset-filters-button"]');
  await expect(resetButton).toBeDisabled();
});

// Scenario 4: 에러 핸들링 - API 실패
test('User sees error when filter API fails', async ({ page }) => {
  // Arrange
  await page.goto('http://localhost:3000/dashboard');

  // Mock API failure
  await page.route('**/api/dashboard/research-funding/*', route =>
    route.fulfill({
      status: 400,
      contentType: 'application/json',
      body: JSON.stringify({
        error: 'invalid_parameter',
        message: '유효하지 않은 파라미터입니다',
        details: { field: 'department' },
        timestamp: new Date().toISOString(),
        request_id: 'test123'
      })
    })
  );

  // Act
  await page.selectOption('[data-testid="department-filter"]', '컴퓨터공학과');
  await page.waitForTimeout(300);

  // Assert
  const errorToast = await page.textContent('[data-testid="error-toast"]');
  expect(errorToast).toContain('유효하지 않은 파라미터입니다');

  const chartErrorCard = await page.textContent('[data-testid="chart-error-card"]');
  expect(chartErrorCard).toContain('재시도');

  // Screenshot
  await page.screenshot({ path: 'screenshots/error-state.png' });
});

// Scenario 5: 에러 재시도
test('User retries after error and succeeds', async ({ page }) => {
  // Arrange
  await page.goto('http://localhost:3000/dashboard');

  let callCount = 0;
  await page.route('**/api/dashboard/research-funding/*', route => {
    callCount++;
    if (callCount === 1) {
      // First call fails
      route.fulfill({ status: 500, body: JSON.stringify({ error: 'server_error' }) });
    } else {
      // Second call succeeds
      route.continue();
    }
  });

  await page.selectOption('[data-testid="department-filter"]', '컴퓨터공학과');
  await page.waitForTimeout(300);

  // Act: Click retry button
  await page.click('[data-testid="chart-error-retry-button"]');
  await page.waitForResponse(response =>
    response.url().includes('/api/dashboard/research-funding/') &&
    response.status() === 200
  );

  // Assert
  const chart = await page.locator('[data-testid="research-funding-chart"]');
  await expect(chart).toBeVisible();

  const errorCard = await page.locator('[data-testid="chart-error-card"]');
  await expect(errorCard).not.toBeVisible();
});

// Scenario 6: 빈 결과 상태
test('User sees empty state when no data matches filter', async ({ page }) => {
  // Arrange
  await page.goto('http://localhost:3000/dashboard');

  await page.route('**/api/dashboard/research-funding/*', route =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        current_balance: 0,
        trend: []
      })
    })
  );

  // Act
  await page.selectOption('[data-testid="department-filter"]', '존재하지않는학과');
  await page.waitForTimeout(300);

  // Assert
  const emptyState = await page.textContent('[data-testid="empty-state"]');
  expect(emptyState).toContain('선택한 조건에 해당하는 데이터가 없습니다');

  const resetButton = await page.locator('[data-testid="empty-state-reset-button"]');
  await expect(resetButton).toBeVisible();
});

// Performance Benchmark
test('Filter application completes within 500ms', async ({ page }) => {
  // Arrange
  await page.goto('http://localhost:3000/dashboard');
  await page.waitForSelector('[data-testid="department-filter"]');

  // Act
  const startTime = Date.now();
  await page.selectOption('[data-testid="department-filter"]', '컴퓨터공학과');
  await page.waitForResponse(response =>
    response.url().includes('/api/dashboard/research-funding/')
  );
  const endTime = Date.now();

  // Assert
  const duration = endTime - startTime;
  expect(duration).toBeLessThan(500);  // 500ms SLA

  console.log(`Filter application took ${duration}ms`);
});

// Cross-browser Test (Safari)
test('Filter works correctly on Safari', async ({ page, browserName }) => {
  test.skip(browserName !== 'webkit', 'Safari-specific test');

  await page.goto('http://localhost:3000/dashboard');
  await page.selectOption('[data-testid="department-filter"]', '컴퓨터공학과');
  await page.waitForTimeout(300);

  const chart = await page.locator('[data-testid="research-funding-chart"]');
  await expect(chart).toBeVisible();
});
```

**Playwright Configuration:**

```javascript
// playwright.config.js

import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  timeout: 30000,
  expect: {
    timeout: 5000,
  },
  fullyParallel: false,  // Run tests sequentially for consistent state
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['json', { outputFile: 'test-results.json' }],
  ],
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
  ],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
});
```

**Implementation Order:**
1. Playwright 설치 및 설정
2. Scenario 1-3 작성 및 실행 (Happy Path)
3. Scenario 4-5 작성 (Error Handling)
4. Scenario 6 작성 (Empty State)
5. Performance Benchmark 추가
6. Cross-browser Tests 추가

**Dependencies:**
- `@playwright/test`
- Node.js 16+

---

### 3.11 Helper Utilities

**Location:**
- `backend/data_ingestion/utils/filter_helpers.py` (신규 생성)
- `frontend/src/utils/filterHelpers.js` (신규 생성)

**Responsibility:**
- 재사용 가능한 유틸리티 함수
- 날짜 파싱, 필터 직렬화, 디바운싱

**Test Strategy:** Unit Tests

#### 3.11.1 Backend Utilities

**Location:** `backend/data_ingestion/utils/filter_helpers.py`

```python
# utils/filter_helpers.py

from datetime import datetime, timedelta
from typing import Dict, Any
from urllib.parse import urlencode


def parse_year_filter(year_param: str) -> Dict[str, Any]:
    """
    연도 필터를 Django ORM 쿼리 조건으로 변환.

    Args:
        year_param: 'latest' | 'YYYY' 형식

    Returns:
        Django ORM filter 조건 딕셔너리

    Examples:
        parse_year_filter('latest') -> {'execution_date__gte': datetime(2024, 1, 1)}
        parse_year_filter('2024') -> {'execution_date__year': 2024}

    Raises:
        ValueError: 잘못된 연도 형식
    """
    if year_param == 'latest':
        one_year_ago = datetime.now() - timedelta(days=365)
        return {'execution_date__gte': one_year_ago}

    try:
        year = int(year_param)
        if year < 2000 or year > 2100:
            raise ValueError(f"Invalid year range: {year}")
        return {'execution_date__year': year}
    except ValueError:
        raise ValueError(f"Invalid year format: {year_param}")


def serialize_filter_params(filters: Dict[str, Any]) -> str:
    """
    필터 딕셔너리를 URL 쿼리 스트링으로 변환.
    'all' 값은 제외함.

    Args:
        filters: 필터 딕셔너리

    Returns:
        URL 쿼리 스트링

    Examples:
        serialize_filter_params({'department': 'all', 'year': '2024'})
        -> 'year=2024'
    """
    filtered_params = {
        k: v for k, v in filters.items()
        if v and v != 'all'
    }
    return urlencode(filtered_params)


def calculate_date_range(period: str) -> tuple[datetime, datetime]:
    """
    기간 키워드를 날짜 범위로 변환.

    Args:
        period: 'latest' | 'this_year' | 'last_year'

    Returns:
        (start_date, end_date) 튜플

    Examples:
        calculate_date_range('this_year') -> (2025-01-01, 2025-12-31)
    """
    now = datetime.now()

    if period == 'latest':
        return (now - timedelta(days=365), now)
    elif period == 'this_year':
        return (datetime(now.year, 1, 1), datetime(now.year, 12, 31))
    elif period == 'last_year':
        return (datetime(now.year - 1, 1, 1), datetime(now.year - 1, 12, 31))
    else:
        raise ValueError(f"Unknown period: {period}")
```

**Test Scenarios:**

```python
# Test 1: 'latest' 키워드 파싱
def test_parse_year_filter_with_latest():
    # Act
    result = parse_year_filter('latest')

    # Assert
    assert 'execution_date__gte' in result
    # 약 1년 전 날짜인지 검증
    one_year_ago = datetime.now() - timedelta(days=365)
    assert (result['execution_date__gte'] - one_year_ago).days < 1

# Test 2: YYYY 형식 파싱
def test_parse_year_filter_with_year():
    # Act
    result = parse_year_filter('2024')

    # Assert
    assert result == {'execution_date__year': 2024}

# Test 3: 잘못된 연도 형식 거부
def test_parse_year_filter_with_invalid_format():
    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        parse_year_filter('24')
    assert 'Invalid year format' in str(exc_info.value)

# Test 4: 필터 직렬화 - 'all' 제외
def test_serialize_filter_params_exclude_all():
    # Arrange
    filters = {'department': 'all', 'year': '2024', 'status': '재학'}

    # Act
    result = serialize_filter_params(filters)

    # Assert
    assert 'department' not in result
    assert 'year=2024' in result
    assert 'status' in result

# Test 5: 빈 필터 직렬화
def test_serialize_filter_params_empty():
    # Arrange
    filters = {'department': 'all', 'year': 'all'}

    # Act
    result = serialize_filter_params(filters)

    # Assert
    assert result == ''

# Test 6: 날짜 범위 계산 - this_year
def test_calculate_date_range_this_year():
    # Act
    start, end = calculate_date_range('this_year')

    # Assert
    now = datetime.now()
    assert start.year == now.year
    assert start.month == 1
    assert start.day == 1
    assert end.year == now.year
    assert end.month == 12
    assert end.day == 31
```

---

#### 3.11.2 Frontend Utilities

**Location:** `frontend/src/utils/filterHelpers.js`

```javascript
// utils/filterHelpers.js

import { useState, useEffect } from 'react';

/**
 * 디바운스 커스텀 Hook.
 * useDashboardFilter에서 추출하여 재사용 가능하게 함.
 *
 * @param {any} value - 디바운스할 값
 * @param {number} delay - 지연 시간 (ms)
 * @returns {any} 디바운스된 값
 *
 * @example
 * const debouncedSearchTerm = useDebounce(searchTerm, 300);
 */
export function useDebounce(value, delay = 300) {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}


/**
 * 필터 파라미터를 API 요청용으로 포맷.
 * 'all' 값과 빈 문자열을 제거.
 *
 * @param {Object} filters - 필터 객체
 * @returns {Object} 정제된 필터 객체
 *
 * @example
 * formatFilterParams({ department: 'all', year: '2024', status: '' })
 * // Returns: { year: '2024' }
 */
export function formatFilterParams(filters) {
  return Object.entries(filters)
    .filter(([_, value]) => value && value !== 'all')
    .reduce((acc, [key, value]) => ({ ...acc, [key]: value }), {});
}


/**
 * 에러 응답에서 사용자 친화적 메시지 추출.
 *
 * @param {Object} errorResponse - 백엔드 에러 응답
 * @returns {string} 표시할 에러 메시지
 *
 * @example
 * extractErrorMessage({ message: '유효하지 않은 파라미터입니다' })
 * // Returns: '유효하지 않은 파라미터입니다'
 */
export function extractErrorMessage(errorResponse) {
  if (!errorResponse) {
    return '알 수 없는 오류가 발생했습니다';
  }

  // 백엔드 표준 에러 응답 포맷
  if (errorResponse.message) {
    return errorResponse.message;
  }

  // Axios 에러 fallback
  if (errorResponse.response?.data?.message) {
    return errorResponse.response.data.message;
  }

  return '데이터를 불러오는 중 오류가 발생했습니다';
}


/**
 * 필터 적용 여부 확인.
 * 모든 필터가 기본값('all', 'latest')인지 검사.
 *
 * @param {Object} filters - 필터 객체
 * @returns {boolean} 필터 적용 여부
 *
 * @example
 * isFilterApplied({ department: 'all', year: 'latest' })  // false
 * isFilterApplied({ department: '컴퓨터공학과', year: 'latest' })  // true
 */
export function isFilterApplied(filters) {
  const defaultValues = ['all', 'latest', ''];
  return Object.values(filters).some(value => !defaultValues.includes(value));
}
```

**Test Scenarios:**

```javascript
// Test 1: useDebounce - 값 지연 업데이트
test('useDebounce should delay value update', () => {
  // Arrange
  jest.useFakeTimers();
  const { result, rerender } = renderHook(
    ({ value }) => useDebounce(value, 300),
    { initialProps: { value: 'initial' } }
  );

  // Act
  rerender({ value: 'updated' });
  jest.advanceTimersByTime(299);

  // Assert
  expect(result.current).toBe('initial');

  // Act
  jest.advanceTimersByTime(1);

  // Assert
  expect(result.current).toBe('updated');

  // Cleanup
  jest.useRealTimers();
});

// Test 2: formatFilterParams - 'all' 및 빈 값 제거
test('formatFilterParams should remove all and empty values', () => {
  // Arrange
  const input = { department: 'all', year: '2024', status: '' };

  // Act
  const result = formatFilterParams(input);

  // Assert
  expect(result).toEqual({ year: '2024' });
  expect(result).not.toHaveProperty('department');
  expect(result).not.toHaveProperty('status');
});

// Test 3: formatFilterParams - 모든 값이 유효한 경우
test('formatFilterParams should keep all valid values', () => {
  // Arrange
  const input = { department: '컴퓨터공학과', year: '2024', status: '재학' };

  // Act
  const result = formatFilterParams(input);

  // Assert
  expect(result).toEqual(input);
});

// Test 4: extractErrorMessage - 표준 에러 응답
test('extractErrorMessage should extract message from standard error response', () => {
  // Arrange
  const errorResponse = {
    error: 'invalid_parameter',
    message: '유효하지 않은 파라미터입니다',
    details: {},
  };

  // Act
  const result = extractErrorMessage(errorResponse);

  // Assert
  expect(result).toBe('유효하지 않은 파라미터입니다');
});

// Test 5: extractErrorMessage - null 처리
test('extractErrorMessage should return default message for null', () => {
  // Act
  const result = extractErrorMessage(null);

  // Assert
  expect(result).toBe('알 수 없는 오류가 발생했습니다');
});

// Test 6: isFilterApplied - 기본값만 있을 때 false
test('isFilterApplied should return false when all values are default', () => {
  // Arrange
  const filters = { department: 'all', year: 'latest' };

  // Act
  const result = isFilterApplied(filters);

  // Assert
  expect(result).toBe(false);
});

// Test 7: isFilterApplied - 하나라도 적용되면 true
test('isFilterApplied should return true when any filter is applied', () => {
  // Arrange
  const filters = { department: '컴퓨터공학과', year: 'latest' };

  // Act
  const result = isFilterApplied(filters);

  // Assert
  expect(result).toBe(true);
});
```

**Implementation Order (TDD Cycle):**
1. Backend: Test 1-3 작성 → parse_year_filter 구현
2. Backend: Test 4-5 작성 → serialize_filter_params 구현
3. Backend: Test 6 작성 → calculate_date_range 구현
4. Frontend: Test 1 작성 → useDebounce 구현
5. Frontend: Test 2-3 작성 → formatFilterParams 구현
6. Frontend: Test 4-5 작성 → extractErrorMessage 구현
7. Frontend: Test 6-7 작성 → isFilterApplied 구현
8. Refactor: useDashboardFilter에서 useDebounce 사용하도록 변경

**Dependencies:**
- Backend: Python `datetime`, `urllib.parse`
- Frontend: React (useState, useEffect)

---

## 4. TDD Workflow

### 4.1 구현 순서 (Outside-In 전략)

**Phase 1: Backend Core Logic (Inside-Out)**
1. `validators.py` - 필터 검증 로직 (Unit Tests)
2. **`validators.py` - Security Validation** (Unit Tests) - CSRF, Input Sanitization, Rate Limiting
3. `filtering_service.py` - 필터링 비즈니스 로직 (Unit Tests)
4. **`error_codes.py` - Error Response Specification** (Unit Tests) - FilterErrorCode, format_error_response
5. **`utils/filter_helpers.py` - Backend Utilities** (Unit Tests) - parse_year_filter, serialize_filter_params
6. `repositories.py` - 쿼리 확장 (Unit Tests)
7. `views.py` - API 엔드포인트 (Integration Tests)

**Phase 2: Frontend State Management**
8. **`utils/filterHelpers.js` - Frontend Utilities** (Unit Tests) - useDebounce, formatFilterParams, extractErrorMessage
9. `useDashboardFilter.js` - 필터 상태 및 디바운싱 (Unit Tests)
10. `useFilterOptions.js` - 메타데이터 로딩 (Unit Tests)
11. `useDashboardData.js` - 필터 기반 데이터 조회 (Integration Tests)

**Phase 3: Frontend UI**
12. `FilterPanel.jsx` - 필터 UI (Unit Tests + QA Sheet)
13. `EmptyState.jsx` - 빈 상태 UI (Unit Tests + QA Sheet)
14. **`ErrorToast.jsx` - Error Toast Component** (Unit Tests + QA Sheet)
15. **`ChartErrorCard.jsx` - Chart Error Card Component** (Unit Tests + QA Sheet)

**Phase 4: End-to-End Integration**
16. **E2E Tests (Playwright)** - 전체 사용자 플로우 (Acceptance Tests)
    - Happy Path 시나리오 (필터 적용, 다중 필터, 초기화)
    - Error Handling 시나리오 (API 실패, 재시도)
    - Empty State 시나리오
    - Performance Benchmark (<500ms)
    - Cross-browser Tests (Chrome, Safari)

**Phase 5: Self-Verification**
17. Phase Completion Checklist 점검
18. Final Implementation Report 작성

### 4.2 각 모듈별 TDD 사이클 예시

**예시: validators.py 구현**

**Red Phase:**
```python
# tests/test_validators.py
def test_validate_department_filter_with_valid_department():
    params = {'department': '컴퓨터공학과'}
    validate_filter_params(params)  # Should not raise

# 실행 → FAIL (함수가 아직 없음)
```

**Green Phase:**
```python
# api/validators.py
VALID_DEPARTMENTS = ['컴퓨터공학과', '전자공학과']

def validate_filter_params(params):
    department = params.get('department')
    if department and department not in VALID_DEPARTMENTS:
        raise ValidationError({'department': '유효하지 않은 학과입니다.'})

# 실행 → PASS
```

**Refactor Phase:**
```python
# api/validators.py
VALID_DEPARTMENTS = ['컴퓨터공학과', '전자공학과']
VALID_STATUSES = ['재학', '졸업', '휴학']

def _validate_enum_field(value, valid_values, field_name):
    if value and value not in valid_values:
        raise ValidationError({field_name: f'유효하지 않은 {field_name}입니다.'})

def validate_filter_params(params):
    _validate_enum_field(params.get('department'), VALID_DEPARTMENTS, 'department')
    _validate_enum_field(params.get('studentStatus'), VALID_STATUSES, 'studentStatus')

# 실행 → PASS (테스트는 여전히 통과)
```

### 4.3 Commit 포인트

각 모듈별 Green Phase 완료 시점에 커밋:

```
feat: add filter parameter validation logic

- Implement validate_filter_params function
- Add whitelist validation for department, year, status
- Handle SQL injection and XSS attempts
- All unit tests passing (10/10)

Related: #006-dashboard-filtering
```

### 4.4 완료 조건

**Definition of Done:**
- [ ] 모든 Unit Tests 통과 (70% 커버리지 이상)
- [ ] 모든 Integration Tests 통과
- [ ] 모든 E2E Tests 통과
- [ ] Refactoring 완료 (중복 코드 제거)
- [ ] 에러 핸들링 구현
- [ ] 로깅 추가 (API 호출 로그)
- [ ] 코드 리뷰 통과
- [ ] QA Sheet 항목 수동 테스트 완료

---

### 4.5 Self-Verification Protocol

구현 완료 전, 모든 항목을 점검하여 누락 없이 구현되었는지 확인합니다.

#### 4.5.1 Phase Completion Checklist (Per Module)

**Backend Module (validators.py, filtering_service.py, error_codes.py, views.py):**

- [ ] 모든 Unit Tests 통과 (pytest -v)
- [ ] Test Coverage ≥ 70% (pytest --cov)
- [ ] **보안 검증 테스트 통과 (CRITICAL)**
  - [ ] CSRF 보호 테스트 통과
  - [ ] SQL Injection 방어 테스트 통과
  - [ ] XSS 방어 테스트 통과
  - [ ] Rate Limiting 테스트 통과
  - [ ] Input Sanitization 테스트 통과
- [ ] **에러 코드 구현 완료 (CRITICAL)**
  - [ ] FilterErrorCode 클래스 정의됨
  - [ ] format_error_response 함수 구현됨
  - [ ] 모든 API 엔드포인트에서 표준 에러 응답 사용
  - [ ] validation_error, invalid_parameter, server_error, rate_limit_exceeded, no_data_found 모두 테스트됨
- [ ] Logging 추가됨 (API 호출, 에러, 성능)
- [ ] TODO/FIXME 코멘트 없음
- [ ] 코드 리뷰 완료 (Peer or Self)

**Frontend Module (Hooks, Components, Utilities):**

- [ ] 모든 Unit Tests 통과 (npm test)
- [ ] Test Coverage ≥ 70% (npm test -- --coverage)
- [ ] Debouncing 정상 작동 (300ms 검증)
- [ ] **에러 표시 UI 구현 완료 (CRITICAL)**
  - [ ] ErrorToast 컴포넌트 구현됨
  - [ ] ChartErrorCard 컴포넌트 구현됨
  - [ ] 에러 발생 시 토스트 표시 확인
  - [ ] 재시도 버튼 작동 확인
  - [ ] request_id 표시 확인
- [ ] **Helper Utilities 구현 완료**
  - [ ] useDebounce hook 구현됨
  - [ ] formatFilterParams 함수 구현됨
  - [ ] extractErrorMessage 함수 구현됨
  - [ ] isFilterApplied 함수 구현됨
- [ ] QA Sheet 항목 수동 테스트 완료 (스크린샷 첨부)
- [ ] Browser Console 에러 없음
- [ ] PropTypes Warnings 없음

**Integration:**

- [ ] 모든 Integration Tests 통과
- [ ] API 엔드포인트가 올바른 에러 코드 반환
- [ ] Frontend가 모든 Backend 에러 코드 처리
- [ ] Performance Benchmark 달성 (<500ms 필터 적용)
- [ ] API 응답 시간 < 200ms (평균)

**E2E (Acceptance Tests):**

- [ ] **모든 E2E Tests 통과 (HIGH PRIORITY)**
  - [ ] Happy Path 시나리오 통과 (필터 적용, 다중 필터, 초기화)
  - [ ] Error Handling 시나리오 통과 (API 실패, 재시도)
  - [ ] Empty State 시나리오 통과
  - [ ] Performance Benchmark 시나리오 통과 (<500ms)
  - [ ] Cross-browser Tests 통과 (Chrome, Safari)
- [ ] 스크린샷/비디오 캡처 완료 (주요 플로우)
- [ ] Playwright Report 생성됨

---

#### 4.5.2 Final Implementation Report Template

구현 완료 후, 아래 템플릿을 작성하여 최종 보고합니다.

```markdown
# Dashboard Filtering Implementation - Final Report

**Implementation Date:** YYYY-MM-DD
**Developer:** [Name]
**Branch:** feature/006-dashboard-filtering
**Commit:** [hash]

---

## Summary

대시보드 필터링 기능을 TDD 원칙에 따라 구현 완료.
모든 Critical/High Priority 요구사항 충족.

---

## Implementation Statistics

**Backend:**
- Files Created:
  - `api/validators.py`
  - `api/error_codes.py`
  - `services/filtering_service.py`
  - `utils/filter_helpers.py`
- Files Modified:
  - `api/views.py`
  - `infrastructure/repositories.py`
  - `settings.py` (CSRF, Rate Limiting)
- Unit Tests: XX passing
- Integration Tests: XX passing
- Test Coverage: XX%

**Frontend:**
- Files Created:
  - `hooks/useDashboardFilter.js`
  - `hooks/useFilterOptions.js`
  - `components/dashboard/FilterPanel.jsx`
  - `components/dashboard/EmptyState.jsx`
  - `components/ui/ErrorToast.jsx`
  - `components/dashboard/ChartErrorCard.jsx`
  - `utils/filterHelpers.js`
- Files Modified:
  - `hooks/useDashboardData.js`
  - `pages/Dashboard.jsx`
- Unit Tests: XX passing
- Integration Tests: XX passing
- Test Coverage: XX%

**E2E:**
- Playwright Tests: XX passing
- Performance Benchmark: XXXms average (target: <500ms)
- Cross-browser Tests: Chrome ✅ Safari ✅

---

## Verification Results

### Security (CRITICAL)

- [x] CSRF protection enabled
  - Test: `test_filter_api_requires_csrf_token` PASSED
- [x] SQL injection tests passing
  - Test: `test_validate_filter_params_reject_sql_injection` PASSED
- [x] XSS prevention tests passing
  - Test: `test_sanitize_filter_input_removes_xss` PASSED
- [x] Rate limiting configured (10 req/min)
  - Test: `test_filter_api_rate_limit` PASSED
- [x] Input sanitization implemented
  - Function: `sanitize_filter_input()` implemented and tested

### Error Handling (CRITICAL)

- [x] All error codes implemented (6 codes)
  - `validation_error`, `invalid_parameter`, `server_error`, `rate_limit_exceeded`, `no_data_found`, `csrf_error`
- [x] Error responses follow standard format
  - Format: `{ error, message, details, timestamp, request_id }`
- [x] Frontend displays all error types
  - ErrorToast: ✅ Implemented
  - ChartErrorCard: ✅ Implemented
- [x] Retry mechanism working
  - Test: `test('User retries after error and succeeds')` PASSED

### E2E Tests (HIGH)

- [x] Happy path scenario passing
  - Test: `test('User filters dashboard by department')` PASSED
  - Test: `test('User applies multiple filters')` PASSED
  - Test: `test('User resets filters to default')` PASSED
- [x] Error handling scenario passing
  - Test: `test('User sees error when filter API fails')` PASSED
  - Test: `test('User retries after error and succeeds')` PASSED
- [x] Empty state scenario passing
  - Test: `test('User sees empty state when no data matches filter')` PASSED
- [x] Performance benchmark met
  - Test: `test('Filter application completes within 500ms')` PASSED (XXXms)

### Helper Utilities (MEDIUM)

**Backend:**
- [x] `parse_year_filter()` implemented
  - Tests: 3/3 passing
- [x] `serialize_filter_params()` implemented
  - Tests: 2/2 passing
- [x] `calculate_date_range()` implemented
  - Tests: 1/1 passing

**Frontend:**
- [x] `useDebounce()` hook extracted
  - Test: `test('useDebounce should delay value update')` PASSED
- [x] `formatFilterParams()` implemented
  - Tests: 2/2 passing
- [x] `extractErrorMessage()` implemented
  - Tests: 2/2 passing
- [x] `isFilterApplied()` implemented
  - Tests: 2/2 passing

### QA Sheet (MEDIUM)

**FilterPanel Component:**
- [x] 드롭다운 클릭 시 옵션 목록 표시됨
- [x] 옵션 선택 시 드롭다운에 반영됨
- [x] 필터 초기화 버튼 작동함
- [x] 필터 적용 시 "전체 보기" 버튼 활성화됨
- [x] 키보드 네비게이션 정상 작동 (Tab, Enter)
- [x] 모바일 화면에서 정상 표시됨

**ErrorToast Component:**
- [x] 에러 발생 시 우측 하단에 토스트 표시됨
- [x] 5초 후 자동으로 사라짐
- [x] 닫기 버튼(X) 클릭 시 즉시 사라짐
- [x] 에러 메시지 한글로 명확히 표시됨
- [x] 다중 에러 발생 시 스택 형태로 쌓임

**ChartErrorCard Component:**
- [x] 차트 영역에 에러 카드 표시됨
- [x] "재시도" 버튼 클릭 시 API 재호출됨
- [x] 재시도 성공 시 에러 카드 사라지고 차트 표시됨
- [x] request_id 하단에 표시됨
- [x] Rate Limit 에러 시 적절한 메시지 표시됨

---

## Known Issues

[이슈가 있으면 여기에 명시, 없으면 "None"]

---

## Performance Metrics

**Filter Application Time:**
- Average: XXXms
- P95: XXXms
- Target: <500ms
- Status: ✅ PASSED

**API Response Time:**
- Average: XXXms
- P95: XXXms
- Target: <200ms
- Status: ✅ PASSED

**Test Execution Time:**
- Backend Unit Tests: XXs
- Frontend Unit Tests: XXs
- Integration Tests: XXs
- E2E Tests: XXs
- Total: XXs

---

## Next Steps

1. Deploy to staging environment
2. Request QA team review
3. Conduct user acceptance testing (UAT)
4. Merge to main after approval
5. Monitor performance metrics in production

---

## Screenshots

### Happy Path
![Filter by Department](./screenshots/filter-by-department.png)
![Multiple Filters](./screenshots/multiple-filters.png)

### Error Handling
![Error State](./screenshots/error-state.png)

### Mobile View
[Attach mobile screenshots here]

---

**Verified By:** [Name]
**Verification Date:** YYYY-MM-DD
**Approval Status:** [APPROVED / NEEDS REVISION]
```

---

#### 4.5.3 자주 누락되는 항목 체크리스트

CLAUDE.md에서 "Frequently Omitted (Extra Attention Required)"로 명시된 항목들:

**Security Validation (CRITICAL):**
- [ ] CSRF 보호 구현 확인
- [ ] Input Sanitization 함수 구현 확인
- [ ] Rate Limiting 설정 확인
- [ ] SQL Injection/XSS 방어 테스트 확인

**Error Codes (CRITICAL):**
- [ ] 모든 에러 코드 enum 정의됨
- [ ] 표준 에러 응답 포맷 적용됨
- [ ] Frontend가 모든 에러 타입 처리함

**Frontend Error Display (CRITICAL):**
- [ ] ErrorToast 컴포넌트 구현됨
- [ ] ChartErrorCard 컴포넌트 구현됨
- [ ] 재시도 버튼 작동함

**E2E Tests (HIGH):**
- [ ] Playwright 설정 완료
- [ ] Happy Path 시나리오 구현됨
- [ ] Error Handling 시나리오 구현됨
- [ ] Performance Benchmark 시나리오 구현됨

**Helper/Utility Functions (MEDIUM):**
- [ ] Backend utilities 구현됨 (filter_helpers.py)
- [ ] Frontend utilities 구현됨 (filterHelpers.js)
- [ ] useDebounce hook 추출됨

---

## 5. 핵심 원칙 및 주의사항

### 5.1 Test First
- **절대 규칙:** 테스트 없이 코드를 작성하지 않음
- 테스트를 먼저 작성하고 실패하는 것을 확인
- 최소 코드로 테스트를 통과시킴

### 5.2 Small Steps
- 한 번에 하나의 시나리오만 구현
- 큰 기능을 작은 테스트 케이스로 분해
- 각 단계마다 커밋

### 5.3 FIRST Principles
- **Fast:** 디바운싱 테스트에서 fake timers 사용
- **Independent:** Mock을 활용하여 외부 의존성 제거
- **Repeatable:** Fixture를 활용하여 일관된 테스트 데이터
- **Self-validating:** Assert 문으로 명확한 검증
- **Timely:** 코드 작성 직전에 테스트 작성

### 5.4 Test Pyramid
- Unit Tests 70%: 빠르고 많이 작성
- Integration Tests 20%: 모듈 경계 테스트
- Acceptance Tests 10%: 핵심 사용자 시나리오만

### 5.5 MVP 원칙 준수
- 오버엔지니어링 회피: 복잡한 다중 선택 제외
- 가장 쉬운 방법: Promise.all 병렬 호출 (단일 API 엔드포인트 제외)
- 당장 필요한 것만: URL 쿼리 파라미터 공유는 POST-MVP

---

## 6. 예상 구현 시간

**Backend (TDD 포함):**
- validators.py (기본 검증): 2시간
- **validators.py (보안 검증 - CSRF, Rate Limiting, Sanitization): 3시간**
- **error_codes.py (에러 코드 및 포맷): 2시간**
- filtering_service.py: 4시간
- **utils/filter_helpers.py (유틸리티 함수): 2시간**
- views.py 확장: 3시간
- Integration Tests: 2시간
- **소계:** 18시간

**Frontend (TDD 포함):**
- **utils/filterHelpers.js (유틸리티 함수): 2시간**
- useDashboardFilter.js: 3시간
- useFilterOptions.js: 2시간
- useDashboardData.js 확장: 2시간
- FilterPanel.jsx: 3시간
- EmptyState.jsx: 1시간
- **ErrorToast.jsx (에러 토스트): 2시간**
- **ChartErrorCard.jsx (에러 카드): 2시간**
- **E2E Tests (Playwright 설정 + 시나리오): 4시간**
- **소계:** 21시간

**Self-Verification & Reporting:**
- Phase Completion Checklist 점검: 1시간
- Final Implementation Report 작성: 1시간
- **소계:** 2시간

**총 예상 시간:** 41시간 (약 5일, 하루 8시간 기준)

**리스크 버퍼:** +20% (8시간) → **최종: 49시간 (약 6-7일)**

---

## 7. 의존성 및 선행 작업

**필수 선행 작업:**
- [ ] 데이터베이스 테이블 생성 완료 (research_projects, students, publications, department_kpis)
- [ ] 기본 대시보드 API 엔드포인트 구현 완료
- [ ] React 프로젝트 구조 설정 완료
- [ ] 테스트 프레임워크 설정 (Jest, React Testing Library, pytest)

**외부 의존성:**
- Django ORM
- DRF Serializers
- React Hooks
- dataApiClient (Axios)

---

## 8. 성공 지표

**기능 성공:**
- [ ] 사용자가 학과 필터 선택 시 300ms 후 차트 업데이트
- [ ] 다중 필터 적용 시 AND 조건으로 데이터 필터링
- [ ] 필터 결과 없음 시 빈 상태 UI 표시
- [ ] 필터 초기화 시 전체 데이터로 복원

**성능 성공:**
- [ ] 필터링 API 응답 시간 < 200ms (평균)
- [ ] 디바운싱으로 불필요한 API 호출 방지 (10회 → 1회)
- [ ] 병렬 API 호출로 전체 로딩 시간 최소화

**품질 성공:**
- [ ] 테스트 커버리지 70% 이상
- [ ] 모든 에러 케이스 핸들링
- [ ] 보안 검증 (SQL Injection, XSS 방어)

---

**문서 끝**
