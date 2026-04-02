---
name: gtfs-fullstack-slice
description: 在 gtfs_new 仓库中处理项目级完整业务切片时使用。适用于新增或调整票价查询、数据看板、首页入口、收藏、通知、审计、换乘、可达性、线路对比、导出等功能，需要同时联动 Flask API、Vue 页面、Axios/Pinia、路由、权限、SQL 或 README。
---

# GTFS Fullstack Slice

这个 skill 面向当前项目最常见的工作方式: 在一套已经完成度较高的 Flask + Vue 应用里，把一条业务链从后端到前端改完整，而不是重新搭骨架。

## 默认判断

- 先落到已有模块，不先发明新层级。
- 默认主用地区只有 `sf` 和 `sydney`，`nyc` 继续按预留处理。
- 最近高频改动集中在票价、数据看板、首页入口、审计记录、通知、导出和分析工具，这些需求通常会同时影响 API 契约和页面接入。

## 后端落点

- 路由入口优先看 `backend/api/app.py`。
- 查询拼装类改动，优先沿用现有 `success_response` / `error_response` 风格。
- 复杂计算优先放 `backend/business_logic/` 或 `backend/services/`，不要继续堆进路由。
- 配置继续走 `backend/core/config.py` 的优先级: 环境变量 > `config.local.json` > `config.json`。
- 需要数据库变更时，把 SQL 放进 `backend/database/` 或 `backend/auth/` 对应 schema，并确认初始化顺序是否受影响。

## 前端落点

- 页面改动优先落在 `frontend/src/views/`。
- 接口改动同步更新 `frontend/src/api/`；只有跨页复用状态时再进 `frontend/src/stores/`。
- 新页面要补 `frontend/src/router/index.js`，并明确是否需要 `requiresAuth` 或 `requiresAdmin`。
- 大多数请求不要手动补 `region`，项目里已经在 `frontend/src/api/index.js` 自动透传。
- 用户可见文案需要确认是否同步到 `frontend/src/i18n/`。

## 必查约束

- 除登录页外，大部分页面默认都要求登录。
- 管理页需要管理员角色。
- 路由切换会自动写审计，不要破坏现有守卫和上报链路。
- 地区切换走 `regionStore`，默认地区是 `sf`。
- 如果改动改变了仓库当前完成情况，要同步根 `README.md`，必要时补 `backend/README.md` 或 `frontend/README.md`。

## 推荐流程

1. 先判断需求属于哪条业务链: GTFS 基础查询、实时/准点率、出行工具、用户体系、管理后台。
2. 先定后端契约，再改前端调用，再改页面展示和文案。
3. 如果新增字段会影响列表、详情、导出、筛选或首页入口，统一检查相关页面。
4. 只做和目标直接相关的改动，不顺手做无关重构。

## 验证基线

- 后端改动至少检查 `/api/health` 和受影响接口。
- 前端改动至少执行一次 `cd frontend && npm run build`。
- 链路较大时，补跑 `backend/tests/test_api_quick.py` 或最接近的脚本式测试。

## 输出偏好

- 说明优先说影响范围、验证结果、剩余风险。
- 如果需要提交信息，延续短中文主题风格。
