#!/bin/bash

# ============================================================================
# 개발 서버 종료 스크립트
# 백엔드와 프론트엔드 개발 서버를 종료합니다.
# ============================================================================

# 색상 정의
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=====================================${NC}"
echo -e "${BLUE}🛑 개발 서버 종료 중...${NC}"
echo -e "${BLUE}=====================================${NC}"
echo ""

# 프로젝트 루트 디렉토리
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_DIR="$PROJECT_ROOT/.dev"

BACKEND_PID_FILE="$PID_DIR/backend.pid"
FRONTEND_PID_FILE="$PID_DIR/frontend.pid"

STOPPED=false

# 백엔드 서버 종료
if [ -f "$BACKEND_PID_FILE" ]; then
    BACKEND_PID=$(cat "$BACKEND_PID_FILE")
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        echo -e "${YELLOW}🔧 백엔드 서버 종료 중... (PID: $BACKEND_PID)${NC}"
        kill $BACKEND_PID 2>/dev/null || true
        sleep 1

        # 강제 종료 확인
        if ps -p $BACKEND_PID > /dev/null 2>&1; then
            echo -e "${RED}⚠️  강제 종료 중...${NC}"
            kill -9 $BACKEND_PID 2>/dev/null || true
        fi

        echo -e "${GREEN}✅ 백엔드 서버 종료됨${NC}"
        STOPPED=true
    fi
    rm "$BACKEND_PID_FILE" 2>/dev/null || true
fi

# 프론트엔드 서버 종료
if [ -f "$FRONTEND_PID_FILE" ]; then
    FRONTEND_PID=$(cat "$FRONTEND_PID_FILE")
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        echo -e "${YELLOW}📱 프론트엔드 서버 종료 중... (PID: $FRONTEND_PID)${NC}"
        kill $FRONTEND_PID 2>/dev/null || true
        sleep 1

        # 강제 종료 확인
        if ps -p $FRONTEND_PID > /dev/null 2>&1; then
            echo -e "${RED}⚠️  강제 종료 중...${NC}"
            kill -9 $FRONTEND_PID 2>/dev/null || true
        fi

        echo -e "${GREEN}✅ 프론트엔드 서버 종료됨${NC}"
        STOPPED=true
    fi
    rm "$FRONTEND_PID_FILE" 2>/dev/null || true
fi

# 추가: 포트를 점유하고 있는 프로세스 종료 (백업)
echo ""
echo -e "${YELLOW}🔍 포트 점유 프로세스 확인 중...${NC}"

# 8000 포트 확인
PORT_8000_PID=$(lsof -ti:8000 2>/dev/null || true)
if [ ! -z "$PORT_8000_PID" ]; then
    echo -e "${YELLOW}⚠️  포트 8000을 점유한 프로세스 발견 (PID: $PORT_8000_PID)${NC}"
    kill $PORT_8000_PID 2>/dev/null || true
    echo -e "${GREEN}✅ 포트 8000 정리됨${NC}"
    STOPPED=true
fi

# 3000 포트 확인
PORT_3000_PID=$(lsof -ti:3000 2>/dev/null || true)
if [ ! -z "$PORT_3000_PID" ]; then
    echo -e "${YELLOW}⚠️  포트 3000을 점유한 프로세스 발견 (PID: $PORT_3000_PID)${NC}"
    kill $PORT_3000_PID 2>/dev/null || true
    echo -e "${GREEN}✅ 포트 3000 정리됨${NC}"
    STOPPED=true
fi

echo ""
if [ "$STOPPED" = true ]; then
    echo -e "${GREEN}✨ 모든 개발 서버가 종료되었습니다.${NC}"
else
    echo -e "${BLUE}ℹ️  실행 중인 개발 서버가 없습니다.${NC}"
fi
echo ""
