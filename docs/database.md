# 데이터베이스 설계 문서 (MVP)

**프로젝트:** 대학교 사내 데이터 시각화 대시보드 MVP
**데이터베이스:** PostgreSQL (Supabase)
**작성일:** 2025년 11월 2일
**버전:** 2.0 (MVP 최적화)

---

## 문서 개요

본 문서는 대학교 사내 데이터 시각화 대시보드의 **최소 스펙(MVP)** 데이터베이스 스키마를 정의합니다. 첫 베타테스트에 필요한 핵심 기능만 포함하며, 오버엔지니어링을 철저히 배제합니다.

**핵심 설계 원칙:**
- 유저플로우에 명시된 데이터만 포함 (YAGNI 원칙)
- 정규화는 필요한 수준까지만 (MVP 성능 우선)
- 간단한 데이터 타입 사용 (복잡한 제약 조건 최소화)
- 확장 가능하지만 간결한 구조

---

## 목차

1. [데이터플로우 개요](#1-데이터플로우-개요)
2. [데이터베이스 스키마](#2-데이터베이스-스키마)
3. [테이블 상세 명세](#3-테이블-상세-명세)
4. [인덱스 전략](#4-인덱스-전략)
5. [데이터 제약 조건](#5-데이터-제약-조건)
6. [데이터 마이그레이션 전략](#6-데이터-마이그레이션-전략)

---

## 1. 데이터플로우 개요

### 1.1 전체 데이터 흐름

```
관리자 업로드
    ↓
CSV/Excel 파일 (4가지 타입)
    ↓
DRF API 엔드포인트 (POST /upload)
    ↓
Pandas 파싱 및 정제 (excel_parser.py)
    ↓
PostgreSQL (Supabase) - 4개 핵심 테이블
    ↓
DRF API 조회 (GET /dashboard/*)
    ↓
React 대시보드 시각화 (Recharts)
```

### 1.2 데이터 타입별 처리 플로우

#### 1.2.1 연구비 집행 데이터
```
research_project_data.csv
    → Pandas 파싱 (필수 컬럼 검증)
    → 날짜/금액 타입 변환
    → 중복 제거 (집행ID 기준)
    → research_projects 테이블 INSERT
    → 집계: 월별 집행 추이, 현재 잔액
```

#### 1.2.2 학생 명단 데이터
```
student_roster.csv
    → Pandas 파싱 (필수 컬럼 검증)
    → 학년/과정구분 정규화
    → 중복 제거 (학번 기준)
    → students 테이블 INSERT
    → 집계: 학과별/과정별/학년별 학생 수
```

#### 1.2.3 논문 목록 데이터
```
publication_list.csv
    → Pandas 파싱 (필수 컬럼 검증)
    → Impact Factor NULL 허용 처리
    → 중복 제거 (논문ID 기준)
    → publications 테이블 INSERT
    → 집계: 저널 등급별 논문 수, 평균 IF
```

#### 1.2.4 학과 KPI 데이터
```
department_kpi.csv
    → Pandas 파싱 (필수 컬럼 검증)
    → 취업률/수입액 타입 변환
    → 중복 제거 (평가년도+학과 복합키)
    → department_kpis 테이블 INSERT
    → 집계: 년도별 KPI 추이
```

### 1.3 데이터 갱신 전략

**MVP에서는 전체 교체 모드(Replace All) 사용:**
1. 관리자가 파일 재업로드 시
2. 해당 타입의 기존 데이터 전체 삭제 (`DELETE FROM table`)
3. 신규 데이터 Bulk Insert (`bulk_create`)
4. Django ORM 트랜잭션으로 원자성 보장

**추후 고려 사항 (MVP 이후):**
- 증분 업데이트 (UPSERT)
- 데이터 변경 이력 추적 (Audit Log)
- Soft Delete (삭제 플래그)

---

## 2. 데이터베이스 스키마

### 2.1 ERD (Entity Relationship Diagram)

```
┌─────────────────────────┐
│  research_projects      │
├─────────────────────────┤
│ PK execution_id         │ (집행ID)
│    department           │ (소속학과)
│    total_budget         │ (총연구비)
│    execution_date       │ (집행일자)
│    execution_amount     │ (집행금액)
│    created_at           │
│    updated_at           │
└─────────────────────────┘

┌─────────────────────────┐
│  students               │
├─────────────────────────┤
│ PK student_id           │ (학번)
│    department           │ (학과)
│    grade                │ (학년)
│    program_type         │ (과정구분)
│    enrollment_status    │ (학적상태)
│    created_at           │
│    updated_at           │
└─────────────────────────┘

┌─────────────────────────┐
│  publications           │
├─────────────────────────┤
│ PK paper_id             │ (논문ID)
│    department           │ (학과)
│    journal_tier         │ (저널등급)
│    impact_factor        │ (Impact Factor, nullable)
│    created_at           │
│    updated_at           │
└─────────────────────────┘

┌─────────────────────────┐
│  department_kpis        │
├─────────────────────────┤
│ PK id (auto)            │
│    evaluation_year      │ (평가년도)
│    department           │ (학과)
│    employment_rate      │ (졸업생 취업률)
│    tech_transfer_income │ (기술이전 수입액)
│    created_at           │
│    updated_at           │
└─────────────────────────┘
│ UNIQUE(evaluation_year, department) │
```

**테이블 간 관계:**
- MVP에서는 명시적 외래키 없음 (복잡도 회피)
- 학과(department) 컬럼으로 암묵적 연결
- 추후 필요 시 `departments` 마스터 테이블 추가 고려

---

## 3. 테이블 상세 명세

### 3.1 research_projects (연구비 집행 데이터)

**용도:** 연구비 집행 추이 시각화 (Line Chart + Metric Card)

| 컬럼명 | 데이터 타입 | Null | 기본값 | 설명 |
|--------|------------|------|--------|------|
| execution_id | VARCHAR(100) | NOT NULL | - | 집행ID (Primary Key) |
| department | VARCHAR(100) | NOT NULL | - | 소속학과 (필터링 기준) |
| total_budget | BIGINT | NOT NULL | - | 총연구비 (원 단위) |
| execution_date | DATE | NOT NULL | - | 집행일자 (시계열 분석) |
| execution_amount | BIGINT | NOT NULL | - | 집행금액 (원 단위) |
| created_at | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP | 레코드 생성 시각 |
| updated_at | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP | 레코드 수정 시각 |

**비즈니스 로직 검증 (Pandas 레이어):**
- `execution_amount <= total_budget` (집행금액은 총연구비 이하)
- `execution_date <= CURRENT_DATE` (미래 날짜 불허)
- `execution_amount >= 0` (음수 불허)
- `total_budget >= 0` (음수 불허)

**집계 쿼리 예시:**
```sql
-- 현재 연구비 잔액 계산
SELECT
    SUM(total_budget) - SUM(execution_amount) AS current_balance
FROM research_projects;

-- 월별 집행 추이
SELECT
    DATE_TRUNC('month', execution_date) AS month,
    SUM(execution_amount) AS monthly_execution
FROM research_projects
GROUP BY month
ORDER BY month;

-- 학과별 연구비 현황
SELECT
    department,
    SUM(total_budget) AS total,
    SUM(execution_amount) AS executed,
    SUM(total_budget) - SUM(execution_amount) AS balance
FROM research_projects
GROUP BY department;
```

---

### 3.2 students (학생 명단)

**용도:** 학과별 학생 현황 시각화 (Stacked Bar Chart)

| 컬럼명 | 데이터 타입 | Null | 기본값 | 설명 |
|--------|------------|------|--------|------|
| student_id | VARCHAR(50) | NOT NULL | - | 학번 (Primary Key) |
| department | VARCHAR(100) | NOT NULL | - | 학과 (필터링 기준) |
| grade | INTEGER | NOT NULL | - | 학년 (1~4) |
| program_type | VARCHAR(20) | NOT NULL | - | 과정구분 (학사/석사/박사) |
| enrollment_status | VARCHAR(20) | NOT NULL | - | 학적상태 (재학/휴학/졸업) |
| created_at | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP | 레코드 생성 시각 |
| updated_at | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP | 레코드 수정 시각 |

**비즈니스 로직 검증 (Pandas 레이어):**
- `grade BETWEEN 1 AND 4` (학년 범위 검증)
- `program_type IN ('학사', '석사', '박사')` (허용된 값만)
- `enrollment_status IN ('재학', '휴학', '졸업')` (허용된 값만)

**집계 쿼리 예시:**
```sql
-- 학과별/과정별 학생 수
SELECT
    department,
    program_type,
    COUNT(*) AS student_count
FROM students
WHERE enrollment_status = '재학'
GROUP BY department, program_type;

-- 학과별 학년 분포
SELECT
    department,
    grade,
    COUNT(*) AS count
FROM students
WHERE enrollment_status = '재학'
GROUP BY department, grade
ORDER BY department, grade;

-- 전체 재학생 수
SELECT COUNT(*) FROM students WHERE enrollment_status = '재학';
```

---

### 3.3 publications (논문 목록)

**용도:** 논문 실적 시각화 (Doughnut Chart + Metric Card)

| 컬럼명 | 데이터 타입 | Null | 기본값 | 설명 |
|--------|------------|------|--------|------|
| paper_id | VARCHAR(100) | NOT NULL | - | 논문ID (Primary Key) |
| department | VARCHAR(100) | NOT NULL | - | 학과 (필터링 기준) |
| journal_tier | VARCHAR(50) | NOT NULL | - | 저널등급 (SCIE/KCI/기타) |
| impact_factor | NUMERIC(5,2) | NULL | NULL | Impact Factor (소수점 2자리) |
| created_at | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP | 레코드 생성 시각 |
| updated_at | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP | 레코드 수정 시각 |

**비즈니스 로직 검증 (Pandas 레이어):**
- `impact_factor >= 0 OR impact_factor IS NULL` (음수 불허)
- `journal_tier IN ('SCIE', 'KCI', ...)` (정의된 등급만 허용)

**집계 쿼리 예시:**
```sql
-- 저널 등급별 논문 수
SELECT
    journal_tier,
    COUNT(*) AS paper_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS percentage
FROM publications
GROUP BY journal_tier;

-- 평균 Impact Factor (NULL 제외)
SELECT
    AVG(impact_factor) AS avg_impact_factor,
    COUNT(*) FILTER (WHERE impact_factor IS NOT NULL) AS papers_with_if
FROM publications;

-- 학과별 논문 성과
SELECT
    department,
    COUNT(*) AS total_papers,
    COUNT(*) FILTER (WHERE journal_tier = 'SCIE') AS scie_count,
    AVG(impact_factor) AS avg_if
FROM publications
GROUP BY department;
```

---

### 3.4 department_kpis (학과 KPI)

**용도:** 학과 KPI 추이 시각화 (Dual-axis Line Chart)

| 컬럼명 | 데이터 타입 | Null | 기본값 | 설명 |
|--------|------------|------|--------|------|
| id | SERIAL | NOT NULL | AUTO | 자동 증가 ID (Primary Key) |
| evaluation_year | INTEGER | NOT NULL | - | 평가년도 (YYYY) |
| department | VARCHAR(100) | NOT NULL | - | 학과 |
| employment_rate | NUMERIC(5,2) | NOT NULL | - | 졸업생 취업률 (%) |
| tech_transfer_income | NUMERIC(10,2) | NOT NULL | - | 기술이전 수입액 (억원) |
| created_at | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP | 레코드 생성 시각 |
| updated_at | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP | 레코드 수정 시각 |

**제약 조건:**
- UNIQUE(evaluation_year, department): 동일 년도+학과 중복 방지

**비즈니스 로직 검증 (Pandas 레이어):**
- `employment_rate BETWEEN 0 AND 100` (취업률 범위)
- `tech_transfer_income >= 0` (음수 불허)
- `evaluation_year >= 2000 AND evaluation_year <= EXTRACT(YEAR FROM CURRENT_DATE)` (유효 년도)

**집계 쿼리 예시:**
```sql
-- 년도별 평균 취업률 및 기술이전 수입액
SELECT
    evaluation_year,
    AVG(employment_rate) AS avg_employment_rate,
    SUM(tech_transfer_income) AS total_tech_income
FROM department_kpis
GROUP BY evaluation_year
ORDER BY evaluation_year;

-- 학과별 KPI 추이
SELECT
    evaluation_year,
    department,
    employment_rate,
    tech_transfer_income
FROM department_kpis
WHERE department = '컴퓨터공학과'
ORDER BY evaluation_year;

-- 최신 년도 평균 KPI
SELECT
    AVG(employment_rate) AS latest_avg_employment_rate,
    SUM(tech_transfer_income) AS latest_total_income
FROM department_kpis
WHERE evaluation_year = (SELECT MAX(evaluation_year) FROM department_kpis);
```

---

## 4. 인덱스 전략 (MVP)

**MVP 인덱스 (필수만):**

| 테이블 | 인덱스 컬럼 | 목적 |
|--------|------------|------|
| research_projects | department | 학과별 필터링 |
| research_projects | execution_date | 시계열 정렬 및 범위 조회 |
| students | department | 학과별 필터링 |
| students | enrollment_status | 학적상태 필터링 (재학생 조회) |
| publications | department | 학과별 필터링 |
| publications | journal_tier | 저널 등급별 집계 |
| department_kpis | evaluation_year | 년도별 정렬 및 필터 |
| department_kpis | (evaluation_year, department) | UNIQUE 제약 (중복 방지) |

**성능 문제 발생 시 추가 고려:**
- 복합 인덱스 (department + 다른 컬럼)
- Partial 인덱스
- 쿼리 최적화

---

## 5. 데이터 제약 조건

### 5.1 NULL 처리 정책

**NOT NULL 필수 컬럼:**
- 모든 PK 컬럼
- 필터링 및 집계에 사용되는 핵심 컬럼 (department, 날짜, 금액 등)

**NULL 허용 컬럼:**
- `publications.impact_factor`: 모든 논문에 IF가 있는 것은 아님
- 추후 추가되는 선택적 메타데이터

### 5.2 데이터 무결성 제약

**애플리케이션 레벨 (Pandas + DRF):**
- 범위 검증 (학년, 취업률, 금액 등)
- 날짜 유효성 (미래 날짜 불허)
- Enum 값 검증 (학적상태, 과정구분 등)
- 비즈니스 로직 (집행금액 <= 총연구비)

**데이터베이스 레벨 (최소):**
- NOT NULL 제약
- UNIQUE 제약 (PK, department_kpis 복합키)
- CHECK 제약 (MVP에서는 사용 안 함 - 애플리케이션에서 처리)

**이유:** MVP에서는 Pandas에서 정제 완료된 데이터만 DB에 삽입하므로, 복잡한 DB 제약은 오버엔지니어링

---

## 6. 데이터 마이그레이션 전략

### 6.1 초기 마이그레이션

**파일:** `/supabase/migrations/20251102000001_create_initial_schema.sql`

**내용:**
1. 4개 핵심 테이블 생성
2. Primary Key 설정
3. 필수 인덱스 생성 (department)
4. UNIQUE 제약 (department_kpis)
5. created_at/updated_at 자동 업데이트 트리거 설정

### 6.2 업데이트 트리거 설정

PostgreSQL에서 `updated_at` 컬럼 자동 업데이트:

```sql
-- 트리거 함수 생성 (공통)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 각 테이블에 트리거 적용
CREATE TRIGGER update_research_projects_updated_at
    BEFORE UPDATE ON research_projects
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

### 6.3 데이터 롤백 전략

**전체 교체 모드의 위험성 완화:**
1. 업로드 전 자동 백업 (선택적)
2. Django ORM 트랜잭션 사용 (ROLLBACK 가능)
3. Supabase 자동 백업 활용

**복구 절차 (추후 구현):**
```sql
-- 테이블 스냅샷 저장 (업로드 전)
CREATE TABLE research_projects_backup_20251102 AS
SELECT * FROM research_projects;

-- 롤백 (필요 시)
TRUNCATE research_projects;
INSERT INTO research_projects SELECT * FROM research_projects_backup_20251102;
```

---

## 7. 확장 고려 사항 (MVP 이후)

### 7.1 추가 테이블 후보

**데이터 변경 이력 추적:**
```sql
CREATE TABLE data_upload_logs (
    id SERIAL PRIMARY KEY,
    job_id UUID NOT NULL,
    data_type VARCHAR(50) NOT NULL,
    file_name VARCHAR(255),
    rows_processed INTEGER,
    rows_inserted INTEGER,
    status VARCHAR(20),
    error_message TEXT,
    uploaded_by VARCHAR(100),
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**학과 마스터 테이블:**
```sql
CREATE TABLE departments (
    code VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**사용자 인증 (DB 기반으로 전환 시):**
```sql
CREATE TABLE admin_users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'admin',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 7.2 파티셔닝 전략 (대용량 데이터)

시계열 데이터 파티셔닝 (년도별):

```sql
CREATE TABLE research_projects (
    -- 기존 컬럼들...
) PARTITION BY RANGE (execution_date);

CREATE TABLE research_projects_2024
    PARTITION OF research_projects
    FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');

CREATE TABLE research_projects_2025
    PARTITION OF research_projects
    FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');
```

---

## 문서 변경 이력

| 버전 | 날짜 | 변경 사항 | 작성자 |
|------|------|-----------|--------|
| 1.0 | 2025-11-02 | 초기 데이터베이스 스키마 문서 작성 | Database Writer Agent |
| 2.0 | 2025-11-02 | MVP 최적화 (불필요한 인덱스/섹션 제거) | Claude Code |

---

## 승인 및 검토

**작성자:** Database Writer Agent / Claude Code
**검토자:** CTO
**승인일:** 2025-11-02

본 데이터베이스 스키마는 **MVP 범위**에 맞춘 최소 데이터 모델입니다. 첫 베타테스트에 필요한 핵심 테이블과 인덱스만 포함하며, 성능 문제 발견 시 추가 최적화를 진행합니다.

---

**문서 끝**
