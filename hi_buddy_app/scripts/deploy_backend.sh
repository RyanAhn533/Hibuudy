#!/bin/bash
# ─────────────────────────────────────────────
# Hi-Buddy 백엔드 배포 스크립트 (Railway)
# 사용법: bash scripts/deploy_backend.sh
#
# 사전 준비:
#   1. Railway CLI 설치: npm i -g @railway/cli
#   2. 로그인: railway login
#   3. 프로젝트 생성: railway init (backend/ 디렉토리에서)
# ─────────────────────────────────────────────

set -e

BACKEND_DIR="$(dirname "$0")/../../backend"

echo "=== Hi-Buddy 백엔드 배포 ==="
echo ""

cd "$BACKEND_DIR"

# Railway CLI 확인
if ! command -v railway &> /dev/null; then
    echo "[ERROR] Railway CLI가 설치되어 있지 않습니다."
    echo "        설치: npm i -g @railway/cli"
    echo ""
    echo "Railway 대신 Render를 쓰려면:"
    echo "  1. https://render.com 에서 New Web Service"
    echo "  2. GitHub 레포 연결"
    echo "  3. Root Directory: backend"
    echo "  4. Build Command: pip install -r requirements.txt"
    echo "  5. Start Command: uvicorn main:app --host 0.0.0.0 --port \$PORT"
    echo "  6. 환경변수 설정 (.env.example 참고)"
    exit 1
fi

echo "[1/2] Railway에 배포 중..."
railway up

echo ""
echo "[2/2] 배포 완료!"
echo ""
echo "배포 URL 확인: railway open"
echo ""
echo "⚠️  환경변수 설정 확인:"
echo "    railway variables set GEMINI_API_KEY=..."
echo "    railway variables set GOOGLE_API_KEY=..."
echo "    railway variables set GOOGLE_CSE_ID=..."
echo "    railway variables set APP_AUTH_TOKEN=..."
