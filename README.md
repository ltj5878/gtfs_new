# GTFS 公交准点率分析系统

基于 GTFS / GTFS-Realtime 的公交数据分析与可视化平台，当前分支已经从基础的线路查询扩展到“实时监控 + 准点率分析 + 出行工具 + 用户体系 + 运维管理”一整套前后端应用。

本文档以当前仓库代码实现为准，重点说明现在这个分支已经落地的功能，而不是早期规划状态。

## 当前完成情况

### 已落地模块

| 模块 | 当前状态 | 说明 |
|------|----------|------|
| GTFS 静态数据导入 | 已完成 | 支持按 `region` 导入 ZIP/目录数据，自动按表依赖顺序写入 PostgreSQL |
| 基础数据查询 API | 已完成 | 线路、站点、班次、时刻表、轨迹、机构、统计信息等 |
| 实时公交监控 | 已完成 | 车辆位置、延误摘要、实时汇总、历史轨迹回放、手动同步 |
| 准点率分析 | 已完成 | 概览、线路榜单、站点榜单、小时分布、趋势总览、明细时刻表、配置刷新 |
| 地图可视化 | 已完成 | 地图视图、线路轨迹、站点热力图、站点详情地图 |
| 出行分析工具 | 已完成 | 换乘规划、站点可达性分析、线路对比、数据导出 |
| 用户系统 | 已完成 | 登录、注册、登出、角色识别、收藏、通知、订阅 |
| 管理后台 | 已完成 | 运维看板、用户管理、审计日志、公告发布、准点率告警检查 |
| 国际化与主题 | 已完成 | 中英文切换、明暗主题切换 |

### 地区支持状态

| 地区 | 前端可选 | 静态数据导入 | 实时/准点率 | 备注 |
|------|----------|--------------|-------------|------|
| 旧金山湾区 `sf` | 是 | 是 | 是 | 当前主用地区 |
| 悉尼 `sydney` | 是 | 是 | 是 | 当前主用地区 |
| 纽约 `nyc` | 否 | 后端预留 | 后端预留/部分接入 | 代码中保留 MTA 采集与服务入口，前端地区选择已屏蔽 |

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3 + Flask 3 + PostgreSQL 16 |
| 前端 | Vue 3 + Vite + Element Plus + Pinia + Vue Router |
| 可视化 | ECharts + Leaflet + leaflet.heat |
| 导出 | XLSX + jsPDF |

## 功能清单

### 1. 基础 GTFS 数据浏览

- 线路列表、线路详情、线路方向、线路站点
- 站点列表、站点详情、经过线路
- 班次列表、班次详情、站点时刻表
- 线路运营时间分析
- 轨迹 `shapes` 查询与地图展示

### 2. 实时监控与历史回放

- 实时车辆位置查询
- 实时延误与汇总统计
- 历史车辆轨迹按日期回放
- 手动同步实时数据
- GPS 速度计算与模拟数据降级

### 3. 准点率分析

- 系统准点率概览
- 线路准点率排行与详情
- 站点准点率排行与详情
- 小时粒度准点率分布
- 趋势总览与多天聚合
- 线路/站点时刻表准点率明细
- 准点率阈值配置、手动刷新、采集服务

### 4. 出行与分析工具

- 我的收藏
- 换乘规划
- 站点可达性分析
- 线路对比分析
- 数据导出
  - 线路
  - 站点
  - 线路准点率
  - 站点准点率
  - 趋势数据
  - 机构数据
  - 收藏数据
  - 公告数据
  - 审计日志（管理员）

### 5. 用户与管理能力

- 用户登录 / 注册 / 登出 / 当前用户信息
- 用户角色区分（普通用户 / 管理员）
- 管理员用户管理
- 通知中心与未读计数
- 线路订阅与准点率告警
- 系统公告发布
- 页面访问与关键操作审计日志
- 运维看板
  - 数据库容量与表占用
  - API 调用健康度
  - 数据时效性
  - 最近错误记录

## 项目结构

```text
gtfs_new/
├── backend/
│   ├── api/                  # Flask API 路由
│   ├── auth/                 # 登录注册、用户模型、用户表结构
│   ├── business_logic/       # 准点率、换乘、可达性、速度计算
│   ├── core/                 # 配置、数据库、审计、线路属性映射
│   ├── data_acquisition/     # GTFS 静态/实时数据获取与导入
│   ├── database/             # 主 schema 与扩展 schema
│   ├── scripts/              # 测试数据生成、服务启动脚本
│   ├── services/             # 准点率采集服务、模拟数据生成
│   └── tests/                # 脚本式测试
├── frontend/
│   ├── src/api/              # Axios 请求封装
│   ├── src/components/       # 通用组件
│   ├── src/router/           # 路由守卫与页面审计
│   ├── src/stores/           # Pinia 状态管理
│   ├── src/views/            # 页面视图
│   └── src/i18n/             # 中英文文案
├── gtfs_data/                # 本地 GTFS ZIP 文件（不提交）
├── start.sh                  # 一键启动前后端
└── README.md
```

## 快速启动

### 环境要求

- Python 3.8+
- Node.js 16+
- PostgreSQL 16+
- macOS + Homebrew（`start.sh` 默认按这个环境处理 PostgreSQL）

### 1. 安装依赖

```bash
pip3 install -r backend/requirements.txt
cd frontend && npm install && cd ..
```

### 2. 配置 API Key

```bash
cp backend/config.example.json backend/config.json
```

支持通过 `backend/config.json` 或环境变量配置：

| 地区 | 环境变量 |
|------|----------|
| 旧金山湾区 | `SF_511_API_KEY` |
| 纽约 | `MTA_API_KEY` |
| 悉尼 | `TFNSW_API_KEY` |

### 3. 初始化数据库

首次初始化建议按下面顺序执行：

```bash
createdb gtfs_db

psql gtfs_db -f backend/database/schema.sql
psql gtfs_db -f backend/auth/user_schema.sql
psql gtfs_db -f backend/database/user_migration.sql
psql gtfs_db -f backend/database/punctuality_schema.sql
psql gtfs_db -f backend/database/admin_schema.sql
psql gtfs_db -f backend/database/favorites_schema.sql
psql gtfs_db -f backend/database/notification_schema.sql
psql gtfs_db -f backend/database/audit_schema.sql
```

### 4. 导入 GTFS 静态数据

```bash
# 旧金山湾区
python3 backend/data_acquisition/gtfs_importer.py \
  --zip gtfs_data/gtfs_SF_20251119.zip \
  --region sf \
  --clean

# 悉尼
python3 backend/data_acquisition/gtfs_importer.py \
  --zip gtfs_data/gtfs_sydney.zip \
  --region sydney \
  --clean
```

### 5. 启动项目

推荐使用根目录脚本：

```bash
./start.sh start
```

常用命令：

```bash
./start.sh stop
./start.sh status
./start.sh restart
```

启动后默认访问地址：

- 前端：http://localhost:5173
- 后端：http://localhost:5001

如果只启动后端，请显式指定 `5001` 端口，和前端代理保持一致：

```bash
cd backend
PORT=5001 python3 -m api.app
```

### 6. 启动准点率采集服务（可选）

```bash
python3 backend/scripts/start_punctuality_service.py --region sf
python3 backend/scripts/start_punctuality_service.py --region sydney
```

## 默认账号与认证说明

- 当 `users` 表为空时，后端会自动创建默认管理员账号：`admin / admin`
- 当前 token 存储在后端内存中，后端重启后登录态会失效
- 前端路由包含登录校验和管理员页面权限校验

## API 概览

当前后端已经提供 60+ 个接口，覆盖以下模块：

- 基础：`/api/health`、`/api/regions`、`/api/stats`
- 线路与站点：`/api/routes`、`/api/stops`、`/api/trips`
- 实时：`/api/realtime/vehicles`、`/api/realtime/summary`、`/api/realtime/vehicles/history`
- 准点率：`/api/punctuality/overview`、`/api/punctuality/routes`、`/api/punctuality/stops`、`/api/punctuality/trends`
- 用户：`/api/auth/*`、`/api/favorites`、`/api/subscriptions`、`/api/notifications`
- 管理：`/api/admin/*`、`/api/users`、`/api/audit/track`
- 分析工具：`/api/planner/transfer`、`/api/analysis/reachability`

更详细接口说明可参考：

- [backend/docs/API_DOCUMENTATION.md](./backend/docs/API_DOCUMENTATION.md)
- [backend/README.md](./backend/README.md)

## 测试与验证

当前仓库主要使用脚本测试：

```bash
cd backend
python3 tests/test_api_quick.py
python3 tests/test_punctuality.py
python3 tests/check_db.py
python3 tests/check_data_detail.py
```

运行这些脚本前，请先启动 PostgreSQL 和后端服务。

## 已实现但需要注意的限制

- `start.sh` 默认依赖 macOS + Homebrew 的 PostgreSQL 16 安装路径
- 纽约 `nyc` 相关后端能力仍属于预留/试验性接入，当前前端不开放选择
- 实时数据依赖外部 API；当接口不可用时，部分链路会降级为模拟数据
- 当前鉴权 token 为内存态，不适合生产环境长期会话

## 开发规范

- Python 使用 4 空格缩进、`snake_case`、新增代码尽量补类型标注
- Vue 使用 Composition API、`<script setup>`、2 空格缩进、单引号、无分号
- 现有项目以中文注释和中文业务文案为主，新代码保持一致
- 不要提交 `backend/config.json`、GTFS ZIP、日志文件、前端构建产物

## 相关文档

- [backend/README.md](./backend/README.md)
- [backend/docs/README_SETUP.md](./backend/docs/README_SETUP.md)
- [backend/docs/API_DOCUMENTATION.md](./backend/docs/API_DOCUMENTATION.md)

## 许可证

本项目仅供学习、课程研究与原型验证使用。
