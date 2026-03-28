# GTFS 公交数据分析系统

基于 GTFS (General Transit Feed Specification) 规范的多地区公交数据获取、存储、分析和可视化平台，支持旧金山湾区和悉尼公交两个地区的实时数据监控与准点率分析。

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3 + Flask 3.0 + PostgreSQL 16 |
| 前端 | Vue 3 (Composition API) + Vite + Element Plus + Pinia |
| 数据可视化 | ECharts + Leaflet |

## 功能概览

- **多地区支持**：旧金山湾区（SF）、悉尼（Sydney），统一架构管理
- **GTFS 静态数据**：线路、站点、班次、时刻表完整导入与查询
- **实时数据监控**：车辆位置实时追踪，速度计算（Haversine 公式）
- **准点率分析**：线路/站点维度准点率统计，支持按时段聚合
- **地图可视化**：Leaflet 地图展示站点与线路轨迹
- **用户系统**：登录/注册/收藏，管理员后台
- **数据降级**：API 不可用时自动切换模拟数据，对用户透明

## 快速启动

### 环境要求

- Python 3.8+
- Node.js 16+
- PostgreSQL 16+

### 首次配置

```bash
# 1. 安装后端依赖
pip3 install -r backend/requirements.txt

# 2. 安装前端依赖
cd frontend && npm install && cd ..

# 3. 初始化数据库
createdb gtfs_db
psql gtfs_db -f backend/database/schema.sql
psql gtfs_db -f backend/database/punctuality_schema.sql

# 4. 导入 GTFS 静态数据
python3 backend/data_acquisition/gtfs_importer.py \
  --zip gtfs_data/gtfs_SF_20251119.zip \
  --region sf \
  --clean
```

### 日常启动

```bash
./start.sh start    # 启动前后端（自动检查 PostgreSQL）
./start.sh stop     # 停止服务
./start.sh status   # 查看状态
```

服务启动后：
- 后端 API：http://localhost:5001
- 前端应用：http://localhost:5173

### 准点率数据收集（可选）

```bash
# 需要配置 backend/config.json 中的 API Key
python3 backend/scripts/start_punctuality_service.py --region sf &
python3 backend/scripts/start_punctuality_service.py --region sydney &
```

## 项目结构

```
gtfs_new/
├── backend/                    # 后端服务（详见 backend/README.md）
│   ├── api/                    # Flask 路由
│   ├── auth/                   # 用户认证
│   ├── core/                   # 数据库连接、配置管理
│   ├── business_logic/         # 速度计算、准点率计算
│   ├── data_acquisition/       # GTFS 数据获取与导入
│   ├── services/               # 准点率收集服务
│   ├── database/               # SQL 表结构
│   ├── scripts/                # 工具脚本
│   ├── config.example.json     # 配置模板（提交到 Git）
│   └── requirements.txt
├── frontend/                   # 前端应用（详见 frontend/README.md）
│   └── src/
│       ├── api/                # Axios 请求封装
│       ├── views/              # 页面组件
│       ├── components/         # 通用组件
│       └── stores/             # Pinia 状态管理
├── gtfs_data/                  # GTFS ZIP 数据文件（不提交 Git）
├── start.sh                    # 一键启动脚本
└── README.md
```

## API Key 配置

在 `backend/config.json` 中配置（不提交 Git，参考 `config.example.json`）：

| 地区 | 数据源 | 环境变量 |
|------|--------|----------|
| 旧金山湾区 | 511 SF Bay API | `SF_511_API_KEY` |
| 悉尼 | TfNSW Open Data | `TFNSW_API_KEY` |

## 数据库

- 数据库名：`gtfs_db`（PostgreSQL 16）
- 所有主表含 `region` 字段，支持多地区数据隔离
- 核心表：`routes`、`stops`、`trips`、`stop_times`、`shapes`、`punctuality_records`、`users`

## 故障排查

```bash
# PostgreSQL 未启动
brew services restart postgresql@16
tail -f /opt/homebrew/var/log/postgresql@16.log

# 后端端口占用
lsof -i :5001
tail -f /tmp/gtfs_backend.log

# 前端依赖问题
rm -rf frontend/node_modules && cd frontend && npm install
```

## 开发规范

- Python：PEP 8，类型提示，中文注释
- Vue：Composition API + `<script setup>`，中文注释
- Git：Conventional Commits（`feat:`、`fix:`、`docs:` 等）
- 不提交：`config.json`、`gtfs_data/`、`.venv/`

## 许可证

本项目仅供学习和研究使用。
