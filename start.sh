#!/bin/bash
# ==============================================
#  IALMD — 双环境启动脚本（Windows Git Bash / Linux 通用）
#  用法: bash start.sh [backend|frontend|all]
# ==============================================
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$ROOT/backend"
FRONTEND_DIR="$ROOT/frontend"
MODE="${1:-all}"

# --- 端口检测与清理 ---
killport() {
  local port=$1
  if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    # Windows Git Bash
    local pid=$(netstat -ano 2>/dev/null | grep ":$port " | grep LISTENING | awk '{print $5}' | head -1)
    [ -n "$pid" ] && taskkill -F -PID "$pid" 2>/dev/null && echo "  [OK] Killed PID $pid on :$port" || true
  else
    # Linux
    local pid=$(lsof -ti:$port 2>/dev/null)
    [ -n "$pid" ] && kill -9 $pid 2>/dev/null && echo "  [OK] Killed PID $pid on :$port" || true
  fi
  sleep 1
}

# --- 后端 ---
start_backend() {
  echo "[BACKEND] Starting on :8002 ..."
  killport 8002

  if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    # Windows: use managed Python
    local PY="C:/Users/zhanghh/.workbuddy/binaries/python/versions/3.13.12/python.exe"
  else
    # Linux: use venv
    cd "$BACKEND_DIR" && source venv/bin/activate
    local PY="python"
  fi

  cd "$BACKEND_DIR"
  "$PY" -m uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload &
  sleep 2
  echo "  [OK] Backend: http://localhost:8002"
}

# --- 前端 ---
start_frontend() {
  echo "[FRONTEND] Starting on :5174 ..."
  killport 5174

  cd "$FRONTEND_DIR"
  if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    local NODE="C:/Users/zhanghh/.workbuddy/binaries/node/versions/22.22.2/node.exe"
  else
    local NODE="node"
  fi

  # 确保依赖已安装
  [ -d node_modules ] || npm install

  # 可以通过环境变量指定后端端口
  export VITE_API_TARGET="${VITE_API_TARGET:-http://127.0.0.1:8002}"
  "$NODE" node_modules/vite/bin/vite.js --port 5174 --host &
  sleep 3
  echo "  [OK] Frontend: http://localhost:5174"
}

# --- 主流程 ---
echo "============================================"
echo "  IALMD — 保险经营智能分析平台"
echo "  OS: $OSTYPE"
echo "============================================"

case "$MODE" in
  backend)   start_backend ;;
  frontend)  start_frontend ;;
  all|*)     start_backend && start_frontend ;;
esac

echo ""
echo "  前端:    http://localhost:5174"
echo "  后端:    http://localhost:8002"
echo "  API文档: http://localhost:8002/api/docs"
echo "  停止:    bash stop.sh"
echo "============================================"
