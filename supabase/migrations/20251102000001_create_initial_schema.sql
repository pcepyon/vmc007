-- ============================================================================
-- Migration: Initial Database Schema (MVP)
-- Project: 대학교 사내 데이터 시각화 대시보드 MVP
-- Version: 2.0
-- Created: 2025-11-02
-- Updated: 2025-11-02
-- Description: 4개 핵심 테이블 + MVP 필수 인덱스만 (복합 인덱스 제외)
-- ============================================================================

-- ============================================================================
-- 1. 연구비 집행 데이터 테이블 (Research Projects)
-- ============================================================================

CREATE TABLE IF NOT EXISTS research_projects (
    -- Primary Key
    execution_id VARCHAR(100) NOT NULL PRIMARY KEY,

    -- 필수 컬럼
    department VARCHAR(100) NOT NULL,
    total_budget BIGINT NOT NULL,
    execution_date DATE NOT NULL,
    execution_amount BIGINT NOT NULL,

    -- 메타데이터
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스: 학과별 필터링 (MVP 필수)
CREATE INDEX idx_research_projects_department
    ON research_projects(department);

-- 인덱스: 시계열 정렬 및 범위 조회 (MVP 필수)
CREATE INDEX idx_research_projects_execution_date
    ON research_projects(execution_date);

-- 테이블 코멘트
COMMENT ON TABLE research_projects IS '연구비 집행 데이터 - Ecount research_project_data.csv';
COMMENT ON COLUMN research_projects.execution_id IS '집행ID (Primary Key)';
COMMENT ON COLUMN research_projects.department IS '소속학과';
COMMENT ON COLUMN research_projects.total_budget IS '총연구비 (원 단위)';
COMMENT ON COLUMN research_projects.execution_date IS '집행일자';
COMMENT ON COLUMN research_projects.execution_amount IS '집행금액 (원 단위)';

-- ============================================================================
-- 2. 학생 명단 테이블 (Students)
-- ============================================================================

CREATE TABLE IF NOT EXISTS students (
    -- Primary Key
    student_id VARCHAR(50) NOT NULL PRIMARY KEY,

    -- 필수 컬럼
    department VARCHAR(100) NOT NULL,
    grade INTEGER NOT NULL,
    program_type VARCHAR(20) NOT NULL,
    enrollment_status VARCHAR(20) NOT NULL,

    -- 메타데이터
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스: 학과별 필터링 (MVP 필수)
CREATE INDEX idx_students_department
    ON students(department);

-- 인덱스: 학적상태 필터링 (MVP 필수)
CREATE INDEX idx_students_enrollment_status
    ON students(enrollment_status);

-- 테이블 코멘트
COMMENT ON TABLE students IS '학생 명단 - Ecount student_roster.csv';
COMMENT ON COLUMN students.student_id IS '학번 (Primary Key)';
COMMENT ON COLUMN students.department IS '학과';
COMMENT ON COLUMN students.grade IS '학년 (1-4)';
COMMENT ON COLUMN students.program_type IS '과정구분 (학사/석사/박사)';
COMMENT ON COLUMN students.enrollment_status IS '학적상태 (재학/휴학/졸업)';

-- ============================================================================
-- 3. 논문 목록 테이블 (Publications)
-- ============================================================================

CREATE TABLE IF NOT EXISTS publications (
    -- Primary Key
    paper_id VARCHAR(100) NOT NULL PRIMARY KEY,

    -- 필수 컬럼
    department VARCHAR(100) NOT NULL,
    journal_tier VARCHAR(50) NOT NULL,

    -- 선택적 컬럼 (NULL 허용)
    impact_factor NUMERIC(5,2),

    -- 메타데이터
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스: 학과별 필터링 (MVP 필수)
CREATE INDEX idx_publications_department
    ON publications(department);

-- 인덱스: 저널 등급별 집계 (MVP 필수)
CREATE INDEX idx_publications_journal_tier
    ON publications(journal_tier);

-- 테이블 코멘트
COMMENT ON TABLE publications IS '논문 목록 - Ecount publication_list.csv';
COMMENT ON COLUMN publications.paper_id IS '논문ID (Primary Key)';
COMMENT ON COLUMN publications.department IS '학과';
COMMENT ON COLUMN publications.journal_tier IS '저널등급 (SCIE/KCI/기타)';
COMMENT ON COLUMN publications.impact_factor IS 'Impact Factor (선택적)';

-- ============================================================================
-- 4. 학과 KPI 테이블 (Department KPIs)
-- ============================================================================

CREATE TABLE IF NOT EXISTS department_kpis (
    -- Primary Key (Auto Increment)
    id SERIAL PRIMARY KEY,

    -- 필수 컬럼
    evaluation_year INTEGER NOT NULL,
    department VARCHAR(100) NOT NULL,
    employment_rate NUMERIC(5,2) NOT NULL,
    tech_transfer_income NUMERIC(10,2) NOT NULL,

    -- 메타데이터
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- 복합 UNIQUE 제약: 동일 년도+학과 중복 방지
    CONSTRAINT uq_department_kpis_year_dept UNIQUE (evaluation_year, department)
);

-- 인덱스: 년도별 정렬 및 필터
CREATE INDEX idx_department_kpis_year
    ON department_kpis(evaluation_year);

-- 인덱스: 학과별 필터링
CREATE INDEX idx_department_kpis_department
    ON department_kpis(department);

-- 복합 UNIQUE 인덱스는 CONSTRAINT에서 자동 생성됨

-- 테이블 코멘트
COMMENT ON TABLE department_kpis IS '학과 KPI 데이터 - Ecount department_kpi.csv';
COMMENT ON COLUMN department_kpis.evaluation_year IS '평가년도 (YYYY)';
COMMENT ON COLUMN department_kpis.department IS '학과';
COMMENT ON COLUMN department_kpis.employment_rate IS '졸업생 취업률 (%)';
COMMENT ON COLUMN department_kpis.tech_transfer_income IS '기술이전 수입액 (억원)';

-- ============================================================================
-- 5. updated_at 자동 업데이트 트리거 함수
-- ============================================================================

-- 공통 트리거 함수 생성
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

CREATE TRIGGER update_students_updated_at
    BEFORE UPDATE ON students
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_publications_updated_at
    BEFORE UPDATE ON publications
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_department_kpis_updated_at
    BEFORE UPDATE ON department_kpis
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- 6. 샘플 데이터 삽입 (개발/테스트용, 선택적)
-- ============================================================================

-- 샘플 연구비 데이터
-- INSERT INTO research_projects (execution_id, department, total_budget, execution_date, execution_amount)
-- VALUES
--     ('EXEC-2024-001', '컴퓨터공학과', 500000000, '2024-01-15', 50000000),
--     ('EXEC-2024-002', '전자공학과', 300000000, '2024-02-20', 30000000);

-- 샘플 학생 데이터
-- INSERT INTO students (student_id, department, grade, program_type, enrollment_status)
-- VALUES
--     ('2024001', '컴퓨터공학과', 3, '학사', '재학'),
--     ('2024002', '전자공학과', 2, '학사', '재학');

-- 샘플 논문 데이터
-- INSERT INTO publications (paper_id, department, journal_tier, impact_factor)
-- VALUES
--     ('PAPER-2024-001', '컴퓨터공학과', 'SCIE', 3.45),
--     ('PAPER-2024-002', '전자공학과', 'KCI', NULL);

-- 샘플 KPI 데이터
-- INSERT INTO department_kpis (evaluation_year, department, employment_rate, tech_transfer_income)
-- VALUES
--     (2023, '컴퓨터공학과', 85.50, 12.30),
--     (2023, '전자공학과', 78.20, 8.50);

-- ============================================================================
-- 7. 마이그레이션 검증 쿼리
-- ============================================================================

-- 테이블 존재 확인
-- SELECT table_name FROM information_schema.tables
-- WHERE table_schema = 'public'
-- AND table_name IN ('research_projects', 'students', 'publications', 'department_kpis');

-- 인덱스 확인
-- SELECT tablename, indexname FROM pg_indexes
-- WHERE schemaname = 'public'
-- AND tablename IN ('research_projects', 'students', 'publications', 'department_kpis');

-- 트리거 확인
-- SELECT trigger_name, event_object_table
-- FROM information_schema.triggers
-- WHERE trigger_schema = 'public';

-- ============================================================================
-- Migration Complete
-- ============================================================================
