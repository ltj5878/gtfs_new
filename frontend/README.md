# 前端应用

基于 Vue 3 + Vite + Element Plus 的 GTFS 公交数据可视化前端，支持多地区切换、实时监控、准点率分析等功能。

## 技术栈

| 依赖 | 版本 | 用途 |
|------|------|------|
| Vue 3 | ^3.4.0 | 框架（Composition API + script setup） |
| Vite | ^5.0.0 | 构建工具 |
| Element Plus | ^2.5.0 | UI 组件库 |
| Pinia | ^2.1.7 | 状态管理 |
| Vue Router | ^4.2.5 | 路由 |
| Axios | ^1.6.2 | HTTP 请求 |
| ECharts | ^6.0.0 | 数据图表 |
| Leaflet | ^1.9.4 | 地图展示 |

## 目录结构

```
src/
├── api/
│   ├── index.js          # Axios 实例，自动附加 region 参数
│   ├── common.js         # 健康检查、统计、地区列表
│   ├── routes.js         # 线路相关接口
│   ├── stops.js          # 站点相关接口
│   ├── trips.js          # 班次相关接口
│   ├── punctuality.js    # 准点率相关接口
│   ├── favorites.js      # 收藏相关接口
│   ├── auth.js           # 认证相关接口
│   ├── users.js          # 用户管理接口
│   └── admin.js          # 管理员接口
├── stores/
│   ├── appStore.js       # 全局状态（统计数据、机构信息）
│   ├── authStore.js      # 用户认证状态
│   ├── regionStore.js    # 地区选择（持久化到 localStorage）
│   ├── routeStore.js     # 线路数据
│   ├── stopStore.js      # 站点数据
│   ├── punctualityStore.js # 准点率数据
│   └── favoriteStore.js  # 收藏数据
├── views/
│   ├── Home.vue                   # 首页（数据统计总览）
│   ├── Login.vue                  # 登录页
│   ├── Routes.vue                 # 线路列表（搜索、类型筛选、分页）
│   ├── RouteDetail.vue            # 线路详情（站点时刻表、方向切换）
│   ├── RoutePunctuality.vue       # 线路准点率列表
│   ├── RoutePunctualityDetail.vue # 线路准点率详情
│   ├── Stops.vue                  # 站点列表
│   ├── StopDetail.vue             # 站点详情（经过线路）
│   ├── StopPunctuality.vue        # 站点准点率列表
│   ├── StopPunctualityDetail.vue  # 站点准点率详情
│   ├── PunctualityOverview.vue    # 准点率总览（ECharts 图表）
│   ├── RealtimeMonitor.vue        # 实时监控（车辆位置与速度）
│   ├── Map.vue                    # 地图视图（Leaflet）
│   ├── Favorites.vue              # 我的收藏
│   ├── UserManagement.vue         # 用户管理（管理员）
│   └── AdminDashboard.vue         # 管理员后台
├── components/
│   ├── RegionSelector.vue  # 地区切换下拉组件
│   ├── RouteCard.vue       # 线路卡片
│   ├── StopCard.vue        # 站点卡片
│   └── SearchBar.vue       # 搜索栏
├── router/
│   └── index.js            # 路由配置（含权限守卫）
├── App.vue                 # 根组件（导航栏 + 地区选择器）
└── main.js                 # 入口文件
```

## 安装与启动

```bash
# 安装依赖
npm install

# 开发模式（需后端已启动）
npm run dev

# 构建生产包
npm run build

# 预览构建结果
npm run preview
```

开发服务器运行在 http://localhost:5173，后端代理到 http://localhost:5001。

## 多地区架构

地区切换通过 `regionStore` 统一管理：

1. `RegionSelector.vue` 提供切换 UI，当前支持旧金山湾区和悉尼
2. `api/index.js` 拦截器自动在每个请求中附加 `?region=xxx`
3. 切换地区后自动刷新统计数据和机构信息
4. 选择结果持久化到 `localStorage`，刷新页面不丢失

## 页面功能

| 页面 | 路径 | 说明 |
|------|------|------|
| 首页 | `/` | 数据统计卡片，快速入口 |
| 线路列表 | `/routes` | 搜索、类型筛选、分页 |
| 线路详情 | `/routes/:id` | 站点时刻表、方向切换 |
| 线路准点率 | `/punctuality/routes` | 线路维度准点率排行 |
| 站点列表 | `/stops` | 搜索、分页 |
| 站点详情 | `/stops/:id` | 经过线路列表 |
| 站点准点率 | `/punctuality/stops` | 站点维度准点率 |
| 准点率总览 | `/punctuality/overview` | ECharts 图表，按时段分布 |
| 实时监控 | `/realtime` | 车辆实时位置与速度 |
| 地图 | `/map` | Leaflet 地图，站点与轨迹 |
| 我的收藏 | `/favorites` | 收藏的线路和站点 |
| 用户管理 | `/admin/users` | 管理员功能 |

## 状态管理

所有 Store 使用 Pinia Composition API 风格：

- **regionStore**：核心 Store，地区切换影响所有数据请求
- **authStore**：登录状态管理，路由守卫依赖此 Store
- **appStore**：全局统计数据，地区切换时自动重新拉取

## 开发规范

- 使用 `<script setup>` 语法
- 组件名 PascalCase，文件名同组件名
- 变量/函数 camelCase，常量 UPPER_SNAKE_CASE
- 所有注释使用中文
- Store 文件命名：`xxxStore.js`
