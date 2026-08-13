#!/bin/bash
# ============================================================
# IALMD 健康检查脚本 — 由 crontab 每 5 分钟调用
# ============================================================

API_URL="http://127.0.0.1:8002/api/health"
LOG="/opt/ialmd/logs/backend/healthcheck.log"

# 检查 API
API_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL" 2>/dev/null)

if [ "$API_STATUS" != "200" ]; then
    echo "[$(date)] WARN: API health check failed (HTTP $API_STATUS), restarting..."
    sudo systemctl restart ialmd-backend
    sleep 5
    API_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL" 2>/dev/null)
    if [ "$API_STATUS" != "200" ]; then
        echo "[$(date)] CRITICAL: API still down after restart!"
    else
        echo "[$(date)] OK: API recovered after restart"
    fi
fi

# 检查磁盘
DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | tr -d '%')
if [ "$DISK_USAGE" -gt 85 ]; then
    echo "[$(date)] WARN: Disk usage ${DISK_USAGE}%"
fi

# 检查内存
MEM_AVAIL=$(free -m | awk 'NR==2 {print $4}')
if [ "$MEM_AVAIL" -lt 200 ]; then
    echo "[$(date)] WARN: Low memory ${MEM_AVAIL}MB available"
fi
