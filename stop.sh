#!/bin/bash
# ==============================================
#  IALMD — 双环境停止脚本
# ==============================================
killport() {
  local port=$1 label=$2
  if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    local pid=$(netstat -ano 2>/dev/null | grep ":$port " | grep LISTENING | awk '{print $5}' | head -1)
    [ -n "$pid" ] && taskkill -F -PID "$pid" 2>/dev/null && echo "[OK] Stopped $label (:${port})" || echo "[--] $label not running"
  else
    local pid=$(lsof -ti:$port 2>/dev/null)
    [ -n "$pid" ] && kill -9 $pid 2>/dev/null && echo "[OK] Stopped $label (:${port})" || echo "[--] $label not running"
  fi
}

killport 8002 "Backend"
killport 5174 "Frontend"
echo "Done."
