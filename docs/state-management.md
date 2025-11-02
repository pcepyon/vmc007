# React 상태관리 설계 문서 (MVP)

**프로젝트:** 대학교 데이터 시각화 대시보드 MVP
**버전:** 2.0 (간결화 및 수정)
**작성일:** 2025-11-02

---

## 핵심 원칙

- **YAGNI**: 당장 필요하지 않은 상태 제외
- **Separation of Concerns**: 상태 관리와 UI 로직 분리
- **Testability**: 순수 함수 기반 reducer
- **KISS**: Context API + useReducer만 사용 (Redux 배제)

---

## 1. State 구조

### 1.1 Domain State (서버 데이터)

#### 연구비 집행 데이터
```typescript
researchFundingData: {
  current_balance: number
  year_over_year_change: number
  year_over_year_percentage: number
  trend: Array<{
    month: string        // 'YYYY-MM'
    balance: number
    execution: number
  }>
  last_updated: string   // ISO 8601
}
```

#### 학생 현황 데이터
```typescript
studentData: {
  total_students: number
  by_department: Array<{
    department: string
    학사: number
    석사: number
    박사: number
    total: number
  }>
  updated_at: string
}
```

#### 논문 실적 데이터
```typescript
publicationData: {
  total_papers: number
  avg_impact_factor: number | null
  papers_with_if: number
  distribution: Array<{
    journal_tier: 'SCIE' | 'KCI' | '기타'
    count: number
    percentage: number
    avg_if: number | null
  }>
  last_updated: string
}
```

#### 학과 KPI 데이터
```typescript
// NOTE: 필터링된 학과들의 집계 데이터
departmentKpiData: {
  trend: Array<{
    evaluation_year: number
    avg_employment_rate: number     // 필터링된 학과들의 평균 취업률
    total_tech_income: number       // 필터링된 학과들의 기술이전 수입 합계
  }>
  overall_avg_employment_rate: number | null  // 전체 기간 평균 취업률
  overall_total_tech_income: number | null    // 전체 기간 기술이전 수입 합계
  total_count: number                         // 집계에 포함된 데이터 포인트 수
}
```

**중요**: 백엔드는 CSV 컬럼명을 반드시 정규화해야 함 (공백 제거, 특수문자 통일)

---

### 1.2 UI State

#### Loading State
```typescript
loadingState: {
  researchFunding: 'idle' | 'loading' | 'success' | 'error'
  students: 'idle' | 'loading' | 'success' | 'error'
  publications: 'idle' | 'loading' | 'success' | 'error'
  departmentKpi: 'idle' | 'loading' | 'success' | 'error'
  filterOptions: 'idle' | 'loading' | 'success' | 'error'
}
```

#### Error State
```typescript
errorState: {
  researchFunding: Error | null
  students: Error | null
  publications: Error | null
  departmentKpi: Error | null
  filterOptions: Error | null
}
```

---

### 1.3 Filter State

#### 필터 선택 상태
```typescript
filters: {
  department: string      // 기본: 'all'
  year: string            // 기본: 'latest'
  period: string          // 기본: '1y' (옵션: '1y' | '3y')
  studentStatus: string   // 기본: 'all' (옵션: 'all' | '재학' | '졸업' | '휴학')
  journalTier: string     // 기본: 'all' (옵션: 'all' | 'SCIE' | 'KCI')
}
```

#### 필터 옵션 (API에서 동적 로드)
```typescript
filterOptions: {
  departments: string[]   // API에서 로드 (예: ['전체', '컴퓨터공학과', ...])
  years: string[]         // API에서 로드 (예: ['최근 1년', '2024년', ...])
  periods: string[]       // API에서 로드 (예: ['1y', '3y'])
}
```

**고정 상수** (프론트엔드에서 관리):
```typescript
// constants/filters.ts
export const STUDENT_STATUSES = ['all', '재학', '졸업', '휴학'] as const;
export const JOURNAL_TIERS = ['all', 'SCIE', 'KCI'] as const;
```

---

### 1.4 필터 적용 규칙

| 필터 | 연구비 | 학생 | 논문 | KPI |
|------|--------|------|------|-----|
| department | ✓ | ✓ | ✓ | ✓ |
| year | ✓ | ✓ | ✓ | ✓ |
| period | ✓ | ✗ | ✗ | ✓ |
| studentStatus | ✗ | ✓ | ✗ | ✗ |
| journalTier | ✗ | ✗ | ✓ | ✗ |

---

### 1.5 Derived State (계산, Context에 저장 안 함)

```typescript
// 예시: 필터링된 학생 데이터
const filteredStudentData = useMemo(() => {
  if (filters.department === 'all') return studentData.by_department;
  return studentData.by_department.filter(d => d.department === filters.department);
}, [studentData, filters.department]);
```

---

## 2. State Transitions (핵심만)

### 데이터 로딩
| Current | Action | Next | UI |
|---------|--------|------|-----|
| `idle` | `FETCH_REQUEST` | `loading` | 스켈레톤 UI |
| `loading` | `FETCH_SUCCESS` | `success` + data | 차트 표시 |
| `loading` | `FETCH_FAILURE` | `error` + error | 에러 카드 |

### 필터링
| Current | Action | Next | UI |
|---------|--------|------|-----|
| `{department: 'all'}` | `FILTER_UPDATE` | `{department: '컴퓨터공학과'}` | 디바운싱(300ms) 후 API 재호출 |
| `{...}` | `FILTER_RESET` | 기본값 | 전체 데이터 재로드 |

---

## 3. Context 구조

### MVP 범위
- **DashboardContext** (필수): 대시보드 전체 상태 관리
- **UploadContext** (선택): 관리자 업로드 상태 (별도 구현)
- **AuthContext, ThemeContext** (POST-MVP): 제외

### Provider 위치
```
<App>
  <DashboardProvider>
    <DashboardPage />
  </DashboardProvider>
</App>
```

---

## 4. TypeScript 타입 정의

### 4.1 Domain Types
```typescript
// types/domain.ts

export interface ResearchFundingData {
  current_balance: number;
  year_over_year_change: number;
  year_over_year_percentage: number;
  trend: ResearchFundingTrendItem[];
  last_updated: string;
}

export interface ResearchFundingTrendItem {
  month: string;
  balance: number;
  execution: number;
}

export interface StudentData {
  total_students: number;
  by_department: StudentDepartmentItem[];
  updated_at: string;
}

export interface StudentDepartmentItem {
  department: string;
  학사: number;
  석사: number;
  박사: number;
  total: number;
}

export interface PublicationData {
  total_papers: number;
  avg_impact_factor: number | null;
  papers_with_if: number;
  distribution: PublicationDistributionItem[];
  last_updated: string;
}

export interface PublicationDistributionItem {
  journal_tier: 'SCIE' | 'KCI' | '기타';
  count: number;
  percentage: number;
  avg_if: number | null;
}

export interface DepartmentKpiData {
  trend: DepartmentKpiTrendItem[];
  overall_avg_employment_rate: number | null;
  overall_total_tech_income: number | null;
  total_count: number;
}

export interface DepartmentKpiTrendItem {
  evaluation_year: number;
  avg_employment_rate: number;
  total_tech_income: number;
}
```

---

### 4.2 State Types
```typescript
// types/state.ts

export type LoadingStatus = 'idle' | 'loading' | 'success' | 'error';

export interface DashboardState {
  // Domain State
  researchFundingData: ResearchFundingData | null;
  studentData: StudentData | null;
  publicationData: PublicationData | null;
  departmentKpiData: DepartmentKpiData | null;

  // UI State
  loadingState: {
    researchFunding: LoadingStatus;
    students: LoadingStatus;
    publications: LoadingStatus;
    departmentKpi: LoadingStatus;
    filterOptions: LoadingStatus;
  };

  errorState: {
    researchFunding: Error | null;
    students: Error | null;
    publications: Error | null;
    departmentKpi: Error | null;
    filterOptions: Error | null;
  };

  // Filter State
  filters: {
    department: string;
    year: string;
    period: string;
    studentStatus: string;
    journalTier: string;
  };

  filterOptions: {
    departments: string[];
    years: string[];
    periods: string[];
  };
}
```

---

### 4.3 Action Types
```typescript
// types/actions.ts

export type DashboardAction =
  // Data Fetch Actions (각 도메인별 REQUEST/SUCCESS/FAILURE)
  | { type: 'RESEARCH_FUNDING_FETCH_REQUEST' }
  | { type: 'RESEARCH_FUNDING_FETCH_SUCCESS'; payload: ResearchFundingData }
  | { type: 'RESEARCH_FUNDING_FETCH_FAILURE'; payload: Error }

  | { type: 'STUDENT_FETCH_REQUEST' }
  | { type: 'STUDENT_FETCH_SUCCESS'; payload: StudentData }
  | { type: 'STUDENT_FETCH_FAILURE'; payload: Error }

  | { type: 'PUBLICATION_FETCH_REQUEST' }
  | { type: 'PUBLICATION_FETCH_SUCCESS'; payload: PublicationData }
  | { type: 'PUBLICATION_FETCH_FAILURE'; payload: Error }

  | { type: 'DEPARTMENT_KPI_FETCH_REQUEST' }
  | { type: 'DEPARTMENT_KPI_FETCH_SUCCESS'; payload: DepartmentKpiData }
  | { type: 'DEPARTMENT_KPI_FETCH_FAILURE'; payload: Error }

  | { type: 'FILTER_OPTIONS_FETCH_REQUEST' }
  | { type: 'FILTER_OPTIONS_FETCH_SUCCESS'; payload: FilterOptions }
  | { type: 'FILTER_OPTIONS_FETCH_FAILURE'; payload: Error }

  // Filter Actions
  | { type: 'FILTER_UPDATE'; payload: { key: keyof DashboardState['filters']; value: string } }
  | { type: 'FILTER_RESET' }

  // Error Actions
  | { type: 'CLEAR_ERROR'; payload: { key: keyof DashboardState['errorState'] } };

export interface FilterOptions {
  departments: string[];
  years: string[];
  periods: string[];
}
```

---

### 4.4 Context Value Type
```typescript
// types/context.ts

export interface DashboardContextValue {
  state: DashboardState;

  // Data Fetch Actions
  fetchResearchFunding: (filters: DashboardState['filters']) => Promise<void>;
  fetchStudents: (filters: DashboardState['filters']) => Promise<void>;
  fetchPublications: (filters: DashboardState['filters']) => Promise<void>;
  fetchDepartmentKpi: (filters: DashboardState['filters']) => Promise<void>;
  fetchFilterOptions: () => Promise<void>;

  // Filter Actions
  updateFilter: (key: keyof DashboardState['filters'], value: string) => void;
  resetFilters: () => void;

  // Error Actions
  clearError: (key: keyof DashboardState['errorState']) => void;
}
```

---

## 5. Initial State

```typescript
// contexts/DashboardContext.tsx

const initialState: DashboardState = {
  // Domain State
  researchFundingData: null,
  studentData: null,
  publicationData: null,
  departmentKpiData: null,

  // Loading State
  loadingState: {
    researchFunding: 'idle',
    students: 'idle',
    publications: 'idle',
    departmentKpi: 'idle',
    filterOptions: 'idle',
  },

  // Error State
  errorState: {
    researchFunding: null,
    students: null,
    publications: null,
    departmentKpi: null,
    filterOptions: null,
  },

  // Filters
  filters: {
    department: 'all',
    year: 'latest',
    period: '1y',
    studentStatus: 'all',
    journalTier: 'all',
  },

  // Filter Options (빈 배열로 초기화, API에서 로드)
  filterOptions: {
    departments: [],
    years: [],
    periods: [],
  },
};
```

---

## 6. 파일 구조

```
frontend/src/
├── contexts/
│   └── DashboardContext.tsx       # Context + Provider + useDashboard
├── reducers/
│   └── dashboardReducer.ts        # 순수 함수 Reducer
├── types/
│   ├── domain.ts
│   ├── state.ts
│   ├── actions.ts
│   └── context.ts
├── hooks/
│   └── useDashboardData.ts        # API 호출 로직
├── api/
│   └── dataApiClient.ts           # Axios 인스턴스
├── constants/
│   └── filters.ts                 # STUDENT_STATUSES, JOURNAL_TIERS
├── pages/
│   └── Dashboard.tsx
└── components/dashboard/
    ├── FilterPanel.tsx
    ├── ResearchFundingChart.tsx
    ├── StudentChart.tsx
    ├── PublicationChart.tsx
    └── DepartmentKpiChart.tsx
```

---

## 7. Reducer 함수 시그니처

```typescript
// reducers/dashboardReducer.ts

export function dashboardReducer(
  state: DashboardState,
  action: DashboardAction
): DashboardState {
  switch (action.type) {
    case 'RESEARCH_FUNDING_FETCH_REQUEST':
      return {
        ...state,
        loadingState: { ...state.loadingState, researchFunding: 'loading' },
        errorState: { ...state.errorState, researchFunding: null },
      };

    case 'RESEARCH_FUNDING_FETCH_SUCCESS':
      return {
        ...state,
        researchFundingData: action.payload,
        loadingState: { ...state.loadingState, researchFunding: 'success' },
      };

    case 'RESEARCH_FUNDING_FETCH_FAILURE':
      return {
        ...state,
        loadingState: { ...state.loadingState, researchFunding: 'error' },
        errorState: { ...state.errorState, researchFunding: action.payload },
      };

    case 'FILTER_UPDATE':
      return {
        ...state,
        filters: { ...state.filters, [action.payload.key]: action.payload.value },
      };

    case 'FILTER_RESET':
      return {
        ...state,
        filters: initialState.filters,
      };

    // ... 나머지 Action 처리

    default:
      return state;
  }
}
```

---

## 8. 테스트 전략 (TDD)

### Reducer 단위 테스트 (70%)
```typescript
describe('dashboardReducer', () => {
  it('FETCH_REQUEST sets loading', () => {
    const state = { ...initialState };
    const action = { type: 'RESEARCH_FUNDING_FETCH_REQUEST' };
    const newState = dashboardReducer(state, action);

    expect(newState.loadingState.researchFunding).toBe('loading');
    expect(newState.errorState.researchFunding).toBeNull();
  });

  it('FILTER_UPDATE updates specific filter only', () => {
    const state = { ...initialState };
    const action = {
      type: 'FILTER_UPDATE',
      payload: { key: 'department', value: '컴퓨터공학과' }
    };
    const newState = dashboardReducer(state, action);

    expect(newState.filters.department).toBe('컴퓨터공학과');
    expect(newState.filters.year).toBe('latest'); // 다른 필터 유지
  });
});
```

### Context Integration 테스트 (20%)
```typescript
it('provides context values', () => {
  const TestComponent = () => {
    const { state } = useDashboard();
    return <div>{state.loadingState.researchFunding}</div>;
  };

  const { getByText } = render(
    <DashboardProvider><TestComponent /></DashboardProvider>
  );

  expect(getByText('idle')).toBeInTheDocument();
});
```

### E2E 테스트 (10%)
Playwright로 전체 플로우 검증

---

## 9. 성능 최적화

### Context Value Memoization
```typescript
const contextValue = useMemo(
  () => ({ state, fetchResearchFunding, fetchStudents, /* ... */ }),
  [state]
);
```

### Derived State Memoization
```typescript
const filteredData = useMemo(
  () => data.filter(/* ... */),
  [data, filters]
);
```

### Chart Memoization
```typescript
export const ResearchFundingChart = React.memo(({ data, loading }) => {
  // ...
});
```

### Debouncing (300ms)
```typescript
const handleFilterChange = useCallback((key, value) => {
  dispatch({ type: 'FILTER_UPDATE', payload: { key, value } });

  clearTimeout(debounceTimerRef.current);
  debounceTimerRef.current = setTimeout(() => {
    fetchAllDashboardData(filters);
  }, 300);
}, [filters]);
```

---

## 10. 보안

- React 기본 XSS 이스케이프 활용
- `dangerouslySetInnerHTML` 사용 금지
- API Key는 환경 변수로 관리 (Context에 저장 금지)
- TypeScript strict mode 사용
- Redux DevTools는 개발 환경에서만 활성화

---

## 변경 이력

| 버전 | 날짜 | 변경 사항 |
|------|------|-----------|
| 1.0 | 2025-11-02 | 초기 문서 작성 |
| 2.0 | 2025-11-02 | P0/P1 수정사항 반영, 간결화 |

**주요 수정:**
- DepartmentKpiData 구조 명확화 (`overall_total_tech_income` 필드 추가)
- FilterOptions에서 고정값 분리 (STUDENT_STATUSES, JOURNAL_TIERS)
- Period 필터 옵션 명시
- 필터 적용 규칙 테이블 추가
- CSV 컬럼명 정규화 주석 추가
- 불필요한 설명 및 중복 제거

---

**문서 끝**
