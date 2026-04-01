# 后端服务

`backend/` 是项目的 Flask + PostgreSQL 后端，当前分支已经不只是 GTFS 基础查询接口，而是覆盖了静态数据导入、实时采集、准点率分析、换乘/可达性分析、用户认证、通知订阅、审计日志和管理员运维接口的一套完整服务。

## 当前完成情况

### 已实现能力

| 模块 | 状态 | 说明 |
|------|------|------|
| GTFS 静态数据导入 | 已完成 | 支持 ZIP/目录导入，按 `region` 隔离数据 |
| 基础查询 API | 已完成 | 地区、机构、线路、站点、班次、时刻表、轨迹、统计 |
| 实时数据 API | 已完成 | 车辆位置、历史轨迹、延误汇总、手动同步 |
| 准点率 API | 已完成 | 概览、线路、站点、小时分布、趋势、明细时刻表、配置刷新 |
| 用户体系 | 已完成 | 登录、注册、登出、当前用户、用户管理 |
| 收藏 / 订阅 / 通知 | 已完成 | 收藏线路站点、订阅线路告警、站内通知、公告 |
| 审计与管理 | 已完成 | 操作审计、数据库统计、第三方 API 健康、数据时效性 |
| 出行分析 | 已完成 | 换乘规划、站点可达性分析 |

### 地区支持

| 地区 | 静态数据 | 实时采集 | 前端主流程 |
|------|----------|----------|------------|
| `sf` | 支持 | 支持 | 支持 |
| `sydney` | 支持 | 支持 | 支持 |
| `nyc` | 预留/部分接入 | 预留/部分接入 | 当前前端未开放 |

## 目录结构

```text
backend/
├── api/
│   └── app.py                    # Flask 主应用，所有 API 路由
├── auth/
│   ├── routes.py                 # 登录、注册、登出、当前用户
│   ├── models.py                 # 用户模型、密码哈希、内存 token、默认 admin 初始化
│   └── user_schema.sql           # users 基础表结构
├── business_logic/
│   ├── punctuality_calculator.py # 准点率计算
│   ├── reachability.py           # 可达性分析
│   ├── speed_calculator.py       # 车辆速度计算
│   └── transfer_planner.py       # 换乘规划
├── core/
│   ├── audit.py                  # 审计日志记录
│   ├── config.py                 # 配置加载，优先级：环境变量 > config.local.json > config.json
│   ├── db.py                     # PostgreSQL 连接池和查询封装
│   └── route_mappings.py         # 线路属性映射
├── data_acquisition/
│   ├── gtfs_importer.py          # GTFS 静态数据导入器
│   ├── gtfs_data_fetcher.py      # 511 SF Bay 数据获取
│   ├── mta_data_fetcher.py       # 纽约 MTA 数据获取预留
│   └── tfnsw_data_fetcher.py     # TfNSW 数据获取
├── database/
│   ├── schema.sql                # GTFS 主表
│   ├── punctuality_schema.sql    # 准点率表与配置表
│   ├── admin_schema.sql          # API 调用日志、数据导入日志
│   ├── favorites_schema.sql      # 收藏表
│   ├── notification_schema.sql   # 订阅与通知表
│   ├── audit_schema.sql          # 审计日志表
│   └── user_migration.sql        # users 表角色/状态字段迁移
├── scripts/
│   ├── start_punctuality_service.py      # 准点率采集服务启动脚本
│   ├── generate_realtime_data_simple.py  # 实时数据测试样本
│   ├── generate_vehicle_history.py       # 历史轨迹测试数据
│   ├── generate_sample_punctuality_data.py
│   └── example_usage.py
├── services/
│   ├── punctuality_service.py    # 实时采集、重试、降级、入库
│   └── mock_data_generator.py    # 模拟数据生成
├── tests/                        # 脚本式测试
├── config.example.json
└── requirements.txt
```

## 依赖安装

```bash
cd backend
pip3 install -r requirements.txt
```

## 配置

复制模板：

```bash
cp config.example.json config.json
```

配置优先级：

1. 环境变量
2. `config.local.json`
3. `config.json`

支持的环境变量：

| 地区 | 环境变量 |
|------|----------|
| 旧金山湾区 | `SF_511_API_KEY` |
| 纽约 | `MTA_API_KEY` |
| 悉尼 | `TFNSW_API_KEY` |

`config.example.json` 当前包含两类配置：

- `api_keys`
- `punctuality`
  - `fallback_to_mock`
  - `collection_interval_minutes`
  - `retry_attempts`
  - `retry_delay_seconds`

## 数据库初始化

首次初始化建议按下面顺序执行：

```bash
createdb gtfs_db

psql gtfs_db -f database/schema.sql
psql gtfs_db -f auth/user_schema.sql
psql gtfs_db -f database/user_migration.sql
psql gtfs_db -f database/punctuality_schema.sql
psql gtfs_db -f database/admin_schema.sql
psql gtfs_db -f database/favorites_schema.sql
psql gtfs_db -f database/notification_schema.sql
psql gtfs_db -f database/audit_schema.sql
```

说明：

- `schema.sql` 负责 GTFS 主表和 `regions`
- `user_schema.sql` 创建基础 `users` 表
- `user_migration.sql` 补充 `role`、`is_active`
- 其余 schema 负责准点率、管理、收藏、通知、审计扩展能力

## GTFS 数据导入

### 常用导入命令

```bash
# 旧金山湾区
python3 data_acquisition/gtfs_importer.py \
  --zip ../gtfs_data/gtfs_SF_20251119.zip \
  --region sf \
  --clean

# 悉尼
python3 data_acquisition/gtfs_importer.py \
  --zip ../gtfs_data/gtfs_sydney.zip \
  --region sydney \
  --clean
```

### 导入器特性

- 按表依赖顺序导入，避免外键冲突
- 支持 `--zip` 和 `--dir`
- 支持按 `region` 清理，不会直接清空整个表
- 使用批量写入优化导入性能
- 自动忽略 CSV 中数据库不存在的列，兼容不同地区扩展字段

## 启动方式

### 直接启动后端

```bash
cd backend
PORT=5001 python3 -m api.app
```

默认 Flask 代码端口是 `5000`，但项目约定和前端代理使用 `5001`，开发时建议显式传入 `PORT=5001`。

### 使用根目录脚本启动整套服务

```bash
cd ..
./start.sh start
```

## 准点率采集服务

准点率服务独立于 Flask API 进程运行，负责：

- 拉取 GTFS-Realtime 车辆和 trip update
- 记录第三方 API 调用健康度
- 计算准点率并写入数据库
- 在真实 API 失败时按配置降级到模拟数据

启动示例：

```bash
python3 scripts/start_punctuality_service.py --region sf
python3 scripts/start_punctuality_service.py --region sydney
```

服务特性：

- 支持多地区 fetcher 映射
- 支持重试
- 支持模拟数据回退
- 支持从数据库读取准点率配置
- 支持记录 API 延迟、状态码和错误信息

## API 概览

当前 `app.py` 中已实现 60+ 个接口，主要分组如下。

### 基础数据

- `GET /api/health`
- `GET /api/regions`
- `GET /api/agencies`
- `GET /api/agencies/<agency_id>`
- `GET /api/stats`

### 线路、站点、班次、轨迹

- `GET /api/routes`
- `GET /api/routes/<route_id>`
- `GET /api/routes/<route_id>/directions`
- `GET /api/routes/<route_id>/stops`
- `GET /api/routes/schedule-summary`
- `GET /api/routes/<route_id>/schedule-analysis`
- `GET /api/routes/<route_id>/shapes`
- `GET /api/stops`
- `GET /api/stops/<stop_id>`
- `GET /api/stops/<stop_id>/routes`
- `GET /api/stops/frequency`
- `GET /api/trips`
- `GET /api/trips/<trip_id>`
- `GET /api/trips/<trip_id>/stop_times`
- `GET /api/shapes/<shape_id>`
- `GET /api/calendar`

### 实时与回放

- `GET /api/realtime/vehicles`
- `GET /api/realtime/vehicles/dates`
- `GET /api/realtime/vehicles/history`
- `POST /api/realtime/vehicles/sync`
- `GET /api/realtime/delays`
- `GET /api/realtime/summary`

### 准点率

- `GET /api/punctuality/routes`
- `GET /api/punctuality/stops`
- `GET /api/punctuality/overview`
- `GET /api/punctuality/hourly`
- `GET /api/punctuality/config`
- `PUT /api/punctuality/config`
- `POST /api/punctuality/refresh`
- `GET /api/punctuality/routes/<route_id>/timetable`
- `GET /api/punctuality/stops/<stop_id>/timetable`
- `GET /api/punctuality/trends`
- `POST /api/punctuality/collect`

### 用户、收藏、通知

- `POST /api/auth/login`
- `POST /api/auth/register`
- `POST /api/auth/logout`
- `GET /api/auth/me`
- `GET /api/favorites`
- `POST /api/favorites`
- `DELETE /api/favorites`
- `GET /api/subscriptions`
- `POST /api/subscriptions`
- `DELETE /api/subscriptions`
- `GET /api/subscriptions/check`
- `GET /api/notifications`
- `GET /api/notifications/unread-count`
- `PATCH /api/notifications/read`
- `POST /api/notifications/announcement`
- `POST /api/notifications/check-punctuality`

### 管理与审计

- `GET /api/admin/db-stats`
- `GET /api/admin/api-health`
- `GET /api/admin/data-freshness`
- `POST /api/admin/log-api-call`
- `GET /api/admin/audit-logs`
- `GET /api/users`
- `POST /api/users`
- `PATCH /api/users/<user_id>`
- `DELETE /api/users/<user_id>`
- `GET /api/users/<user_id>/password`
- `PUT /api/users/<user_id>/password`
- `POST /api/audit/track`

### 分析工具

- `GET /api/planner/transfer`
- `GET /api/analysis/reachability`

## 认证说明

- 登录成功后返回内存 token
- token 由 `auth/models.py` 中的 `_token_store` 保存
- 后端重启后 token 会失效
- 当 `users` 表为空时，会自动初始化默认管理员 `admin / admin`

## 核心表

### GTFS 主表

`regions`、`agency`、`routes`、`route_attributes`、`directions`、`stops`、`calendar`、`calendar_dates`、`shapes`、`trips`、`stop_times`、`fare_attributes`、`fare_rules`、`feed_info`

### 扩展表

`users`、`user_favorites`、`user_subscriptions`、`notifications`、`audit_logs`、`api_call_logs`、`data_update_logs`、准点率相关统计表与配置表

## 测试

仓库当前使用脚本式测试：

```bash
cd backend
python3 tests/test_api_quick.py
python3 tests/test_punctuality.py
python3 tests/check_db.py
python3 tests/check_data_detail.py
```

运行前请先启动 PostgreSQL 和 API 服务。

## 当前限制

- token 为内存态，不适合生产环境长期会话
- `nyc` 能力仍处于预留/部分接入状态
- 准点率采集依赖第三方实时 API，可按配置降级到模拟数据
- 项目启动脚本默认按 macOS + Homebrew 的 PostgreSQL 16 路径处理

## 相关文档

- [../README.md](../README.md)
- [docs/API_DOCUMENTATION.md](./docs/API_DOCUMENTATION.md)
- [docs/README_SETUP.md](./docs/README_SETUP.md)
