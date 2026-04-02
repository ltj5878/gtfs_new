---
name: gtfs-frontend-page
description: 在 gtfs_new 仓库中处理 Vue 页面、组件、入口卡片、数据看板或管理页时使用。适用于页面改版、列表详情联动、路由接入、状态同步、i18n/主题收口，以及保持现有登录态、region 和管理员权限约束。
---

# GTFS Frontend Page

这个 skill 用于前端页面迭代，特别适合你现在这种“数据看板、入口布局、页面修正、卡片调整”节奏。

## 目标

- 在不推翻现有视觉语言的前提下，让页面更清楚、更能承载公交业务信息。
- 保持页面和后端契约同步，不做只改界面不顾数据流的表层修改。

## 现有前端约束

- 使用 Vue 3 + Vite + Element Plus + Pinia + Vue Router。
- 默认写法是 `<script setup>`、2 空格缩进、单引号、无分号。
- 大多数页面要求登录；管理页还要求管理员权限。
- `region` 默认通过 Axios 拦截器自动补充。
- 路由切换后会自动上报审计，不要破坏现有 `router.afterEach`。

## 页面改动时先查什么

- 页面入口在 `frontend/src/views/`。
- 复用能力看 `frontend/src/components/`。
- 接口封装看 `frontend/src/api/`。
- 跨页状态看 `frontend/src/stores/`。
- 路由准入和管理员限制看 [frontend/src/router/index.js](frontend/src/router/index.js)。

## 页面实现偏好

- 优先让筛选、表格、图表、地图、详情之间的关系更清晰。
- 需要复用两次以上的视图片区块，再抽成组件。
- 只在确实跨页面复用时才新建 store。
- 页面里如果出现重复的状态逻辑，优先压缩成清晰的 `loading / empty / error / ready` 四态。
- 管理页和普通业务页分开处理，不混用入口和权限判断。

## 文案与展示

- 用户可见文案优先保持中文风格统一，必要时补到 `frontend/src/i18n/`。
- 主题切换已存在，新增样式时不要只顾浅色模式。
- 当前项目偏实用型信息界面，避免为了“高级感”破坏信息密度和可读性。

## 常见联动检查

- 新页面是否加了路由。
- 新 API 是否封装进 `src/api/` 而不是直接在页面里散写。
- 新字段是否影响列表页、详情页、导出页或首页卡片。
- 如果页面依赖管理员能力，是否加了 `requiresAdmin`。
- 如果页面依赖地区，是否错误地绕过了 `regionStore`。

## 验证基线

- 至少执行一次 `cd frontend && npm run build`。
- 如果是关键入口页，顺手检查首页导航、卡片入口和返回路径是否顺畅。
- 如果涉及权限，分别按未登录、普通用户、管理员三种状态过一遍逻辑。
