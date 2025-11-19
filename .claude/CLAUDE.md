# 项目上下文 - GTFS 公交数据分析系统

## 项目概述

这是一个基于 GTFS (General Transit Feed Specification) 的公交数据分析系统，主要用于获取、存储和分析旧金山湾区的公交实时数据。项目采用前后端分离架构，包含 Python 后端 API 服务和 Vue3 前端应用。

## 项目目标

1. 从 511 SF Bay API 获取 GTFS 静态数据和实时数据
2. 将 GTFS 静态数据存储到 PostgreSQL 数据库中，避免每次都解析 ZIP 文件
3. 实时计算公交车辆的速度
4. 提供 RESTful API 接口供前端调用
5. 开发 Vue3 前端应用展示公交数据和实时信息

## 技术栈

### 后端
- **语言**: Python 3
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
- **构建工具**: Vite
- **UI 组件库**: Element Plus
- **状态管理**: Pinia
- **路由**: Vue Router
- **地图**: Leaflet / Mapbox GL JS
- **HTTP 客户端**: Axios
- **样式**: CSS3 / SCSS

## 项目结构

```
.
├── .claude/                    # Claude Code 配置目录
│   ├── CLAUDE.md              # 项目上下文文档（本文件）
│   └── settings.local.json    # 本地设置
├── backend/                   # 后端目录（Python）
│   ├── gtfs_data/            # GTFS 数据存储目录
│   │   ├── gtfs_SF_20251119.zip  # GTFS 静态数据压缩包
│   │   └── gtfs_SF/          # 解压后的 GTFS 数据
│   ├── gtfs_data_fetcher.py  # GTFS 数据获取工具
│   ├── gtfs_importer.py      # GTFS 数据导入 PostgreSQL 工具
│   ├── speed_calculator.py   # 车辆速度计算模块
│   ├── db.py                 # 数据库连接池管理
│   ├── api.py                # Flask RESTful API 服务
│   ├── example_usage.py      # 使用示例
│   ├── schema.sql            # PostgreSQL 数据库表结构
│   ├── requirements.txt      # Python 依赖
│   └── API_DOCUMENTATION.md  # API 接口文档
├── frontend/                  # 前端目录（Vue3）
│   ├── src/
│   │   ├── api/              # API 请求封装
│   │   ├── assets/           # 静态资源
│   │   ├── components/       # Vue 组件
│   │   ├── views/            # 页面视图
│   │   ├── router/           # 路由配置
│   │   ├── stores/           # Pinia 状态管理
│   │   ├── utils/            # 工具函数
│   │   ├── App.vue           # 根组件
│   │   └── main.js           # 入口文件
│   ├── public/               # 公共资源
│   ├── index.html            # HTML 模板
│   ├── vite.config.js        # Vite 配置
│   └── package.json          # 前端依赖
├── README.md                 # 项目说明文档
└── README_POSTGRESQL.md      # PostgreSQL 安装配置指南
```

## 核心模块说明

### 后端模块

#### 1. gtfs_data_fetcher.py
- **功能**: 从 511 SF Bay API 获取 GTFS 数据
- **主要类**: `GTFSDataFetcher`
- **支持的操作**:
  - 下载 GTFS 静态数据（ZIP 格式）
  - 获取 GTFS Realtime 数据（车辆位置、行程更新、服务警报）
  - 解析车辆位置和行程更新数据
- **API Key**: 需要从 https://511.org/open-data/token 获取

#### 2. gtfs_importer.py
- **功能**: 将 GTFS 静态数据导入 PostgreSQL 数据库
- **主要类**: `GTFSImporter`
- **支持的操作**:
  - 从 ZIP 文件或目录导入数据
  - 自动处理表依赖关系
  - 批量插入优化性能
  - 导入前清空数据
  - 导入后验证数据
- **使用方法**: `python gtfs_importer.py --zip gtfs_data/gtfs_SF_20251119.zip`

#### 3. speed_calculator.py
- **功能**: 基于连续 GPS 位置计算车辆速度
- **主要类**: `SpeedCalculator`
- **算法**: 使用 Haversine 公式计算两点间距离
- **特性**:
  - 维护车辆位置历史
  - 过滤 GPS 错误（最大速度限制）
  - 处理停止状态（最小距离阈值）
  - 最小时间间隔控制

#### 4. db.py
- **功能**: 数据库连接池管理
- **主要类**: `Database`
- **特性**:
  - 连接池管理（SimpleConnectionPool）
  - 查询工具函数（execute_query, execute_query_one, execute_count）
  - 自动连接管理和归还

#### 5. api.py
- **功能**: Flask RESTful API 服务
- **端口**: 5000（默认）
- **主要接口**:
  - `/api/health`: 健康检查
  - `/api/agencies`: 运营机构查询
  - `/api/routes`: 线路查询（支持分页、搜索、筛选）
  - `/api/stops`: 站点查询（支持地理位置筛选）
  - `/api/trips`: 班次查询
  - `/api/shapes`: 线路轨迹查询
  - `/api/calendar`: 服务日历查询
  - `/api/stats`: 数据统计
- **特性**:
  - CORS 跨域支持
  - 统一响应格式
  - 分页支持
  - 错误处理

#### 6. schema.sql
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

### 前端模块

#### 1. API 请求层 (src/api/)
- **api/index.js**: Axios 实例配置
- **api/routes.js**: 线路相关 API
- **api/stops.js**: 站点相关 API
- **api/trips.js**: 班次相关 API
- **api/realtime.js**: 实时数据 API

#### 2. 组件层 (src/components/)
- **RouteList.vue**: 线路列表组件
- **RouteDetail.vue**: 线路详情组件
- **StopList.vue**: 站点列表组件
- **StopDetail.vue**: 站点详情组件
- **MapView.vue**: 地图展示组件
- **VehicleMarker.vue**: 车辆标记组件
- **SearchBar.vue**: 搜索栏组件

#### 3. 视图层 (src/views/)
- **Home.vue**: 首页
- **Routes.vue**: 线路页面
- **Stops.vue**: 站点页面
- **Map.vue**: 地图页面
- **Realtime.vue**: 实时监控页面

#### 4. 状态管理 (src/stores/)
- **routeStore.js**: 线路状态管理
- **stopStore.js**: 站点状态管理
- **realtimeStore.js**: 实时数据状态管理
- **mapStore.js**: 地图状态管理

#### 5. 路由 (src/router/)
- **index.js**: 路由配置
- 路由守卫
- 懒加载配置

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

### Vue3 / JavaScript 代码规范
- 使用 Vue 3 Composition API
- 使用 `<script setup>` 语法
- 组件名使用 PascalCase
- 文件名使用 PascalCase（组件）或 camelCase（工具函数）
- 使用 ES6+ 语法
- 使用 async/await 处理异步操作
- 所有注释使用中文
- 使用 JSDoc 注释函数

### SQL 规范
- 表名使用小写下划线命名
- 所有表和字段都有中文注释
- 使用外键约束保证数据完整性
- 为常用查询创建索引

### 命名约定

#### 后端（Python）
- 类名: PascalCase (如 `GTFSImporter`)
- 函数名: snake_case (如 `calculate_speed`)
- 常量: UPPER_SNAKE_CASE (如 `EARTH_RADIUS_METERS`)
- 私有方法: 前缀下划线 (如 `_haversine_distance`)

#### 前端（Vue3/JavaScript）
- 组件名: PascalCase (如 `RouteList.vue`)
- 变量/函数: camelCase (如 `fetchRoutes`)
- 常量: UPPER_SNAKE_CASE (如 `API_BASE_URL`)
- 私有变量: 前缀下划线 (如 `_internalState`)
- Store: camelCase + Store 后缀 (如 `routeStore`)
- API 文件: camelCase (如 `routes.js`)

## 开发工作流

### 1. 后端环境设置
```bash
# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装依赖
cd backend
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

### 3. 启动后端服务
```bash
# 启动 Flask API 服务
python api.py

# 服务将运行在 http://localhost:5000
```

### 4. 前端环境设置
```bash
# 安装 Node.js 依赖
cd frontend
npm install

# 或使用 pnpm
pnpm install
```

### 5. 启动前端开发服务器
```bash
# 开发模式
npm run dev

# 前端将运行在 http://localhost:5173
```

### 6. 构建前端生产版本
```bash
# 构建生产版本
npm run build

# 预览生产版本
npm run preview
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

## 前端功能规划

### 核心功能
1. **线路查询**: 浏览所有公交线路，支持搜索和筛选
2. **站点查询**: 查看所有站点，支持地图展示和地理位置搜索
3. **线路详情**: 查看线路的详细信息、站点列表、运行轨迹
4. **站点详情**: 查看站点的详细信息、经过的线路
5. **地图展示**: 在地图上展示线路、站点、车辆位置
6. **实时监控**: 实时显示车辆位置和速度
7. **时刻表查询**: 查看班次时刻表

### UI/UX 设计
- **响应式设计**: 支持桌面和移动端
- **深色模式**: 支持浅色/深色主题切换
- **国际化**: 支持中英文切换
- **无障碍**: 遵循 WCAG 2.1 标准

### 性能优化
- **虚拟滚动**: 大列表使用虚拟滚动
- **懒加载**: 路由和组件懒加载
- **缓存策略**: API 响应缓存
- **防抖节流**: 搜索和地图操作优化

## 未来扩展方向

1. **数据分析**: 分析延误模式、速度分布等
2. **预测模型**: 基于历史数据预测到站时间
3. **多运营商支持**: 扩展支持更多公交运营商
4. **实时数据存储**: 将实时数据存储到时序数据库
5. **用户系统**: 用户注册、登录、收藏功能
6. **通知推送**: 线路延误、到站提醒等
7. **数据可视化**: 图表展示统计数据
8. **移动应用**: 开发 iOS/Android 原生应用

## 故障排查

### 后端问题

#### 数据库连接失败
- 检查 PostgreSQL 是否运行: `brew services list`
- 检查数据库是否存在: `psql -l`
- 查看日志: `tail -f /opt/homebrew/var/log/postgresql@16.log`

#### API 请求失败
- 检查 API Key 是否有效
- 检查网络连接
- 查看 API 响应状态码和错误信息

#### 导入数据失败
- 检查 ZIP 文件路径是否正确
- 确认数据库表已创建
- 使用 `--clean` 选项清空现有数据

#### Flask 服务无法启动
- 检查端口 5000 是否被占用: `lsof -i :5000`
- 检查 Python 依赖是否安装完整
- 查看错误日志

### 前端问题

#### 开发服务器无法启动
- 检查 Node.js 版本（需要 16+）
- 删除 `node_modules` 和 `package-lock.json` 重新安装
- 检查端口 5173 是否被占用

#### API 请求跨域错误
- 确认后端 Flask 已启用 CORS
- 检查 API 基础 URL 配置是否正确
- 查看浏览器控制台错误信息

#### 地图无法显示
- 检查地图 API Key 是否配置
- 检查网络连接
- 查看浏览器控制台错误信息

#### 构建失败
- 检查代码语法错误
- 确认所有依赖已安装
- 清除缓存: `npm run clean` 或删除 `dist` 目录

## 相关文档

- [PostgreSQL 安装配置指南](../backend/README_POSTGRESQL.md)
- [项目 README](../README.md)
- [API 接口文档](../backend/API_DOCUMENTATION.md)
- [GTFS 规范文档](https://gtfs.org/reference/static)
- [511 SF Bay API 文档](https://511.org/open-data/transit)
- [Vue 3 官方文档](https://vuejs.org/)
- [Element Plus 文档](https://element-plus.org/)
- [Pinia 文档](https://pinia.vuejs.org/)

## 注意事项

### 通用
1. **中文注释**: 所有代码注释使用中文
2. **数据隐私**: 不要提交包含真实 API Key 的代码
3. **Git 管理**: `.venv`、`gtfs_data`、`node_modules`、`dist` 目录应在 `.gitignore` 中
4. **数据库备份**: 定期备份数据库数据

### 后端
1. **API 设计**: 遵循 RESTful 规范
2. **错误处理**: 统一错误响应格式
3. **性能优化**: 使用连接池、分页、索引
4. **安全性**: 防止 SQL 注入、XSS 攻击

### 前端
1. **组件化**: 遵循单一职责原则，组件粒度适中
2. **状态管理**: 合理使用 Pinia，避免过度使用全局状态
3. **性能优化**: 使用虚拟滚动、懒加载、防抖节流
4. **用户体验**: 加载状态、错误提示、空状态处理
5. **响应式**: 适配不同屏幕尺寸
6. **无障碍**: 使用语义化 HTML，添加 ARIA 属性

## 开发规范

### Git 提交规范
使用 Conventional Commits 规范：
- `feat`: 新功能
- `fix`: 修复 bug
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 重构
- `perf`: 性能优化
- `test`: 测试相关
- `chore`: 构建/工具相关

示例：
```
feat(frontend): 添加线路列表组件
fix(api): 修复站点查询分页问题
docs: 更新 API 文档
```

### 代码审查要点
1. **功能完整性**: 是否实现了需求
2. **代码质量**: 是否遵循编码规范
3. **性能**: 是否有性能问题
4. **安全性**: 是否有安全隐患
5. **测试**: 是否有足够的测试覆盖
6. **文档**: 是否更新了相关文档
