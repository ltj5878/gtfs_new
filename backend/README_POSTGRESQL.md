# PostgreSQL 安装配置与 GTFS 数据导入指南

## 1. PostgreSQL 安装和配置

### 1.1 安装 PostgreSQL

使用 Homebrew 安装 PostgreSQL 16：

```bash
brew install postgresql@16
```

### 1.2 配置环境变量

将 PostgreSQL 添加到系统路径，编辑 `~/.zshrc` 文件：

```bash
echo 'export PATH="/opt/homebrew/opt/postgresql@16/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

如果使用 bash，则编辑 `~/.bash_profile`：

```bash
echo 'export PATH="/opt/homebrew/opt/postgresql@16/bin:$PATH"' >> ~/.bash_profile
source ~/.bash_profile
```

### 1.3 启动 PostgreSQL 服务

**方式一：作为后台服务启动（推荐）**

```bash
# 启动服务
brew services start postgresql@16

# 查看服务状态
brew services list

# 停止服务
brew services stop postgresql@16

# 重启服务
brew services restart postgresql@16
```

**方式二：前台运行（用于调试）**

```bash
postgres -D /opt/homebrew/var/postgresql@16
```

### 1.4 创建数据库

```bash
# 创建 GTFS 数据库
createdb gtfs_db

# 验证数据库创建成功
psql -l
```

### 1.5 连接数据库

```bash
# 连接到 gtfs_db 数据库
psql gtfs_db
```

在 psql 命令行中常用命令：

```sql
-- 列出所有数据库
\l

-- 列出当前数据库的所有表
\dt

-- 查看表结构
\d table_name

-- 退出
\q
```

## 2. 创建 GTFS 数据表

### 2.1 执行建表脚本

```bash
# 在项目目录下执行
psql gtfs_db -f schema.sql
```

### 2.2 验证表创建

```bash
psql gtfs_db -c "\dt"
```

应该看到以下表：
- agency
- routes
- stops
- trips
- stop_times
- calendar
- calendar_dates
- shapes
- fare_attributes
- fare_rules
- feed_info
- 以及其他扩展表

## 3. 导入 GTFS 数据

### 3.1 安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 3.2 使用导入工具

**基本用法：**

```bash
# 从 ZIP 文件导入
python gtfs_importer.py --zip gtfs_data/gtfs_SF_20251119.zip

# 从已解压的目录导入
python gtfs_importer.py --dir gtfs_data/gtfs_SF

# 指定数据库连接参数
python gtfs_importer.py --zip gtfs_data/gtfs_SF_20251119.zip \
    --host localhost \
    --port 5432 \
    --database gtfs_db \
    --user your_username \
    --password your_password
```

**高级选项：**

```bash
# 导入前清空现有数据
python gtfs_importer.py --zip gtfs_data/gtfs_SF_20251119.zip --clean

# 只导入特定表
python gtfs_importer.py --zip gtfs_data/gtfs_SF_20251119.zip --tables routes stops trips

# 查看帮助
python gtfs_importer.py --help
```

### 3.3 验证数据导入

```bash
psql gtfs_db
```

在 psql 中执行：

```sql
-- 查看各表的记录数
SELECT 'agency' as table_name, COUNT(*) FROM agency
UNION ALL
SELECT 'routes', COUNT(*) FROM routes
UNION ALL
SELECT 'stops', COUNT(*) FROM stops
UNION ALL
SELECT 'trips', COUNT(*) FROM trips
UNION ALL
SELECT 'stop_times', COUNT(*) FROM stop_times;

-- 查看具体数据示例
SELECT * FROM routes LIMIT 5;
SELECT * FROM stops LIMIT 5;
```

## 4. 常用数据库操作

### 4.1 查询示例

```sql
-- 查询所有线路
SELECT route_short_name, route_long_name, route_type
FROM routes
ORDER BY route_short_name;

-- 查询某条线路的所有站点
SELECT DISTINCT s.stop_name, s.stop_lat, s.stop_lon
FROM stops s
JOIN stop_times st ON s.stop_id = st.stop_id
JOIN trips t ON st.trip_id = t.trip_id
JOIN routes r ON t.route_id = r.route_id
WHERE r.route_short_name = 'L'
ORDER BY st.stop_sequence;

-- 查询某个站点的所有经过线路
SELECT DISTINCT r.route_short_name, r.route_long_name
FROM routes r
JOIN trips t ON r.route_id = t.route_id
JOIN stop_times st ON t.trip_id = st.trip_id
JOIN stops s ON st.stop_id = s.stop_id
WHERE s.stop_name LIKE '%Market%'
ORDER BY r.route_short_name;
```

### 4.2 数据维护

```sql
-- 清空所有表数据（保留表结构）
TRUNCATE TABLE stop_times, trips, routes, stops, calendar, calendar_dates,
               shapes, fare_attributes, fare_rules, agency, feed_info CASCADE;

-- 删除并重建表
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
-- 然后重新执行 schema.sql
```

### 4.3 备份和恢复

```bash
# 备份数据库
pg_dump gtfs_db > gtfs_backup_$(date +%Y%m%d).sql

# 恢复数据库
psql gtfs_db < gtfs_backup_20251119.sql

# 备份为自定义格式（推荐，支持并行恢复）
pg_dump -Fc gtfs_db > gtfs_backup.dump

# 从自定义格式恢复
pg_restore -d gtfs_db gtfs_backup.dump
```

## 5. Python 连接示例

```python
import psycopg2
from psycopg2.extras import RealDictCursor

# 连接数据库
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="gtfs_db",
    user="your_username",
    password="your_password"
)

# 使用字典游标
cursor = conn.cursor(cursor_factory=RealDictCursor)

# 查询数据
cursor.execute("SELECT * FROM routes LIMIT 5")
routes = cursor.fetchall()

for route in routes:
    print(f"{route['route_short_name']}: {route['route_long_name']}")

# 关闭连接
cursor.close()
conn.close()
```

## 6. 性能优化建议

### 6.1 创建索引

导入工具会自动创建基本索引，如需额外优化：

```sql
-- 为常用查询字段创建索引
CREATE INDEX IF NOT EXISTS idx_stop_times_stop_id ON stop_times(stop_id);
CREATE INDEX IF NOT EXISTS idx_stop_times_trip_id ON stop_times(trip_id);
CREATE INDEX IF NOT EXISTS idx_trips_route_id ON trips(route_id);
CREATE INDEX IF NOT EXISTS idx_stops_name ON stops(stop_name);

-- 为地理位置查询创建空间索引（需要 PostGIS 扩展）
CREATE EXTENSION IF NOT EXISTS postgis;
ALTER TABLE stops ADD COLUMN geom geometry(Point, 4326);
UPDATE stops SET geom = ST_SetSRID(ST_MakePoint(stop_lon, stop_lat), 4326);
CREATE INDEX idx_stops_geom ON stops USING GIST(geom);
```

### 6.2 分析表统计信息

```sql
-- 更新表统计信息以优化查询计划
ANALYZE;

-- 或针对特定表
ANALYZE stop_times;
```

## 7. 故障排查

### 7.1 无法连接数据库

```bash
# 检查 PostgreSQL 是否运行
brew services list

# 查看日志
tail -f /opt/homebrew/var/log/postgresql@16.log
```

### 7.2 权限问题

```sql
-- 授予用户权限
GRANT ALL PRIVILEGES ON DATABASE gtfs_db TO your_username;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_username;
```

### 7.3 导入失败

- 检查 ZIP 文件或目录路径是否正确
- 确认数据库连接参数
- 查看导入工具的错误日志
- 使用 `--clean` 选项清空现有数据后重试

## 8. 卸载 PostgreSQL

如需卸载：

```bash
# 停止服务
brew services stop postgresql@16

# 卸载
brew uninstall postgresql@16

# 删除数据目录（可选）
rm -rf /opt/homebrew/var/postgresql@16
```
