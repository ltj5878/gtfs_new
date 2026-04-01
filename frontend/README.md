# 前端应用

`frontend/` 是项目的 Vue 3 前端，当前分支已经覆盖数据浏览、实时监控、准点率分析、出行工具、通知中心和管理员后台，不再只是一个基础 GTFS 查询页面集合。

## 当前完成情况

### 已实现页面能力

| 模块 | 状态 | 说明 |
|------|------|------|
| 登录注册 | 已完成 | 登录、注册、登出、管理员识别 |
| GTFS 数据浏览 | 已完成 | 线路、站点、详情、地图、时刻分析 |
| 实时功能 | 已完成 | 实时监控、车辆历史回放 |
| 准点率分析 | 已完成 | 概览、线路、站点、趋势、详情 |
| 出行工具 | 已完成 | 收藏、换乘规划、站点可达性、线路对比、数据导出 |
| 管理后台 | 已完成 | 运维看板、用户管理、审计日志 |
| 全局体验 | 已完成 | 地区切换、中英文切换、明暗主题、通知铃铛 |

### 当前可选地区

| 地区 | 前端是否开放 |
|------|--------------|
| `sf` | 是 |
| `sydney` | 是 |
| `nyc` | 否，当前在 `regionStore` 中被过滤 |

## 技术栈

| 技术 | 用途 |
|------|------|
| Vue 3 | UI 框架 |
| Vite | 开发与构建 |
| Element Plus | 组件库 |
| Pinia | 状态管理 |
| Vue Router | 路由与权限守卫 |
| Vue I18n | 中英文切换 |
| Axios | API 请求 |
| ECharts | 图表可视化 |
| Leaflet + leaflet.heat | 地图与热力图 |
| xlsx | Excel 导出 |
| jsPDF | PDF 导出工具基础能力 |

## 目录结构

```text
frontend/
├── public/
│   └── fonts/
├── src/
│   ├── api/
│   │   ├── index.js         # Axios 实例、token 注入、region 自动附加
│   │   ├── common.js        # 地区、统计、机构
│   │   ├── routes.js        # 线路接口
│   │   ├── stops.js         # 站点接口
│   │   ├── trips.js         # 班次接口
│   │   ├── punctuality.js   # 准点率和实时接口
│   │   ├── auth.js          # 登录注册
│   │   ├── favorites.js     # 收藏
│   │   ├── subscription.js  # 订阅
│   │   ├── notification.js  # 通知与公告
│   │   ├── admin.js         # 运维后台
│   │   ├── users.js         # 用户管理
│   │   ├── audit.js         # 审计日志
│   │   ├── planner.js       # 换乘规划
│   │   └── analysis.js      # 可达性分析
│   ├── components/
│   │   ├── NotificationBell.vue
│   │   ├── RegionSelector.vue
│   │   ├── RouteCard.vue
│   │   ├── SearchBar.vue
│   │   ├── StopCard.vue
│   │   └── SubscribeButton.vue
│   ├── i18n/
│   ├── router/
│   │   └── index.js         # 路由表、登录守卫、管理员守卫、页面访问审计
│   ├── stores/
│   │   ├── appStore.js
│   │   ├── authStore.js
│   │   ├── favoriteStore.js
│   │   ├── notificationStore.js
│   │   ├── punctualityStore.js
│   │   ├── regionStore.js
│   │   ├── routeStore.js
│   │   ├── stopStore.js
│   │   └── themeStore.js
│   ├── styles/
│   ├── utils/
│   │   └── exportHelper.js
│   ├── views/
│   ├── App.vue               # 顶部导航、地区切换、主题切换、通知入口
│   └── main.js
├── index.html
├── package.json
└── vite.config.js
```

## 安装与启动

```bash
cd frontend
npm install
npm run dev
```

其他命令：

```bash
npm run build
npm run preview
```

默认地址：

- 前端开发服务器：http://localhost:5173
- 默认后端代理：http://localhost:5001

如果需要指定后端地址，可通过 `VITE_API_BASE_URL` 覆盖默认 `http://localhost:5001/api`。

## 路由与页面

当前路由定义在 `src/router/index.js`，除登录页外，页面默认都要求登录。

### 认证与首页

| 路径 | 页面 |
|------|------|
| `/login` | 登录/注册 |
| `/` | 首页 |

### 线路与站点

| 路径 | 页面 |
|------|------|
| `/routes` | 线路列表 |
| `/routes/:id` | 线路详情 |
| `/stops` | 站点列表 |
| `/stops/:id` | 站点详情 |
| `/map` | 地图视图 |
| `/heatmap` | 站点热力图 |
| `/schedule` | 线路运营时间分析 |
| `/playback` | 车辆历史回放 |

### 准点率

| 路径 | 页面 |
|------|------|
| `/punctuality` | 准点率概览 |
| `/punctuality/routes` | 线路准点率 |
| `/punctuality/routes/:routeId` | 线路准点率详情 |
| `/punctuality/stops` | 站点准点率 |
| `/punctuality/stops/:stopId` | 站点准点率详情 |
| `/punctuality/realtime` | 实时监控 |
| `/punctuality/trends` | 准点率趋势总览 |

### 出行工具

| 路径 | 页面 |
|------|------|
| `/favorites` | 我的收藏 |
| `/planner/transfer` | 换乘规划 |
| `/analysis/reachability` | 站点可达性分析 |
| `/compare/routes` | 线路对比 |
| `/export` | 数据导出 |

### 管理页

| 路径 | 页面 |
|------|------|
| `/admin` | 运维监控看板 |
| `/users` | 用户管理 |
| `/admin/audit-logs` | 审计日志 |

说明：

- `/admin`、`/users`、`/admin/audit-logs` 需要管理员角色
- 非管理员访问管理员页面会被重定向到首页

## 核心交互机制

### 1. 地区切换

- `RegionSelector.vue` 提供切换 UI
- `regionStore` 持久化 `selected_region`
- `api/index.js` 会自动给大部分请求追加 `region`
- 当前前端会过滤掉 `nyc`，只展示 `sf` 和 `sydney`

### 2. 认证与权限

- `authStore` 持久化 `auth_token`、`auth_username`、`auth_role`
- Axios 请求头自动附加 `Authorization: Bearer <token>`
- 401 响应会清理本地登录态并跳转 `/login`
- 路由守卫区分普通登录页和管理员页面

### 3. 审计与通知

- 路由切换后会异步调用审计接口记录页面访问
- 登录后自动拉取收藏和未读通知数量
- `NotificationBell.vue` 提供通知列表和一键已读
- `SubscribeButton.vue` 支持线路订阅和告警阈值设置

### 4. 全局体验

- 支持中英文切换
- 支持浅色 / 深色主题切换
- 顶部导航按业务模块分组

## 页面能力说明

### 基础浏览

- 首页展示统计概览和功能入口
- 线路列表支持搜索、分页、机构筛选、类型筛选
- 线路详情支持方向、站点和地图展示
- 站点详情展示基础信息和经过线路
- 地图页面支持线路和站点可视化
- 站点热力图展示站点服务频率
- 运营时间分析页面展示线路时段特征

### 实时与准点率

- 实时监控页面展示车辆和延误数据
- 历史回放页面按日期播放车辆轨迹
- 准点率概览页面展示系统级统计
- 线路和站点准点率页面支持排行、筛选和详情跳转
- 趋势总览页面展示多维趋势图表

### 出行与用户功能

- 收藏线路和站点
- 线路订阅与告警阈值设置
- 换乘规划
- 站点可达性分析
- 线路对比分析
- 数据导出页面支持导出路线、站点、准点率、机构、收藏、公告和审计日志

### 管理能力

- 运维看板展示数据库空间、API 健康、数据时效和错误记录
- 管理员可发布公告和触发准点率告警检查
- 用户管理页支持创建、启停、删除、密码管理
- 审计日志页查看关键操作与页面访问记录

## 状态管理

当前 Pinia Store 主要分工如下：

| Store | 用途 |
|------|------|
| `appStore` | 统计信息、机构列表 |
| `authStore` | 登录态、用户名、角色 |
| `favoriteStore` | 收藏列表与操作 |
| `notificationStore` | 通知列表、未读计数、已读操作 |
| `punctualityStore` | 实时车辆、延误、准点率概览和配置 |
| `regionStore` | 当前地区与地区列表 |
| `routeStore` | 线路列表、详情、方向、站点 |
| `stopStore` | 站点列表、详情、经过线路 |
| `themeStore` | 明暗主题 |

## 导出能力

`src/utils/exportHelper.js` 当前封装了：

- CSV 导出
- Excel 导出
- PDF 导出基础工具函数

当前 `DataExport.vue` 页面主流程使用 CSV 和 Excel 导出。

## 开发约定

- 使用 Vue 3 Composition API 和 `<script setup>`
- 使用 2 空格缩进、单引号、无分号
- 组件文件和视图文件使用 PascalCase
- Store 文件使用 `xxxStore.js`
- 中文文案为主，英文通过 `i18n` 维护

## 当前限制

- 前端当前不开放 `nyc` 地区选择
- 几乎所有业务页面依赖登录态
- 数据导出页面目前 UI 主流程只开放 CSV/Excel
- 运行依赖后端 `5001` 端口或相应的 `VITE_API_BASE_URL` 配置

## 相关文档

- [../README.md](../README.md)
- [../backend/README.md](../backend/README.md)
