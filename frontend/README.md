# GTFS 公交数据分析系统 - 前端

基于 Vue 3 + Vite + Element Plus 的公交数据可视化前端应用。

## 技术栈

- **Vue 3**: 渐进式 JavaScript 框架
- **Vite**: 下一代前端构建工具
- **Element Plus**: Vue 3 UI 组件库
- **Pinia**: Vue 状态管理库
- **Vue Router**: Vue 官方路由
- **Axios**: HTTP 客户端

## 项目结构

```
frontend/
├── src/
│   ├── api/              # API 请求封装
│   │   ├── index.js      # Axios 配置
│   │   ├── routes.js     # 线路 API
│   │   ├── stops.js      # 站点 API
│   │   ├── trips.js      # 班次 API
│   │   └── common.js     # 通用 API
│   ├── assets/           # 静态资源
│   ├── components/       # 公共组件
│   │   ├── SearchBar.vue # 搜索栏
│   │   ├── RouteCard.vue # 线路卡片
│   │   └── StopCard.vue  # 站点卡片
│   ├── views/            # 页面视图
│   │   ├── Home.vue      # 首页
│   │   ├── Routes.vue    # 线路列表
│   │   ├── RouteDetail.vue # 线路详情
│   │   ├── Stops.vue     # 站点列表
│   │   ├── StopDetail.vue  # 站点详情
│   │   └── Map.vue       # 地图视图
│   ├── router/           # 路由配置
│   │   └── index.js
│   ├── stores/           # Pinia 状态管理
│   │   ├── routeStore.js # 线路状态
│   │   ├── stopStore.js  # 站点状态
│   │   └── appStore.js   # 应用状态
│   ├── App.vue           # 根组件
│   └── main.js           # 入口文件
├── public/               # 公共资源
├── index.html            # HTML 模板
├── vite.config.js        # Vite 配置
└── package.json          # 项目依赖

## 快速开始

### 安装依赖

```bash
npm install
```

或使用 pnpm:

```bash
pnpm install
```

### 开发模式

```bash
npm run dev
```

应用将运行在 http://localhost:5173

### 构建生产版本

```bash
npm run build
```

### 预览生产版本

```bash
npm run preview
```

## 功能特性

### 已实现功能

- ✅ 首页数据统计展示
- ✅ 线路列表浏览（支持分页、搜索、筛选）
- ✅ 线路详情查看（包含方向、站点列表）
- ✅ 站点列表浏览（支持分页、搜索）
- ✅ 站点详情查看（包含经过的线路）
- ✅ 响应式设计（支持移动端）
- ✅ 统一的错误处理
- ✅ 加载状态提示

### 待开发功能

- ⏳ 地图展示（Leaflet 集成）
- ⏳ 实时车辆位置
- ⏳ 线路轨迹显示
- ⏳ 班次时刻表查询
- ⏳ 深色模式
- ⏳ 国际化支持

## API 配置

后端 API 地址配置在 `vite.config.js` 中：

```javascript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:5000',
      changeOrigin: true
    }
  }
}
```

也可以通过环境变量 `VITE_API_BASE_URL` 配置。

## 开发规范

### 组件命名

- 组件文件名使用 PascalCase: `RouteCard.vue`
- 组件使用 `<script setup>` 语法
- 使用 Composition API

### 代码风格

- 使用 ES6+ 语法
- 使用 async/await 处理异步
- 所有注释使用中文
- 使用 JSDoc 注释函数

### Git 提交

遵循 Conventional Commits 规范：

```
feat(frontend): 添加线路列表组件
fix(frontend): 修复分页问题
docs: 更新前端文档
```

## 浏览器支持

- Chrome >= 87
- Firefox >= 78
- Safari >= 14
- Edge >= 88

## 许可证

本项目遵循项目主许可证。
