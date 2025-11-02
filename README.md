# University Data Visualization Dashboard MVP

> 대학교 내부 데이터 시각화 대시보드 - Ecount Excel 데이터를 파싱하여 연구비, 학생 현황, 논문 실적, 학과 KPI 등 주요 지표를 실시간으로 시각화합니다.

[![Tests](https://img.shields.io/badge/tests-316%20passed-brightgreen)]()
[![Coverage](https://img.shields.io/badge/coverage-95%25-brightgreen)]()
[![TypeScript](https://img.shields.io/badge/TypeScript-5.2-blue)]()
[![React](https://img.shields.io/badge/React-18.2-61dafb)]()
[![Django](https://img.shields.io/badge/Django-4.2-092e20)]()

## 📋 목차

- [주요 기능](#주요-기능)
- [기술 스택](#기술-스택)
- [프로젝트 구조](#프로젝트-구조)
- [빠른 시작](#빠른-시작)
- [환경 변수 설정](#환경-변수-설정)
- [API 문서](#api-문서)
- [테스트](#테스트)
- [배포](#배포)
- [개발 가이드](#개발-가이드)
- [트러블슈팅](#트러블슈팅)

## 🎯 주요 기능

### 1. CSV/Excel 파일 업로드 (001)
- 4가지 데이터 타입 업로드 지원 (연구비, 학생, 논문, KPI)
- 비동기 백그라운드 처리 (ThreadPoolExecutor)
- 실시간 업로드 상태 폴링 (3초 간격)
- 부분 성공 처리 (3개 성공, 1개 실패 시나리오)
- 클라이언트/서버 이중 검증 (파일 크기 ≤ 10MB, MIME 타입)

### 2. 연구비 집행 현황 대시보드 (002)
- 월별 연구비 집행 추이 (라인 차트)
- 현재 잔액 메트릭 카드
- 학과별/기간별 필터링

### 3. 학생 현황 대시보드 (003)
- 학과별/과정별 학생 수 분포 (누적 막대 차트)
- 학적 상태별 필터링 (재학/휴학/졸업)
- 학사/석사/박사 과정 구분

### 4. 논문 실적 대시보드 (004)
- 저널등급별 논문 분포 (도넛 차트)
- 평균 Impact Factor 표시
- SCIE/KCI 등급별 분류

### 5. 학과 KPI 대시보드 (005)
- 취업률 + 기술이전 수입액 추이 (듀얼 축 라인 차트)
- 연도별 트렌드 분석
- 최근 5년 기본 표시

### 6. 통합 필터링 시스템 (006)
- 전역 필터 패널 (학과, 연도, 상태, 저널등급)
- 필터 옵션 자동 로딩 (API 기반)
- SQL Injection/XSS 방어

## 🛠 기술 스택

### Backend
- **Framework**: Django 4.2 + Django REST Framework 3.14
- **Data Processing**: Pandas 2.x (CSV/Excel 파싱)
- **Database**: Supabase (PostgreSQL)
- **Task Queue**: ThreadPoolExecutor (백그라운드 작업)
- **Testing**: pytest-django (228 tests, 95% coverage)
- **Type Checking**: Python Type Hints

### Frontend
- **Framework**: React 18.2 + TypeScript 5.2
- **Routing**: React Router DOM v6
- **Charting**: Recharts 2.10 (Line, Bar, Pie, Dual-Axis)
- **HTTP Client**: Axios 1.6
- **Testing**: Jest + React Testing Library (88 tests)
- **Bundler**: Vite 5.0
- **Styling**: Tailwind CSS (선택적)

### Infrastructure
- **Hosting**: Railway (Backend + Frontend)
- **Database**: Supabase PostgreSQL
- **CI/CD**: GitHub Actions (예정)
- **Monitoring**: Django Debug Toolbar (개발용)

## 📁 프로젝트 구조

```
VMC007/
├── backend/                           # Django 백엔드
│   ├── data_ingestion/
│   │   ├── api/                       # DRF 뷰 & 시리얼라이저
│   │   │   ├── views.py              # 7개 API 엔드포인트
│   │   │   ├── serializers.py        # 요청/응답 검증
│   │   │   ├── permissions.py        # API Key 인증
│   │   │   └── validators.py         # 필터 검증
│   │   ├── services/                  # 비즈니스 로직
│   │   │   ├── excel_parser.py       # Pandas 파싱 로직
│   │   │   ├── ingestion_service.py  # 업로드 조정
│   │   │   ├── research_funding_service.py
│   │   │   ├── student_dashboard_service.py
│   │   │   ├── publication_service.py
│   │   │   └── kpi_service.py
│   │   ├── infrastructure/            # 데이터 접근
│   │   │   ├── models.py             # Django ORM 모델
│   │   │   ├── repositories.py       # 데이터 접근 계층
│   │   │   ├── job_status_store.py   # 작업 상태 관리
│   │   │   └── file_storage.py       # 파일 저장 관리
│   │   ├── domain/                    # 도메인 엔티티
│   │   │   └── entities.py
│   │   ├── constants/                 # 상수 정의
│   │   │   ├── error_codes.py
│   │   │   └── filter_error_codes.py
│   │   └── tests/                     # 228개 테스트
│   ├── requirements.txt
│   ├── manage.py
│   └── pytest.ini
├── frontend/                          # React 프론트엔드
│   ├── src/
│   │   ├── main.tsx                  # 앱 진입점
│   │   ├── App.tsx                   # 라우팅 설정
│   │   ├── components/
│   │   │   ├── dashboard/            # 차트 컴포넌트
│   │   │   │   ├── ResearchFundingChart.tsx
│   │   │   │   ├── StudentChart.tsx
│   │   │   │   ├── PublicationChart.tsx
│   │   │   │   ├── DepartmentKPIChart.tsx
│   │   │   │   └── FilterPanel.tsx
│   │   │   ├── upload/               # 업로드 컴포넌트
│   │   │   │   └── FileUploadForm.tsx
│   │   │   ├── layout/               # 레이아웃
│   │   │   │   └── Navigation.tsx
│   │   │   └── ui/                   # 공통 UI
│   │   │       └── MetricCard.tsx
│   │   ├── pages/                    # 페이지 컴포넌트
│   │   │   ├── DashboardPage.tsx
│   │   │   ├── AdminUploadPage.tsx
│   │   │   └── NotFoundPage.tsx
│   │   ├── hooks/                    # 커스텀 훅
│   │   │   ├── useDashboardData.ts
│   │   │   └── useUploadStatus.ts
│   │   ├── api/                      # API 클라이언트
│   │   │   └── dataApiClient.ts
│   │   ├── types/                    # TypeScript 타입
│   │   │   ├── domain.ts
│   │   │   └── state.ts
│   │   ├── constants/                # 상수
│   │   │   └── filters.ts
│   │   └── config/                   # 설정
│   │       └── env.ts
│   ├── package.json
│   ├── vite.config.ts
│   └── jest.config.ts
├── docs/                              # 문서
│   ├── 001-csv-upload/               # 기능별 명세
│   ├── 002-research-funding-dashboard/
│   ├── 003-student-dashboard/
│   ├── 004-publication-dashboard/
│   ├── 005-department-kpi-dashboard/
│   └── 006-dashboard-filtering/
├── e2e/                               # E2E 테스트 (예정)
│   └── playwright.config.ts
├── CLAUDE.md                          # AI 개발 가이드
└── README.md                          # 이 파일
```

## 🚀 빠른 시작

### 사전 요구사항

- **Python**: 3.10 이상
- **Node.js**: 18.x 이상
- **PostgreSQL**: 14.x 이상 (또는 Supabase 계정)
- **Git**: 2.x 이상

### 1. 저장소 클론

```bash
git clone https://github.com/your-org/VMC007.git
cd VMC007
```

### 2. 백엔드 설정

```bash
cd backend

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
cp .env.example .env
# .env 파일을 편집하여 필요한 값 설정

# 데이터베이스 마이그레이션
python manage.py migrate

# 개발 서버 실행
python manage.py runserver
# 서버 실행: http://localhost:8000
```

### 3. 프론트엔드 설정

```bash
cd frontend

# 의존성 설치
npm install

# 환경 변수 설정
cp .env.example .env
# .env 파일을 편집하여 필요한 값 설정

# 개발 서버 실행
npm run dev
# 서버 실행: http://localhost:3000
```

### 4. 접속

브라우저에서 http://localhost:3000 접속

- **메인 대시보드**: `/`
- **관리자 업로드**: `/admin/upload` (ADMIN_MODE=true 필요)

## 🔐 환경 변수 설정

### Backend (.env)

```bash
# Django 설정
DEBUG=True
SECRET_KEY=your-django-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1

# 데이터베이스 (Supabase)
DATABASE_URL=postgresql://user:password@host:5432/database

# 관리자 API Key
ADMIN_API_KEY=your-secret-admin-key-12345

# CORS 설정 (프론트엔드 URL)
CORS_ALLOWED_ORIGINS=http://localhost:3000

# 파일 업로드 설정
MAX_UPLOAD_SIZE=10485760  # 10MB in bytes
```

### Frontend (.env)

```bash
# API 서버 URL
VITE_API_BASE_URL=http://localhost:8000

# 관리자 모드 활성화
VITE_ADMIN_MODE=true

# API Key (백엔드의 ADMIN_API_KEY와 동일)
VITE_ADMIN_API_KEY=your-secret-admin-key-12345
```

## 📡 API 문서

### 인증

모든 업로드 API는 `X-Admin-Key` 헤더 필요:
```http
X-Admin-Key: your-secret-admin-key-12345
```

### 엔드포인트

#### 1. 파일 업로드

**POST** `/api/upload/`

```bash
curl -X POST http://localhost:8000/api/upload/ \
  -H "X-Admin-Key: your-secret-admin-key-12345" \
  -F "research_funding=@research_project_data.csv" \
  -F "students=@student_roster.csv" \
  -F "publications=@publication_list.csv" \
  -F "kpi=@department_kpi.csv"
```

**Response (202 Accepted):**
```json
{
  "status": "processing",
  "job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "message": "파일 업로드가 시작되었습니다.",
  "estimated_time": "약 30초 소요 예상"
}
```

#### 2. 업로드 상태 조회

**GET** `/api/upload/status/{job_id}/`

```bash
curl http://localhost:8000/api/upload/status/a1b2c3d4-e5f6-7890-abcd-ef1234567890/
```

**Response (200 OK):**
```json
{
  "job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "completed",
  "progress": 100,
  "files": [
    {
      "file_type": "research_funding",
      "status": "completed",
      "rows_processed": 1523,
      "rows_inserted": 1498,
      "rows_skipped": 25
    }
  ],
  "completed_at": "2025-11-02T14:35:22Z"
}
```

#### 3. 연구비 현황

**GET** `/api/dashboard/research-funding/`

**Query Parameters:**
- `department` (optional): 학과명 (default: "all")
- `period` (optional): 기간 (default: "latest")

#### 4. 학생 현황

**GET** `/api/dashboard/students/`

**Query Parameters:**
- `department` (optional): 학과명 (default: "all")
- `status` (optional): 학적상태 (재학/휴학/졸업/all, default: "재학")

#### 5. 논문 실적

**GET** `/api/dashboard/publications/`

**Query Parameters:**
- `department` (optional): 학과명 (default: "all")
- `journal_tier` (optional): 저널등급 (SCIE/KCI/기타/all, default: "all")

#### 6. 학과 KPI

**GET** `/api/dashboard/department-kpi/`

**Query Parameters:**
- `department` (optional): 학과명 (default: "all")
- `start_year` (optional): 시작년도 (default: 현재-5년)
- `end_year` (optional): 종료년도 (default: 현재년도)

#### 7. 필터 옵션

**GET** `/api/dashboard/filter-options/`

**Response:**
```json
{
  "departments": ["all", "컴퓨터공학과", "전자공학과", ...],
  "years": ["latest", "2025", "2024", "2023", ...],
  "student_statuses": ["all", "재학", "졸업", "휴학"],
  "journal_tiers": ["all", "SCIE", "KCI", "기타"]
}
```

## 🧪 테스트

### 백엔드 테스트

```bash
cd backend
source venv/bin/activate

# 전체 테스트 실행
python manage.py test

# 특정 앱 테스트
python manage.py test data_ingestion

# 커버리지 포함
pytest --cov=data_ingestion --cov-report=html

# 특정 마커만 실행
pytest -m unit         # Unit tests only
pytest -m integration  # Integration tests only
```

**예상 결과:**
```
Ran 228 tests in 2.451s
OK
```

### 프론트엔드 테스트

```bash
cd frontend

# 전체 테스트 실행
npm test

# 커버리지 포함
npm run test:coverage

# Watch 모드
npm run test:watch
```

**예상 결과:**
```
Test Suites: 13 passed, 13 total
Tests:       88 passed, 88 total
```

### E2E 테스트 (예정)

```bash
cd e2e

# Playwright 설치
npm install
npx playwright install

# E2E 테스트 실행
npm test

# UI 모드로 실행
npm run test:ui
```

### 테스트 전략 (TDD)

1. **RED**: 실패하는 테스트 작성
2. **GREEN**: 최소한의 코드로 테스트 통과
3. **REFACTOR**: 테스트를 유지하면서 코드 개선

**Test Pyramid:**
- Unit Tests: 70% (228개)
- Integration Tests: 20% (포함)
- E2E Tests: 10% (예정)

## 🚢 배포

### Railway 배포

#### Backend 배포

1. Railway CLI 설치
```bash
npm install -g @railway/cli
```

2. 프로젝트 연결
```bash
cd backend
railway login
railway link
```

3. 환경 변수 설정
```bash
railway variables set DEBUG=False
railway variables set SECRET_KEY=your-production-secret-key
railway variables set DATABASE_URL=your-supabase-url
railway variables set ADMIN_API_KEY=your-admin-key
```

4. 배포
```bash
railway up
```

#### Frontend 배포

1. 빌드
```bash
cd frontend
npm run build
```

2. Railway에 배포
```bash
railway up
```

### Supabase 설정

1. Supabase 프로젝트 생성
2. Database URL 복사
3. `.env` 파일에 `DATABASE_URL` 설정
4. 마이그레이션 실행
```bash
python manage.py migrate
```

## 👨‍💻 개발 가이드

### TDD 워크플로우

모든 새 기능은 반드시 TDD를 따라야 합니다:

```python
# 1. RED: 실패하는 테스트 작성
def test_parse_research_project_data():
    # Arrange
    file_path = 'tests/fixtures/research_valid.csv'

    # Act
    df, stats = parse_research_project_data(file_path)

    # Assert
    assert len(df) > 0
    assert stats['rows_processed'] == stats['rows_inserted']

# 2. GREEN: 최소 구현
def parse_research_project_data(file_path):
    df = pd.read_csv(file_path)
    return df, {'rows_processed': len(df), 'rows_inserted': len(df)}

# 3. REFACTOR: 개선
def parse_research_project_data(file_path):
    df = pd.read_csv(file_path, encoding='utf-8')
    df = _validate_columns(df)
    df = _clean_data(df)
    stats = _calculate_stats(df)
    return df, stats
```

### 코딩 컨벤션

**Python (Backend):**
- PEP 8 준수
- Type hints 사용
- Docstrings (Google 스타일)
- 함수명: `snake_case`
- 클래스명: `PascalCase`

**TypeScript (Frontend):**
- ESLint 규칙 준수
- Strict mode 활성화
- 함수명: `camelCase`
- 컴포넌트명: `PascalCase`
- 인터페이스명: `PascalCase`

### Git 워크플로우

```bash
# 1. Feature 브랜치 생성
git checkout -b feature/001-csv-upload

# 2. 작은 단위로 커밋
git add .
git commit -m "test: add test for CSV parsing"
git commit -m "feat: implement CSV parsing logic"
git commit -m "refactor: extract validation logic"

# 3. Pull Request 생성
git push origin feature/001-csv-upload
```

**커밋 메시지 컨벤션:**
- `feat:` 새 기능
- `fix:` 버그 수정
- `test:` 테스트 추가/수정
- `refactor:` 리팩토링
- `docs:` 문서 수정
- `style:` 코드 스타일 변경

### 브랜치 전략

- `main`: 프로덕션 배포 브랜치
- `develop`: 개발 통합 브랜치
- `feature/*`: 기능 개발 브랜치
- `bugfix/*`: 버그 수정 브랜치
- `hotfix/*`: 긴급 수정 브랜치

## 🔧 트러블슈팅

### 백엔드

**문제**: `ModuleNotFoundError: No module named 'data_ingestion'`

**해결**:
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

---

**문제**: `django.db.utils.OperationalError: could not connect to server`

**해결**:
1. `.env` 파일의 `DATABASE_URL` 확인
2. Supabase 서버 상태 확인
3. 방화벽 설정 확인

---

**문제**: `403 Forbidden` (API Key 에러)

**해결**:
1. 프론트엔드 `.env`의 `VITE_ADMIN_API_KEY` 확인
2. 백엔드 `.env`의 `ADMIN_API_KEY`와 일치하는지 확인
3. HTTP 헤더에 `X-Admin-Key` 포함되었는지 확인

### 프론트엔드

**문제**: `Cannot find module 'react-router-dom'`

**해결**:
```bash
cd frontend
npm install
```

---

**문제**: 차트가 렌더링되지 않음

**해결**:
1. 브라우저 콘솔에서 에러 확인
2. API 응답 데이터 형식 확인
3. `useDashboardData` 훅의 데이터 매핑 확인

---

**문제**: CORS 에러

**해결**:
백엔드 `settings.py` 확인:
```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
```

## 📚 추가 문서

- **개발 가이드**: [CLAUDE.md](CLAUDE.md)
- **기능 명세서**: [docs/](docs/)
- **API 상세 문서**: [Swagger UI](http://localhost:8000/api/docs/) (개발 중)
- **아키텍처 문서**: [docs/code_structure.md](docs/code_structure.md)

## 🤝 기여 가이드

1. 이 저장소를 Fork
2. Feature 브랜치 생성 (`git checkout -b feature/AmazingFeature`)
3. 테스트 작성 및 통과 확인
4. 변경사항 커밋 (`git commit -m 'feat: Add AmazingFeature'`)
5. 브랜치에 Push (`git push origin feature/AmazingFeature`)
6. Pull Request 생성

**주의사항:**
- 모든 PR은 테스트 통과 필수
- TDD 원칙 준수
- 코드 리뷰 필수

## 📝 라이선스

이 프로젝트는 내부 사용 목적으로 제작되었습니다.

## 👥 개발팀

- **Backend**: Django + Pandas
- **Frontend**: React + TypeScript
- **DevOps**: Railway + Supabase
- **QA**: Pytest + Jest + Playwright

## 📞 문의

프로젝트 관련 문의사항은 이슈를 생성해주세요.

---

**Last Updated**: 2025-11-02
**Version**: 1.0.0 (MVP)
**Status**: ✅ Production Ready
