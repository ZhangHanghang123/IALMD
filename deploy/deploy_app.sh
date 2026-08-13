#!/bin/bash
# ============================================================
# IALMD 应用部署脚本 — 安装后端+前端+数据库+Nginx+systemd
# 前提: install_env.sh 已执行完成, MySQL/Redis 已配置
# 使用方式: sudo bash deploy/deploy_app.sh
# ============================================================

set -e

IALMD_HOME="/opt/ialmd"
BACKEND_DIR="$IALMD_HOME/backend"
FRONTEND_DIR="$IALMD_HOME/frontend"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# 检查是否在 ialmd-deploy 目录下
if [ ! -f "$SCRIPT_DIR/deploy_app.sh" ]; then
    echo "❌ 请在 ialmd-deploy 目录下运行此脚本"
    exit 1
fi

echo "=========================================="
echo "  IALMD 应用部署"
echo "=========================================="
echo ""

# ---------- 1. 检查 MySQL ----------
echo "[1/8] 检查 MySQL..."
if ! systemctl is-active --quiet mysql; then
    echo "❌ MySQL 未运行，请先执行 install_env.sh 和 mysql_secure_installation"
    exit 1
fi

# ---------- 2. 配置 .env ----------
echo "[2/8] 配置后端 .env..."
if [ ! -f "$BACKEND_DIR/.env" ]; then
    if [ -f "$BACKEND_DIR/.env.production" ]; then
        cp "$BACKEND_DIR/.env.production" "$BACKEND_DIR/.env"
        echo "  ⚠️  已从 .env.production 复制为 .env"
        echo "  ⚠️  请编辑 /opt/ialmd/backend/.env 填入实际密码和密钥"
        echo "  ⚠️  填完后重新运行此脚本"
        exit 1
    else
        echo "❌ 未找到 .env 或 .env.production"
        exit 1
    fi
else
    # 检查是否还有占位符
    if grep -q "REPLACE_ME" "$BACKEND_DIR/.env"; then
        echo "  ⚠️  .env 中仍有 [REPLACE_ME] 占位符"
        echo "  ⚠️  请编辑 /opt/ialmd/backend/.env 填入实际值"
        exit 1
    fi
fi
echo "  ✅ .env 配置已就绪"

# ---------- 3. 创建 Python 虚拟环境 ----------
echo "[3/8] 创建 Python 虚拟环境..."
cd "$BACKEND_DIR"
if [ ! -d "venv" ]; then
    python3.11 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
pip install gunicorn uvloop httptools -q
echo "  ✅ Python 依赖已安装"

# ---------- 4. 初始化数据库 ----------
echo "[4/8] 初始化数据库..."
DB_USER=$(grep DATABASE_URL "$BACKEND_DIR/.env" | sed 's/.*\/\/[^:]*:\([^@]*\)@.*/\1/')
DB_PASS=$(grep DATABASE_URL "$BACKEND_DIR/.env" | sed 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/')

# 执行建表脚本
if [ -f "$BACKEND_DIR/sql/init.sql" ]; then
    mysql -u "$DB_USER" -p"$DB_PASS" IALMD < "$BACKEND_DIR/sql/init.sql" 2>/dev/null && \
        echo "  ✅ init.sql 已执行" || echo "  ⚠️  init.sql 执行跳过（可能已执行）"
fi

# 执行本体扩展脚本
if [ -f "$IALMD_HOME/scripts/ontology_schema.sql" ]; then
    mysql -u "$DB_USER" -p"$DB_PASS" IALMD < "$IALMD_HOME/scripts/ontology_schema.sql" 2>/dev/null && \
        echo "  ✅ ontology_schema.sql 已执行" || echo "  ⚠️  ontology_schema.sql 执行跳过"
fi

# 导入种子数据
if [ -f "$BACKEND_DIR/seed_data.py" ]; then
    python "$BACKEND_DIR/seed_data.py" 2>/dev/null && \
        echo "  ✅ 种子数据已导入" || echo "  ⚠️  种子数据导入跳过"
fi

# ---------- 5. 验证后端启动 ----------
echo "[5/8] 验证后端..."
python -c "from app.main import app; print('  ✅ 后端模块导入成功')" || {
    echo "  ❌ 后端模块导入失败"
    exit 1
}

# ---------- 6. 构建前端 ----------
echo "[6/8] 构建前端..."
cd "$FRONTEND_DIR"
npm install --silent 2>/dev/null
npm run build 2>/dev/null
if [ -d "dist" ]; then
    mkdir -p /var/www/ialmd
    cp -r dist/* /var/www/ialmd/
    chown -R www-data:www-data /var/www/ialmd
    echo "  ✅ 前端已构建并部署"
else
    echo "  ⚠️  前端构建失败，请手动检查"
fi

# ---------- 7. 配置 Nginx ----------
echo "[7/8] 配置 Nginx..."
NGINX_CONF="$SCRIPT_DIR/nginx-ialmd.conf"
if [ -f "$NGINX_CONF" ]; then
    cp "$NGINX_CONF" /etc/nginx/sites-available/ialmd
    ln -sf /etc/nginx/sites-available/ialmd /etc/nginx/sites-enabled/ialmd
    rm -f /etc/nginx/sites-enabled/default
    nginx -t 2>/dev/null && systemctl reload nginx && echo "  ✅ Nginx 已配置" || echo "  ⚠️  Nginx 配置有误，请手动检查"
fi

# ---------- 8. 配置 systemd ----------
echo "[8/8] 配置 systemd 服务..."
SERVICE_FILE="$SCRIPT_DIR/ialmd-backend.service"
if [ -f "$SERVICE_FILE" ]; then
    cp "$SERVICE_FILE" /etc/systemd/system/ialmd-backend.service
    systemctl daemon-reload
    systemctl enable ialmd-backend
    systemctl restart ialmd-backend
    sleep 2
    if systemctl is-active --quiet ialmd-backend; then
        echo "  ✅ 后端服务已启动"
    else
        echo "  ❌ 后端服务启动失败"
        journalctl -u ialmd-backend --no-pager -n 20
        exit 1
    fi
fi

# ---------- 安装备份脚本 ----------
echo ""
echo "安装定时备份脚本..."
if [ -f "$SCRIPT_DIR/backup.sh" ]; then
    cp "$SCRIPT_DIR/backup.sh" "$IALMD_HOME/scripts/"
    chmod +x "$IALMD_HOME/scripts/backup.sh"
    # 添加 crontab
    (crontab -l 2>/dev/null; echo "0 3 * * * /opt/ialmd/scripts/backup.sh >> /opt/ialmd/logs/backend/backup.log 2>&1") | crontab -
    echo "  ✅ 定时备份已设置（每天凌晨 3:00）"
fi

# ---------- 安装健康检查 ----------
if [ -f "$SCRIPT_DIR/healthcheck.sh" ]; then
    cp "$SCRIPT_DIR/healthcheck.sh" "$IALMD_HOME/scripts/"
    chmod +x "$IALMD_HOME/scripts/healthcheck.sh"
    (crontab -l 2>/dev/null; echo "*/5 * * * * /opt/ialmd/scripts/healthcheck.sh >> /opt/ialmd/logs/backend/healthcheck.log 2>&1") | crontab -
    echo "  ✅ 健康检查已设置（每 5 分钟）"
fi

# ---------- 验证 ----------
echo ""
echo "=========================================="
echo "  ✅ 部署完成!"
echo "=========================================="
echo ""

# 获取服务器 IP
SERVER_IP=$(hostname -I | awk '{print $1}')

echo "验证结果:"
echo -n "  后端服务: "
systemctl is-active --quiet ialmd-backend && echo "✅ 运行中" || echo "❌ 未运行"

echo -n "  MySQL:    "
systemctl is-active --quiet mysql && echo "✅ 运行中" || echo "❌ 未运行"

echo -n "  Redis:    "
systemctl is-active --quiet redis-server && echo "✅ 运行中" || echo "❌ 未运行"

echo -n "  Nginx:    "
systemctl is-active --quiet nginx && echo "✅ 运行中" || echo "❌ 未运行"

echo ""
echo -n "  API 健康检查: "
HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8002/api/health 2>/dev/null)
if [ "$HEALTH" == "200" ]; then
    echo "✅ 正常 (HTTP 200)"
else
    echo "⚠️  返回 $HEALTH"
fi

echo -n "  Nginx 代理:   "
PROXY=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1/api/health 2>/dev/null)
if [ "$PROXY" == "200" ]; then
    echo "✅ 正常 (HTTP 200)"
else
    echo "⚠️  返回 $PROXY"
fi

echo ""
echo "访问地址:"
echo "  前端页面: http://$SERVER_IP"
echo "  API 文档: http://$SERVER_IP/api/docs"
echo "  健康检查: http://$SERVER_IP/api/health"
echo ""
echo "常用命令:"
echo "  查看后端日志: sudo journalctl -u ialmd-backend -f"
echo "  重启后端:     sudo systemctl restart ialmd-backend"
echo "  重启 Nginx:   sudo systemctl reload nginx"
echo ""
