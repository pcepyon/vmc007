## 🚀 MVP 1.0 GO-LIVE MANDATE: MINIMALIST TDD IMPLEMENTATION

**TO:** AI Coding Agent
**FROM:** CTO (Senior Architect)
**DATE:** 2025-11-02
**PRIORITY:** P0 - Critical Blockers First

---

### I. 🎯 핵심 철학 (CTO Mandate)

| 항목 | 지침 | 회피 사항 (오버엔지니어링 금지) |
| :--- | :--- | :--- |
| **속도** | **Test First, Small Steps, Red-Green-Refactor 엄격 준수.** | 복잡한 Task Queue (Celery, RQ, Redis) 도입 금지. |
| **간결함** | `unittest.mock`을 사용하여 모든 외부/API 의존성 격리. | 별도의 Mock 서버 (Mountebank, Wiremock) 구축 금지. |
| **인프라** | `pytest-django`의 기본 기능을 최대한 활용하여 환경 구축 최소화. | DB 기반 Auth 시스템 구축 금지 (하드코딩 API Key 사용). |
| **안정성** | **P0 Blocker 해소 전, 어떤 기능 개발도 금지.** | |

---

### II. 🛠️ 확정 기술 스택 및 환경 구축 계획

| 계층 | 테스트 유형 | 라이브러리/도구 | 역할 및 선택 근거 |
| :--- | :--- | :--- | :--- |
| **Backend Core** | 단위/통합 | `pytest` + `pytest-django` | Python 표준, 간결한 구문, 자동 DB 테스트 환경 제공. |
| **Mocking** | 단위 | `unittest.mock` | Python 표준 라이브러리, 외부 의존성(API 통신, DB 접근) 완벽 격리. |
| **Frontend** | 단위 | `Jest` + `RTL` | React/TS 표준, 사용자 행동 기반 컴포넌트 테스트. |
| **E2E** | 인수 | `Playwright` | CI/CD 친화적, 빠른 브라우저 자동화 (Cross-Browser 지원). |
| **데이터** | 검증 | `Pandas` | MVP의 핵심 비즈니스 로직(데이터 정제, 유효성 검사) 검증. |

---

### III. 🚨 P0 CRITICAL BLOCKER: 동시성 결함 해소 (즉시 착수)

**블로커:** 메모리 기반 `job_status_store.py`의 Thread-Safe 보장 부재.

**최우선 조치사항:**

1.  **구현:** `backend/data_ingestion/infrastructure/job_status_store.py` 파일 내 모든 상태 접근/변경 로직에 **`threading.Lock()`**을 적용하여 동시성 이슈를 해결합니다.
2.  **증명 (P0 단위 테스트):** `job_status_store.py`에 대해 최소 1개의 **멀티스레드 동시성 테스트**를 작성하고 통과시켜 `threading.Lock`의 정확한 작동을 **증명**해야 합니다.

| 테스트 대상 | 테스트 시나리오 (최소) | 기대 결과 |
| :--- | :--- | :--- |
| `job_status_store.py` | 10개 이상의 스레드가 동시에 `job_id`의 상태 변수를 덮어쓰거나 카운팅을 수행. | 최종 카운트 값이 정확히 10 (또는 예상되는 최종 값)과 일치해야 합니다. |

---

### IV. 📐 TDD 구현 전략 및 순서 (Blocker 해소 후)

**전략:** **Inside-Out (핵심 로직 우선)** 및 **TDD 원칙**에 따라 구현합니다.

| 순서 | 대상 계층 | 핵심 책임 및 TDD 지침 | 테스트 비율 |
| :--- | :--- | :--- | :--- |
| **1순위** | **Core Logic (Pandas)** | `excel_parser.py` (Pandas 로직): **70% 이상의 커버리지 달성.** 모든 비즈니스 규칙(집행금액 $\le$ 총연구비, 취업률 0%~100%, PK 중복 처리)을 단위 테스트로 증명. | **70% (Unit)** |
| **2순위** | Service/Repo | `repositories.py` (DB 접근), `filtering_service.py` (AND 조건 결합): Mock 기반으로 비즈니스 로직 및 쿼리 필터링 검증. | **15% (Unit)** |
| **3순위** | **Presentation/API** | View (Thin Controller) 및 Serializer: **X-Admin-Key(403)** 및 **필터 입력값(400)** 검증 통합 테스트. 표준 에러 응답 포맷 준수 확인. | **10% (Integration)** |
| **4순위** | Frontend Hooks | `useDashboardData.js`, `useDashboardFilter.js`: API 호출 및 300ms 디바운싱 로직 검증. | **4% (Unit)** |
| **5순위** | E2E | `Playwright` 테스트: **핵심 사용자 Happy Path** 및 **Empty/Error State** 검증 (API Mocking 적극 활용). | **1% (E2E)** |

---

### V. ✅ 최종 완료 기준 (Definition of Done)

1.  **Blocker 해소:** `job_status_store.py`의 동시성 테스트가 **통과(Green)** 되었음.
2.  **Core Logic:** `excel_parser.py`의 코드 커버리지가 **90% 이상**이며, 모든 비즈니스 규칙 테스트 통과.
3.  **안정성:** 모든 단위/통합/E2E 테스트가 **Green** 상태이며, CI/CD 파이프라인(가정)에서 통과됨.
4.  **보안 최소화:** `X-Admin-Key` 검증 로직 및 **필터 입력값에 대한 SQLi/XSS 방어 테스트**가 단위 테스트 레벨에서 통과됨.
5.  **프론트엔드:** E2E 테스트에서 **필터 적용** 및 **Empty/Error State UI 분기점**이 정확히 작동함을 증명함.
6.  **기술 부채 최소화:** 코드베이스에 `TODO: POST-MVP` 이외의 `FIXME` 또는 `CRITICAL` 주석이 남아있지 않음.