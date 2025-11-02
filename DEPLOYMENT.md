# Railway 배포 가이드

## 사전 준비

1. Railway 계정 생성 (https://railway.app)
2. Supabase 프로젝트 생성 (https://supabase.com)
3. GitHub 저장소 연결

## Railway 배포 단계

### 1. 백엔드 배포

1. Railway 대시보드에서 "New Project" 클릭
2. "Deploy from GitHub repo" 선택
3. 저장소 선택 후 "Deploy Now" 클릭

### 2. 환경 변수 설정

Railway 프로젝트 설정에서 다음 환경 변수를 추가:

```
DJANGO_SECRET_KEY=<강력한 시크릿 키 생성>
DEBUG=False
ALLOWED_HOSTS=<railway-domain>.railway.app

DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=<supabase-db-password>
DB_HOST=<supabase-project-ref>.supabase.co
DB_PORT=5432

ADMIN_API_KEY=<강력한 관리자 API 키 생성>
```

### 3. 데이터베이스 마이그레이션

배포 후 Railway CLI 또는 대시보드 터미널에서:

```bash
python backend/manage.py migrate
```

### 4. 프론트엔드 배포 (옵션 1: Vercel)

1. Vercel 계정 생성 (https://vercel.com)
2. GitHub 저장소 연결
3. Root Directory를 `frontend`로 설정
4. Framework Preset: Vite
5. 환경 변수 설정:

```
VITE_API_BASE_URL=https://<your-railway-domain>.railway.app
VITE_ADMIN_MODE=true
VITE_ADMIN_API_KEY=<railway에서 설정한 ADMIN_API_KEY와 동일>
```

### 5. 프론트엔드 배포 (옵션 2: Railway Static Site)

1. 프론트엔드용 별도 Railway 프로젝트 생성
2. Build Command: `cd frontend && npm install && npm run build`
3. Start Command: `npx serve -s frontend/dist -l $PORT`
4. 환경 변수 동일하게 설정

### 6. CORS 설정 업데이트

백엔드의 `data_ingestion/settings.py`에서 CORS 설정 업데이트:

```python
CORS_ALLOWED_ORIGINS = [
    'https://<your-frontend-domain>.vercel.app',  # Vercel
    # or
    'https://<your-frontend-domain>.railway.app',  # Railway
]
```

## 배포 확인

1. Railway 백엔드 URL 접속: `https://<railway-domain>.railway.app/api/health`
2. 프론트엔드 접속하여 대시보드 확인
3. 파일 업로드 기능 테스트

## 문제 해결

### 정적 파일 404 에러
```bash
python backend/manage.py collectstatic --noinput
```

### 데이터베이스 연결 오류
- Supabase 데이터베이스 접속 정보 확인
- `DB_HOST`가 올바른지 확인
- Supabase Connection Pooler 사용 (`transaction` 모드)

### CORS 에러
- `CORS_ALLOWED_ORIGINS`에 프론트엔드 도메인 추가 확인
- 프로토콜(https/http) 정확히 일치하는지 확인

## 주요 파일

- `Procfile`: Railway 시작 명령
- `nixpacks.toml`: Nixpacks 빌드 설정
- `railway.json`: Railway 배포 설정
- `backend/requirements.txt`: Python 의존성
- `backend/data_ingestion/wsgi.py`: WSGI 애플리케이션 진입점

## 보안 체크리스트

- [ ] `DEBUG=False` 설정 확인
- [ ] `DJANGO_SECRET_KEY` 강력한 키로 설정
- [ ] `ADMIN_API_KEY` 강력한 키로 설정
- [ ] `ALLOWED_HOSTS`에 실제 도메인만 포함
- [ ] Supabase Row Level Security (RLS) 검토
- [ ] `.env` 파일 `.gitignore`에 포함 확인
