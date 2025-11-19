# GTFS 公交数据分析系统

一个基于 GTFS (General Transit Feed Specification) 的公交数据获取、存储和分析系统，专注于旧金山湾区公交实时数据处理。

## 项目简介

本项目提供了一套完整的工具链，用于：
- 从 511 SF Bay API 获取 GTFS 静态数据和实时数据
- 将 GTFS 静态数据存储到 PostgreSQL 数据库
- 实时计算公交车辆速度
- 为数据分析和可视化提供基础支持

## 主要特性

- **数据获取**: 支持从 511 SF Bay API 下载 GTFS 静态数据和实时数据
- **数据存储**: 将 GTFS 数据导入 PostgreSQL，避免重复解析 ZIP 文件
- **速度计算**: 基于 GPS 位置实时计算车辆速度
- **完整的 GTFS 支持**: 支持所有 GTFS 标准表和 SF Muni 扩展
- **性能优化**: 批量插入、索引优化、数据验证
- **易于使用**: 提供命令行工具和 Python API

## 快速开始

### 1. 环境要求

- Python 3.8+
- PostgreSQL 16+
- macOS (使用 Homebrew)

### 2. 安装依赖

```bash
# 克隆项目
git clone <repository-url>
cd <project-directory>

# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装 Python 依赖
pip install -r requirements.txt

# 安装 PostgreSQL
brew install postgresql@16
brew services start postgresql@16
```

### 3. 初始化数据库

```bash
# 创建数据库
createdb gtfs_db

# 创建表结构
psql gtfs_db -f schema.sql
```

### 4. 导入 GTFS 数据

```bash
# 从 ZIP 文件导入
python gtfs_importer.py --zip gtfs_data/gtfs_SF_20251119.zip

# 或从目录导入
python gtfs_importer.py --dir gtfs_data/gtfs_SF
```

### 5. 运行示例

```bash
# 实时监控车辆速度
python example_usage.py
```

## 项目结构

```
.
├── .claude/                    # Claude Code 配置
│   ├── CLAUDE.md              # 项目上下文文档
│   └── settings.local.json    # 本地设置
├── gtfs_data/                 # GTFS 数据目录
│   ├── gtfs_SF_20251119.zip  # 静态数据压缩包
│   └── gtfs_SF/              # 解压后的数据
├── gtfs_data_fetcher.py      # 数据获取工具
├── gtfs_importer.py          # 数据导入工具
├── speed_calculator.py       # 速度计算模块
├── example_usage.py          # 使用示例
├── schema.sql                # 数据库表结构
├── requirements.txt          # Python 依赖
├── README.md                 # 本文件
└── README_POSTGRESQL.md      # PostgreSQL 详细指南
```

## 核心模块

### GTFSDataFetcher - 数据获取

从 511 SF Bay API 获取 GTFS 数据。

```python
from gtfs_data_fetcher import GTFSDataFetcher

# 初始化（需要 API Key）
fetcher = GTFSDataFetcher(api_key="your_api_key")

# 下载静态数据
gtfs_dir = fetcher.download_gtfs_static(operator_id="SF")

# 获取实时车辆位置
vehicle_feed = fetcher.fetch_gtfs_realtime(
    operator_id="SF",
    feed_type="vehiclepositions"
)

# 解析车辆位置
vehicles = fetcher.parse_vehicle_positions(vehicle_feed)
```

**获取 API Key**: https://511.org/open-data/token

### GTFSImporter - 数据导入

将 GTFS 数据导入 PostgreSQL 数据库。

```bash
# 基本用法
python gtfs_importer.py --zip gtfs_data/gtfs_SF.zip

# 清空现有数据后导入
python gtfs_importer.py --zip gtfs_data/gtfs_SF.zip --clean

# 只导入特定表
python gtfs_importer.py --zip gtfs_data/gtfs_SF.zip --tables routes stops trips

# 指定数据库连接
python gtfs_importer.py --zip gtfs_data/gtfs_SF.zip \
    --host localhost \
    --port 5432 \
    --database gtfs_db \
    --user your_username
```

### SpeedCalculator - 速度计算

基于连续 GPS 位置计算车辆速度。

```python
from speed_calculator import SpeedCalculator

# 初始化
calculator = SpeedCalculator(
    min_time_delta=5,           # 最小时间间隔（秒）
    min_distance_threshold=5,   # 最小距离阈值（米）
    max_speed_kmh=120          # 最大合理速度（km/h）
)

# 计算速度
result = calculator.calculate_speed(
    vehicle_id="1234",
    latitude=37.7749,
    longitude=-122.4194,
    timestamp=1700000000
)

if result:
    print(f"速度: {result.speed_kmh:.2f} km/h")
    print(f"距离: {result.distance_meters:.2f} m")
```

## 数据库表结构

### GTFS 标准表

| 表名 | 说明 |
|------|------|
| `agency` | 运营机构信息 |
| `routes` | 线路信息 |
| `stops` | 站点信息 |
| `trips` | 班次信息 |
| `stop_times` | 站点时刻表 |
| `calendar` | 服务日历 |
| `calendar_dates` | 特殊日期服务 |
| `shapes` | 线路地理轨迹 |
| `fare_attributes` | 票价属性 |
| `fare_rules` | 票价规则 |
| `feed_info` | 数据源信息 |

### SF Muni 扩展表

| 表名 | 说明 |
|------|------|
| `route_attributes` | 线路属性 |
| `directions` | 方向信息 |
| `calendar_attributes` | 日历属性 |
| `rider_categories` | 乘客类别 |
| `fare_rider_categories` | 票价乘客类别 |
| `attributions` | 数据归属 |

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

### 查询某条线路的实时班次

```sql
SELECT t.trip_id, t.trip_headsign, st.stop_name, st.arrival_time
FROM trips t
JOIN stop_times st ON t.trip_id = st.trip_id
JOIN stops s ON st.stop_id = s.stop_id
JOIN routes r ON t.route_id = r.route_id
WHERE r.route_short_name = 'L'
  AND t.service_id = 'WEEKDAY'
ORDER BY st.stop_sequence;
```

## 使用示例

### 完整的实时监控示例

```python
from gtfs_data_fetcher import GTFSDataFetcher
from speed_calculator import SpeedCalculator
import time

# 初始化
api_key = "your_api_key"
fetcher = GTFSDataFetcher(api_key)
calculator = SpeedCalculator()

print("开始实时监控...")

while True:
    # 获取车辆位置
    vehicle_feed = fetcher.fetch_gtfs_realtime(
        operator_id='SF',
        feed_type='vehiclepositions'
    )

    if vehicle_feed:
        vehicles = fetcher.parse_vehicle_positions(vehicle_feed)

        # 计算每辆车的速度
        for vehicle in vehicles:
            result = calculator.calculate_speed(
                vehicle_id=vehicle['vehicle_id'],
                latitude=vehicle['latitude'],
                longitude=vehicle['longitude'],
                timestamp=vehicle['timestamp']
            )

            if result:
                print(f"车辆 {result.vehicle_id}: "
                      f"{result.speed_kmh:.2f} km/h")

    # 每 30 秒更新一次
    time.sleep(30)
```

## 性能优化

### 数据库优化

1. **创建索引**（已在 schema.sql 中定义）
   - 线路查询索引
   - 站点位置索引
   - 时刻表查询索引

2. **更新统计信息**
   ```sql
   ANALYZE;
   ```

3. **使用连接池**（生产环境推荐）
   ```python
   from psycopg2 import pool
   connection_pool = pool.SimpleConnectionPool(1, 20, **conn_params)
   ```

### 导入优化

- 使用批量插入（默认每批 1000 条）
- 导入前使用 `--clean` 清空数据
- 大数据集考虑使用 `COPY` 命令

## 故障排查

### 数据库连接失败

```bash
# 检查 PostgreSQL 是否运行
brew services list

# 查看日志
tail -f /opt/homebrew/var/log/postgresql@16.log

# 重启服务
brew services restart postgresql@16
```

### API 请求失败

- 检查 API Key 是否有效
- 检查网络连接
- 查看 API 限流情况

### 导入数据失败

- 确认数据库表已创建
- 检查 ZIP 文件路径
- 使用 `--clean` 选项清空现有数据

## 开发指南

### 代码规范

- Python 代码遵循 PEP 8
- 使用类型提示
- 所有注释使用中文
- 函数和类使用 docstring

### 提交规范

- 不要提交 `.venv` 目录
- 不要提交 `gtfs_data` 目录
- 不要提交包含真实 API Key 的代码
- 提交前运行测试

### 测试

```bash
# 运行单元测试（待实现）
python -m pytest tests/

# 测试数据导入
python gtfs_importer.py --zip gtfs_data/gtfs_SF.zip --no-verify
```

## 未来计划

- [ ] 开发 Web 前端界面
- [ ] 添加数据分析功能
- [ ] 实现到站时间预测
- [ ] 支持更多公交运营商
- [ ] 提供 RESTful API
- [ ] 添加单元测试
- [ ] 实时数据存储到时序数据库
- [ ] 性能监控和日志系统

## 相关资源

- [GTFS 规范文档](https://gtfs.org/reference/static)
- [GTFS Realtime 规范](https://gtfs.org/reference/realtime/v2/)
- [511 SF Bay API 文档](https://511.org/open-data/transit)
- [PostgreSQL 文档](https://www.postgresql.org/docs/)
- [PostgreSQL 安装配置指南](./README_POSTGRESQL.md)

## 许可证

本项目仅供学习和研究使用。

## 贡献

欢迎提交 Issue 和 Pull Request。

## 联系方式

如有问题或建议，请通过 Issue 联系。

---

**注意**: 本项目目前专注于后端数据处理，前端部分将在未来开发。
