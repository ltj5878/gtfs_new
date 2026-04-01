# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This project is a GTFS transit analysis system with a Python/Flask backend and JavaScript frontend. Do NOT assume Java/Spring Boot unless explicitly on a Java branch.

## Workflow Rules section

When exploring the codebase, limit exploration to 4-5 minutes max before presenting a concrete plan or asking a specific question. Do not spend extended time reading files without producing output.


## Common Pitfalls section

The backend API uses axios interceptors that already unwrap responses. Do not double-unwrap with `response.data.data`. Check interceptor config before editing API calls.

## Testing & Verification section

After making frontend/backend changes, verify the feature works by checking the running service (start if needed) before marking complete. Don't just edit files and stop.

## 项目概述

GTFS 公交数据分析系统 - 基于 GTFS (General Transit Feed Specification) 规范的多地区公交数据获取、存储、分析和可视化平台。支持旧金山湾区(sf)、纽约地铁(nyc)、悉尼公交(sydney) 三个地区的实时数据监控和准点率分析。

## 技术栈

- **后端**: Python 3 + Flask 3.0 + PostgreSQL 16 + psycopg2 连接池
- **前端**: Vue 3 (Composition API) + Vite + Element Plus + Pinia + ECharts + Leaflet
- **国际化**: vue-i18n（zh-CN / en）
- **端口**: 后端 5001, 前端 5173

## 核心命令

```bash
# 启动/停止
./start.sh start | stop | status

# 数据库初始化
psql gtfs_db -f backend/database/schema.sql
psql gtfs_db -f backend/database/punctuality_schema.sql

# GTFS 数据导入（必须指定 --region）
python3 backend/data_acquisition/gtfs_importer.py --zip gtfs_data/gtfs_SF_20251119.zip --region sf --clean

# 车辆历史数据生成（用于回放页面）
python3 backend/scripts/generate_vehicle_history.py --region sf --date 2025-03-30 --trips-per-hour 20

# 依赖安装
pip3 install -r backend/requirements.txt
cd frontend && npm install

# 后端测试
python3 backend/tests/test_api_quick.py

# 准点率数据收集（需要 API Key 环境变量）
SF_511_API_KEY=xxx python3 backend/scripts/start_punctuality_service.py --region sf &
```

## 架构要点

### 多地区数据隔离
所有数据库主表包含 `region` 字段（sf/nyc/sydney）。前端 `regionStore` 管理当前选中地区，`api/index.js` 的 Axios 拦截器自动附加 `?region=` 参数，后端所有查询自动过滤。新增 API 或查询时必须考虑 region 过滤。

### 后端架构（backend/）
- **单文件路由**: 所有 API 路由定义在 `api/app.py`（~2600行，~60+ 路由），没有使用 Blueprint
- **数据库连接**: `core/db.py` 管理 psycopg2 连接池，所有 SQL 为原生 SQL（无 ORM）
- **认证**: `auth/routes.py` + `auth/models.py`，基于 session 的登录/注册
- **数据库 schema**: `database/` 下有多个 SQL 文件（schema.sql 是主表，其余为功能模块的扩展表）

### 前端架构（frontend/src/）
- **路由**: `router/index.js` 定义所有页面路由
- **状态管理**: `stores/` 下每个功能模块一个 Pinia store（regionStore 是核心）
- **API 封装**: `api/` 下每个功能模块一个文件，`api/index.js` 是 Axios 实例（含 region 拦截器）
- **国际化**: `i18n/zh-CN.js` 和 `i18n/en.js`，新增 UI 文本需同时更新两个文件
- **主题**: `themeStore` 管理深色/浅色模式切换
- **页面组件**: `views/` 下每个页面一个 Vue 文件，使用 `<script setup>` + Composition API

### 关键功能模块
- **准点率分析**: 对比实时到站时间与计划时刻表，支持按线路/站点/时段聚合。阈值可配置
- **车辆回放**: `VehiclePlayback.vue` + `generate_vehicle_history.py`，基于 `realtime_vehicle_positions` 表模拟历史轨迹
- **通知系统**: 订阅 + 通知 + 公告，`NotificationBell.vue` 组件
- **收藏功能**: 线路/站点收藏，`favoriteStore` + `favorites_schema.sql`
- **审计日志**: API 调用记录，`audit_schema.sql` + `AuditLog.vue`
- **管理后台**: `AdminDashboard.vue` + `UserManagement.vue`，数据库统计/API 健康/用户管理

## 编码规范

- **语言**: 所有代码注释必须使用中文
- **Python**: PEP 8，类型提示，docstring，snake_case 函数/UPPER_SNAKE_CASE 常量
- **Vue/JS**: Composition API + `<script setup>`，camelCase 变量/PascalCase 组件，Store 文件命名 `xxxStore.js`
- **SQL**: 小写下划线表名，所有表和字段包含中文注释，使用外键约束
- **Git**: Conventional Commits（`feat(api): 添加准点率统计接口`）

## 数据源 API Key

| 地区 | 数据源 | 环境变量 |
|------|--------|----------|
| 旧金山湾区 | 511 SF Bay API | `SF_511_API_KEY` |
| 纽约地铁 | MTA Real-Time Data Feeds | `MTA_API_KEY` |
| 悉尼公交 | TfNSW Open Data | `TFNSW_API_KEY` |

API Key 配置在 `backend/config.json`（不提交 Git，参考 `config.example.json`）。

## 故障排查

```bash
brew services restart postgresql@16          # PostgreSQL 重启
tail -f /opt/homebrew/var/log/postgresql@16.log  # PG 日志
lsof -i :5001                                # 后端端口占用
tail -f /tmp/gtfs_backend.log                # 后端日志
lsof -i :5173                                # 前端端口占用
```
