# 保险经营智能分析平台（IALMD）

AI 驱动的保险业经营分析智能平台，基于银行版 ALMD 架构改造，覆盖偿付能力分析、同业对比、智能对话等核心场景。

## 技术栈

- 后端：FastAPI + SQLAlchemy + MySQL 8.0（端口 8002）
- 前端：React 18 + TypeScript + Ant Design 5 + Vite（端口 5174）
- 缓存：Redis
- 大模型：DeepSeek（SSE 流式对话）

## 目录结构

```
IALMD/
├── backend/          # FastAPI 后端
│   ├── app/          # 应用代码（models/routers/schemas/services）
│   ├── .env          # 本地配置（gitignore）
│   ├── .env.example  # 配置模板
│   ├── seed_data.py  # 种子数据（保险公司+保险指标+管理员）
│   └── sql/init.sql  # 建表 SQL
├── frontend/         # React 前端
├── deploy/           # 生产部署脚本
├── start.sh / stop.sh  # 本地启停脚本
└── docs/             # 文档
```

## 与 ALMD 的核心差异

| 维度 | 银行版 ALMD | 保险版 IALMD |
|------|------------|-------------|
| 核心监管 | 资本充足率 + 流动性 | 偿付能力充足率（偿二代/C-ROSS） |
| 核心指标 | 净息差、不良率 | 综合偿付能力充足率、综合成本率、新业务价值 |
| 核心功能 | 流动性压力测试 | 偿付能力分析 |
| 报告类型 | 年报等 10 类 | +偿付能力报告、精算报告、保费公告 |

## 本地开发

### 1. 环境准备

- MySQL 8.0（127.0.0.1:3306，root/root）
- Python 3.11+（建议复用 ALMD 的 .venv）
- Node 18+

### 2. 初始化

```bash
# 创建数据库
mysql -uroot -proot -e "CREATE DATABASE IALMD DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_bin"

# 配置环境变量
cd backend && cp .env.example .env  # 修改端口为 8002

# 建表 + 初始化种子数据
python -c "from app.database import Base, engine; import app.models; Base.metadata.create_all(bind=engine)"
python seed_data.py

# 安装前端依赖
cd ../frontend && npm install
```

### 3. 启动

```bash
bash start.sh all
```

- 前端：http://localhost:5174
- 后端：http://localhost:8002
- API 文档：http://localhost:8002/api/docs
- 登录：admin / admin123

## 服务器部署（与 ALMD 并存）

```bash
# 1. 安装环境（创建 ialmd 用户、MySQL、Redis、Nginx、Node）
sudo bash deploy/install_env.sh

# 2. 创建数据库
sudo mysql -uroot -p
> CREATE DATABASE IALMD DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_bin;
> CREATE USER 'ialmd'@'localhost' IDENTIFIED BY '你的密码';
> GRANT ALL ON IALMD.* TO 'ialmd'@'localhost';

# 3. 上传代码并部署
sudo bash deploy/deploy_app.sh
```

服务器路径：
- 项目：/opt/ialmd
- 前端：/var/www/ialmd（Nginx 托管）
- 后端：systemd 服务 ialmd-backend（端口 8002）
- 与 ALMD（/opt/almd，端口 8000）完全隔离并存
