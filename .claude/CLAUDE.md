# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

GTFS 公交数据分析系统 - 基于 GTFS (General Transit Feed Specification) 规范的多地区公交数据获取、存储、分析和可视化平台。支持旧金山湾区、纽约地铁、悉尼公交三个地区的实时数据监控和准点率分析。

## 技术栈

**后端**: Python 3 + Flask 3.0 + PostgreSQL 16
**前端**: Vue 3 (Composition API) + Vite + Element Plus + Pinia
**端口**: 后端 5001, 前端 5173

## 核心命令

### 启动/停止服务
```bash
./start.sh start    # 启动前后端（自动检查 PostgreSQL）
./start.sh stop     # 停止服务
./start.sh status   # 查看状态
```

### 数据导入
```bash
# 导入 GTFS 静态数据（支持多地区）
python3 backend/data_acquisition/gtfs_importer.py \
  --zip gtfs_data/gtfs_SF_20251119.zip \
  --region sf \
  --clean

# 其他地区
--region nyc     # 纽约地铁
--region sydney  # 悉尼公交
```

### 数据库操作
```bash
# 初始化数据库表结构
psql gtfs_db -f backend/database/schema.sql

# 初始化准点率表
psql gtfs_db -f backend/database/punctuality_schema.sql

# 检查数据库连接
psql gtfs_db -c "SELECT COUNT(*) FROM routes;"
```

### 开发环境
```bash
# 后端依赖安装
pip3 install -r backend/requirements.txt

# 前端依赖安装
cd frontend && npm install

# 运行后端测试
python3 backend/tests/test_api_quick.py
```

### 准点率数据收集（可选）
```bash
# 需要设置对应地区的 API Key 环境变量
SF_511_API_KEY=xxx python3 backend/scripts/start_punctuality_service.py --region sf &
MTA_API_KEY=xxx python3 backend/scripts/start_punctuality_service.py --region nyc &
TFNSW_API_KEY=xxx python3 backend/scripts/start_punctuality_service.py --region sydney &
```

## 项目架构

### 后端模块结构（backend/）

```
api/
  app.py                    # Flask 主应用，所有 API 路由定义
auth/
  routes.py                 # 用户认证路由（登录/注册/登出）
  models.py                 # 用户模型和默认用户初始化
core/
  db.py                     # PostgreSQL 连接池管理（psycopg2）
  route_mappings.py         # 线路属性映射和富化逻辑
business_logic/
  speed_calculator.py       # 车辆速度计算（Haversine 公式）
  punctuality_calculator.py # 准点率计算逻辑
data_acquisition/
  gtfs_data_fetcher.py      # 511 SF Bay API 数据获取
  mta_data_fetcher.py       # 纽约 MTA API 数据获取
  tfnsw_data_fetcher.py     # 悉尼 TfNSW API 数据获取
  gtfs_importer.py          # GTFS ZIP 导入工具（支持多地区）
services/
  punctuality_service.py    # 准点率数据收集服务
database/
  schema.sql                # GTFS 主表结构（PostgreSQL）
  punctuality_schema.sql    # 准点率表结构
scripts/
  start_punctuality_service.py  # 准点率服务启动脚本
  generate_sample_punctuality_data.py  # 生成测试数据
```

### 前端模块结构（frontend/src/）

```
api/
  index.js                  # Axios 实例配置，自动附加 region 参数
  routes.js, stops.js, ...  # 各模块 API 封装
stores/
  regionStore.js            # 地区选择状态管理（Pinia）
  routeStore.js, stopStore.js, ...
components/
  RegionSelector.vue        # 地区切换组件
  RouteCard.vue, StopCard.vue, ...
views/
  Home.vue                  # 首页（数据统计）
  Routes.vue, Stops.vue     # 线路/站点列表
  RouteDetail.vue, StopDetail.vue
  Punctuality.vue           # 准点率分析页面
```

### 数据库设计要点

**多地区支持**: 所有主表包含 `region` 字段（sf/nyc/sydney），通过 `regions` 配置表管理地区元数据。

**GTFS 标准表**: agency, routes, stops, trips, stop_times, calendar, calendar_dates, shapes, fare_*

**扩展表**:
- route_attributes（SF Muni 线路属性）
- punctuality_records（准点率记录）
- users（用户认证）

**关键索引**:
- routes(region, route_id)
- stops(region, stop_id)
- trips(region, trip_id)
- stop_times(trip_id, stop_sequence)

## API 接口规范

所有接口支持 `?region=sf|nyc|sydney` 参数过滤地区数据。

**核心接口**:
- GET /api/health - 健康检查
- GET /api/stats?region=sf - 数据统计
- GET /api/regions - 地区列表
- GET /api/routes, /api/routes/{id} - 线路查询
- GET /api/stops, /api/stops/{id} - 站点查询
- GET /api/trips/{id}/stop_times - 班次时刻表
- GET /api/realtime/vehicles - 实时车辆位置
- GET /api/punctuality/routes - 线路准点率
- POST /api/auth/login - 用户登录

## 编码规范

### Python
- 使用类型提示（typing 模块）
- 遵循 PEP 8
- 所有注释使用中文
- 函数使用 docstring 说明
- 命名：类 PascalCase，函数 snake_case，常量 UPPER_SNAKE_CASE

### Vue3/JavaScript
- 使用 Composition API + `<script setup>`
- 组件名 PascalCase，文件名同组件名
- 变量/函数 camelCase，常量 UPPER_SNAKE_CASE
- 所有注释使用中文
- Store 命名：xxxStore.js

### SQL
- 表名小写下划线
- 所有表和字段包含中文注释
- 使用外键约束保证数据完整性

## 关键实现细节

### GTFS 导入器（gtfs_importer.py）
- 自动处理表依赖关系（agency → routes → trips → stop_times）
- 批量插入优化（每批 1000 条）
- 自动跳过 CSV 中数据库表不存在的列（兼容不同地区的 GTFS 扩展）
- 支持 `--clean` 选项清空现有数据

### 速度计算（speed_calculator.py）
- 使用 Haversine 公式计算两点间距离
- 维护车辆位置历史
- 过滤 GPS 错误（最大速度限制 120 km/h）
- 最小时间间隔控制（默认 5 秒）

### 准点率计算（punctuality_calculator.py）
- 对比实时到站时间与计划时刻表
- 早到/准点/晚到分类（阈值可配置）
- 支持按线路、站点、时段聚合统计

### 多地区架构
- 前端 regionStore 管理当前选中地区
- api/index.js 拦截器自动附加 region 参数
- 后端所有查询自动过滤 region 字段
- 数据导入时必须指定 --region 参数

## 数据源和 API Key

**旧金山湾区**: 511 SF Bay API
获取地址: https://511.org/open-data/token

**纽约地铁**: MTA Real-Time Data Feeds
获取地址: https://api.mta.info/

**悉尼公交**: TfNSW Open Data
获取地址: https://opendata.transport.nsw.gov.au/
当前 API Key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiJiT1pUTzVrUFlGRUltV25mNHUtbzJYNFBucEx2UXZyb3h3eHJmMC12eWIwIiwiaWF0IjoxNzczNDE5MjcxfQ.4bXRaCjrCWHYmJk3xaDMu6-GPH_pQzOOykQ8_ePqGPM

## 故障排查

### PostgreSQL 连接失败
```bash
brew services list                          # 检查服务状态
brew services restart postgresql@16         # 重启服务
tail -f /opt/homebrew/var/log/postgresql@16.log  # 查看日志
```

### 后端启动失败
```bash
lsof -i :5001                               # 检查端口占用
tail -f /tmp/gtfs_backend.log               # 查看后端日志
```

### 前端启动失败
```bash
lsof -i :5173                               # 检查端口占用
rm -rf frontend/node_modules frontend/package-lock.json
cd frontend && npm install                  # 重新安装依赖
```

### 数据导入失败
- 确认 PostgreSQL 已启动
- 确认数据库表已创建（运行 schema.sql）
- 使用 `--clean` 选项清空现有数据
- 检查 ZIP 文件路径是否正确

## Git 提交规范

使用 Conventional Commits：
- feat: 新功能
- fix: 修复 bug
- docs: 文档更新
- refactor: 重构
- perf: 性能优化
- test: 测试相关
- chore: 构建/工具相关

示例：`feat(api): 添加准点率统计接口`

## 注意事项

1. **中文注释**: 所有代码注释必须使用中文
2. **API Key 安全**: 不要提交包含真实 API Key 的代码到 Git
3. **数据库备份**: 定期备份 gtfs_db 数据库
4. **多地区测试**: 修改 API 时确保所有地区参数都能正常工作
5. **性能优化**: 大数据量查询使用分页，避免一次性加载所有数据
