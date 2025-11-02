# 학과별 학생 현황 대시보드 구현 계획 (TDD 기반)

**기능 ID:** UC-003
**기능명:** 학과별 학생 현황 시각화 (P0-MVP)
**작성일:** 2025-11-02
**버전:** 1.0

---

## 1. 개요

### 1.1 구현 모듈 요약

| 레이어 | 모듈 | 위치 | 책임 | TDD 적용 |
|--------|------|------|------|----------|
| Infrastructure | Student Model | `backend/data_ingestion/infrastructure/models.py` | DB 스키마 정의 (Django ORM) | Migration Test + Schema Validation |
| Infrastructure | StudentRepository | `backend/data_ingestion/infrastructure/repositories.py` | 데이터 접근 계층 (필터링 쿼리) | Unit Test + Performance Test |
| Util | validationUtils | `backend/data_ingestion/utils/validation_utils.py` | XSS/SQL Injection 방어, 입력 검증 | Unit Test |
| Service | StudentDashboardService | `backend/data_ingestion/services/student_dashboard_service.py` | 비즈니스 로직 (집계, 검증, 보안) | Unit Test |
| Presentation | StudentDashboardView | `backend/data_ingestion/api/views.py` | HTTP 요청 처리 (Thin Controller) | Integration Test + Performance Test |
| Presentation | StudentDashboardSerializer | `backend/data_ingestion/api/serializers.py` | API 응답 직렬화 | Unit Test |
| Util | formatUtils | `frontend/src/utils/formatUtils.js` | 숫자/날짜 포맷 헬퍼 | Unit Test |
| Frontend Hook | useStudentDashboardData | `frontend/src/hooks/useStudentDashboardData.js` | API 호출 및 상태 관리 | Unit Test |
| Frontend Component | StudentBarChart | `frontend/src/components/dashboard/StudentBarChart.jsx` | Recharts 차트 렌더링 | Unit Test |
| Frontend Component | StudentMetricCard | `frontend/src/components/dashboard/StudentMetricCard.jsx` | 총 학생 수 카드 | Unit Test |
| Frontend Component | StudentDashboardFilters | `frontend/src/components/dashboard/StudentDashboardFilters.jsx` | 필터 UI (학과, 학적상태) | Unit Test |
| Frontend Component | ErrorBoundary | `frontend/src/components/ui/ErrorBoundary.jsx` | React 에러 캐치 및 폴백 UI | Unit Test |
| Frontend Component | ErrorCard | `frontend/src/components/ui/ErrorCard.jsx` | 에러 메시지 카드 (재시도 버튼) | Unit Test |
| Frontend Component | ErrorToast | `frontend/src/components/ui/ErrorToast.jsx` | 일시적 에러 토스트 메시지 | Unit Test |
| Frontend Page | StudentDashboardPage | `frontend/src/pages/StudentDashboardPage.jsx` | 페이지 통합 + 에러 처리 | E2E Test |

### 1.2 TDD 적용 범위

- **Unit Tests (70%)**: 모든 Service, Repository, Hook, Component
- **Integration Tests (10%)**: API 엔드포인트 + DB 조회 플로우
- **E2E Tests (10%)**: 전체 사용자 시나리오 (필터링, 차트 인터랙션)
- **Manual QA (10%)**: Recharts 시각적 검증, 브라우저 호환성

---

## 2. Architecture Diagram

```mermaid
graph TB
    subgraph Frontend["Frontend (React)"]
        Page[StudentDashboardPage]
        Hook[useStudentDashboardData]
        Chart[StudentBarChart]
        Metric[StudentMetricCard]
        Filters[StudentDashboardFilters]

        Page --> Hook
        Page --> Chart
        Page --> Metric
        Page --> Filters
        Hook --> Chart
        Hook --> Metric
    end

    subgraph API["API Layer (DRF)"]
        View[StudentDashboardView]
        Serializer[StudentDashboardSerializer]

        View --> Serializer
    end

    subgraph Service["Service Layer"]
        Service[StudentDashboardService]

        Service --> View
    end

    subgraph Infrastructure["Infrastructure Layer"]
        Repo[StudentRepository]
        Model[Student Model]

        Repo --> Model
        Service --> Repo
    end

    subgraph Database["Database (Supabase)"]
        DB[(students 테이블)]

        Model --> DB
    end

    Hook -->|GET /api/dashboard/students/| View

    style Frontend fill:#e1f5ff
    style API fill:#fff4e1
    style Service fill:#ffe1f5
    style Infrastructure fill:#e1ffe1
    style Database fill:#f0f0f0
```

---

## 3. Implementation Plan

### 3.1 Phase 1: Infrastructure Layer (DB 스키마 및 Repository)

#### Module: Student Model

**Location**: `backend/data_ingestion/infrastructure/models.py`

**Responsibility**:
- students 테이블 Django ORM 모델 정의
- 필드: student_id (PK), department, grade, program_type, enrollment_status, created_at, updated_at
- 필수 컬럼 NOT NULL 제약

**Test Strategy**: Migration Test + Model Field Validation

**Test Scenarios (Red Phase)**:
```python
# tests/test_student_model.py

# AAA Pattern 예시
def test_student_model_has_required_fields():
    """Arrange: 필수 필드를 모두 채운 Student 인스턴스 생성
       Act: save() 메서드 호출
       Assert: DB에 저장 성공 및 필드 값 검증"""
    pass

def test_student_id_is_primary_key():
    """Assert: _meta.pk.name == 'student_id'"""
    pass

def test_created_at_auto_now_add():
    """Assert: created_at이 현재 시간으로 자동 설정"""
    pass

def test_updated_at_auto_now():
    """Assert: 레코드 수정 시 updated_at 자동 업데이트"""
    pass

# Edge Cases
def test_duplicate_student_id_raises_integrity_error():
    """Assert: 동일 학번 중복 시 IntegrityError 발생"""
    pass

def test_department_max_length_100():
    """Assert: 학과명 100자 초과 시 ValidationError"""
    pass
```

**Implementation Order (TDD Cycle)**:
1. **Red**: `test_student_model_has_required_fields` 작성 → 실패 확인
2. **Green**: `Student` 모델 기본 필드 정의 → 테스트 통과
3. **Refactor**: 필드 이름 명확화, verbose_name 추가
4. **Red**: `test_student_id_is_primary_key` 작성 → 실패
5. **Green**: `student_id` 필드를 PK로 설정 → 통과
6. **Refactor**: Meta 클래스 정리
7. **Commit**: "Add Student model with required fields"

**Dependencies**: None (순수 Django ORM)

---

#### Module: StudentRepository

**Location**: `backend/data_ingestion/infrastructure/repositories.py`

**Responsibility**:
- 학과/학적상태 필터링 쿼리 전담
- `get_students_by_filter(department, status)` 메서드
- `get_all_departments()` 메서드 (학과 목록 조회)

**Test Strategy**: Unit Test (DB 쿼리 결과 검증)

**Test Scenarios (Red Phase)**:
```python
# tests/test_student_repository.py

@pytest.fixture
def sample_students(db):
    """테스트 데이터 픽스처: 다양한 학과/과정/학적상태 학생 생성"""
    return Student.objects.bulk_create([
        Student(student_id='2024001', department='컴퓨터공학과', grade=1, program_type='학사', enrollment_status='재학'),
        Student(student_id='2024002', department='컴퓨터공학과', grade=1, program_type='석사', enrollment_status='재학'),
        Student(student_id='2024003', department='전자공학과', grade=2, program_type='학사', enrollment_status='휴학'),
        Student(student_id='2024004', department='전자공학과', grade=3, program_type='학사', enrollment_status='졸업'),
    ])

def test_get_students_by_filter_all_departments_all_status(sample_students):
    """Arrange: 4명의 학생 데이터
       Act: repo.get_students_by_filter('all', 'all')
       Assert: 4명 전부 반환"""
    pass

def test_get_students_by_filter_specific_department(sample_students):
    """Act: repo.get_students_by_filter('컴퓨터공학과', 'all')
       Assert: 컴퓨터공학과 학생 2명만 반환"""
    pass

def test_get_students_by_filter_enrollment_status_only(sample_students):
    """Act: repo.get_students_by_filter('all', '재학')
       Assert: 재학생 2명만 반환"""
    pass

def test_get_students_by_filter_combined_filters(sample_students):
    """Act: repo.get_students_by_filter('컴퓨터공학과', '재학')
       Assert: 컴퓨터공학과 재학생 2명만 반환"""
    pass

def test_get_all_departments_returns_distinct_list(sample_students):
    """Act: repo.get_all_departments()
       Assert: ['컴퓨터공학과', '전자공학과'] 반환 (중복 제거)"""
    pass

# Edge Cases
def test_filter_nonexistent_department_returns_empty_queryset(sample_students):
    """Act: repo.get_students_by_filter('존재하지않는학과', 'all')
       Assert: QuerySet.count() == 0"""
    pass

def test_get_all_departments_empty_db():
    """Arrange: 학생 데이터 없음
       Act: repo.get_all_departments()
       Assert: 빈 리스트 반환"""
    pass
```

**Performance & Schema Validation Tests:**

```python
# tests/test_student_model.py (데이터베이스 스키마 검증)

def test_student_model_matches_database_schema():
    """Assert: Student 모델이 database.md 명세와 완전히 일치"""
    from django.db import connection

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = 'students'
            ORDER BY ordinal_position;
        """)
        columns = cursor.fetchall()

    # database.md에 정의된 필드 검증
    expected_columns = {
        'student_id': ('character varying', 'NO'),
        'department': ('character varying', 'NO'),
        'grade': ('integer', 'NO'),
        'program_type': ('character varying', 'NO'),
        'enrollment_status': ('character varying', 'NO'),
        'created_at': ('timestamp with time zone', 'NO'),
        'updated_at': ('timestamp with time zone', 'NO'),
    }

    for col_name, data_type, is_nullable, _ in columns:
        assert col_name in expected_columns, f"예상치 못한 컬럼: {col_name}"
        expected_type, expected_nullable = expected_columns[col_name]
        assert expected_type in data_type, f"{col_name} 타입 불일치"
        assert is_nullable == expected_nullable, f"{col_name} NULL 제약 불일치"
```

**Implementation Order (TDD Cycle)**:
1. **Red**: `test_get_students_by_filter_all_departments_all_status` 작성 → 실패
2. **Green**: `StudentRepository` 클래스 생성, 기본 쿼리 로직 작성 → 통과
3. **Refactor**: 코드 정리, 변수명 명확화
4. **Red**: `test_get_students_by_filter_specific_department` 작성 → 실패
5. **Green**: department 필터 로직 추가 → 통과
6. **Red**: `test_get_students_by_filter_enrollment_status_only` 작성 → 실패
7. **Green**: enrollment_status 필터 로직 추가 → 통과
8. **Refactor**: 필터 조건을 메서드로 분리
9. **Commit**: "Add StudentRepository with filtering logic"

**Dependencies**: Student Model

---

### 3.2 Phase 2: Service Layer (비즈니스 로직)

#### Module: StudentDashboardService

**Location**: `backend/data_ingestion/services/student_dashboard_service.py`

**Responsibility**:
- 입력 파라미터 검증 (학과 존재 여부, 학적상태 화이트리스트)
- Repository를 통한 데이터 조회
- 학과별/과정별 집계 로직 (`_aggregate_by_department`)
- 응답 데이터 구조화 (total_students, by_department, updated_at)
- XSS 방어 및 SQL Injection 방지

**Security Implementation**:
```python
import bleach

class StudentDashboardService:
    def _sanitize_input(self, value):
        """XSS 방어: HTML 태그 제거"""
        return bleach.clean(value, strip=True)

    def _validate_inputs(self, department, status):
        """입력 검증 (SQL Injection, XSS 방어)"""
        # 학적상태 화이트리스트 검증
        ALLOWED_STATUSES = ['all', '재학', '휴학', '졸업']
        if status not in ALLOWED_STATUSES:
            raise ValidationError(f"유효하지 않은 학적상태: {status}")

        # 학과명 SQL Injection 방어
        if department != 'all':
            department = self._sanitize_input(department)
            valid_departments = self.repository.get_all_departments()
            if department not in valid_departments:
                raise ValidationError(f"존재하지 않는 학과: {department}")
```

**Test Strategy**: Unit Test (Repository 의존성은 Mock 처리)

**Test Scenarios (Red Phase)**:
```python
# tests/test_student_dashboard_service.py

@pytest.fixture
def mock_repo(mocker):
    """StudentRepository Mock 생성"""
    return mocker.Mock(spec=StudentRepository)

def test_validate_inputs_valid_parameters(mock_repo):
    """Arrange: 유효한 department='컴퓨터공학과', status='재학'
       Act: service._validate_inputs(department, status)
       Assert: ValidationError 발생하지 않음"""
    pass

def test_validate_inputs_invalid_status_raises_error(mock_repo):
    """Arrange: status='invalid_status'
       Act: service._validate_inputs('all', status)
       Assert: ValidationError('유효하지 않은 학적상태') 발생"""
    pass

def test_validate_inputs_nonexistent_department_raises_error(mock_repo):
    """Arrange: department='존재하지않는학과', mock_repo.get_all_departments() 반환 ['컴퓨터공학과']
       Act: service._validate_inputs(department, '재학')
       Assert: ValidationError('존재하지 않는 학과') 발생"""
    pass

def test_get_student_dashboard_data_all_students(mock_repo):
    """Arrange: mock_repo.get_students_by_filter() 반환 값 설정 (QuerySet Mock)
       Act: service.get_student_dashboard_data('all', '재학')
       Assert:
         - total_students == 예상 값
         - by_department 리스트 구조 검증
         - updated_at 존재"""
    pass

def test_aggregate_by_department_groups_by_program_type(mock_repo):
    """Arrange: 컴퓨터공학과 학생 (학사 2명, 석사 1명) QuerySet Mock
       Act: service._aggregate_by_department(queryset)
       Assert: 반환 리스트에 {'department': '컴퓨터공학과', '학사': 2, '석사': 1, '박사': 0, 'total': 3} 포함"""
    pass

def test_aggregate_by_department_orders_by_total_desc(mock_repo):
    """Arrange: 전자공학과(10명), 컴퓨터공학과(20명) QuerySet Mock
       Act: service._aggregate_by_department(queryset)
       Assert: 반환 리스트 첫 번째 항목이 컴퓨터공학과 (학생 수 내림차순)"""
    pass

# Edge Cases
def test_get_student_dashboard_data_no_students(mock_repo):
    """Arrange: mock_repo.get_students_by_filter() 반환 빈 QuerySet
       Act: service.get_student_dashboard_data('all', '재학')
       Assert: total_students == 0, by_department == []"""
    pass

def test_aggregate_handles_missing_program_types(mock_repo):
    """Arrange: 학과에 학사만 있고 석사/박사 없음
       Act: service._aggregate_by_department(queryset)
       Assert: {'학사': N, '석사': 0, '박사': 0}"""
    pass
```

**Implementation Order (TDD Cycle)**:
1. **Red**: `test_validate_inputs_valid_parameters` 작성 → 실패
2. **Green**: `StudentDashboardService` 클래스 생성, `_validate_inputs` 메서드 구현 → 통과
3. **Red**: `test_validate_inputs_invalid_status_raises_error` 작성 → 실패
4. **Green**: 학적상태 화이트리스트 검증 로직 추가 → 통과
5. **Red**: `test_validate_inputs_nonexistent_department_raises_error` 작성 → 실패
6. **Green**: 학과 존재 여부 검증 로직 추가 → 통과
7. **Refactor**: 검증 로직 메서드 분리, 매직 넘버 상수화
8. **Red**: `test_get_student_dashboard_data_all_students` 작성 → 실패
9. **Green**: `get_student_dashboard_data` 메서드 구현 → 통과
10. **Red**: `test_aggregate_by_department_groups_by_program_type` 작성 → 실패
11. **Green**: `_aggregate_by_department` 메서드 구현 (Django ORM annotate 사용) → 통과
12. **Refactor**: 쿼리 최적화, 변수명 정리
13. **Commit**: "Add StudentDashboardService with validation and aggregation"

**Dependencies**: StudentRepository

---

### 3.2.5 Phase 2.5: Utility Functions

#### Module: formatUtils.js

**Location**: `frontend/src/utils/formatUtils.js`

**Functions:**
1. `formatNumber(value)`: 천 단위 쉼표 포맷 (1234 → "1,234")
2. `formatDate(isoString)`: ISO 8601 → "2025년 11월 2일"
3. `formatPercentage(value)`: 소수 → "78.5%"

**Test Scenarios:**
```javascript
describe('formatUtils', () => {
  it('formatNumber adds thousand separators', () => {
    expect(formatNumber(1234)).toBe('1,234');
    expect(formatNumber(1234567)).toBe('1,234,567');
    expect(formatNumber(0)).toBe('0');
  });

  it('formatDate converts ISO to Korean format', () => {
    expect(formatDate('2025-11-02T14:35:22Z')).toBe('2025년 11월 2일');
  });

  it('formatPercentage formats decimal to percentage', () => {
    expect(formatPercentage(0.785)).toBe('78.5%');
    expect(formatPercentage(1)).toBe('100.0%');
  });
});
```

---

#### Module: validationUtils.py

**Location**: `backend/data_ingestion/utils/validation_utils.py`

**Functions:**
1. `sanitize_string(value)`: XSS 방어용 HTML 태그 제거
2. `validate_department_name(name)`: 학과명 형식 검증
3. `validate_enum_value(value, allowed_values)`: Enum 검증

**Test Scenarios:**
```python
def test_sanitize_string_removes_html_tags():
    assert sanitize_string('<script>alert("XSS")</script>') == 'alert("XSS")'
    assert sanitize_string('컴퓨터공학과') == '컴퓨터공학과'

def test_validate_department_name():
    assert validate_department_name('컴퓨터공학과') is True
    assert validate_department_name('') is False
    assert validate_department_name('A' * 101) is False  # 100자 초과

def test_validate_enum_value():
    allowed = ['재학', '휴학', '졸업']
    assert validate_enum_value('재학', allowed) is True
    assert validate_enum_value('invalid', allowed) is False
```

---

### 3.3 Phase 3: Presentation Layer (API 엔드포인트)

#### Module: StudentDashboardSerializer

**Location**: `backend/data_ingestion/api/serializers.py`

**Responsibility**:
- API 응답 데이터 직렬화
- 필드: total_students, by_department, updated_at

**Test Strategy**: Unit Test

**Test Scenarios (Red Phase)**:
```python
# tests/test_student_dashboard_serializer.py

def test_serializer_with_valid_data():
    """Arrange: 유효한 딕셔너리 데이터 (total_students, by_department, updated_at)
       Act: serializer = StudentDashboardSerializer(data)
       Assert: serializer.data가 예상 JSON 구조와 일치"""
    pass

def test_serializer_datetime_format():
    """Arrange: updated_at이 datetime 객체인 데이터
       Act: serializer.data['updated_at']
       Assert: ISO 8601 포맷 문자열 (예: '2025-11-02T14:35:22Z')"""
    pass

# Edge Cases
def test_serializer_with_empty_by_department():
    """Arrange: by_department = []
       Act: serializer.data
       Assert: 정상 직렬화 (빈 리스트 허용)"""
    pass
```

**Implementation Order (TDD Cycle)**:
1. **Red**: `test_serializer_with_valid_data` 작성 → 실패
2. **Green**: `StudentDashboardSerializer` 클래스 생성, 필드 정의 → 통과
3. **Red**: `test_serializer_datetime_format` 작성 → 실패
4. **Green**: DateTimeField 설정 추가 → 통과
5. **Commit**: "Add StudentDashboardSerializer"

**Dependencies**: None (순수 DRF Serializer)

---

#### Module: StudentDashboardView

**Location**: `backend/data_ingestion/api/views.py`

**Responsibility**:
- GET /api/dashboard/students/ 엔드포인트 처리
- Query Parameter 파싱 (department, status)
- StudentDashboardService 호출
- HTTP 응답 반환 (200 OK, 400 Bad Request, 404 Not Found)

**Test Strategy**: Integration Test (DRF APIClient 사용)

**Test Scenarios (Red Phase)**:
```python
# tests/integration/test_student_dashboard_api.py

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def sample_students(db):
    """통합 테스트용 실제 DB 데이터"""
    return Student.objects.bulk_create([
        Student(student_id='2024001', department='컴퓨터공학과', grade=1, program_type='학사', enrollment_status='재학'),
        Student(student_id='2024002', department='컴퓨터공학과', grade=2, program_type='석사', enrollment_status='재학'),
        Student(student_id='2024003', department='전자공학과', grade=1, program_type='학사', enrollment_status='휴학'),
    ])

def test_get_endpoint_returns_200_with_valid_params(api_client, sample_students):
    """Arrange: 샘플 학생 데이터 존재
       Act: GET /api/dashboard/students/?department=all&status=재학
       Assert:
         - status_code == 200
         - response.json()에 total_students, by_department, updated_at 포함"""
    pass

def test_get_endpoint_filters_by_department(api_client, sample_students):
    """Act: GET /api/dashboard/students/?department=컴퓨터공학과&status=all
       Assert:
         - total_students == 2
         - by_department 리스트 길이 1 (컴퓨터공학과만)"""
    pass

def test_get_endpoint_filters_by_enrollment_status(api_client, sample_students):
    """Act: GET /api/dashboard/students/?department=all&status=재학
       Assert:
         - total_students == 2 (재학생만)"""
    pass

def test_get_endpoint_invalid_status_returns_400(api_client):
    """Act: GET /api/dashboard/students/?status=invalid_status
       Assert:
         - status_code == 400
         - response.json()['error'] 존재"""
    pass

def test_get_endpoint_nonexistent_department_returns_400(api_client, sample_students):
    """Act: GET /api/dashboard/students/?department=존재하지않는학과
       Assert:
         - status_code == 400
         - error message 포함"""
    pass

def test_get_endpoint_no_data_returns_empty_list(api_client):
    """Arrange: 학생 데이터 없음
       Act: GET /api/dashboard/students/
       Assert:
         - status_code == 200
         - total_students == 0
         - by_department == []"""
    pass

# Edge Cases
def test_get_endpoint_missing_query_params_uses_defaults(api_client, sample_students):
    """Act: GET /api/dashboard/students/ (파라미터 없음)
       Assert:
         - department='all', status='재학' 기본값 적용
         - status_code == 200"""
    pass
```

**Implementation Order (TDD Cycle)**:
1. **Red**: `test_get_endpoint_returns_200_with_valid_params` 작성 → 실패
2. **Green**: `StudentDashboardView` 클래스 생성, GET 메서드 구현 → 통과
3. **Red**: `test_get_endpoint_filters_by_department` 작성 → 실패
4. **Green**: Query Parameter 파싱 로직 추가 → 통과
5. **Red**: `test_get_endpoint_invalid_status_returns_400` 작성 → 실패
6. **Green**: try-except로 ValidationError 처리, 400 응답 반환 → 통과
7. **Refactor**: 에러 응답 포맷 통일, 코드 정리
8. **Commit**: "Add StudentDashboardView API endpoint"

**Dependencies**: StudentDashboardService, StudentDashboardSerializer

---

### 3.3.1 에러 코드 및 응답 구조 명세

#### 표준 에러 응답 형식

모든 에러는 다음 JSON 구조로 반환:
```json
{
  "error": "error_code",
  "message": "User-friendly error message (Korean)",
  "details": "Optional detailed information",
  "timestamp": "2025-11-02T14:35:22Z"
}
```

#### 에러 코드 매핑 테이블

| HTTP Status | Error Code | 발생 시나리오 | 메시지 예시 | 권장 조치 |
|-------------|------------|-------------|-----------|---------|
| 400 | `validation_error` | 유효하지 않은 학적상태 입력 | "유효하지 않은 학적상태: 'invalid_status'" | 허용된 값: 재학, 휴학, 졸업, all |
| 400 | `validation_error` | 존재하지 않는 학과 | "존재하지 않는 학과: '존재하지않는학과'" | 학과 목록 조회 후 재시도 |
| 400 | `invalid_parameter` | 잘못된 쿼리 파라미터 형식 | "잘못된 파라미터 형식" | API 문서 참조 |
| 404 | `not_found` | 필터 조건에 해당하는 학생 없음 | "조건에 맞는 학생 데이터가 없습니다" | 필터 조건 변경 또는 '전체 보기' |
| 500 | `server_error` | 데이터베이스 연결 실패 | "서버 오류가 발생했습니다" | 잠시 후 재시도 |
| 500 | `server_error` | 예상치 못한 서버 에러 | "데이터 처리 중 문제가 발생했습니다" | 관리자 문의 |

#### 테스트 시나리오 추가

```python
# tests/integration/test_student_dashboard_api.py

def test_error_response_structure(api_client):
    """Act: 잘못된 요청 전송
       Assert: 에러 응답이 표준 구조를 따름 (error, message, details, timestamp)"""
    response = api_client.get('/api/dashboard/students/?status=invalid')
    assert response.status_code == 400
    data = response.json()
    assert 'error' in data
    assert 'message' in data
    assert 'timestamp' in data

def test_404_error_with_empty_result(api_client):
    """Arrange: DB에 데이터 없음
       Act: GET /api/dashboard/students/
       Assert: 200 OK with empty list (설계 결정: 빈 결과는 404가 아닌 200 반환)"""
    response = api_client.get('/api/dashboard/students/')
    assert response.status_code == 200
    data = response.json()
    assert data['total_students'] == 0
    assert data['by_department'] == []
```

#### Security Test Scenarios

```python
# tests/test_student_dashboard_service.py (보안 검증)

def test_xss_prevention_in_department_filter(mock_repo):
    """Act: department='<script>alert("XSS")</script>' 전송
       Assert: Sanitized된 값으로 처리 또는 ValidationError 발생"""
    service = StudentDashboardService(mock_repo)
    mock_repo.get_all_departments.return_value = ['컴퓨터공학과']

    with pytest.raises(ValidationError) as exc:
        service.get_student_dashboard_data('<script>alert("XSS")</script>', '재학')

    assert '존재하지 않는 학과' in str(exc.value)

def test_sql_injection_prevention(mock_repo):
    """Act: department="'; DROP TABLE students; --" 전송
       Assert: ValidationError 발생, DB 영향 없음"""
    service = StudentDashboardService(mock_repo)
    mock_repo.get_all_departments.return_value = ['컴퓨터공학과']

    with pytest.raises(ValidationError) as exc:
        service.get_student_dashboard_data("'; DROP TABLE students; --", '재학')

    assert '존재하지 않는 학과' in str(exc.value)
```

#### API Performance Requirements Test

```python
# tests/integration/test_student_dashboard_api.py (성능 검증)

import time

def test_api_response_time_meets_sla(api_client, sample_students):
    """Act: GET /api/dashboard/students/ 10회 호출
       Assert: 평균 응답 시간 < 500ms"""
    durations = []

    for _ in range(10):
        start = time.time()
        response = api_client.get('/api/dashboard/students/?department=all&status=재학')
        duration = (time.time() - start) * 1000  # ms
        durations.append(duration)
        assert response.status_code == 200

    avg_duration = sum(durations) / len(durations)
    assert avg_duration < 500, f"평균 응답 시간 {avg_duration:.2f}ms가 500ms를 초과합니다"

    # 최악의 경우도 1초 이내
    max_duration = max(durations)
    assert max_duration < 1000, f"최대 응답 시간 {max_duration:.2f}ms가 1000ms를 초과합니다"
```

---

### 3.4 Phase 4: Frontend Hook (API 통신 및 상태 관리)

#### Module: useStudentDashboardData

**Location**: `frontend/src/hooks/useStudentDashboardData.js`

**Responsibility**:
- API 호출 (GET /api/dashboard/students/)
- 로딩/에러 상태 관리
- 필터 상태 관리 (department, status)
- 300ms 디바운싱

**Test Strategy**: Unit Test (Jest + React Testing Library)

**Test Scenarios (Red Phase)**:
```javascript
// tests/useStudentDashboardData.test.js

import { renderHook, waitFor, act } from '@testing-library/react';
import { useStudentDashboardData } from './useStudentDashboardData';
import * as api from '../api/dataApiClient';

jest.mock('../api/dataApiClient');

describe('useStudentDashboardData', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('loads data on mount with default filters', async () => {
    // Arrange
    const mockData = { total_students: 100, by_department: [], updated_at: '2025-11-02T14:35:22Z' };
    api.fetchStudentData.mockResolvedValue(mockData);

    // Act
    const { result } = renderHook(() => useStudentDashboardData());

    // Assert (초기 로딩 상태)
    expect(result.current.loading).toBe(true);

    // Assert (데이터 로드 완료)
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.data).toEqual(mockData);
    expect(result.current.error).toBeNull();
    expect(api.fetchStudentData).toHaveBeenCalledWith({ department: 'all', status: '재학' });
  });

  it('updates data when filter changes', async () => {
    // Arrange
    api.fetchStudentData.mockResolvedValue({ total_students: 50, by_department: [] });
    const { result } = renderHook(() => useStudentDashboardData());
    await waitFor(() => expect(result.current.loading).toBe(false));

    // Act
    act(() => {
      result.current.updateFilter('department', '컴퓨터공학과');
    });

    // Assert (디바운싱 후 API 재호출)
    await waitFor(() =>
      expect(api.fetchStudentData).toHaveBeenCalledWith({ department: '컴퓨터공학과', status: '재학' })
    );
  });

  it('handles API error gracefully', async () => {
    // Arrange
    const errorMessage = 'Network error';
    api.fetchStudentData.mockRejectedValue(new Error(errorMessage));

    // Act
    const { result } = renderHook(() => useStudentDashboardData());

    // Assert
    await waitFor(() => expect(result.current.error).toBe(errorMessage));
    expect(result.current.data).toBeNull();
    expect(result.current.loading).toBe(false);
  });

  it('resets filters to default values', async () => {
    // Arrange
    api.fetchStudentData.mockResolvedValue({ total_students: 0, by_department: [] });
    const { result } = renderHook(() => useStudentDashboardData());
    await waitFor(() => expect(result.current.loading).toBe(false));

    act(() => {
      result.current.updateFilter('department', '전자공학과');
    });

    // Act
    act(() => {
      result.current.resetFilters();
    });

    // Assert
    await waitFor(() =>
      expect(api.fetchStudentData).toHaveBeenCalledWith({ department: 'all', status: '재학' })
    );
  });

  // Edge Cases
  it('debounces rapid filter changes (300ms)', async () => {
    // Arrange
    jest.useFakeTimers();
    api.fetchStudentData.mockResolvedValue({ total_students: 0, by_department: [] });
    const { result } = renderHook(() => useStudentDashboardData());

    // Act (연속 3번 필터 변경)
    act(() => {
      result.current.updateFilter('department', '컴퓨터공학과');
      result.current.updateFilter('department', '전자공학과');
      result.current.updateFilter('department', '기계공학과');
    });

    // Assert (300ms 내에는 API 호출 안 됨)
    expect(api.fetchStudentData).toHaveBeenCalledTimes(1); // mount 시 1번만

    // Act (300ms 경과)
    act(() => {
      jest.advanceTimersByTime(300);
    });

    // Assert (마지막 필터 값으로만 API 호출)
    await waitFor(() =>
      expect(api.fetchStudentData).toHaveBeenCalledWith({ department: '기계공학과', status: '재학' })
    );
    expect(api.fetchStudentData).toHaveBeenCalledTimes(2); // mount + debounced call

    jest.useRealTimers();
  });
});
```

**Implementation Order (TDD Cycle)**:
1. **Red**: `loads data on mount with default filters` 작성 → 실패
2. **Green**: useStudentDashboardData Hook 기본 구조 구현 (useState, useEffect) → 통과
3. **Red**: `updates data when filter changes` 작성 → 실패
4. **Green**: updateFilter 함수 구현 → 통과
5. **Red**: `handles API error gracefully` 작성 → 실패
6. **Green**: try-catch 에러 처리 추가 → 통과
7. **Red**: `debounces rapid filter changes` 작성 → 실패
8. **Green**: setTimeout 디바운싱 로직 추가 → 통과
9. **Refactor**: 상수 분리 (DEBOUNCE_DELAY), 코드 정리
10. **Commit**: "Add useStudentDashboardData hook with debouncing"

**Dependencies**: dataApiClient.js

---

### 3.5 Phase 5: Frontend Components (UI 렌더링)

#### Module: StudentBarChart

**Location**: `frontend/src/components/dashboard/StudentBarChart.jsx`

**Responsibility**:
- Recharts BarChart 렌더링
- 학사/석사/박사 스택 바 표시
- 커스텀 Tooltip 표시
- 로딩 상태 및 Empty State 처리

**Test Strategy**: Unit Test (React Testing Library)

**Test Scenarios (Red Phase)**:
```javascript
// tests/StudentBarChart.test.jsx

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import StudentBarChart from './StudentBarChart';

describe('StudentBarChart', () => {
  const mockData = [
    { name: '컴퓨터공학과', 학사: 120, 석사: 35, 박사: 12 },
    { name: '전자공학과', 학사: 98, 석사: 28, 박사: 9 },
  ];

  it('renders chart with provided data', () => {
    // Act
    render(<StudentBarChart data={mockData} loading={false} />);

    // Assert
    expect(screen.getByText('컴퓨터공학과')).toBeInTheDocument();
    expect(screen.getByText('전자공학과')).toBeInTheDocument();
  });

  it('shows loading skeleton when loading prop is true', () => {
    // Act
    render(<StudentBarChart data={null} loading={true} />);

    // Assert
    expect(screen.getByTestId('skeleton-loader')).toBeInTheDocument();
    expect(screen.queryByText('컴퓨터공학과')).not.toBeInTheDocument();
  });

  it('shows empty state when data is empty array', () => {
    // Act
    render(<StudentBarChart data={[]} loading={false} />);

    // Assert
    expect(screen.getByText('학생 데이터가 없습니다.')).toBeInTheDocument();
  });

  it('renders stacked bars for each program type', () => {
    // Arrange
    const { container } = render(<StudentBarChart data={mockData} loading={false} />);

    // Assert (Recharts SVG 요소 확인)
    const bars = container.querySelectorAll('.recharts-bar');
    expect(bars.length).toBe(3); // 학사, 석사, 박사
  });

  // Edge Cases
  it('handles null data gracefully', () => {
    // Act
    render(<StudentBarChart data={null} loading={false} />);

    // Assert
    expect(screen.getByText('학생 데이터가 없습니다.')).toBeInTheDocument();
  });

  it('renders chart with single department', () => {
    // Arrange
    const singleDeptData = [{ name: '컴퓨터공학과', 학사: 50, 석사: 10, 박사: 5 }];

    // Act
    render(<StudentBarChart data={singleDeptData} loading={false} />);

    // Assert
    expect(screen.getByText('컴퓨터공학과')).toBeInTheDocument();
  });
});

describe('CustomTooltip', () => {
  it('displays tooltip with all program types and total', () => {
    // Arrange
    const mockPayload = [
      { name: '학사', value: 120, color: '#3B82F6' },
      { name: '석사', value: 35, color: '#10B981' },
      { name: '박사', value: 12, color: '#F59E0B' },
    ];
    const mockLabel = '컴퓨터공학과';

    // Act
    const { container } = render(
      <CustomTooltip active={true} payload={mockPayload} label={mockLabel} />
    );

    // Assert
    expect(screen.getByText('컴퓨터공학과')).toBeInTheDocument();
    expect(screen.getByText('학사: 120명')).toBeInTheDocument();
    expect(screen.getByText('석사: 35명')).toBeInTheDocument();
    expect(screen.getByText('박사: 12명')).toBeInTheDocument();
    expect(screen.getByText('총: 167명')).toBeInTheDocument();
  });

  it('does not render when active is false', () => {
    // Act
    const { container } = render(
      <CustomTooltip active={false} payload={[]} label="" />
    );

    // Assert
    expect(container).toBeEmptyDOMElement();
  });
});
```

**Implementation Order (TDD Cycle)**:
1. **Red**: `renders chart with provided data` 작성 → 실패
2. **Green**: StudentBarChart 컴포넌트 기본 구조 + Recharts BarChart 추가 → 통과
3. **Red**: `shows loading skeleton when loading prop is true` 작성 → 실패
4. **Green**: loading 조건부 렌더링 추가 → 통과
5. **Red**: `shows empty state when data is empty array` 작성 → 실패
6. **Green**: EmptyState 컴포넌트 추가 → 통과
7. **Red**: CustomTooltip 테스트 작성 → 실패
8. **Green**: CustomTooltip 컴포넌트 구현 → 통과
9. **Refactor**: 컴포넌트 분리, 스타일 정리
10. **Commit**: "Add StudentBarChart component with Recharts"

**Dependencies**: Recharts, EmptyState, SkeletonLoader (공통 UI 컴포넌트)

---

#### Module: StudentMetricCard

**Location**: `frontend/src/components/dashboard/StudentMetricCard.jsx`

**Responsibility**:
- 총 재학생 수 표시
- 천 단위 쉼표 포맷 (1,234명)
- 필터 적용 시 학과명 표시

**Test Strategy**: Unit Test

**Test Scenarios (Red Phase)**:
```javascript
// tests/StudentMetricCard.test.jsx

import { render, screen } from '@testing-library/react';
import StudentMetricCard from './StudentMetricCard';

describe('StudentMetricCard', () => {
  it('displays total student count with comma separator', () => {
    // Act
    render(<StudentMetricCard total={1234} department="all" />);

    // Assert
    expect(screen.getByText('총 재학생')).toBeInTheDocument();
    expect(screen.getByText('1,234명')).toBeInTheDocument();
  });

  it('displays department name when filtered', () => {
    // Act
    render(<StudentMetricCard total={167} department="컴퓨터공학과" />);

    // Assert
    expect(screen.getByText('총 재학생 (컴퓨터공학과)')).toBeInTheDocument();
    expect(screen.getByText('167명')).toBeInTheDocument();
  });

  it('handles zero students', () => {
    // Act
    render(<StudentMetricCard total={0} department="all" />);

    // Assert
    expect(screen.getByText('0명')).toBeInTheDocument();
  });

  // Edge Cases
  it('formats large numbers correctly (10,000+)', () => {
    // Act
    render(<StudentMetricCard total={12345} department="all" />);

    // Assert
    expect(screen.getByText('12,345명')).toBeInTheDocument();
  });
});
```

**Implementation Order (TDD Cycle)**:
1. **Red**: `displays total student count with comma separator` 작성 → 실패
2. **Green**: StudentMetricCard 컴포넌트 생성, toLocaleString() 사용 → 통과
3. **Red**: `displays department name when filtered` 작성 → 실패
4. **Green**: 조건부 텍스트 렌더링 추가 → 통과
5. **Refactor**: 포맷 함수 분리 (formatNumber 유틸리티)
6. **Commit**: "Add StudentMetricCard component"

**Dependencies**: None (순수 React 컴포넌트)

---

#### Module: StudentDashboardFilters

**Location**: `frontend/src/components/dashboard/StudentDashboardFilters.jsx`

**Responsibility**:
- 학과 필터 드롭다운
- 학적상태 필터 라디오 버튼
- 필터 초기화 버튼

**Test Strategy**: Unit Test

**Test Scenarios (Red Phase)**:
```javascript
// tests/StudentDashboardFilters.test.jsx

import { render, screen, fireEvent } from '@testing-library/react';
import StudentDashboardFilters from './StudentDashboardFilters';

describe('StudentDashboardFilters', () => {
  const mockOnFilterChange = jest.fn();
  const mockOnReset = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders department dropdown and status radio buttons', () => {
    // Arrange
    const departments = ['컴퓨터공학과', '전자공학과'];

    // Act
    render(
      <StudentDashboardFilters
        departments={departments}
        selectedDepartment="all"
        selectedStatus="재학"
        onFilterChange={mockOnFilterChange}
        onReset={mockOnReset}
      />
    );

    // Assert
    expect(screen.getByLabelText('학과')).toBeInTheDocument();
    expect(screen.getByLabelText('재학')).toBeInTheDocument();
    expect(screen.getByLabelText('휴학')).toBeInTheDocument();
    expect(screen.getByLabelText('졸업')).toBeInTheDocument();
    expect(screen.getByText('전체 보기')).toBeInTheDocument();
  });

  it('calls onFilterChange when department is selected', () => {
    // Arrange
    const departments = ['컴퓨터공학과'];
    render(
      <StudentDashboardFilters
        departments={departments}
        selectedDepartment="all"
        selectedStatus="재학"
        onFilterChange={mockOnFilterChange}
        onReset={mockOnReset}
      />
    );

    // Act
    const dropdown = screen.getByLabelText('학과');
    fireEvent.change(dropdown, { target: { value: '컴퓨터공학과' } });

    // Assert
    expect(mockOnFilterChange).toHaveBeenCalledWith('department', '컴퓨터공학과');
  });

  it('calls onFilterChange when status is changed', () => {
    // Arrange
    render(
      <StudentDashboardFilters
        departments={[]}
        selectedDepartment="all"
        selectedStatus="재학"
        onFilterChange={mockOnFilterChange}
        onReset={mockOnReset}
      />
    );

    // Act
    const radioButton = screen.getByLabelText('휴학');
    fireEvent.click(radioButton);

    // Assert
    expect(mockOnFilterChange).toHaveBeenCalledWith('status', '휴학');
  });

  it('calls onReset when reset button is clicked', () => {
    // Arrange
    render(
      <StudentDashboardFilters
        departments={[]}
        selectedDepartment="컴퓨터공학과"
        selectedStatus="재학"
        onFilterChange={mockOnFilterChange}
        onReset={mockOnReset}
      />
    );

    // Act
    const resetButton = screen.getByText('전체 보기');
    fireEvent.click(resetButton);

    // Assert
    expect(mockOnReset).toHaveBeenCalled();
  });

  // Edge Cases
  it('renders empty dropdown when no departments provided', () => {
    // Act
    render(
      <StudentDashboardFilters
        departments={[]}
        selectedDepartment="all"
        selectedStatus="재학"
        onFilterChange={mockOnFilterChange}
        onReset={mockOnReset}
      />
    );

    // Assert
    const dropdown = screen.getByLabelText('학과');
    expect(dropdown.options.length).toBe(1); // "전체 학과" 옵션만
  });
});
```

**Implementation Order (TDD Cycle)**:
1. **Red**: `renders department dropdown and status radio buttons` 작성 → 실패
2. **Green**: 기본 필터 UI 구현 → 통과
3. **Red**: `calls onFilterChange when department is selected` 작성 → 실패
4. **Green**: onChange 핸들러 추가 → 통과
5. **Red**: 나머지 테스트 작성 → 실패
6. **Green**: 나머지 핸들러 구현 → 통과
7. **Refactor**: 컴포넌트 분리, 스타일 정리
8. **Commit**: "Add StudentDashboardFilters component"

**Dependencies**: None

---

### 3.5.4 Phase 5.4: 에러 처리 UI 컴포넌트

#### Module: ErrorBoundary

**Location**: `frontend/src/components/ui/ErrorBoundary.jsx`

**Responsibility:**
- React 렌더링 에러 캐치
- 사용자 친화적 폴백 UI 표시
- 에러 로그 전송 (POST-MVP: Sentry 연동)

**Test Scenarios:**
```javascript
describe('ErrorBoundary', () => {
  it('catches rendering errors and shows fallback UI', () => {
    const ThrowError = () => { throw new Error('Test error'); };

    render(
      <ErrorBoundary>
        <ThrowError />
      </ErrorBoundary>
    );

    expect(screen.getByText('문제가 발생했습니다')).toBeInTheDocument();
    expect(screen.getByText('새로고침')).toBeInTheDocument();
  });
});
```

---

#### Module: ErrorCard

**Location**: `frontend/src/components/ui/ErrorCard.jsx`

**Responsibility:**
- 차트 로딩 실패 시 에러 카드 표시
- 재시도 버튼 제공
- 에러 타입별 아이콘 및 메시지

**Props:**
- `errorType`: 'network' | 'validation' | 'server'
- `message`: 사용자에게 표시할 메시지
- `onRetry`: 재시도 콜백 함수

**Test Scenarios:**
```javascript
describe('ErrorCard', () => {
  it('displays error message with retry button', () => {
    const mockRetry = jest.fn();

    render(
      <ErrorCard
        errorType="network"
        message="데이터를 불러올 수 없습니다"
        onRetry={mockRetry}
      />
    );

    expect(screen.getByText('데이터를 불러올 수 없습니다')).toBeInTheDocument();

    const retryButton = screen.getByText('다시 시도');
    fireEvent.click(retryButton);

    expect(mockRetry).toHaveBeenCalled();
  });
});
```

---

#### Module: ErrorToast

**Location**: `frontend/src/components/ui/ErrorToast.jsx`

**Responsibility:**
- 일시적 에러 메시지 토스트 표시
- 3초 후 자동 사라짐
- 우측 상단에 슬라이드 인 애니메이션

**Usage Example:**
```javascript
// hooks/useStudentDashboardData.js
import { showErrorToast } from '../components/ui/ErrorToast';

const fetchData = async () => {
  try {
    // ...
  } catch (error) {
    showErrorToast('네트워크 오류가 발생했습니다');
  }
};
```

---

#### StudentDashboardPage 수정 (에러 처리 추가)

```jsx
// pages/StudentDashboardPage.jsx

import ErrorBoundary from '../components/ui/ErrorBoundary';
import ErrorCard from '../components/ui/ErrorCard';

export default function StudentDashboardPage() {
  const { data, loading, error, refetch } = useStudentDashboardData();

  return (
    <ErrorBoundary>
      <div className="dashboard-page">
        {error ? (
          <ErrorCard
            errorType="network"
            message="학생 데이터를 불러오는 중 오류가 발생했습니다"
            onRetry={refetch}
            data-testid="error-message"
          />
        ) : (
          // 차트 컴포넌트들...
        )}
      </div>
    </ErrorBoundary>
  );
}
```

---

#### Module: StudentDashboardPage

**Location**: `frontend/src/pages/StudentDashboardPage.jsx`

**Responsibility**:
- 모든 컴포넌트 통합
- useStudentDashboardData Hook 사용
- 레이아웃 구성

**Test Strategy**: E2E Test (Cypress)

**Test Scenarios (Red Phase)**:
```javascript
// cypress/e2e/student_dashboard.cy.js

describe('Student Dashboard E2E', () => {
  beforeEach(() => {
    cy.visit('/dashboard');
  });

  it('displays student chart and metric card on initial load', () => {
    // Assert
    cy.get('[data-testid="student-bar-chart"]').should('be.visible');
    cy.get('[data-testid="student-metric-card"]').should('contain', '명');
    cy.get('[data-testid="student-metric-card"]').should('contain', '총 재학생');
  });

  it('filters chart by department', () => {
    // Act
    cy.get('[data-testid="department-filter"]').select('컴퓨터공학과');
    cy.wait(500); // 디바운싱 대기

    // Assert
    cy.get('[data-testid="student-bar-chart"]').should('contain', '컴퓨터공학과');
    cy.get('[data-testid="student-metric-card"]').should('contain', '컴퓨터공학과');
  });

  it('filters chart by enrollment status', () => {
    // Act
    cy.get('[data-testid="status-filter-all"]').click();
    cy.wait(500);

    // Assert
    cy.get('[data-testid="student-metric-card"]').should('not.contain', '재학생');
    cy.get('[data-testid="student-metric-card"]').should('contain', '학생'); // 전체 학생
  });

  it('shows tooltip on chart hover', () => {
    // Act
    cy.get('[data-testid="student-bar-chart"] .recharts-bar-rectangle')
      .first()
      .trigger('mouseover');

    // Assert
    cy.get('.custom-tooltip').should('be.visible');
    cy.get('.custom-tooltip').should('contain', '총:');
  });

  it('resets filters to default', () => {
    // Arrange (필터 변경)
    cy.get('[data-testid="department-filter"]').select('전자공학과');
    cy.wait(500);

    // Act
    cy.get('[data-testid="reset-filters-btn"]').click();
    cy.wait(500);

    // Assert
    cy.get('[data-testid="department-filter"]').should('have.value', 'all');
    cy.get('[data-testid="status-filter-재학"]').should('be.checked');
  });

  // Edge Cases
  it('displays empty state when no students exist', () => {
    // Arrange (DB 비우기 - API Mock 필요)
    cy.intercept('GET', '/api/dashboard/students/*', {
      statusCode: 200,
      body: { total_students: 0, by_department: [], updated_at: '2025-11-02T14:35:22Z' }
    });

    // Act
    cy.reload();

    // Assert
    cy.get('[data-testid="student-bar-chart"]').should('contain', '학생 데이터가 없습니다');
  });

  it('displays error message on API failure', () => {
    // Arrange
    cy.intercept('GET', '/api/dashboard/students/*', { statusCode: 500 });

    // Act
    cy.reload();

    // Assert
    cy.get('[data-testid="error-message"]').should('be.visible');
    cy.get('[data-testid="error-message"]').should('contain', '데이터를 불러오는 중 오류가 발생했습니다');
  });
});
```

**Implementation Order (TDD Cycle)**:
1. **Red**: E2E 테스트 작성 → 실패
2. **Green**: StudentDashboardPage 컴포넌트 생성, 모든 하위 컴포넌트 통합 → 통과
3. **Refactor**: 레이아웃 CSS 정리, 반응형 디자인 추가
4. **Commit**: "Add StudentDashboardPage with full integration"

**Dependencies**: 모든 하위 컴포넌트, useStudentDashboardData Hook

---

### 3.6 Phase 6: QA Sheet (Presentation Layer 수동 테스트)

#### Manual Testing Checklist

**테스트 환경**: Chrome 최신 버전, Firefox 최신 버전, Edge 최신 버전

**시각적 검증 항목**:

| 항목 | 검증 내용 | 통과 기준 | 담당자 | 상태 |
|------|----------|----------|--------|------|
| 차트 렌더링 | Recharts BarChart가 정상 표시되는가? | 모든 학과 막대가 보이고 스택 색상 구분 명확 | QA | [ ] |
| 색상 구분 | 학사(파랑), 석사(초록), 박사(주황) 색상 정확한가? | 범례와 막대 색상 일치 | QA | [ ] |
| Tooltip 표시 | 호버 시 Tooltip이 정확히 표시되는가? | 학과명, 각 과정별 인원, 총합 표시 | QA | [ ] |
| 가로 스크롤 | 학과가 10개 이상일 때 스크롤 작동하는가? | 스크롤 바 표시, 모든 학과 접근 가능 | QA | [ ] |
| Metric Card | 총 재학생 수가 천 단위 쉼표로 표시되는가? | "1,234명" 포맷 | QA | [ ] |
| 필터 UI | 드롭다운과 라디오 버튼이 정상 작동하는가? | 클릭/변경 시 즉시 반영 | QA | [ ] |
| 로딩 상태 | 스켈레톤 UI가 300ms 이상 표시되는가? | 부드러운 로딩 애니메이션 | QA | [ ] |
| Empty State | 데이터 없을 때 안내 메시지 표시되는가? | "학생 데이터가 없습니다" 표시 | QA | [ ] |
| 에러 상태 | API 실패 시 에러 메시지 표시되는가? | 사용자 친화적 에러 메시지 | QA | [ ] |
| 반응형 디자인 | 모바일(768px 이하)에서 레이아웃 정상인가? | 스크롤 가능, 텍스트 겹침 없음 | QA | [ ] |

---

## 4. TDD Workflow Summary

### 4.1 전체 구현 순서 (Outside-In)

```
Phase 1: Infrastructure Layer (DB 기반)
  ├─ Red: Student Model 테스트 작성
  ├─ Green: Student Model 구현
  ├─ Red: StudentRepository 테스트 작성
  └─ Green: StudentRepository 구현

Phase 2: Service Layer (비즈니스 로직)
  ├─ Red: StudentDashboardService 테스트 작성 (Mock Repository)
  └─ Green: StudentDashboardService 구현

Phase 3: Presentation Layer (API)
  ├─ Red: StudentDashboardSerializer 테스트 작성
  ├─ Green: StudentDashboardSerializer 구현
  ├─ Red: StudentDashboardView Integration 테스트 작성
  └─ Green: StudentDashboardView 구현

Phase 4: Frontend Hook (데이터 계층)
  ├─ Red: useStudentDashboardData 테스트 작성
  └─ Green: useStudentDashboardData 구현

Phase 5: Frontend Components (UI 계층)
  ├─ Red: StudentBarChart 테스트 작성
  ├─ Green: StudentBarChart 구현
  ├─ Red: StudentMetricCard 테스트 작성
  ├─ Green: StudentMetricCard 구현
  ├─ Red: StudentDashboardFilters 테스트 작성
  └─ Green: StudentDashboardFilters 구현

Phase 6: Integration (전체 통합)
  ├─ Red: StudentDashboardPage 컴포넌트 생성
  ├─ Red: E2E 테스트 작성 (Cypress)
  ├─ Green: 모든 컴포넌트 통합
  └─ Refactor: 레이아웃 최적화, 성능 개선

Phase 7: QA (수동 테스트)
  ├─ QA Sheet 체크리스트 실행
  └─ 발견된 버그 수정 (TDD 사이클 적용)
```

### 4.2 Commit 포인트 제안

- `feat: Add Student model with required fields` (Phase 1-1)
- `feat: Add StudentRepository with filtering logic` (Phase 1-2)
- `feat: Add StudentDashboardService with validation and aggregation` (Phase 2)
- `feat: Add StudentDashboardSerializer` (Phase 3-1)
- `feat: Add StudentDashboardView API endpoint` (Phase 3-2)
- `feat: Add useStudentDashboardData hook with debouncing` (Phase 4)
- `feat: Add StudentBarChart component with Recharts` (Phase 5-1)
- `feat: Add StudentMetricCard component` (Phase 5-2)
- `feat: Add StudentDashboardFilters component` (Phase 5-3)
- `feat: Add StudentDashboardPage with full integration` (Phase 6)
- `test: Add E2E tests for student dashboard` (Phase 6)
- `docs: Add QA checklist for student dashboard` (Phase 7)

### 4.3 완료 기준 (Definition of Done)

**Phase별 완료 조건:**

- [ ] 모든 테스트 통과 (Unit + Integration + E2E)
- [ ] 코드 커버리지 70% 이상 (Unit Test 기준)
- [ ] **모든 보안 요구사항 구현**:
  - [ ] CSRF 방어: Django 기본 CSRF 미들웨어 활성화
  - [ ] XSS 방어: `validationUtils.sanitize_string()` 구현 및 적용
  - [ ] SQL Injection 방어: validationUtils + 학과 화이트리스트 검증
  - [ ] 입력 검증: 학적상태/학과 Enum 화이트리스트 검증
  - [ ] 보안 테스트 통과: `test_xss_prevention`, `test_sql_injection_prevention`
- [ ] **모든 에러 코드 구현** (400 validation_error, 400 invalid_parameter, 404 not_found, 500 server_error)
- [ ] **에러 UI 컴포넌트 구현**:
  - [ ] ErrorBoundary (React 렌더링 에러 캐치)
  - [ ] ErrorCard (차트 로딩 실패 시 에러 카드 + 재시도 버튼)
  - [ ] ErrorToast (일시적 에러 메시지)
  - [ ] StudentDashboardPage에 에러 처리 통합 (`data-testid="error-message"`)
- [ ] **Helper/Utility 함수 구현**:
  - [ ] formatUtils.js (formatNumber, formatDate, formatPercentage)
  - [ ] validationUtils.py (sanitize_string, validate_department_name, validate_enum_value)
- [ ] **성능 요구사항 충족**:
  - [ ] API 응답 시간 < 500ms (평균, 10회 측정)
  - [ ] 최대 응답 시간 < 1000ms
  - [ ] 차트 초기 렌더링 < 1초
- [ ] **데이터베이스 스키마 검증**:
  - [ ] `test_student_model_matches_database_schema` 통과
  - [ ] database.md 명세와 Student 모델 완전 일치
- [ ] QA Sheet 100% 통과
- [ ] 브라우저 호환성 검증 (Chrome, Firefox, Edge 최신 2개 버전)

**최종 완료 조건:**

- [ ] 모든 Phase 완료
- [ ] Spec 문서의 모든 사용자 스토리 구현
- [ ] **모든 P0 보안 요구사항 충족** (CLAUDE.md "Frequently Omitted" 항목)
- [ ] **모든 P1 품질 요구사항 충족** (Helper Functions, Performance Tests, Schema Validation)
- [ ] 모든 Edge Case 처리
- [ ] 모든 에러 시나리오 구현 (userflow.md Section 7)
- [ ] CTO 리뷰 승인

---

## 5. 핵심 원칙 재확인

### 5.1 TDD 사이클 준수

- **Red Phase**: 실패하는 테스트를 먼저 작성 (한 번에 하나씩)
- **Green Phase**: 테스트를 통과시키는 최소 코드 작성 (YAGNI)
- **Refactor Phase**: 중복 제거, 가독성 개선 (테스트는 항상 Green 유지)

### 5.2 MVP 간결성 유지

- 오버엔지니어링 회피: POST-MVP 기능은 구현하지 않음 (Redis 캐싱, Rate Limiting 등)
- 필수 기능만 구현: 학과/학적상태 필터링, Stacked Bar Chart, Metric Card
- 간단한 데이터 구조: by_grade 제거, API 응답 최소화

### 5.3 Test Pyramid 비율

- **Unit Tests (70%)**: Service, Repository, Hook, Component 단위 테스트
- **Integration Tests (10%)**: API 엔드포인트 + DB 조회 플로우
- **E2E Tests (10%)**: 사용자 시나리오 전체 검증
- **Manual QA (10%)**: 시각적 검증, 브라우저 호환성

### 5.4 FIRST 원칙

- **Fast**: 모든 Unit Test는 1초 이내 완료
- **Independent**: 테스트 간 의존성 없음 (각 테스트 독립 실행 가능)
- **Repeatable**: 동일 입력 → 동일 결과 (Mock 사용)
- **Self-validating**: Assert로 자동 검증 (수동 확인 불필요)
- **Timely**: 코드 작성 직전에 테스트 작성 (Red → Green)

---

## 6. 위험 요소 및 대응 방안

| 위험 요소 | 발생 확률 | 영향도 | 대응 방안 |
|----------|----------|--------|----------|
| Recharts 렌더링 성능 저하 (학과 15개 이상) | 중 | 중 | 가로 스크롤 구현, 차트 높이 조정, 또는 Tremor.so 대안 검토 |
| Django ORM 집계 쿼리 느림 (학생 10,000명 이상) | 중 | 고 | 인덱스 추가 (department, enrollment_status), 쿼리 최적화 |
| API 디바운싱으로 인한 UX 지연 | 저 | 저 | 디바운싱 시간 300ms → 200ms 단축 검토 |
| 학과명 긴 경우 X축 레이블 겹침 | 중 | 중 | 레이블 회전 (45도), Tooltip으로 전체 이름 표시 |
| 학생 데이터 없을 때 빈 화면 | 저 | 저 | Empty State 컴포넌트 구현 (명확한 안내 메시지) |
| 브라우저 호환성 (IE11 등 구형 브라우저) | 저 | 중 | 지원 브라우저 명시 (Chrome/Firefox/Edge 최신 2개 버전만), 미지원 브라우저 안내 페이지 |
| E2E 테스트 불안정 (Flaky Test) | 중 | 중 | cy.wait() 적절히 사용, 네트워크 요청 Mock 처리 |

---

## 7. 참고 자료

- **Spec 문서**: `/docs/003-student-dashboard/spec.md`
- **데이터베이스 스키마**: `/docs/database.md`
- **코드베이스 구조**: `/docs/code_structure.md`
- **TDD 가이드**: `/prompt/tdd.md`
- **샘플 데이터**: `/docs/db/student_roster.csv`

---

**문서 끝**
