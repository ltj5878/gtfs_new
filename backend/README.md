# 后端服务

基于 Flask 3.0 + PostgreSQL 16 的 GTFS 公交数据后端，提供 RESTful API、实时数据采集、准点率计算等功能。

## 模块结构

```
backend/
├── api/
│   └── app.py                      # Flask 主应用，所有 API 路由定义
├── auth/
│   ├── routes.py                   # 登录/注册/登出路由
│   ├── models.py                   # 用户模型，默认用户初始化
│   └── user_schema.sql             # 用户表结构
├── core/
│   ├── db.py                       # PostgreSQL 连接池（psycopg2）
│   ├── config.py                   # 配置管理（优先级：环境变量 > config.local.json > config.json）
│   └── route_mappings.py           # 线路属性映射与富化逻辑
├── business_logic/
│   ├── speed_calculator.py         # 车辆速度计算（Haversine 公式）
│   └── punctuality_calculator.py   # 准点率计算逻辑
├── data_acquisition/
│   ├── gtfs_importer.py            # GTFS ZIP 导入工具（多地区）
│   ├── gtfs_data_fetcher.py        # 旧金山 511 SF Bay API
│   ├── mta_data_fetcher.py         # 纽约 MTA API（暂未启用）
│   └── tfnsw_data_fetcher.py       # 悉尼 TfNSW API
├── services/
│   ├── punctuality_service.py      # 准点率数据收集（含重试+自动降级）
│   └── mock_data_generator.py      # 降级时的模拟数据生成器
├── database/
│   ├── schema.sql                  # GTFS 主表结构
│   ├── punctuality_schema.sql      # 准点率表结构
│   ├── admin_schema.sql            # 管理员相关表
│   └── favorites_schema.sql        # 收藏功能表
├── scripts/
│   ├── start_punctuality_service.py        # 准点率服务启动脚本
│   ├── generate_sample_punctuality_data.py # 生成测试数据
│   └── generate_realtime_data_simple.py    # 生成实时数据测试样本
├── config.example.json             # 配置模板（提交到 Git）
├── config.json                     # 实际配置（不提交，含 API Key）
└── requirements.txt
```

## 安装依赖

```bash
pip3 install -r requirements.txt
```

## 配置

复制配置模板并填入 API Key：

```bash
cp config.example.json config.json
```

`config.json` 结构：

```json
{
  "api_keys": {
    "sf": "your_511_api_key",
    "sydney": "your_tfnsw_api_key"
  },
  "punctuality": {
    "early_threshold": -60,
    "late_threshold": 300
  }
}
```

也可通过环境变量覆盖：`SF_511_API_KEY`、`TFNSW_API_KEY`

## 数据库初始化

```bash
createdb gtfs_db
psql gtfs_db -f database/schema.sql
psql gtfs_db -f database/punctuality_schema.sql
psql gtfs_db -f database/admin_schema.sql
psql gtfs_db -f database/favorites_schema.sql
psql gtfs_db -f auth/user_schema.sql
```

## GTFS 数据导入

```bash
# 导入旧金山数据
python3 data_acquisition/gtfs_importer.py \
  --zip ../gtfs_data/gtfs_SF_20251119.zip \
  --region sf \
  --clean

# 导入悉尼数据
python3 data_acquisition/gtfs_importer.py \
  --zip ../gtfs_data/gtfs_sydney.zip \
  --region sydney \
  --clean
```

导入器特性：
- 自动处理表依赖顺序（agency → routes → trips → stop_times）
- 批量插入优化（每批 1000 条）
- 自动跳过 CSV 中数据库不存在的列（兼容不同地区 GTFS 扩展）

## 启动服务

```bash
# 直接启动（开发）
python3 api/app.py

# 通过根目录脚本启动（推荐）
cd .. && ./start.sh start
```

服务运行在 http://localhost:5001

## API 接口

所有接口支持 `?region=sf|sydney` 参数。

### 基础

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 健康检查 |
| GET | `/api/stats` | 数据统计 |
| GET | `/api/regions` | 地区列表 |

### 线路与站点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/routes` | 线路列表（支持分页、搜索、类型筛选） |
| GET | `/api/routes/{id}` | 线路详情 |
| GET | `/api/stops` | 站点列表 |
| GET | `/api/stops/{id}` | 站点详情 |
| GET | `/api/trips/{id}/stop_times` | 班次时刻表 |

### 实时数据

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/realtime/vehicles` | 实时车辆位置 |

### 准点率

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/punctuality/routes` | 线路准点率列表 |
| GET | `/api/punctuality/overview` | 准点率总览 |
| GET | `/api/punctuality/hourly` | 按小时准点率分布 |

### 用户认证

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/login` | 登录 |
| POST | `/api/auth/register` | 注册 |
| POST | `/api/auth/logout` | 登出 |
| GET | `/api/auth/me` | 当前用户信息 |

## 准点率服务

准点率服务独立运行，定期从实时 API 拉取数据并写入数据库：

```bash
# 后台启动
python3 scripts/start_punctuality_service.py --region sf &
python3 scripts/start_punctuality_service.py --region sydney &
```

服务特性：
- 失败自动重试（3 次，间隔 5 秒）
- API 不可用时自动降级到模拟数据（对用户透明）

## 核心模块说明

### speed_calculator.py

使用 Haversine 公式计算相邻 GPS 点间距离，过滤 GPS 漂移（最大速度 120 km/h），最小采样间隔 5 秒。

### punctuality_calculator.py

对比实时到站时间与计划时刻表，按阈值分类：
- 早到：提前超过 60 秒
- 准点：±60~300 秒内
- 晚到：延误超过 300 秒

### config.py

配置优先级：环境变量 > `config.local.json` > `config.json`，支持本地覆盖而不影响提交。

## 测试

```bash
python3 tests/test_api_quick.py
```

## 数据库表说明

### GTFS 标准表
`agency`、`routes`、`stops`、`trips`、`stop_times`、`calendar`、`calendar_dates`、`shapes`、`fare_attributes`、`fare_rules`

### 扩展表
`route_attributes`（SF Muni 线路属性）、`punctuality_records`（准点率记录）、`users`（用户）、`favorites`（收藏）

所有主表含 `region` 字段（`sf` / `sydney`），通过 `regions` 配置表管理地区元数据。
