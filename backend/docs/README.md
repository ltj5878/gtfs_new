# GTFS 后端服务

这是 GTFS 公交数据分析系统的后端服务，提供数据获取、导入和 RESTful API 接口。

## 快速启动

### 前置要求

- Python 3.8+
- PostgreSQL 16+
- 已安装 Homebrew (macOS)

### 完整启动步骤

```bash
# 1. 进入后端目录
cd backend

# 2. 安装 Python 依赖
pip install -r requirements.txt

# 3. 安装并启动 PostgreSQL（如果未安装）
brew install postgresql@16
brew services start postgresql@16

# 4. 创建数据库
createdb gtfs_db

# 5. 创建表结构
psql gtfs_db -f schema.sql

# 6. 导入 GTFS 数据（首次运行必需）
python gtfs_importer.py --zip ../gtfs_data/gtfs_SF_20251119.zip

# 7. 启动 API 服务
python api.py
```

**API 服务将运行在**: http://localhost:5000

### 快速启动（已配置环境）

如果已经完成数据库初始化和数据导入：

```bash
cd backend
python api.py
```

### 验证服务

```bash
# 健康检查
curl http://localhost:5000/api/health

# 查看数据统计
curl http://localhost:5000/api/stats
```

## 详细配置

### 1. 安装依赖

```bash
# 从项目根目录
cd backend
pip install -r requirements.txt
```

### 2. 初始化数据库

```bash
# 创建数据库
createdb gtfs_db

# 创建表结构
psql gtfs_db -f schema.sql
```

### 3. 导入 GTFS 数据

```bash
# 从 ZIP 文件导入
python gtfs_importer.py --zip ../gtfs_data/gtfs_SF_20251119.zip

# 清空现有数据后导入
python gtfs_importer.py --zip ../gtfs_data/gtfs_SF_20251119.zip --clean
```

### 4. 启动 API 服务

```bash
python api.py
```

API 服务将运行在 http://localhost:5000

## 模块说明

### api.py
Flask RESTful API 服务，提供 15+ 个接口用于查询 GTFS 数据。

**主要接口**:
- `GET /api/health` - 健康检查
- `GET /api/agencies` - 获取运营机构列表
- `GET /api/routes` - 获取线路列表
- `GET /api/stops` - 获取站点列表
- `GET /api/trips` - 获取班次列表
- `GET /api/stats` - 获取数据统计

详细接口文档请查看 [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)

### db.py
数据库连接池管理模块，提供数据库连接和查询工具函数。

### gtfs_data_fetcher.py
从 511 SF Bay API 获取 GTFS 静态数据和实时数据。

**使用示例**:
```python
from gtfs_data_fetcher import GTFSDataFetcher

fetcher = GTFSDataFetcher(api_key="your_api_key")
gtfs_dir = fetcher.download_gtfs_static(operator_id="SF")
```

### gtfs_importer.py
将 GTFS 数据导入 PostgreSQL 数据库。

**命令行用法**:
```bash
python gtfs_importer.py --zip ../gtfs_data/gtfs_SF.zip
python gtfs_importer.py --zip ../gtfs_data/gtfs_SF.zip --clean
python gtfs_importer.py --dir ../gtfs_data/gtfs_SF
```

### speed_calculator.py
基于连续 GPS 位置计算车辆速度。

**使用示例**:
```python
from speed_calculator import SpeedCalculator

calculator = SpeedCalculator()
result = calculator.calculate_speed(
    vehicle_id="1234",
    latitude=37.7749,
    longitude=-122.4194,
    timestamp=1700000000
)
```

### example_usage.py
实时监控车辆速度的完整示例。

**运行示例**:
```bash
python example_usage.py
```

### schema.sql
PostgreSQL 数据库表结构定义，包含 17 个表（GTFS 标准表 + SF Muni 扩展表）。

## 数据库配置

默认数据库连接参数（在 db.py 中）:
- Host: localhost
- Port: 5432
- Database: gtfs_db
- User: 当前系统用户

可以通过环境变量覆盖：
```bash
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=gtfs_db
export DB_USER=your_username
export DB_PASSWORD=your_password
```

## API 测试

```bash
# 健康检查
curl http://localhost:5000/api/health

# 获取统计信息
curl http://localhost:5000/api/stats

# 获取线路列表
curl http://localhost:5000/api/routes?page=1&page_size=10

# 获取站点列表
curl http://localhost:5000/api/stops?page=1&page_size=10
```

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

### 导入数据失败
- 确认数据库表已创建
- 检查 ZIP 文件路径
- 使用 `--clean` 选项清空现有数据

### API 请求失败
- 检查 API Key 是否有效
- 检查网络连接
- 查看 API 限流情况

## 技术栈

- **Python**: 3.8+
- **Flask**: 3.0+ (Web 框架)
- **PostgreSQL**: 16 (数据库)
- **依赖包**:
  - `requests>=2.31.0` - HTTP 请求库
  - `gtfs-realtime-bindings>=1.0.0` - GTFS Realtime 数据解析
  - `protobuf>=4.24.0` - Protocol Buffers 支持
  - `psycopg2-binary>=2.9.9` - PostgreSQL 数据库驱动
  - `flask>=3.0.0` - Web 框架
  - `flask-cors>=4.0.0` - CORS 跨域支持

## 相关文档

- [API 接口文档](./API_DOCUMENTATION.md)
- [项目主 README](../README.md)
- [PostgreSQL 安装配置指南](../README_POSTGRESQL.md)
