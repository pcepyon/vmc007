# University Data Visualization Dashboard - MVP

대학교 사내 데이터 시각화 대시보드 프로젝트입니다. Ecount 엑셀 데이터를 파싱하여 주요 지표(연구비, 학생 수, 논문, 부서 KPI)를 시각화합니다.

## Tech Stack

- **Backend**: Django Rest Framework + Pandas
- **Frontend**: React + TypeScript + Recharts
- **Database**: Supabase (PostgreSQL)
- **Deployment**: Railway
- **Testing**: pytest-django, Jest, React Testing Library, Playwright

## Project Structure

```
VMC007/
├── backend/                    # Django backend
│   ├── data_ingestion/
│   │   ├── api/               # DRF views & serializers
│   │   ├── services/          # Business logic (Pandas)
│   │   ├── domain/            # Domain entities
│   │   ├── infrastructure/    # DB models & repositories
│   │   └── tests/             # Unit & integration tests
│   ├── requirements.txt
│   └── pytest.ini
├── frontend/                   # React frontend
│   ├── src/
│   │   ├── components/        # UI components
│   │   ├── hooks/             # Custom hooks
│   │   ├── pages/             # Page components
│   │   └── __tests__/         # Jest tests
│   ├── package.json
│   └── jest.config.ts
├── e2e/                        # Playwright E2E tests
│   ├── tests/
│   └── playwright.config.ts
└── docs/                       # Documentation

```

## Getting Started

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest

# Run with coverage
pytest --cov=data_ingestion --cov-report=html

# Run server (after Django setup is complete)
python manage.py runserver
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run tests
npm test

# Run tests with coverage
npm run test:coverage

# Start dev server
npm run dev
```

### E2E Testing

```bash
cd e2e

# Install dependencies
npm install

# Install Playwright browsers
npx playwright install

# Run E2E tests
npm test

# Run with UI mode
npm run test:ui
```

## Test Strategy (Following test-plan.md)

### Test Pyramid
- **Unit Tests (70%)**: Fast, isolated, core business logic
- **Integration Tests (20%)**: API endpoints, module boundaries
- **E2E Tests (10%)**: User scenarios, happy paths

### P0 Critical: Thread Safety
- `job_status_store.py`: Thread-safe in-memory job tracking with `threading.Lock()`
- Concurrency tests validate no race conditions occur

### TDD Process
1. **RED**: Write failing test first
2. **GREEN**: Implement minimal code to pass
3. **REFACTOR**: Clean up while keeping tests green

### Running Tests

```bash
# Backend unit tests (marked with @pytest.mark.unit)
cd backend
pytest -m unit

# Backend integration tests
pytest -m integration

# Frontend unit tests
cd ../frontend
npm test

# E2E tests
cd ../e2e
npm test
```

## Development Guidelines

- Follow TDD: Write tests FIRST
- Keep tests FIRST (Fast, Independent, Repeatable, Self-validating, Timely)
- Use AAA pattern (Arrange, Act, Assert)
- Mock external dependencies with `unittest.mock`
- See `CLAUDE.md` for detailed development guidelines

## CI/CD

Tests run automatically on:
- Pull requests
- Main branch commits

All tests must pass before merging.

## Documentation

- `docs/requirements.md`: Project requirements
- `docs/prd.md`: Product requirements document
- `docs/test-plan.md`: Test strategy and implementation plan
- `docs/techstack.md`: Technology decisions
- `CLAUDE.md`: Development guidelines for AI coding agents
