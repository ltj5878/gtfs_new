# GTFS 公交数据分析系统

一个基于 GTFS (General Transit Feed Specification) 的公交数据分析系统，采用前后端分离架构，专注于旧金山湾区公交数据的获取、存储、分析和可视化展示。

## 项目简介

本项目提供了一套完整的解决方案，包括：
- 从 511 SF Bay API 获取 GTFS 静态数据和实时数据
- 将 GTFS 静态数据存储到 PostgreSQL 数据库
- 实时计算公交车辆速度
- 提供 RESTful API 接口供前端调用
- Vue3 前端应用展示公交数据和实时信息

## 主要特性

### 后端特性
- **数据获取**: 支持从 511 SF Bay API 下载 GTFS 静态数据和实时数据
- **数据存储**: 将 GTFS 数据导入 PostgreSQL，避免重复解析 ZIP 文件
- **速度计算**: 基于 GPS 位置实时计算车辆速度
- **RESTful API**: 提供 15+ 个 API 接口，支持分页、搜索、筛选
- **完整的 GTFS 支持**: 支持所有 GTFS 标准表和 SF Muni 扩展
- **性能优化**: 批量插入、连接池管理、索引优化、数据验证

### 前端特性
- **现代化框架**: 基于 Vue 3 Composition API + Vite 构建
- **UI 组件库**: 使用 Element Plus 提供美观的用户界面
- **状态管理**: Pinia 管理应用状态
- **响应式设计**: 适配桌面和移动端
- **地图展示**: 集成 Leaflet 地图库（开发中）
- **实时数据**: 支持实时车辆位置和速度展示（开发中）

## 快速开始

### 环境要求

**后端**
- Python 3.8+
- PostgreSQL 16+
- macOS (使用 Homebrew) 或 Linux

**前端**
- Node.js 16+
- npm 或 pnpm

### 完整启动流程（首次运行）

#### 步骤 1: 克隆项目

```bash
git clone <repository-url>
cd gtfs_new
```

#### 步骤 2: 后端设置

```bash
# 2.1 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 2.2 安装 Python 依赖
pip install -r backend/requirements.txt

# 2.3 安装并启动 PostgreSQL
brew install postgresql@16
brew services start postgresql@16

# 2.4 创建数据库和表结构
createdb gtfs_db
psql gtfs_db -f backend/schema.sql

# 2.5 导入 GTFS 数据
python backend/gtfs_importer.py --zip gtfs_data/gtfs_SF_20251119.zip
```

#### 步骤 3: 前端设置

```bash
# 3.1 进入前端目录
cd frontend

# 3.2 安装依赖
npm install
# 或使用 pnpm
pnpm install
```

#### 步骤 4: 启动服务

**终端 1 - 启动后端 API 服务**:
```bash
cd gtfs_new
source .venv/bin/activate
cd backend
python api.py
```
✅ 后端 API 运行在: http://localhost:5000

**终端 2 - 启动前端开发服务器**:
```bash
cd gtfs_new/frontend
npm run dev
```
✅ 前端应用运行在: http://localhost:5173

#### 步骤 5: 访问应用

打开浏览器访问 **http://localhost:5173** 即可使用前端应用。

### 快速启动（已配置环境）

如果已经完成初始配置，后续启动只需：

```bash
# 终端 1: 启动后端
cd gtfs_new
source .venv/bin/activate
cd backend
python api.py

# 终端 2: 启动前端
cd gtfs_new/frontend
npm run dev
```

### 验证安装

```bash
# 检查后端 API
curl http://localhost:5000/api/health

# 检查数据统计
curl http://localhost:5000/api/stats

# 访问前端
# 浏览器打开 http://localhost:5173
```

### 常见问题

**Q: PostgreSQL 连接失败？**
```bash
# 检查 PostgreSQL 是否运行
brew services list

# 重启 PostgreSQL
brew services restart postgresql@16
```

**Q: 前端无法连接后端？**
- 确保后端 API 服务已启动（http://localhost:5000）
- 检查浏览器控制台是否有 CORS 错误

**Q: 数据导入失败？**
```bash
# 清空数据后重新导入
python backend/gtfs_importer.py --zip gtfs_data/gtfs_SF_20251119.zip --clean
```

## 项目结构

```
.
├── .claude/                    # Claude Code 配置
│   ├── CLAUDE.md              # 项目上下文文档
│   └── settings.local.json    # 本地设置
├── backend/                   # 后端目录
│   ├── api.py                # Flask RESTful API 服务
│   ├── db.py                 # 数据库连接池管理
│   ├── gtfs_data_fetcher.py  # 数据获取工具
│   ├── gtfs_importer.py      # 数据导入工具
│   ├── speed_calculator.py   # 速度计算模块
│   ├── example_usage.py      # 使用示例
│   ├── schema.sql            # 数据库表结构
│   ├── requirements.txt      # Python 依赖
│   └── API_DOCUMENTATION.md  # API 接口文档
├── frontend/                  # 前端目录
│   ├── src/
│   │   ├── api/              # API 请求封装
│   │   ├── assets/           # 静态资源
│   │   ├── components/       # Vue 组件
│   │   │   ├── RouteCard.vue
│   │   │   ├── SearchBar.vue
│   │   │   └── StopCard.vue
│   │   ├── views/            # 页面视图
│   │   │   ├── Home.vue
│   │   │   ├── Routes.vue
│   │   │   ├── RouteDetail.vue
│   │   │   ├── Stops.vue
│   │   │   ├── StopDetail.vue
│   │   │   └── Map.vue
│   │   ├── router/           # 路由配置
│   │   ├── stores/           # Pinia 状态管理
│   │   ├── App.vue           # 根组件
│   │   └── main.js           # 入口文件
│   ├── public/               # 公共资源
│   ├── index.html            # HTML 模板
│   ├── vite.config.js        # Vite 配置
│   └── package.json          # 前端依赖
├── gtfs_data/                 # GTFS 数据目录
│   ├── gtfs_SF_20251119.zip  # 静态数据压缩包
│   └── gtfs_SF/              # 解压后的数据
├── README.md                 # 本文件
└── README_POSTGRESQL.md      # PostgreSQL 详细指南
```

## 核心模块

### 后端模块

#### 1. GTFSDataFetcher - 数据获取

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

#### 2. GTFSImporter - 数据导入

将 GTFS 数据导入 PostgreSQL 数据库。

```bash
# 基本用法
python backend/gtfs_importer.py --zip gtfs_data/gtfs_SF.zip

# 清空现有数据后导入
python backend/gtfs_importer.py --zip gtfs_data/gtfs_SF.zip --clean

# 只导入特定表
python backend/gtfs_importer.py --zip gtfs_data/gtfs_SF.zip --tables routes stops trips

# 指定数据库连接
python backend/gtfs_importer.py --zip gtfs_data/gtfs_SF.zip \
    --host localhost \
    --port 5432 \
    --database gtfs_db \
    --user your_username
```

#### 3. SpeedCalculator - 速度计算

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

#### 4. Flask API 服务

提供 RESTful API 接口。

```bash
# 启动 API 服务
cd backend
python api.py

# 服务将运行在 http://localhost:5000
```

**主要接口**:
- `GET /api/health` - 健康检查
- `GET /api/agencies` - 获取运营机构列表
- `GET /api/routes` - 获取线路列表（支持分页、搜索、筛选）
- `GET /api/routes/<route_id>` - 获取线路详情
- `GET /api/routes/<route_id>/stops` - 获取线路站点
- `GET /api/stops` - 获取站点列表
- `GET /api/stops/<stop_id>` - 获取站点详情
- `GET /api/stops/<stop_id>/routes` - 获取站点经过的线路
- `GET /api/trips` - 获取班次列表
- `GET /api/shapes/<shape_id>` - 获取线路轨迹
- `GET /api/stats` - 获取数据统计

详细 API 文档请查看 [API_DOCUMENTATION.md](./backend/API_DOCUMENTATION.md)

### 前端模块

#### 1. 页面视图

- **Home.vue**: 首页，展示数据统计和快速访问入口
- **Routes.vue**: 线路列表页，支持搜索和类型筛选
- **RouteDetail.vue**: 线路详情页，展示线路信息和站点列表
- **Stops.vue**: 站点列表页，支持搜索
- **StopDetail.vue**: 站点详情页，展示站点信息和经过的线路
- **Map.vue**: 地图页面（开发中）

#### 2. 组件

- **SearchBar.vue**: 搜索栏组件
- **RouteCard.vue**: 线路卡片组件
- **StopCard.vue**: 站点卡片组件

#### 3. 状态管理

- **appStore.js**: 应用全局状态
- **routeStore.js**: 线路状态管理
- **stopStore.js**: 站点状态管理

#### 4. API 请求层

- **api/index.js**: Axios 实例配置
- **api/routes.js**: 线路相关 API
- **api/stops.js**: 站点相关 API
- **api/trips.js**: 班次相关 API
- **api/common.js**: 通用 API

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
import sys
sys.path.append('backend')

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

或者直接运行示例文件：

```bash
cd backend
python example_usage.py
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
python backend/gtfs_importer.py --zip gtfs_data/gtfs_SF.zip --no-verify

# 测试 API 服务
cd backend
python api.py
# 在另一个终端测试
curl http://localhost:5000/api/health

# 测试前端
cd frontend
npm run dev
```

## 技术栈

### 后端
- **语言**: Python 3.8+
- **框架**: Flask 3.0+
- **数据库**: PostgreSQL 16
- **主要依赖**:
  - `flask`: Web 框架
  - `flask-cors`: 跨域支持
  - `psycopg2-binary`: PostgreSQL 数据库连接
  - `requests`: HTTP 请求
  - `gtfs-realtime-bindings`: GTFS Realtime 数据解析
  - `protobuf`: Protocol Buffers 支持

### 前端
- **框架**: Vue 3 (Composition API)
- **构建工具**: Vite 5.0+
- **UI 组件库**: Element Plus 2.5+
- **状态管理**: Pinia 2.1+
- **路由**: Vue Router 4.2+
- **地图**: Leaflet 1.9+
- **HTTP 客户端**: Axios 1.6+
- **样式**: CSS3 / SCSS

## 已完成功能

- [x] GTFS 数据获取和导入
- [x] PostgreSQL 数据库设计和优化
- [x] 车辆速度计算模块
- [x] RESTful API 服务（15+ 接口）
- [x] Vue3 前端应用框架
- [x] 首页数据统计展示
- [x] 线路列表和详情页面
- [x] 站点列表和详情页面
- [x] 搜索和筛选功能
- [x] 分页功能
- [x] 响应式设计

## 开发中功能

- [ ] 地图展示（Leaflet 集成）
- [ ] 实时车辆位置追踪
- [ ] 实时速度展示

## 未来计划

- [ ] 添加数据分析功能（延误分析、速度分布等）
- [ ] 实现到站时间预测
- [ ] 支持更多公交运营商
- [ ] 添加单元测试和集成测试
- [ ] 实时数据存储到时序数据库
- [ ] 性能监控和日志系统
- [ ] 用户系统（注册、登录、收藏）
- [ ] 通知推送（线路延误、到站提醒）
- [ ] 数据可视化（图表展示）
- [ ] 移动应用（iOS/Android）

## 相关资源

### 文档
- [GTFS 规范文档](https://gtfs.org/reference/static)
- [GTFS Realtime 规范](https://gtfs.org/reference/realtime/v2/)
- [511 SF Bay API 文档](https://511.org/open-data/transit)
- [PostgreSQL 文档](https://www.postgresql.org/docs/)
- [PostgreSQL 安装配置指南](backend/README_POSTGRESQL.md)
- [API 接口文档](./backend/API_DOCUMENTATION.md)
- [项目上下文文档](./.claude/CLAUDE.md)

### 技术文档
- [Vue 3 官方文档](https://vuejs.org/)
- [Element Plus 文档](https://element-plus.org/)
- [Pinia 文档](https://pinia.vuejs.org/)
- [Vite 文档](https://vitejs.dev/)
- [Leaflet 文档](https://leafletjs.com/)
- [Flask 文档](https://flask.palletsprojects.com/)

## 功能展示

### 1. 首页
- 展示系统数据统计（运营机构、线路、站点、班次等）
- 提供快速访问按钮（浏览线路、查找站点、地图视图）
- 显示系统信息（数据来源、覆盖区域、数据类型、更新频率）

### 2. 线路管理
- **线路列表**:
  - 网格布局展示所有线路
  - 支持按线路编号或名称搜索
  - 支持按类型筛选（公交、轻轨/地铁、有轨电车、缆车）
  - 分页功能（10/20/50/100 条/页）
  - 响应式设计（移动端自动切换为单列）

- **线路详情**:
  - 显示线路完整信息（ID、名称、编号、类型、类别等）
  - 方向选择（单选按钮组）
  - 站点列表（时间轴展示，按顺序排列）
  - 线路颜色徽章显示

### 3. 站点管理
- **站点列表**:
  - 网格布局展示所有站点
  - 支持按站点名称或编号搜索
  - 分页功能
  - 显示站点位置（经纬度）

- **站点详情**:
  - 显示站点完整信息
  - 列出经过该站点的所有线路
  - 点击线路可跳转到线路详情

### 4. 地图功能（开发中）
- 在地图上显示站点位置
- 显示线路轨迹
- 实时车辆位置标记
- 点击查看详细信息
- 按线路筛选显示

### 5. 实时监控（计划中）
- 实时车辆位置追踪
- 车辆速度显示
- 延误信息提示
- 到站时间预测

## 许可证

本项目仅供学习和研究使用。

## 贡献

欢迎提交 Issue 和 Pull Request。

### 贡献指南

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'feat: 添加某个功能'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 提交规范

使用 Conventional Commits 规范：
- `feat`: 新功能
- `fix`: 修复 bug
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 重构
- `perf`: 性能优化
- `test`: 测试相关
- `chore`: 构建/工具相关

## 联系方式

如有问题或建议，请通过 Issue 联系。

---

**项目状态**: 活跃开发中

**最后更新**: 2025-11-19
