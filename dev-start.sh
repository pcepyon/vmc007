#!/bin/bash

# ============================================================================
# 개발 서버 시작 스크립트
# 백엔드(Django)와 프론트엔드(React/Vite)를 동시에 시작합니다.
# ============================================================================

set -e  # 에러 발생 시 스크립트 중단

# 색상 정의
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=====================================${NC}"
echo -e "${BLUE}🚀 개발 서버 시작 중...${NC}"
echo -e "${BLUE}=====================================${NC}"
echo ""

# 프로젝트 루트 디렉토리
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

# PID 파일 저장 위치
PID_DIR="$PROJECT_ROOT/.dev"
mkdir -p "$PID_DIR"

BACKEND_PID_FILE="$PID_DIR/backend.pid"
FRONTEND_PID_FILE="$PID_DIR/frontend.pid"

# 기존 서버 종료
if [ -f "$BACKEND_PID_FILE" ]; then
    OLD_PID=$(cat "$BACKEND_PID_FILE")
    if ps -p $OLD_PID > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  기존 백엔드 서버 종료 중... (PID: $OLD_PID)${NC}"
        kill $OLD_PID 2>/dev/null || true
        sleep 1
    fi
    rm "$BACKEND_PID_FILE"
fi

if [ -f "$FRONTEND_PID_FILE" ]; then
    OLD_PID=$(cat "$FRONTEND_PID_FILE")
    if ps -p $OLD_PID > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  기존 프론트엔드 서버 종료 중... (PID: $OLD_PID)${NC}"
        kill $OLD_PID 2>/dev/null || true
        sleep 1
    fi
    rm "$FRONTEND_PID_FILE"
fi

# 1. 백엔드 서버 시작
echo -e "${GREEN}[1/2] 백엔드 서버 시작 중...${NC}"
cd "$BACKEND_DIR"

# 가상환경 확인
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ 가상환경을 찾을 수 없습니다. backend/venv 디렉토리를 확인하세요.${NC}"
    exit 1
fi

# .env 파일 확인
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ backend/.env 파일을 찾을 수 없습니다.${NC}"
    exit 1
fi

# 백엔드 서버 백그라운드 실행
source venv/bin/activate
nohup python manage.py runserver > "$PID_DIR/backend.log" 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > "$BACKEND_PID_FILE"
echo -e "${GREEN}✅ 백엔드 서버 시작됨 (PID: $BACKEND_PID)${NC}"
echo -e "   📍 URL: ${BLUE}http://localhost:8000${NC}"
echo -e "   📄 로그: ${PID_DIR}/backend.log"
echo ""

# 백엔드 서버가 준비될 때까지 대기
sleep 3

# 2. 프론트엔드 서버 시작
echo -e "${GREEN}[2/2] 프론트엔드 서버 시작 중...${NC}"
cd "$FRONTEND_DIR"

# node_modules 확인
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}⚠️  node_modules를 찾을 수 없습니다. npm install 실행 중...${NC}"
    npm install
fi

# 프론트엔드 서버 백그라운드 실행
nohup npm run dev > "$PID_DIR/frontend.log" 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > "$FRONTEND_PID_FILE"
echo -e "${GREEN}✅ 프론트엔드 서버 시작됨 (PID: $FRONTEND_PID)${NC}"
echo -e "   📍 URL: ${BLUE}http://localhost:3000${NC}"
echo -e "   📄 로그: ${PID_DIR}/frontend.log"
echo ""

# 프론트엔드 서버가 준비될 때까지 대기
sleep 3

# 최종 확인
echo -e "${BLUE}=====================================${NC}"
echo -e "${GREEN}✨ 개발 서버가 성공적으로 시작되었습니다!${NC}"
echo -e "${BLUE}=====================================${NC}"
echo ""
echo -e "📱 ${BLUE}프론트엔드:${NC} http://localhost:3000"
echo -e "🔧 ${BLUE}백엔드:${NC}     http://localhost:8000"
echo ""
echo -e "💡 ${YELLOW}서버 종료:${NC} ./dev-stop.sh"
echo -e "📋 ${YELLOW}로그 확인:${NC} tail -f .dev/backend.log"
echo -e "            tail -f .dev/frontend.log"
echo ""
