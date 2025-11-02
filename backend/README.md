# Backend - Django Rest Framework + Pandas

## Architecture

Following Clean Architecture principles with simplified layers:

```
api/                    # Presentation Layer (DRF Views & Serializers)
services/               # Service/Use Case Layer (Business Logic)
domain/                 # Domain Layer (Business Entities)
infrastructure/         # Persistence Layer (Django Models & Repositories)
tests/                  # Test Suite
```

## Key Components

### Services Layer
- `excel_parser.py`: Pure Pandas data parsing & validation (70%+ test coverage target)
- `ingestion_service.py`: Upload flow orchestration (to be implemented)

### Infrastructure Layer
- `job_status_store.py`: Thread-safe in-memory job tracking (P0 Critical)
- `models.py`: Django ORM models (to be implemented)
- `repositories.py`: Data access layer (to be implemented)

## Testing

### Running Tests

```bash
# All tests
pytest

# Unit tests only (fast)
pytest -m unit

# Integration tests
pytest -m integration

# With coverage
pytest --cov=data_ingestion --cov-report=html

# Specific test file
pytest data_ingestion/tests/test_excel_parser.py

# Specific test class
pytest data_ingestion/tests/test_excel_parser.py::TestResearchProjectDataParser

# Verbose output
pytest -v

# Stop on first failure
pytest -x
```

### Test Markers

- `@pytest.mark.unit`: Fast, isolated unit tests
- `@pytest.mark.integration`: Tests with DB/external dependencies
- `@pytest.mark.slow`: Long-running tests

### Fixtures

Available in `tests/conftest.py`:
- `sample_research_data`: Research project DataFrame
- `sample_student_roster`: Student roster DataFrame
- `sample_publication_list`: Publication data DataFrame
- `sample_department_kpi`: Department KPI DataFrame

## P0 Critical: Thread Safety

The `job_status_store.py` module provides thread-safe job tracking:

```python
from data_ingestion.infrastructure.job_status_store import get_job_store, JobStatus

store = get_job_store()
store.create_job('job-123')
store.update_status('job-123', JobStatus.PROCESSING)
store.increment_progress('job-123')  # Thread-safe atomic increment
```

Concurrency tests in `test_job_status_store_concurrency.py` prove thread safety under load (10+ concurrent threads).

## Data Validation Rules

### Research Project Data
- 집행ID: Unique primary key
- 집행금액 ≤ 총연구비
- All monetary values ≥ 0

### Student Roster
- 학번: Unique primary key
- 학년: 1-7 range

### Department KPI
- 졸업생 취업률: 0-100%
- 기술이전 수입액 ≥ 0

## Development Workflow

1. Write test FIRST (Red)
2. Implement minimal code (Green)
3. Refactor while keeping tests green
4. Commit small, frequently

See `../docs/test-plan.md` for detailed TDD process.
