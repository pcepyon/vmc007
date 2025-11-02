# Railway 배포 가이드

## 사전 준비

1. Railway 계정 생성 (https://railway.app)
2. Supabase 프로젝트 생성 (https://supabase.com)
3. GitHub 저장소 연결

## 배포 방식

이 프로젝트는 **Dockerfile 기반 배포**를 사용합니다.

**이유**: `python-magic` 패키지가 시스템 라이브러리 `libmagic`에 의존하는데, Railway Nixpacks로는 안정적인 설치가 어려워 Dockerfile을 사용합니다.

## Railway 내부 네트워킹

Railway는 **Private Networking**을 제공합니다:
- 서비스 주소: `<service-name>.railway.internal`
- 예: `vmc007.railway.internal`
- **장점**:
  - 더 빠른 통신 (내부 네트워크)
  - 외부 인터넷을 거치지 않음
  - 대역폭 절약
  - 보안 강화 (내부 트래픽)

## Railway 배포 단계

### 1. 백엔드 배포

1. Railway 대시보드에서 "New Project" 클릭
2. "Deploy from GitHub repo" 선택
3. 저장소 선택 후 "Deploy Now" 클릭
4. Railway가 자동으로 Dockerfile을 감지하여 빌드

### 2. 환경 변수 설정

Railway 프로젝트 설정(Variables 탭)에서 다음 환경 변수를 추가:

```bash
# Django Settings
DEBUG=False
SECRET_KEY=<강력한 시크릿 키 생성 - 50자 이상>
ALLOWED_HOSTS=<your-app-name>.railway.app

# Database (Supabase - 기존 프로젝트 값 사용)
DB_NAME=postgres
DB_USER=postgres.tysiwxkeyzgkrhwtdmhg
DB_PASSWORD=XZ41dYGloJLr8kO5
DB_HOST=aws-1-ap-northeast-2.pooler.supabase.com
DB_PORT=5432

# Admin API Key
ADMIN_API_KEY=<강력한 관리자 API 키 생성>

# CORS (프론트엔드 배포 후 추가)
# 옵션 1: Railway 내부 네트워킹 (권장 - 더 빠름)
FRONTEND_URL=https://vmc007-frontend.railway.internal

# 옵션 2: 공개 도메인 (외부 접근 필요 시)
# FRONTEND_URL=https://<your-frontend-domain>.up.railway.app
```

**주의**:
- `SECRET_KEY`는 반드시 프로덕션용 강력한 키로 변경하세요
- `ADMIN_API_KEY`도 프로덕션용으로 변경하세요
- `ALLOWED_HOSTS`는 Railway에서 제공하는 실제 도메인으로 설정하세요

### 3. 데이터베이스 마이그레이션

**자동 마이그레이션**: Dockerfile의 `CMD`에서 시작 시 자동으로 마이그레이션이 실행됩니다.

수동으로 실행하려면 Railway 대시보드 터미널에서:

```bash
cd backend && python manage.py migrate
```

**참고**: Dockerfile 기반 배포에서는 Procfile의 `release` 단계가 사용되지 않습니다.

### 4. 프론트엔드 배포 (Railway)

1. Railway 대시보드에서 "New Project" 클릭
2. "Deploy from GitHub repo" 선택 (같은 저장소 사용 가능)
3. 프로젝트 생성 후 Settings로 이동

#### 4.1. Root Directory 설정
- Settings → "Root Directory" → `frontend` 입력
- 이렇게 하면 frontend 폴더만 독립적으로 배포됨

#### 4.2. Build & Start 명령 설정
Railway Settings → Deploy에서 다음 설정:

**Build Command:**
```bash
npm install && npm run build
```

**Start Command (옵션 1 - serve 사용):**
```bash
npx serve@latest -s dist -l $PORT
```

**Start Command (옵션 2 - Vite preview):**
```bash
npm run preview -- --port $PORT --host 0.0.0.0
```

**권장**: serve 사용 (더 안정적)

#### 4.3. 환경 변수 설정 (Variables 탭)
```bash
# 옵션 1: Railway 내부 네트워킹 (권장)
VITE_API_BASE_URL=https://vmc007.railway.internal

# 옵션 2: 공개 도메인 (개발/테스트 시)
# VITE_API_BASE_URL=https://<backend-domain>.up.railway.app

VITE_ADMIN_MODE=true
VITE_ADMIN_API_KEY=<백엔드에서 설정한 ADMIN_API_KEY와 동일>
```

**참고**:
- 백엔드와 프론트엔드는 별도 Railway 서비스로 배포
- 같은 GitHub 저장소를 두 번 배포 (Root Directory로 구분)
- **내부 네트워킹**: 같은 Railway 프로젝트 내 서비스끼리는 `.railway.internal` 주소로 통신
- **공개 도메인**: 브라우저에서 직접 접근해야 하는 경우 `.up.railway.app` 사용

### 5. CORS 설정 업데이트

백엔드 Railway 환경 변수에 `FRONTEND_URL` 추가:

```bash
# 내부 네트워킹 사용 시
FRONTEND_URL=https://vmc007-frontend.railway.internal

# 또는 공개 도메인 사용 시
# FRONTEND_URL=https://<frontend-domain>.up.railway.app
```

**자동 적용**: `settings.py`가 환경 변수 `FRONTEND_URL`을 읽어서 CORS 설정에 자동 추가합니다.

**중요**: 브라우저는 `.railway.internal` 주소에 직접 접근할 수 없으므로, 실제로는 프론트엔드의 공개 도메인을 CORS에 추가해야 합니다.

## Railway 네트워킹 이해하기

### Private Networking (`.railway.internal`)
**사용 시나리오**: 서버 간 통신 (서비스 to 서비스)
- ✅ 백엔드 → 데이터베이스
- ✅ 프론트엔드 SSR → 백엔드 API
- ✅ 마이크로서비스 간 통신
- ❌ 브라우저 → 백엔드 (브라우저는 접근 불가)

**장점**:
- 더 빠른 속도 (내부 네트워크)
- 외부 대역폭 사용 안함
- 추가 비용 없음

### Public Domain (`.up.railway.app`)
**사용 시나리오**: 외부 접근 (브라우저, 외부 API 등)
- ✅ 브라우저 → 백엔드 API
- ✅ 브라우저 → 프론트엔드
- ✅ 외부 웹훅, 써드파티 서비스

**이 프로젝트의 네트워킹 구성**:
```
브라우저
  │
  ├─→ https://vmc007-frontend.up.railway.app (공개)
  │     │
  │     └─→ https://vmc007.railway.internal (내부) ← 프론트엔드 → 백엔드
  │
  └─→ https://vmc007.up.railway.app (공개, 직접 API 호출 시)
```

**권장 설정**:
1. **프론트엔드 → 백엔드**: `.railway.internal` 사용 (더 빠름)
2. **CORS 설정**: 프론트엔드 공개 도메인 추가 (브라우저 Origin 용)

## 배포 확인

1. Railway 백엔드 URL 접속: `https://vmc007.up.railway.app/api/health`
2. 프론트엔드 접속하여 대시보드 확인: `https://vmc007-frontend.up.railway.app`
3. 파일 업로드 기능 테스트

## 문제 해결

### pip: command not found 오류
**원인**: Nixpacks가 Python을 자동으로 감지하지 못함

**해결**:
- 루트 디렉토리에 `requirements.txt` 파일이 있어야 함 (프로젝트에 이미 포함됨)
- Railway가 자동으로 Python 프로젝트로 감지하여 pip 설치

### libmagic 오류 (ImportError: failed to find libmagic)
**원인**: `python-magic` 패키지가 시스템 라이브러리 `libmagic`에 의존

**해결**: Dockerfile 기반 배포로 전환
- Nixpacks로는 `libmagic` 설치가 불안정함 (Railway 커뮤니티 권장사항)
- Dockerfile에서 `apt-get install libmagic1 libmagic-dev file`로 명시적 설치
- 파일 업로드 시 MIME 타입 검증을 위해 필수

**참고**: `python-magic`은 보안을 위해 필수입니다 (악성 파일 업로드 방지)

### 정적 파일 404 에러
**자동 실행**: Dockerfile의 `RUN` 단계에서 빌드 시 자동으로 `collectstatic` 실행

수동 실행:
```bash
cd backend && python manage.py collectstatic --noinput
```

**참고**: Dockerfile 배포에서는 `railway.json`의 `buildCommand`가 사용되지 않습니다.

### 데이터베이스 연결 오류
- Supabase 데이터베이스 접속 정보 확인
- `DB_HOST`가 올바른지 확인 (Session Pooler 주소 사용)
- Supabase Connection Pooler 사용 중 (`transaction` 모드)

### CORS 에러
- Railway 환경 변수에 `FRONTEND_URL` 설정 확인
- 프로토콜(https/http) 정확히 일치하는지 확인
- 프론트엔드 도메인 정확히 입력 (trailing slash 없이)

### 빌드 시간 초과
- 첫 배포 시 패키지 설치로 인해 시간이 걸릴 수 있음 (2-3분)
- 이후 배포는 캐시 사용으로 빠름

## 주요 파일

### 배포 관련 (Dockerfile 기반)
- **`Dockerfile`**: Railway 배포 설정 (메인)
  - libmagic 시스템 패키지 설치
  - Python 의존성 설치
  - collectstatic 자동 실행
  - 마이그레이션 + Gunicorn 서버 시작
- **`.dockerignore`**: Docker 이미지 최적화 (불필요한 파일 제외)

### 레거시 파일 (Dockerfile 사용 시 무시됨)
- `Procfile`: Nixpacks 전용 (Dockerfile 있으면 사용 안됨)
- `railway.json`: Nixpacks 전용
- `nixpacks.toml`: Nixpacks 시스템 패키지 설정 (참고용)

### 기타
- `requirements.txt` (루트): Python 프로젝트 자동 감지용
- `backend/requirements.txt`: Python 의존성 목록
- `backend/data_ingestion/wsgi.py`: WSGI 애플리케이션 진입점
- `.env.example`: 환경 변수 템플릿 (개발/프로덕션)

## 보안 체크리스트

- [ ] `DEBUG=False` 설정 확인
- [ ] `DJANGO_SECRET_KEY` 강력한 키로 설정
- [ ] `ADMIN_API_KEY` 강력한 키로 설정
- [ ] `ALLOWED_HOSTS`에 실제 도메인만 포함
- [ ] Supabase Row Level Security (RLS) 검토
- [ ] `.env` 파일 `.gitignore`에 포함 확인
