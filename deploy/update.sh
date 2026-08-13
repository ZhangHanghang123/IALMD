#!/bin/bash
# ============================================================
# IALMD 代码更新脚本 — 拉取最新代码并重新部署
# 使用方式: bash deploy/update.sh
# ============================================================

set -e

IALMD_HOME="/opt/ialmd"
BACKEND_DIR="$IALMD_HOME/backend"
FRONTEND_DIR="$IALMD_HOME/frontend"

echo "=========================================="
echo "  IALMD 代码更新"
echo "=========================================="

# 1. 更新后端依赖
echo "[1/4] 更新 Python 依赖..."
cd "$BACKEND_DIR"
source venv/bin/activate
pip install -r requirements.txt -q
echo "  ✅ 依赖已更新"

# 2. 重启后端
echo "[2/4] 重启后端服务..."
sudo systemctl restart ialmd-backend
sleep 2
systemctl is-active --quiet ialmd-backend && echo "  ✅ 后端已重启" || {
    echo "  ❌ 后端启动失败"
    sudo journalctl -u ialmd-backend --no-pager -n 20
    exit 1
}

# 3. 构建前端
echo "[3/4] 构建前端..."
cd "$FRONTEND_DIR"
npm install --silent 2>/dev/null
npm run build 2>/dev/null
if [ -d "dist" ]; then
    sudo cp -r dist/* /var/www/ialmd/
    sudo chown -R www-data:www-data /var/www/ialmd
    echo "  ✅ 前端已更新"
else
    echo "  ⚠️  前端构建失败"
fi

# 4. 验证
echo "[4/4] 验证..."
sleep 2
STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8002/api/health 2>/dev/null)
if [ "$STATUS" == "200" ]; then
    echo "  ✅ 更新成功! API 正常"
else
    echo "  ❌ API 返回 $STATUS"
    echo "  查看日志: sudo journalctl -u ialmd-backend -f"
fi

echo ""
echo "=========================================="
echo "  ✅ 更新完成"
echo "=========================================="
