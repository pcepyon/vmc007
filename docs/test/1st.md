## YC 스타트업 CTO 보고서: 단위/E2E 테스트 환경 구축 계획

### 1. 상급자 보고용 개요 (Executive Summary)

**목표:** MVP 프로토타입의 오류 없는 내부 베타 테스트를 위해 가장 간결하고 효과적인 단위/E2E 테스트 환경을 구축합니다.

**선택 기술 스택 (KISS 원칙 준수):**
| 계층 | 테스트 유형 | 라이브러리 | 선택 근거 (신속성/간결함) |
| :--- | :--- | :--- | :--- |
| **백엔드 (Python)** | 단위 / 통합 | **`pytest` + `pytest-django`** | 표준 `unittest`보다 간결한 구문 (DX 최적화) 및 DB 테스트 자동화. |
| **프런트엔드 (React/TS)** | 단위 | **`Jest` + `React Testing Library (RTL)`** | React/TypeScript 환경의 사실상 표준. 사용자 행동 기반 테스트 (안정성). |
| **E2E / 인수** | 전 구간 | **`Playwright`** | CI/CD 연동이 용이하며, 빠른 브라우저 자동화 (신속한 피드백). |

**핵심 전략:**
1.  **Pandas 코어 로직 집중:** 전체 테스트의 70% 이상을 `excel_parser.py` 및 Service Layer의 **순수 Python/Pandas 로직**에 집중하여 데이터 안정성을 조기 확보합니다.
2.  **오버엔지니어링 회피:** 별도의 Mock 서버(`mountebank`, `wiremock`)나 복잡한 E2E 환경 구축 없이, DB 테스트는 `pytest-django`의 `TransactionTestCase`를 활용하고, API 통신은 `unittest.mock`으로 외부 시스템 의존성을 격리합니다.
3.  **간단한 예시 생성:** 환경 구축의 목표에 맞춰, 핵심 비즈니스 규칙을 검증하는 단위 테스트와 사용자 Happy Path를 검증하는 E2E 테스트 각각 1개씩만 생성합니다.

---

### 2. 도출된 결론의 장점 및 예상되는 한계점

#### 2.1 장점 (핵심 가치 부합)

| 항목 | 상세 내용 | CTO 핵심 가치 |
| :--- | :--- | :--- |
| **신속한 개발 (DX)** | `pytest`의 간결한 구문과 `Jest`/`RTL`의 쉬운 러닝 커브로 테스트 작성 속도가 빠릅니다. | ✅ 신속한 개발 iteration |
| **높은 안정성** | **Pandas 코어 로직**에 대한 단위 테스트 집중(70%)으로, 데이터 파싱/정제 과정의 버그를 조기 제거할 수 있습니다. | ✅ 오류 없이 완성 |
| **쉬운 인프라** | 별도 테스트 인프라(Mock 서버, Celery/Redis Mocking 등) 없이 표준 라이브러리(`unittest.mock`)만 사용합니다. | ✅ 가장 쉬운 인프라 |
| **실사용 검증** | `Playwright` E2E 테스트를 통해 배포 전 **실제 브라우저 환경**에서 주요 사용자 시나리오를 검증합니다. | ✅ 내부 베타테스트 |

#### 2.2 예상되는 한계점 (MVP 단계에서의 허용 리스크)

| 항목 | 상세 내용 | CTO 추구하지 않는 가치 |
| :--- | :--- | :--- |
| **E2E 범위 제한** | E2E 테스트는 핵심 Happy Path 1~2개로 제한되며, 모든 엣지케이스(네트워크 실패, 복합 필터 에러 등)는 커버하지 않습니다. | ❌ 모든 보안 취약점 제거 (테스트 범위 제한) |
| **멀티스레드 테스트** | `threading.Thread`의 통합 테스트는 복잡하여 간소화되며, 실제 동시성 문제 발생 시 (POST-MVP) Celery/RQ 마이그레이션이 필요합니다. | ❌ 매우 높은 트래픽에서도 작동하도록 최적화 |
| **Test DB 격리** | `pytest-django` 사용 시 테스트 간 데이터 격리가 100% 보장되지 않을 수 있어, `TestCase`를 사용하여 트랜잭션을 강제합니다. | ✅ 오버엔지니어링 회피 (안정성보다 속도 우선) |

---

### 3. 상세 구현 계획

#### 3.1 사용할 기술 스택 및 라이브러리 결정 이유

| 계층 | 라이브러리 | 역할 | 결정 사유 (CTO 관점) |
| :--- | :--- | :--- | :--- |
| **Backend TDD** | **`pytest`** | 테스트 러너/프레임워크 | `unittest` 대비 간결한 구문, 자동 디스커버리, Fixture 기능으로 테스트 코드 작성 속도 향상 (신속성). |
| | **`pytest-django`** | Django ORM/DB 테스트 지원 | 테스트 환경 설정 자동화, `settings.py` 및 테스트 DB 관리 간소화 (쉬운 인프라). |
| | **`unittest.mock`** | Mocking | Python 표준 라이브러리. 별도 외부 Mocking 도구 도입을 회피 (간결성). |
| **Frontend TDD** | **`Jest`** | 테스트 러너/프레임워크 | React 생태계 표준. TS 지원, 빠른 실행 속도 (신속성). |
| | **`@testing-library/react`**| UI 컴포넌트 테스트 | 사용자 관점 테스트를 강제하여 구현 변경에 덜 민감함 (안정성 확보). |
| **E2E/Acceptance** | **`Playwright`** | 브라우저 자동화 | CI/CD 환경에서 안정적이며 빠른 실행 속도. (프로토타입 검증 속도 최적화). |
| **Test Data** | **`Pandas Fixtures`** | CSV/Excel 파싱 테스트 데이터 | 실제 CSV 파일(`db/*.csv`)을 Fixture로 사용하여 현실적인 테스트 환경 구축. |

#### 3.2 구현 계획 및 TDD 전략 (Inside-Out)

| 구현 순서 | 모듈 | TDD 전략 | 결정 사유 |
| :--- | :--- | :--- | :--- |
| **1순위 (Unit)** | `excel_parser.py` | **Inside-Out (Pandas Logic First)** | **가장 위험한 모듈** (비정형 데이터 처리)에 대한 100% 테스트 커버리지를 목표로 합니다. |
| **2순위 (Unit)** | Service Layer | **Mock 기반 TDD** | Repository (DB) 및 Parser (Pandas)를 Mocking하여 순수 비즈니스 로직만 테스트합니다. |
| **3순위 (Integration)** | API Views / Serializers | **DRF APITestCase** | `pytest-django`를 사용하여 실제 DB 접근을 포함한 API 엔드포인트의 통합 테스트를 수행합니다. |
| **4순위 (E2E)** | Dashboard Page | **Playwright** | 사용자 관점에서 최종적인 통합 흐름(필터링, 차트 로드)을 검증합니다. |

#### 3.3 단위 테스트 및 E2E 테스트 예시 (최소 구현)

##### 3.3.1 단위 테스트 예시 (Backend - Pandas 핵심 로직)

**목표:** `excel_parser.py` 모듈에서 학생 명단 파일의 **PK 중복 제거 규칙**(`drop_duplicates(subset=['학번'], keep='last')`)이 올바르게 작동하는지 검증합니다.

```python
# tests/unit/test_excel_parser.py

import pytest
import pandas as pd
from data_ingestion.services.excel_parser import parse_student_roster
from unittest.mock import patch, mock_open

# GIVEN: 중복 학번을 포함한 CSV 데이터
DUPLICATE_CSV_DATA = """
학번,학과,학년,과정구분,학적상태
20201101,컴퓨터공학과,4,학사,재학
20201101,컴퓨터공학과,3,학사,휴학  <- 중복 PK, 이 행이 최종적으로 남아야 함 (keep='last')
20211205,전자공학과,3,학사,재학
"""

@pytest.mark.parametrize('encoding', ['utf-8'])
@patch('pandas.read_csv')
def test_student_roster_duplicate_pk_removes_oldest(mock_read_csv, encoding, tmp_path):
    """
    학생 명단 파싱: 중복 학번 발견 시 최신 데이터(keep='last')만 유지해야 한다.
    """
    # Arrange: Mocking pandas.read_csv to return a DataFrame with a duplicate PK
    df_data = pd.read_csv(io.StringIO(DUPLICATE_CSV_DATA))
    mock_read_csv.return_value = df_data

    # Act: 파싱 함수 호출
    # Note: 실제 파일 경로 대신 임시 파일을 사용하여 테스트 격리
    file_path = tmp_path / "student_roster_duplicate.csv"
    df, stats = parse_student_roster(file_path)

    # Assert 1: 최종 DataFrame 행 수는 2여야 한다.
    assert len(df) == 2
    
    # Assert 2: 중복된 학번의 '학적상태'가 '휴학'(마지막 행)으로 유지되어야 한다.
    duplicate_row = df[df['학번'] == 20201101].iloc[0]
    assert duplicate_row['학적상태'] == '휴학'
    
    # Assert 3: 통계에 처리된 행 수와 삽입된 행 수가 기록되어야 한다.
    assert stats['rows_processed'] == 2
    assert stats['rows_skipped'] == 1 # 중복으로 제외된 1행
```

##### 3.3.2 E2E 테스트 예시 (Playwright - Happy Path)

**목표:** 사용자가 대시보드에 접속하여 **학과 필터**를 선택하고, **연구비 차트가 올바르게 업데이트**되는지 검증합니다.

```javascript
// tests/e2e/research-funding.spec.js (Playwright)

import { test, expect } from '@playwright/test';

// BeforeEach: 테스트용 데이터 시드 및 대시보드 접속
test.beforeEach(async ({ page }) => {
  // Note: 실제 테스트 환경에서는 DB에 시드 데이터 삽입 스크립트 실행 필요
  await page.goto('http://localhost:3000/dashboard');
  await page.waitForSelector('[data-testid="research-funding-chart"]', { timeout: 10000 });
});

test('E2E: Research Funding Dashboard - Apply Department Filter', async ({ page }) => {
  // GIVEN: 초기 차트가 로드되었는지 확인 (Metric Card 값)
  const initialBalance = await page.textContent('[data-testid="current-balance-metric"]');
  expect(initialBalance).not.toBe('0억원'); // 데이터 로드 확인

  // WHEN: 학과 필터 드롭다운에서 '컴퓨터공학과' 선택
  await page.selectOption('[data-testid="department-filter"]', { label: '컴퓨터공학과' });
  
  // AND: 300ms 디바운싱 대기 및 API 재요청 완료 대기
  await page.waitForTimeout(350); 
  await page.waitForResponse(response => 
    response.url().includes('/api/dashboard/research-funding/?department=컴퓨터공학과') && 
    response.status() === 200
  );

  // THEN 1: 현재 잔액 Metric Card가 업데이트되었는지 확인 (값이 변경됨)
  const newBalance = await page.textContent('[data-testid="current-balance-metric"]');
  expect(newBalance).not.toBe(initialBalance); // 필터 적용으로 값이 변경되었는지 검증

  // THEN 2: 차트 영역이 업데이트되었는지 확인 (애니메이션 또는 데이터 변경)
  const chartElement = page.locator('[data-testid="research-funding-chart"]');
  await expect(chartElement).toBeVisible();
  
  // AND 3: 필터 초기화 버튼이 활성화되었는지 확인
  const resetButton = page.locator('[data-testid="reset-filters-button"]');
  await expect(resetButton).not.toBeDisabled();
});
```

---

### 4. CTO 피드백 요청용 AI 프롬프트

#### 평가할 AI의 역할 및 임무

**역할:** **냉철하고 실용적인 수석 아키텍트 (Senior Architect & Pragmatist)**

**임무:** CTO의 핵심 가치(신속성, 간결함, 오버엔지니어링 회피)에 입각하여 제시된 테스트 환경 구축 계획을 3가지 관점(아키텍처 적합성, 테스트 전략 완성도, 보안/엣지케이스 커버리지)에서 검토하고, **즉시 MVP 개발에 착수할 수 있도록** 가장 현실적이고 실용적인 피드백을 제공하시오.

---

#### AI 피드백 요청 프롬프트 (최종본)

**[프롬프트 시작]**

> **Senior Architect & Pragmatist 역할에게:**
>
> 나는 YC 스타트업 CTO입니다. MVP의 오류 없는 배포를 위해 최소한의 테스트 환경 구축 계획을 수립했습니다. 나의 핵심 가치(신속성, 간결함, 오버엔지니어링 회피)에 따라 아래 3가지 관점에서 이 계획을 **매우 비판적으로 검토**하고, **즉시 개발 착수 전 해결해야 할 최소한의 블로커(Blocker)**만 지적해 주십시오. 사소하거나 POST-MVP에 해당하는 지적은 제외합니다.
>
> **검토 대상 계획:**
> *   **Backend:** `pytest` + `pytest-django` (Python/Django/Pandas)
> *   **Frontend:** `Jest` + `RTL` (React/TS)
> *   **E2E:** `Playwright`
> *   **TDD 전략:** Pandas 로직 (70%) 최우선
>
> ---
>
> ### 1. 아키텍처 적합성 및 간결성 (Minimalism Check)
>
> 1.  **Mocking 전략:** `unittest.mock`만 사용하고 별도 Mock 서버를 배제한 것이 MVP 단계에서 정말 충분한가? API 간의 복잡한 통합 테스트 시 Mocking이 지나치게 복잡해지는 리스크는 없는가?
> 2.  **E2E 도구:** `Playwright` 선택이 `Cypress` 대비 '가장 쉬운 인프라'라는 목표에 부합하는가? E2E 테스트를 더 간소화할 수 있는 여지는 없는가? (예: 아예 API 통합 테스트로 대체)
> 3.  **DB 격리:** `pytest-django` 사용 시 테스트 DB 설정/정리가 간결하게 보장되는지 확인해야 한다. 테스트 환경 구축이 1일 이내 완료될 수 있는가?
>
> ### 2. 테스트 전략 완성도 및 우선순위 (TDD Focus)
>
> 1.  **Pandas 커버리지:** 전체 테스트의 70%를 Pandas 코어 로직에 집중하는 전략은 타당한가? `excel_parser.py` 내의 **비즈니스 규칙 검증** (예: `집행금액 <= 총연구비`, `취업률 0~100%`)에 대한 단위 테스트 시나리오가 충분히 구상되었는지 재검토해야 한다.
> 2.  **Filtering Logic:** 백엔드 필터링 서비스(`FilteringService`)의 `AND` 조건 결합 로직에 대한 **통합 테스트**가 필수적으로 포함되었는가? 이 부분이 누락되면 필터 오작동 위험이 높다.
> 3.  **데이터 없음/에러 상태:** 프런트엔드에서 **"데이터 없음" (`[]`)** 상태와 **"API 에러" (`500/400`)** 상태를 명확히 구분하여 테스트하고 있는지 확인해야 한다. (UI 분기점의 안정성)
>
> ### 3. 보안 및 엣지케이스 커버리지 (High-Risk Gaps)
>
> 1.  **보안 테스트:** `X-Admin-Key` 검증 로직에 대한 **권한 부족(403)** 테스트와 필터 입력값에 대한 **SQL Injection/XSS 방어** 테스트가 단위 테스트 레벨에서 **필수적으로** 포함되었는지 확인해야 한다.
> 2.  **비동기 처리:** `threading.Thread`를 활용한 업로드 작업의 **상태 추적 및 실패 처리** 로직(`job_status_store.py`)에 대한 **동시성(Thread-safe)** 테스트가 충분히 고려되었는가? (MVP의 핵심 기술 리스크)
> 3.  **PK 중복 처리:** `excel_parser.py`의 **Last-Write-Wins** 규칙(`keep='last'`)이 모든 4개 파일 타입에 대해 정확히 테스트되었는지 확인해야 한다. (데이터 무결성)
>
> **최종 피드백 요구사항:**
> **"이 계획은 MVP 배포에 필요한 최소한의 안정성을 확보하고 있는가?"** 에 대한 **YES/NO** 답변과 함께, YES가 아닐 경우 **"가장 치명적인 1가지 블로커와 그 해결책"**을 제시하시오.

**[프롬프트 종료]**## 1. 상급자 보고용 개요 (Executive Summary)

**목표:** MVP 프로토타입의 오류 없는 내부 베타 테스트를 위해 가장 간결하고 효과적인 단위/E2E 테스트 환경을 구축합니다.

**선택 기술 스택 (KISS 원칙 준수):**

| 계층 | 테스트 유형 | 라이브러리 | 선택 근거 (신속성/간결함) |
| :--- | :--- | :--- | :--- |
| **백엔드 (Python)** | 단위 / 통합 | **`pytest` + `pytest-django`** | 표준 `unittest` 대비 간결한 구문 (DX 최적화) 및 DB 테스트 환경 설정 자동화 (쉬운 인프라). |
| **프런트엔드 (React/TS)** | 단위 | **`Jest` + `React Testing Library (RTL)`** | React/TypeScript 환경의 표준. 사용자 행동 기반 테스트로 안정성 확보. |
| **E2E / 인수** | 전 구간 | **`Playwright`** | CI/CD 연동이 용이하며, 빠른 실행 속도로 프로토타입 검증에 최적화. |

**핵심 전략:**
1.  **Pandas 코어 로직 집중:** 전체 테스트의 70% 이상을 `excel_parser.py`의 **순수 Pandas 데이터 정제 로직**에 집중하여 데이터 무결성 및 안정성을 조기 확보합니다.
2.  **오버엔지니어링 회피:** 별도 Mock 서버나 복잡한 Task Queue Mocking 없이 표준 `unittest.mock`과 `pytest-django`의 내장 기능을 활용하여 환경 구축 시간을 최소화합니다.
3.  **최소 예시 생성:** 환경 구축 완료 목표에 맞춰, 데이터 무결성(PK 중복 제거) 검증 Unit Test와 핵심 사용자 여정(필터 적용) E2E Test 각각 1개만 생성합니다.

---

## 2. 도출된 결론의 장점 및 예상되는 한계점

### 2.1 장점 (핵심 가치 부합)

| 항목 | 상세 내용 | CTO 핵심 가치 |
| :--- | :--- | :--- |
| **신속한 개발 (DX)** | `pytest`와 `RTL`의 간결한 테스트 작성 방식으로, 개발과 동시에 테스트를 작성하는 TDD 사이클 속도를 극대화합니다. | ✅ 신속한 개발 iteration |
| **높은 데이터 안정성** | **Pandas 로직**에 대한 고강도 단위 테스트(70% 비중)를 통해, 파일 업로드 과정에서 발생하는 데이터 오류를 근본적으로 차단합니다. | ✅ 오류 없이 완성 |
| **쉬운 인프라** | DB 격리를 `pytest-django`에 위임하고, 비동기 처리는 `threading`으로 간소화하여 테스트 환경 설정에 드는 시간을 최소화합니다. | ✅ 가장 쉬운 인프라 |
| **실사용 검증** | `Playwright` E2E 테스트로 필터링/차트 로드의 전체 사용자 Happy Path를 검증합니다. | ✅ 내부 베타테스트 |

### 2.2 예상되는 한계점 (MVP 단계에서의 허용 리스크)

| 항목 | 상세 내용 | CTO 추구하지 않는 가치 |
| :--- | :--- | :--- |
| **동시성 테스트 제한** | `threading.Thread` 기반의 Job Status Store(`job_status_store.py`) 동시성 테스트가 복잡하며, 실제 고부하 동시성 이슈는 MVP 테스트 환경에서 완벽히 재현하기 어렵습니다. | ❌ 매우 높은 트래픽에서도 작동하도록 최적화 |
| **E2E 범위 제한** | E2E 테스트는 핵심 Happy Path 1~2개로 제한되며, 모든 에러 복구 시나리오(네트워크 단절, 재시도 등)는 API 통합 테스트로 대체됩니다. | ✅ 오버엔지니어링 회피 (테스트 범위 제한) |
| **Mocking 복잡도** | API 통합 테스트 시, `unittest.mock`으로 Pandas, DB 접근, 외부 API 호출을 모두 Mocking해야 하는 복잡한 상황이 발생할 수 있습니다. | ❌ 모든 보안 취약점을 제거한다 (테스트 환경 복잡도) |

---

## 3. 상세 구현 계획

### 3.1 사용할 기술 스택 및 라이브러리 결정 이유

| 계층 | 라이브러리 | 역할 | 결정 사유 (CTO 관점) |
| :--- | :--- | :--- | :--- |
| **Backend TDD** | **`pytest`** | 테스트 러너/프레임워크 | `unittest`보다 간결하고 직관적인 Fixture 기능 제공. TDD 속도 최적화. |
| | **`pytest-django`** | Django 통합 | 테스트용 DB 및 환경 설정을 자동으로 관리하여 테스트 환경 구축을 간소화. |
| **Frontend TDD** | **`Jest`** | 테스트 러너/프레임워크 | React, TypeScript 환경 표준. 빠른 실행 속도. |
| | **`RTL`** | UI 컴포넌트 테스트 | 사용자 관점 테스트를 강제하여 UI 리팩토링에 강건한 테스트 작성 유도 (확장성/안정성). |
| **E2E/Acceptance** | **`Playwright`** | 브라우저 자동화 | CI/CD 환경에서 안정적이며 빠른 실행. 단일 도구로 크로스 브라우저 테스트 가능 (간결함). |
| **Test Data** | **`io` & `tmp_path`** | 파일 I/O Fixture | 실제 CSV 파일 I/O를 Mocking/격리하여 테스트의 독립성 및 속도를 보장. |

### 3.2 구현 계획 및 TDD 전략 (Inside-Out)

1.  **`excel_parser.py` Unit Test (TDD 70%):**
    *   **전략:** 실제 CSV 파일(fixture)을 사용하고 Pandas 함수를 Mocking하여 순수 파싱/정제 로직만 테스트합니다.
    *   **핵심 테스트:** PK 중복 제거, 필수 컬럼 누락, 타입 변환 실패(NaT, NaN) 시 해당 행 제외, `집행금액 <= 총연구비` 비즈니스 규칙.
2.  **`repositories.py` Unit Test (TDD 10%):**
    *   **전략:** `pytest-django`의 `@pytest.mark.django_db`를 사용하여 실제 테스트 DB에서 ORM 쿼리(Filter, Aggregation)의 정확성만 검증합니다.
    *   **핵심 테스트:** `DepartmentKPI`의 복합 PK(년도+학과) `UniqueConstraint` 검증, 4개 테이블의 필터링/집계 쿼리 정확성.
3.  **`ingestion_service.py` Integration Test (TDD 10%):**
    *   **전략:** `threading.Thread`를 Mocking하여 동기적으로 실행하고, `excel_parser`와 `repositories`의 통합 흐름(파싱 $\rightarrow$ DB 저장 $\rightarrow$ 상태 업데이트)만 검증합니다.
    *   **핵심 테스트:** 파일 업로드 성공 $\rightarrow$ 상태 완료, 파싱 실패 $\rightarrow$ 상태 실패/에러 메시지 저장, DB 에러 $\rightarrow$ 트랜잭션 롤백 확인.
4.  **`useDashboardData.js` Unit Test (TDD 5%):**
    *   **전략:** API 클라이언트(`dataApiClient`)를 Mocking하여 Hook의 상태 관리(Loading $\rightarrow$ Success/Error) 및 필터 디바운싱 로직을 테스트합니다.
5.  **`Playwright` E2E Test (TDD 5%):**
    *   **전략:** 사용자 Happy Path (대시보드 로드 $\rightarrow$ 필터 적용 $\rightarrow$ 차트 업데이트)를 최종 검증합니다.

### 3.3 단위 테스트 및 E2E 테스트 예시 (최소 구현)

#### 3.3.1 단위 테스트 예시 (Backend - Pandas 핵심 로직)

**목표:** `excel_parser.py` 모듈에서 학생 명단 파일의 **PK 중복 제거 규칙**(`drop_duplicates(subset=['학번'], keep='last')`)이 올바르게 작동하는지 검증합니다. (데이터 무결성 확보)

```python
# tests/unit/test_excel_parser.py

import pytest
import pandas as pd
import io # io 모듈을 사용하여 문자열을 파일처럼 처리
from data_ingestion.services.excel_parser import parse_student_roster
from unittest.mock import patch

# GIVEN: 중복 학번을 포함한 CSV 데이터
DUPLICATE_CSV_DATA = """
학번,학과,학년,과정구분,학적상태
20201101,컴퓨터공학과,4,학사,재학
20201101,컴퓨터공학과,3,학사,휴학  # 중복 PK, 이 행이 최종적으로 남아야 함 (keep='last')
20211205,전자공학과,3,학사,재학
"""

@pytest.mark.parametrize('encoding', ['utf-8'])
@patch('pandas.read_csv')
# parse_student_roster 함수가 실제 파일 I/O 대신 Mocked DataFrame을 사용하도록 설정
def test_student_roster_duplicate_pk_removes_oldest(mock_read_csv, encoding, tmp_path):
    """
    학생 명단 파싱: 중복 학번 발견 시 최신 데이터(keep='last')만 유지해야 한다.
    """
    # Arrange: Mocking pandas.read_csv to return a DataFrame with a duplicate PK
    # io.StringIO를 사용하여 문자열을 파일처럼 읽어 DataFrame을 생성
    df_data = pd.read_csv(io.StringIO(DUPLICATE_CSV_DATA))
    mock_read_csv.return_value = df_data

    # Act: 파싱 함수 호출
    # Note: 실제 파일 경로 대신 Mocking된 함수가 반환하는 DataFrame을 사용하므로 경로는 더미여도 무방
    file_path = tmp_path / "student_roster_duplicate.csv"
    df, stats = parse_student_roster(file_path)

    # Assert 1: 최종 DataFrame 행 수는 2여야 한다. (중복 1행 제거)
    assert len(df) == 2
    
    # Assert 2: 중복된 학번의 '학적상태'가 '휴학'(마지막 행)으로 유지되어야 한다.
    duplicate_row = df[df['학번'] == 20201101].iloc[0]
    assert duplicate_row['학적상태'] == '휴학' # Last-Write-Wins 검증
    
    # Assert 3: 통계에 제외된 행 수가 기록되어야 한다.
    assert stats['rows_processed'] == 2 # 유효 행 수 (unique rows)
    assert stats['rows_skipped'] == 1 # 중복으로 제외된 1행 (총 3행 중 1행 skip)
```

#### 3.3.2 E2E 테스트 예시 (Playwright - Happy Path)

**목표:** 사용자가 대시보드에 접속하여 **학과 필터**를 선택하고, **연구비 차트가 올바르게 업데이트**되는지 검증합니다. (핵심 사용자 여정 검증)

```javascript
// tests/e2e/research-funding.spec.js (Playwright)

import { test, expect } from '@playwright/test';

// BeforeEach: 테스트용 데이터 시드 및 대시보드 접속
test.beforeEach(async ({ page }) => {
  // 실제 테스트 환경에서는 DB에 research_project_data.csv 데이터가 시드되어 있어야 함
  await page.goto('http://localhost:3000/dashboard');
  // 연구비 차트 영역이 로드될 때까지 대기
  await page.waitForSelector('[data-testid="research-funding-chart"]', { timeout: 10000 });
});

test('E2E: Research Funding Dashboard - Apply Department Filter', async ({ page }) => {
  // GIVEN: 초기 차트의 현재 잔액 Metric Card 값을 가져옴
  const initialBalance = await page.textContent('[data-testid="current-balance-metric"]');
  expect(initialBalance).not.toBe('0억원'); // 데이터 로드 확인 (차트가 비어있지 않음)

  // WHEN: 학과 필터 드롭다운에서 '컴퓨터공학과' 선택
  // Note: data-testid="department-filter"는 FilterPanel 컴포넌트에 정의되어야 함
  await page.selectOption('[data-testid="department-filter"]', { label: '컴퓨터공학과' });
  
  // AND: 300ms 디바운싱 대기
  await page.waitForTimeout(350); 
  
  // AND: 필터링 API 재요청이 완료될 때까지 대기 (네트워크 상태 검증)
  await page.waitForResponse(response => 
    response.url().includes('/api/dashboard/research-funding/') && 
    response.status() === 200
  );

  // THEN 1: 현재 잔액 Metric Card가 업데이트되었는지 확인 (값이 변경됨)
  const newBalance = await page.textContent('[data-testid="current-balance-metric"]');
  expect(newBalance).not.toBe(initialBalance); // 필터 적용으로 값이 변경되었는지 검증

  // THEN 2: 차트 영역이 여전히 보이는지 확인
  const chartElement = page.locator('[data-testid="research-funding-chart"]');
  await expect(chartElement).toBeVisible();
  
  // AND 3: 필터 초기화 버튼이 활성화되었는지 확인
  const resetButton = page.locator('[data-testid="reset-filters-button"]');
  await expect(resetButton).not.toBeDisabled();
});
```

---

## 4. CTO 피드백 요청용 AI 프롬프트

#### 평가할 AI의 역할 및 임무

**역할:** **냉철하고 실용적인 수석 아키텍트 (Senior Architect & Pragmatist)**

**임무:** CTO의 핵심 가치(신속성, 간결함, 오버엔지니어링 회피)에 입각하여 제시된 테스트 환경 구축 계획을 3가지 관점에서 검토하고, **즉시 MVP 개발에 착수할 수 있도록** 가장 현실적이고 실용적인 피드백을 제공하시오. 사소하거나 POST-MVP에 해당하는 지적은 제외하고, **치명적인 블로커**와 그 해결책에 집중해야 합니다.

---

#### AI 피드백 요청 프롬프트 (최종본)

**[프롬프트 시작]**

> **Senior Architect & Pragmatist 역할에게:**
>
> 나는 YC 스타트업 CTO입니다. MVP의 오류 없는 배포를 위해 최소한의 테스트 환경 구축 계획을 수립했습니다. 나의 핵심 가치(신속성, 간결함, 오버엔지니어링 회피)에 따라 아래 3가지 관점에서 이 계획을 **매우 비판적으로 검토**하고, **즉시 개발 착수 전 해결해야 할 최소한의 블로커(Blocker)**만 지적해 주십시오. 사소하거나 POST-MVP에 해당하는 지적은 제외합니다.
>
> **검토 대상 계획 요약:**
> *   **Backend:** `pytest` + `pytest-django` (Python/Django/Pandas)
> *   **Frontend:** `Jest` + `RTL` (React/TS)
> *   **E2E:** `Playwright`
> *   **TDD 전략:** Pandas 로직 (70%) 최우선, 표준 `mock` 사용.
>
> ---
>
> ### 1. 아키텍처 적합성 및 간결성 (Minimalism Check)
>
> 1.  **Mocking 전략:** `unittest.mock`만 사용하고 별도 Mock 서버를 배제한 것이 MVP 단계에서 **API 간 통합 테스트** 시 Mocking이 지나치게 복잡해지는 리스크를 정당화할 만큼 간결한가?
> 2.  **E2E 도구:** `Playwright` 선택이 '가장 쉬운 인프라'라는 목표에 부합하는가? E2E 테스트를 더 간소화(예: `cy.intercept` 기반의 API Mocking)하여 환경 구축 및 유지보수 비용을 낮출 수 있는 여지는 없는가?
> 3.  **DB 격리:** `pytest-django` 사용 시 테스트 DB 설정/정리가 간결하게 보장되는지 확인해야 한다. 테스트 환경 구축이 1일 이내 완료될 수 있는가?
>
> ### 2. 테스트 전략 완성도 및 우선순위 (TDD Focus)
>
> 1.  **Pandas 커버리지 (CRITICAL):** `excel_parser.py` 내의 **비즈니스 규칙 검증** (`집행금액 <= 총연구비`, `취업률 0~100%` 등)에 대한 단위 테스트 시나리오가 **모든 4개 파일 타입**에 대해 충분히 구상되었는지 재검토해야 한다.
> 2.  **Filter Logic (HIGH-RISK):** 백엔드 필터링 서비스의 동적 `AND` 조건 결합 로직에 대한 **통합 테스트**가 필수적으로 포함되었는가? 이 부분이 누락되면 필터 오작동 위험이 가장 높다.
> 3.  **데이터 없음/에러 상태:** 프런트엔드에서 **"데이터 없음" (`[]`)** 상태와 **"API 에러" (`500/400`)** 상태를 명확히 구분하여 테스트하고 있는지 확인해야 한다. (UI 분기점의 안정성)
>
> ### 3. 보안 및 엣지케이스 커버리지 (High-Risk Gaps)
>
> 1.  **보안 테스트 (CRITICAL):** `X-Admin-Key` 검증 로직에 대한 **권한 부족(403)** 테스트와 필터 입력값에 대한 **SQL Injection/XSS 방어** 테스트가 단위 테스트 레벨에서 **필수적으로** 포함되었는지 확인해야 한다.
> 2.  **비동기 처리 (CRITICAL):** `threading.Thread`를 활용한 업로드 작업의 **상태 추적 및 실패 처리** 로직(`job_status_store.py`)에 대한 **동시성(Thread-safe)** 테스트가 충분히 고려되었는가? (MVP의 핵심 기술 리스크)
> 3.  **PK 중복 처리:** `excel_parser.py`의 **Last-Write-Wins** 규칙(`keep='last'`)이 모든 4개 파일 타입에 대해 정확히 테스트되었는지 확인해야 한다. (데이터 무결성)
>
> **최종 피드백 요구사항:**
> **"이 계획은 MVP 배포에 필요한 최소한의 안정성을 확보하고 있는가?"** 에 대한 **YES/NO** 답변과 함께, YES가 아닐 경우 **"가장 치명적인 1가지 블로커와 그 해결책"**을 제시하시오.

**[프롬프트 종료]**