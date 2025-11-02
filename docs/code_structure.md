## 최종 코드베이스 구조 (Final Codebase Structure)

CTO의 핵심 가치(신속성, 간결함, 오버엔지니어링 회피)와 아키텍처 원칙(레이어 분리, SRP)을 준수하여 최종 확정된 코드베이스 구조는 다음과 같습니다. 이 구조는 **Simple Layered Architecture**를 기반으로 MVP의 성공적인 완수를 위한 **최소한의 확장성**을 보장합니다.

---

### 1. 백엔드 (DRF, Pandas, Supabase) 구조

핵심은 **`data_ingestion`** 앱 내부에 Presentation, Service, Infrastructure, Domain 계층을 명확히 분리하여, MVP의 핵심 컴포넌트인 `excel_parser.py`의 안정성을 극대화하는 것입니다.

```
my_mvp_project/
├── backend/
│   ├── config/             # Django Project 설정 및 환경 구성 (settings, urls 등)
│   ├── data_ingestion/     # 💡 핵심 비즈니스 로직 앱 (단일 책임: 데이터 수집/파싱/저장)
│   │   ├── api/            # 1. Presentation Layer (HTTP/Serialization/Contract)
│   │   │   ├── views.py      # DRF ViewSets: 요청 처리 및 Service 위임 (Thin Controller)
│   │   │   └── serializers.py  # 요청/응답 데이터 구조 정의 (External Contract)
│   │   │
│   │   ├── services/       # 2. Service/Use Case Layer (Business Logic)
│   │   │   ├── ingestion_service.py # **Use Case**: 데이터 흐름 조정 및 트랜잭션 관리 (Flow/Transaction SRP)
│   │   │   └── excel_parser.py    # **Pure Business Logic**: Pandas를 사용한 데이터 정제/검증 (Pandas Logic SRP)
│   │   │
│   │   ├── domain/         # 4. Domain Layer (Pure Concepts)
│   │   │   └── entities.py   # 순수 Python 기반 비즈니스 엔티티 (DB/API 독립적)
│   │   │
│   │   └── infrastructure/ # 3. Infrastructure/Persistence Layer (Streamlined DAO)
│   │       ├── models.py     # Django Models (Supabase 스키마 매핑)
│   │       └── repositories.py # Data Access Object (DAO): Django ORM 직접 사용 (MVP 간소화 전략)
│   │
│   └── users/              # 사용자 인증/권한 관리 앱
│       └── ...
│
├── frontend/               # React Codebase
└── infra/                  # Railway/Supabase 최소 설정 및 배포 스크립트
```

#### 핵심 모듈별 책임 (SRP 준수)

| 파일/모듈 | 레이어 | 책임 (SRP) | 간결함/확장성 전략 반영 |
| :--- | :--- | :--- | :--- |
| `api/views.py` | Presentation | HTTP 요청 처리 및 Service 호출 위임. | **Thin Controller** 원칙 준수. |
| `services/excel_parser.py` | Service | **Pandas 기반 데이터 정제 및 유효성 검증.** | 인프라 무관 **높은 테스트 용이성** 확보. |
| `services/ingestion_service.py` | Service | 데이터 파싱 $\rightarrow$ 저장 Use Case 흐름 조정 및 트랜잭션. | **단일 Use Case** 책임. |
| `infrastructure/repositories.py`| Persistence | DB (ORM)와의 데이터 입출력 (CRUD) 전담. | **추상 인터페이스 생략**으로 MVP 신속성 확보. |

---

### 2. 프런트엔드 (React) 구조

Presentation Logic과 Data Handling Logic을 분리하여, UI/라이브러리 전환에 유연한 구조를 유지합니다.

```
frontend/
└── src/
    ├── components/       # 1. Presentation/UI Components (UI 라이브러리 교체 유연성 확보)
    │   ├── ui/             # 공통 UI 요소 (Button, Input 등)
    │   └── dashboard/      # Recharts/Tremor 등 특정 라이브러리에 의존하는 Chart/Widget
    │
    ├── pages/            # View/Screen 정의 (Components 및 Hooks 조합)
    │
    ├── hooks/            # 2. State & Data Handling Logic (Business/State Logic)
    │   └── useDashboardData.js # API 호출, 데이터 필터링/변환 로직 (UI 라이브러리 독립적)
    │
    └── api/              # 3. API Contract Layer
        └── dataApiClient.js # 백엔드와의 통신(Axios 등) 전담 (Contract 변경 대응)
```