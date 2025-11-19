# GTFS 公交数据分析系统 - 前端

基于 Vue 3 + Vite + Element Plus 的公交数据可视化前端应用。

## 快速启动

### 前置要求

- Node.js 16+
- npm 或 pnpm
- 后端 API 服务已启动（运行在 http://localhost:5000）

### 完整启动步骤

```bash
# 1. 进入前端目录
cd frontend

# 2. 安装依赖
npm install
# 或使用 pnpm
pnpm install

# 3. 启动开发服务器
npm run dev
```

**前端应用将运行在**: http://localhost:5173

### 快速启动（已安装依赖）

```bash
cd frontend
npm run dev
```

### 构建生产版本

```bash
# 构建
npm run build

# 预览构建结果
npm run preview
```

### 验证应用

打开浏览器访问 http://localhost:5173，你应该能看到：
- 首页显示数据统计
- 可以浏览线路列表
- 可以查看站点信息

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

## 环境变量

创建 `.env.local` 文件配置环境变量：

```bash
# API 基础 URL
VITE_API_BASE_URL=http://localhost:5000/api
```

## 目录说明

- **api/**: API 请求封装，统一管理所有后端接口调用
- **assets/**: 静态资源文件（图片、字体等）
- **components/**: 可复用的 Vue 组件
- **views/**: 页面级组件
- **router/**: Vue Router 路由配置
- **stores/**: Pinia 状态管理
- **utils/**: 工具函数和辅助方法

## 相关文档

- [项目主 README](../README.md)
- [后端 API 文档](../backend/API_DOCUMENTATION.md)
- [Vue 3 文档](https://vuejs.org/)
- [Element Plus 文档](https://element-plus.org/)
- [Pinia 文档](https://pinia.vuejs.org/)
- [Vite 文档](https://vitejs.dev/)

## 许可证

本项目遵循项目主许可证。
