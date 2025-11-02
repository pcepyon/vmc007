## 최종 PRD (Product Requirements Document) - CTO 승인 버전

**문서 작성자:** CTO
**작성일:** 2025년 11월 1일
**대상:** 개발팀 (AI Agent)

---

### 1. 제품 개요 (Product Overview)

| 항목 | 내용 |
| :--- | :--- |
| **프로젝트명** | 대학교 사내 핵심 지표 시각화 대시보드 MVP |
| **제품 목표** | Ecount 추출 데이터(연구비 집행, 논문 실적, 학생 현황, 학과 KPI)를 기반으로 대학 내부 핵심 지표를 **직관적인 웹 차트**로 제공하여 의사결정 속도 및 데이터 활용도를 높인다. **(핵심 가치: 신속성, 간결함)** |
| **핵심 기능** | **4가지 핵심 데이터 파일** (연구비, 학생, 논문, KPI) 업로드 (관리자) $\rightarrow$ **Pandas를 활용한 데이터 파싱/정제** (DRF 백엔드) $\rightarrow$ Supabase 저장 $\rightarrow$ React/Recharts 기반 시각화 대시보드 제공. |
| **성공 기준** | **제공된 4가지 데이터셋**을 기반으로 주요 지표를 오류 없이 시각적으로 정확하게 표현한 첫 번째 프로토타입 완성. |
| **기술 스택** | DRF, Pandas, React, Recharts, Supabase, Railway (확정) |

### 2. Stakeholders

| 역할 | 책임 및 관심사 |
| :--- | :--- |
| **CTO** (발신자) | 신속한 개발 iteration, 간결하고 확장성 있는 구조, MVP 완성 및 배포. **(오버엔지니어링 금지)** |
| **경영진** (수신) | 데이터 기반의 신속하고 정확한 의사결정 지원. |
| **개발 팀 리드** (수신) | 오류 없는 핵심 로직(`DRF-Pandas` 연동) 개발 및 일정 준수. |
| **내부 직원** (최종 사용자) | 편리하고 시인성 높은 웹 기반 데이터 확인. |

### 3. 포함 페이지 (Included Pages - MVP Scope & 명확화)

| 페이지명 | 대상 사용자 | 핵심 기능 및 요구사항 (**구체화**) |
| :--- | :--- | :--- |
| **데이터 업로드 페이지** | 관리자 | 4가지 CSV/엑셀 파일 업로드 및 처리 상태 확인 인터페이스. **(MVP 관리자 접근 통제 방식: 하드코딩 API Key 사용)** |
| **메인 대시보드 페이지** | 전 사용자 | **4대 핵심 지표 시각화 제공.** 기간/학과별 필터링 기능. **(필터링 Scope 제한: 드롭다운 기반의 단일/단순 선택만 허용. 복잡한 다중 선택 또는 커스텀 기간 설정은 MVP 제외)** |

#### 3.1. 4대 핵심 지표 최소 시각화 요구사항 (신속성 확보)

| 지표명 | 필수 차트 종류 (Recharts) |
| :--- | :--- |
| **연구비 집행 추이** | **라인 차트** (Line Chart, 시간에 따른 잔액 추이) 및 **지표 카드** (Metric Card, 현재 잔액) |
| **학과별 학생 현황** | **누적 막대 그래프** (Stacked Bar Chart, 학과별/학년/과정별 학생 수 비교) |
| **논문 실적 (Impact Factor)** | **도넛 차트** (Doughnut Chart, 저널 등급별 논문 비율) 및 **단순 지표 카드** (Aggregated Value) |
| **학과 KPI 추이** | **라인 차트** (Line Chart, 취업률 및 기술이전 수입액 추이) |

### 4. 사용자 여정 (User Journey) 및 시스템 로직 (비동기화 지침 추가)

#### 4.1. 관리자 여정 (Admin / Data Ingestion) - **비동기 처리 지침**

| Target User Segment | 페이지 | 액션 / 시스템 로직 (DRF/Pandas) |
| :--- | :--- | :--- |
| **관리자** | 데이터 업로드 페이지 | 1. 4가지 CSV/엑셀 파일 선택 후 업로드 요청. **(최대 파일 크기: $10MB$ 이하로 제한)**<br>2. **[System Logic: DRF View 호출]** 파일 수신 후 즉시 **백그라운드 처리** 요청 응답. **(Non-Blocking UI를 위해 비동기(Async) 처리 필수. Python `threading` 또는 간단한 백그라운드 태스크 구현 지시)**<br>3. **[System Logic: Pandas/excel\_parser.py]** 백그라운드에서 각 파일을 파싱, 정제, 유효성 검증 수행. **(역할 명확화: 오직 Pandas T/F 로직만 담당)**<br>4. **[System Logic: Supabase/repositories.py]** 정제된 데이터를 DB에 Bulk Insert. **(역할 명확화: DB 접근 로직만 담당)** |
| **관리자** | 메인 대시보드 | 최신 데이터가 반영되었는지 시각적으로 검증. |

#### 4.2. 내부 직원 여정 (End User / Viewer)

| Target User Segment | 페이지 | 액션 / 목적 |
| :--- | :--- | :--- |
| **내부 직원** | 메인 대시보드 | 핵심 지표를 확인하여 의사결정에 활용. |

### 5. IA: 정보 구조 시각화 (Information Architecture)

```mermaid
graph TD
    A[Start: 웹 접근] --> C(메인 대시보드 페이지);
    
    subgraph Core Product
    C
    D(데이터 업로드 페이지)
    end
    
    C -->|데이터 확인/필터| C;
    C -->|관리자 기능 접근| D;
    D -->|파일 업로드/처리| C;
    
    style D fill:#f9f,stroke:#333,stroke-width:2px,color:#333
    
    note for D: 관리자 전용 (하드코딩 API Key 사용)
    note for C: 핵심 지표 차트 시각화
```

### 6. Data Ingestion Specification (명확성 및 구체화)

#### 6.1. 데이터 소스 최소 칼럼 명세 (Pandas 로직 개발 선행 조건)

`excel_parser.py` 개발을 위해 아래 **필수 칼럼**을 기준으로 데이터 파싱/정제 로직을 설계해야 합니다. (제시된 CSV 파일 기반)

| 파일명 | 필수 칼럼 (Pandas Column Name) | 데이터 타입 (DRF/Pandas Type) | 용도 |
| :--- | :--- | :--- | :--- |
| `research_project_data.csv` | `집행ID` | String | PK/고유 식별자 |
| | `소속학과` | String | 학과별 필터링/집계 |
| | `총연구비` | Integer/Float | 잔액 계산을 위한 기준 금액 |
| | `집행일자` | Date/DateTime | 시계열 추이 분석 |
| | `집행금액` | Integer/Float | 잔액 계산 |
| `student_roster.csv` | `학번` | String | PK/고유 식별자 |
| | `학과` | String | 학과별 필터링/집계 |
| | `학년` | Integer | 학년별 학생 수 집계 |
| | `과정구분` | String (학사/석사/박사) | 과정별 학생 수 집계 |
| | `학적상태` | String (재학/휴학/졸업) | 현재 학생 현황 집계 |
| `publication_list.csv` | `논문ID` | String | PK/고유 식별자 |
| | `학과` | String | 학과별 필터링/집계 |
| | `저널등급` | String (SCIE, KCI 등) | 논문 성과 비율 분석 |
| | `Impact Factor` | Float (Nullable) | 핵심 성과 지표 계산 |
| `department_kpi.csv` | `평가년도` | Integer | 시계열 추이 분석 |
| | `학과` | String | 학과별 필터링/집계 |
| | `졸업생 취업률 (%)` | Float | KPI 추이 시각화 |
| | `연간 기술이전 수입액 (억원)` | Float | KPI 추이 시각화 |

#### 6.2. 관리자 접근 통제 (오버엔지니어링 회피)

로그인 기능은 MVP에서 제외되었으므로, **'관리자 전용'** 페이지 및 API 접근은 다음과 같이 **간단하게 구현**합니다.

1.  **백엔드 (DRF):** `POST /upload` API에 **하드코딩된 API Key** (`X-Admin-Key`)를 환경 변수로 설정하고, 이 키가 요청 헤더에 포함되었는지 검증하는 **가벼운 인증 미들웨어**를 사용합니다.
2.  **프런트엔드 (React):** `데이터 업로드 페이지`로의 UI 접근은 `if (process.env.ADMIN_MODE === 'true')`와 같이 간단한 환경 변수나, 상기 **하드코딩된 API Key**를 기반으로 한 단순 문자열 인증 (URL 숨김) 방식으로 제한합니다.

**$\rightarrow$ 별도의 DB 기반 User/Auth 시스템 구현은 MVP에서 절대 금지.**