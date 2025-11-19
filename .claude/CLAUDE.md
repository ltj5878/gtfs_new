# 项目上下文 - GTFS 公交数据分析系统

## 项目概述

这是一个基于 GTFS (General Transit Feed Specification) 的公交数据分析系统，主要用于获取、存储和分析旧金山湾区的公交实时数据。项目采用前后端分离架构，目前专注于后端数据处理部分。

## 项目目标

1. 从 511 SF Bay API 获取 GTFS 静态数据和实时数据
2. 将 GTFS 静态数据存储到 PostgreSQL 数据库中，避免每次都解析 ZIP 文件
3. 实时计算公交车辆的速度
4. 为未来的前端应用提供数据支持

## 技术栈

- **语言**: Python 3
- **数据库**: PostgreSQL 16
- **主要依赖**:
  - `psycopg2-binary`: PostgreSQL 数据库连接
  - `requests`: HTTP 请求
  - `gtfs-realtime-bindings`: GTFS Realtime 数据解析
  - `protobuf`: Protocol Buffers 支持

## 项目结构

```
.
├── .claude/                    # Claude Code 配置目录
│   ├── CLAUDE.md              # 项目上下文文档（本文件）
│   └── settings.local.json    # 本地设置
├── gtfs_data/                 # GTFS 数据存储目录
│   ├── gtfs_SF_20251119.zip  # GTFS 静态数据压缩包
│   └── gtfs_SF/              # 解压后的 GTFS 数据
├── gtfs_data_fetcher.py      # GTFS 数据获取工具
├── gtfs_importer.py          # GTFS 数据导入 PostgreSQL 工具
├── speed_calculator.py       # 车辆速度计算模块
├── example_usage.py          # 使用示例
├── schema.sql                # PostgreSQL 数据库表结构
├── requirements.txt          # Python 依赖
├── README.md                 # 项目说明文档
└── README_POSTGRESQL.md      # PostgreSQL 安装配置指南
```

## 核心模块说明

### 1. gtfs_data_fetcher.py
- **功能**: 从 511 SF Bay API 获取 GTFS 数据
- **主要类**: `GTFSDataFetcher`
- **支持的操作**:
  - 下载 GTFS 静态数据（ZIP 格式）
  - 获取 GTFS Realtime 数据（车辆位置、行程更新、服务警报）
  - 解析车辆位置和行程更新数据
- **API Key**: 需要从 https://511.org/open-data/token 获取

### 2. gtfs_importer.py
- **功能**: 将 GTFS 静态数据导入 PostgreSQL 数据库
- **主要类**: `GTFSImporter`
- **支持的操作**:
  - 从 ZIP 文件或目录导入数据
  - 自动处理表依赖关系
  - 批量插入优化性能
  - 导入前清空数据
  - 导入后验证数据
- **使用方法**: `python gtfs_importer.py --zip gtfs_data/gtfs_SF_20251119.zip`

### 3. speed_calculator.py
- **功能**: 基于连续 GPS 位置计算车辆速度
- **主要类**: `SpeedCalculator`
- **算法**: 使用 Haversine 公式计算两点间距离
- **特性**:
  - 维护车辆位置历史
  - 过滤 GPS 错误（最大速度限制）
  - 处理停止状态（最小距离阈值）
  - 最小时间间隔控制

### 4. schema.sql
- **功能**: PostgreSQL 数据库表结构定义
- **包含的表**:
  - `agency`: 运营机构信息
  - `routes`: 线路信息
  - `stops`: 站点信息
  - `trips`: 班次信息
  - `stop_times`: 站点时刻表
  - `calendar`: 服务日历
  - `calendar_dates`: 特殊日期服务
  - `shapes`: 线路地理轨迹
  - `fare_*`: 票价相关表
  - 以及 SF Muni 扩展表

## 数据库设计

### GTFS 标准表
遵循 GTFS 规范，包含所有标准表和字段，支持完整的公交数据模型。

### SF Muni 扩展表
- `route_attributes`: 线路属性（类别、子类别、运行方式）
- `directions`: 方向信息
- `calendar_attributes`: 日历属性
- `rider_categories`: 乘客类别
- `fare_rider_categories`: 票价乘客类别

### 索引优化
为常用查询字段创建了索引，包括：
- 线路查询索引
- 站点位置索引
- 班次查询索引
- 时刻表查询索引

## 编码规范

### Python 代码规范
- 使用 Python 3 类型提示
- 遵循 PEP 8 代码风格
- 使用 dataclass 定义数据结构
- 所有注释使用中文
- 函数和类使用 docstring 说明

### SQL 规范
- 表名使用小写下划线命名
- 所有表和字段都有中文注释
- 使用外键约束保证数据完整性
- 为常用查询创建索引

### 命名约定
- 类名: PascalCase (如 `GTFSImporter`)
- 函数名: snake_case (如 `calculate_speed`)
- 常量: UPPER_SNAKE_CASE (如 `EARTH_RADIUS_METERS`)
- 私有方法: 前缀下划线 (如 `_haversine_distance`)

## 开发工作流

### 1. 环境设置
```bash
# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 安装和启动 PostgreSQL
brew install postgresql@16
brew services start postgresql@16
createdb gtfs_db
```

### 2. 数据库初始化
```bash
# 创建表结构
psql gtfs_db -f schema.sql

# 导入 GTFS 数据
python gtfs_importer.py --zip gtfs_data/gtfs_SF_20251119.zip
```

### 3. 运行示例
```bash
# 实时监控车辆速度
python example_usage.py
```

## 常用查询示例

### 查询所有线路
```sql
SELECT route_short_name, route_long_name, route_type
FROM routes
ORDER BY route_short_name;
```

### 查询某条线路的所有站点
```sql
SELECT DISTINCT s.stop_name, s.stop_lat, s.stop_lon
FROM stops s
JOIN stop_times st ON s.stop_id = st.stop_id
JOIN trips t ON st.trip_id = t.trip_id
JOIN routes r ON t.route_id = r.route_id
WHERE r.route_short_name = 'L'
ORDER BY st.stop_sequence;
```

### 查询某个站点的所有经过线路
```sql
SELECT DISTINCT r.route_short_name, r.route_long_name
FROM routes r
JOIN trips t ON r.route_id = t.route_id
JOIN stop_times st ON t.trip_id = st.trip_id
JOIN stops s ON st.stop_id = s.stop_id
WHERE s.stop_name LIKE '%Market%'
ORDER BY r.route_short_name;
```

## API 密钥管理

- 511 SF Bay API Key 存储在代码中（示例用）
- 生产环境应使用环境变量或配置文件
- API Key 获取地址: https://511.org/open-data/token

## 数据更新策略

### GTFS 静态数据
- 定期下载最新的 GTFS 静态数据（建议每周）
- 使用 `--clean` 选项清空旧数据后重新导入
- 保留历史 ZIP 文件用于回溯

### GTFS Realtime 数据
- 实时数据不存储到数据库
- 通过 API 实时获取
- 用于速度计算和实时监控

## 性能优化建议

1. **批量插入**: 使用 `execute_batch` 进行批量插入，每批 1000 条
2. **索引优化**: 为常用查询字段创建索引
3. **连接池**: 生产环境使用连接池管理数据库连接
4. **缓存**: 对静态数据（如线路、站点）使用缓存
5. **分析统计**: 定期运行 `ANALYZE` 更新表统计信息

## 未来扩展方向

1. **前端开发**: 开发 Web 界面展示实时数据
2. **数据分析**: 分析延误模式、速度分布等
3. **预测模型**: 基于历史数据预测到站时间
4. **多运营商支持**: 扩展支持更多公交运营商
5. **API 服务**: 提供 RESTful API 供前端调用
6. **实时数据存储**: 将实时数据存储到时序数据库

## 故障排查

### 数据库连接失败
- 检查 PostgreSQL 是否运行: `brew services list`
- 检查数据库是否存在: `psql -l`
- 查看日志: `tail -f /opt/homebrew/var/log/postgresql@16.log`

### API 请求失败
- 检查 API Key 是否有效
- 检查网络连接
- 查看 API 响应状态码和错误信息

### 导入数据失败
- 检查 ZIP 文件路径是否正确
- 确认数据库表已创建
- 使用 `--clean` 选项清空现有数据

## 相关文档

- [PostgreSQL 安装配置指南](../README_POSTGRESQL.md)
- [项目 README](../README.md)
- [GTFS 规范文档](https://gtfs.org/reference/static)
- [511 SF Bay API 文档](https://511.org/open-data/transit)

## 注意事项

1. **前后端分离**: 当前只关注后端，前端部分暂不涉及
2. **中文注释**: 所有代码注释使用中文
3. **数据隐私**: 不要提交包含真实 API Key 的代码
4. **Git 管理**: `.venv` 和 `gtfs_data` 目录应在 `.gitignore` 中
5. **数据库备份**: 定期备份数据库数据
