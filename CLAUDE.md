# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

University internal data visualization dashboard MVP for parsing Ecount Excel exports and displaying key metrics (research funding, student enrollment, publications, department KPIs).

**Core Values (CTO Mandate):**
- Rapid iteration with minimal but extensible architecture
- Avoid over-engineering - build only what's immediately necessary
- Simplest infrastructure approach (Railway + Supabase)

**Tech Stack:** Django Rest Framework (DRF), Pandas, React, Recharts, Supabase (PostgreSQL), Railway

## Architecture Principles

### Backend: Simple Layered Architecture (DRF + Pandas)

Located in `backend/data_ingestion/`:

```
data_ingestion/
├── api/                    # Presentation Layer
│   ├── views.py              # Thin controllers (DRF ViewSets)
│   └── serializers.py        # Request/response contracts
├── services/               # Service/Use Case Layer
│   ├── excel_parser.py       # Pure Pandas logic (SRP: data cleaning/validation)
│   └── ingestion_service.py  # Flow orchestration & transactions
├── domain/                 # Domain Layer
│   └── entities.py           # Pure Python business entities
└── infrastructure/         # Persistence Layer
    ├── models.py             # Django models (Supabase schema)
    └── repositories.py       # Data access (Django ORM direct usage)
```

**Key Separation:**
- `excel_parser.py`: Infrastructure-agnostic Pandas transformations (highly testable)
- `ingestion_service.py`: Single responsibility - data parsing → storage flow + transaction management
- `repositories.py`: No abstraction layer in MVP - direct Django ORM usage for speed

### Frontend: Logic Separation

Located in `frontend/src/`:

```
src/
├── components/
│   ├── ui/                  # Generic UI components
│   └── dashboard/           # Chart/widget components (Recharts dependent)
├── pages/                   # View composition
├── hooks/                   # State & data handling logic
│   └── useDashboardData.js  # API calls, filtering, transforms (UI library agnostic)
└── api/
    └── dataApiClient.js     # Backend communication layer
```

## Core Data Processing Flow

**4 CSV File Types:**
1. `research_project_data.csv` - Research funding execution tracking
2. `student_roster.csv` - Student enrollment by department/year/program
3. `publication_list.csv` - Publication records with Impact Factor
4. `department_kpi.csv` - Employment rates and tech transfer revenue

**Data Pipeline:**
1. Admin uploads CSV/Excel → DRF endpoint (`POST /upload`)
2. **Async background processing** (Python threading or simple task queue)
3. `excel_parser.py`: Pandas parsing, cleaning, validation
4. `repositories.py`: Bulk insert to Supabase
5. React dashboard fetches data for visualization

## Required Column Schema

**research_project_data.csv:**
- 집행ID (String, PK), 소속학과 (String), 총연구비 (Int/Float), 집행일자 (Date), 집행금액 (Int/Float)

**student_roster.csv:**
- 학번 (String, PK), 학과 (String), 학년 (Int), 과정구분 (String: 학사/석사/박사), 학적상태 (String: 재학/휴학/졸업)

**publication_list.csv:**
- 논문ID (String, PK), 학과 (String), 저널등급 (String: SCIE/KCI), Impact Factor (Float, Nullable)

**department_kpi.csv:**
- 평가년도 (Int), 학과 (String), 졸업생 취업률(%) (Float), 연간 기술이전 수입액(억원) (Float)

## Mandatory Development Process

### TDD Required for All Code Changes

**Red → Green → Refactor Cycle:**
1. Write failing test FIRST (one scenario at a time)
2. Implement minimal code to pass
3. Refactor while keeping tests green
4. Commit frequently in small steps

**Test Pyramid:**
- Unit tests (70%): Fast, isolated, infrastructure-agnostic
- Integration tests (20%): Module boundaries, DRF API endpoints
- Acceptance tests (10%): E2E user scenarios

**FIRST Principles:**
- Fast, Independent, Repeatable, Self-validating, Timely

### Implementation Flow (Strict)

When implementing from plan documents (`docs/spec/*/plan.md`):

1. **Document Analysis:** Read all phases, identify scope (backend/frontend/DB), security requirements, error handling, test requirements
2. **TodoWrite Checklist:** Create todos for ALL phases/tasks using TodoWrite tool
3. **Sequential Implementation:** Complete one phase → verify Acceptance Tests → mark todo complete → next phase
4. **Self-Verification:**
   - All phases complete?
   - All security requirements (auth, validation, CSRF/XSS defense)?
   - All error codes implemented?
   - Tests written and passing (unit + integration + E2E)?
   - Documentation complete?
5. **Final Report:** Summarize completed items, verification results, generated files

**Frequently Omitted (Extra Attention Required):**
- Security validation logic (CSRF, input validation)
- All specific error codes from spec
- Frontend error display UI
- E2E tests
- Helper/utility functions

## Authentication (MVP Simplification)

**No DB-based user/auth system.** Admin access control:
- Backend: Hardcoded API key (`X-Admin-Key`) in env vars, lightweight auth middleware
- Frontend: Simple env var check (`ADMIN_MODE=true`) or URL obfuscation for upload page access

## Visualization Requirements

**4 Core Metrics + Chart Types (Recharts):**
- Research funding trend: Line Chart + Metric Card (current balance)
- Student enrollment by department: Stacked Bar Chart (by year/program)
- Publication performance: Doughnut Chart (by journal tier) + Metric Card
- Department KPI trend: Line Chart (employment rate + tech transfer revenue)

**Filtering:** Simple dropdown-based single selection only (no complex multi-select or custom date ranges in MVP)

## Writing Rules/Guidelines

- Project documentation (`docs/`, `spec/`): Write in Korean
- Rule documents (`.cursor/rules/`, prompt files): Write in English

When creating rule documents:
- Use prompt engineering techniques
- Start with high-level overview → specific actionable requirements
- Show DO/DON'T code examples
- Reference actual codebase code when possible
- Keep DRY (cross-reference other rules)
- Skip generic guidelines (Clean Code, etc.)
- Prefer terse bullet points over full sentences

## Key Development Commands

**Backend:**
```bash
# Django development server
python manage.py runserver

# Run tests
python manage.py test

# Migrations
python manage.py makemigrations
python manage.py migrate

# Type checking (if using mypy)
mypy backend/
```

**Frontend:**
```bash
# Development server
npm run dev

# Build
npm run build

# Lint
npm run lint

# Tests
npm run test
```

**Deployment:**
- Railway: Push to main branch triggers auto-deploy
- Supabase: DB migrations via Django ORM
- Env vars: Configure in Railway dashboard + `.env.local` for frontend

## Important Constraints

- Max file upload size: 10MB
- Async file processing mandatory (non-blocking UI)
- No separate ETL pipeline (over-engineering)
- Infrastructure setup: Max 1 day - focus on core business logic
- **Strategic Chart Library Note:** If Recharts + custom UI building is slow, consider switching to Tremor.so or Mantine Data Components for high-level dashboard components (with CTO approval)

## Documentation References

- Project Requirements: `docs/requirements.md`
- PRD: `docs/prd.md`
- Architecture: `docs/code_structure.md`
- Tech Stack Rationale: `docs/techstack.md`
- Implementation Guidelines: `prompt/implement copy.md`
- TDD Process: `prompt/tdd.md`
- Sample Data: `docs/db/*.csv`
