#!/bin/bash
# ============================================================
# IALMD 环境一键安装脚本 (Ubuntu 22.04 LTS)
# 使用方式: sudo bash deploy/install_env.sh
# ============================================================

set -e

echo "=========================================="
echo "  IALMD 环境一键安装 (Ubuntu 22.04)"
echo "=========================================="
echo ""

# 检查 root 权限
if [ "$EUID" -ne 0 ]; then
    echo "❌ 请使用 sudo 运行此脚本"
    exit 1
fi

# 检测是否有 ialmd 用户
if ! id "ialmd" &>/dev/null; then
    echo "[0/8] 创建部署用户 ialmd..."
    adduser --disabled-password --gecos "" ialmd
    usermod -aG sudo ialmd
    echo "ialmd ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers
    echo "✅ 用户 ialmd 已创建 (免密 sudo)"
fi

# 1. 系统更新
echo "[1/8] 系统更新..."
apt update -qq && apt upgrade -y -qq

# 2. 基础工具
echo "[2/8] 安装基础工具..."
apt install -y -qq build-essential curl wget git vim unzip \
    software-properties-common apt-transport-https ca-certificates \
    htop tmux net-tools tree fail2ban logrotate

# 3. MySQL 8.0
echo "[3/8] 安装 MySQL 8.0..."
apt install -y -qq mysql-server mysql-client
systemctl start mysql
systemctl enable mysql

# 4. Redis
echo "[4/8] 安装 Redis..."
apt install -y -qq redis-server
systemctl start redis-server
systemctl enable redis-server

# 5. Python 3.11
echo "[5/8] 安装 Python 3.11..."
add-apt-repository ppa:deadsnakes/ppa -y
apt update -qq
apt install -y -qq python3.11 python3.11-venv python3.11-dev

# 6. Node.js 18
echo "[6/8] 安装 Node.js 18..."
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt install -y -qq nodejs
npm config set registry https://registry.npmmirror.com

# 7. Nginx
echo "[7/8] 安装 Nginx..."
apt install -y -qq nginx
systemctl start nginx
systemctl enable nginx

# 8. 目录结构 + 系统优化
echo "[8/8] 创建目录和系统优化..."
mkdir -p /opt/ialmd/{backend,frontend,reports,logs/backend,logs/nginx,backup,scripts}
chown -R ialmd:ialmd /opt/ialmd

# 时区
timedatectl set-timezone Asia/Shanghai

# Swap (如不存在则创建)
if [ ! -f /swapfile ]; then
    echo "  创建 2GB Swap..."
    fallocate -l 2G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
    echo 'vm.swappiness=10' >> /etc/sysctl.conf
    sysctl -p
fi

# 防火墙
ufw default deny incoming 2>/dev/null
ufw default allow outgoing 2>/dev/null
ufw allow 22/tcp 2>/dev/null
ufw allow 80/tcp 2>/dev/null
ufw allow 443/tcp 2>/dev/null
echo "y" | ufw enable 2>/dev/null

# SSH 加固
sed -i 's/#PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
sed -i 's/#MaxAuthTries.*/MaxAuthTries 3/' /etc/ssh/sshd_config
systemctl restart sshd

echo ""
echo "=========================================="
echo "  ✅ 环境安装完成!"
echo "=========================================="
echo ""
echo "版本信息:"
echo "  MySQL:   $(mysql --version)"
echo "  Redis:   $(redis-server --version)"
echo "  Python:  $(python3.11 --version)"
echo "  Node.js: $(node --version)"
echo "  NPM:     $(npm --version)"
echo "  Nginx:   $(nginx -v 2>&1)"
echo ""
echo "=========================================="
echo "  下一步操作:"
echo "=========================================="
echo ""
echo "1. MySQL 安全初始化:"
echo "   sudo mysql_secure_installation"
echo ""
echo "2. 创建数据库和用户:"
echo "   sudo mysql -u root -p"
echo "   > CREATE DATABASE IALMD DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_bin;"
echo "   > CREATE USER 'ialmd_user'@'localhost' IDENTIFIED BY '你的密码';"
echo "   > GRANT ALL ON IALMD.* TO 'ialmd_user'@'localhost';"
echo "   > FLUSH PRIVILEGES;"
echo ""
echo "3. 上传代码包到 /opt/ialmd/"
echo "   scp ialmd-deploy.tar.gz ialmd@服务器IP:/opt/ialmd/"
echo "   cd /opt/ialmd && tar xzf ialmd-deploy.tar.gz"
echo ""
echo "4. 执行部署脚本:"
echo "   sudo bash /opt/ialmd/deploy/deploy_app.sh"
echo ""
