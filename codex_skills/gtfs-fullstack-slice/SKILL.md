---
name: gtfs-fullstack-slice
description: 在 gtfs_new 仓库中做完整业务切片修改时使用。适用于新增或调整路线、站点、实时监控、准点率、收藏、通知、管理后台等功能，需要同时联动 Flask API、Vue 页面、Axios/Pinia、路由、SQL 或文档，并遵守本项目的 region、auth、audit 约束。
---

# GTFS Fullstack Slice

这个 skill 面向“从后端到前端一条链改完”的任务，不适合只改单个样式或只跑一次测试。

## 默认判断

- 先把需求落到已有模块，不要先拆架构。
- 这个仓库当前已经是完成度较高的业务系统，不按“新项目搭骨架”的思路处理。
- 默认主用地区只有 `sf` 和 `sydney`。`nyc` 目前是预留状态，除非用户明确要求，不要顺手放开。

## 后端工作方式

- 优先从 [backend/api/app.py](backend/api/app.py) 找对应接口和返回结构。
- 如果只是查询或拼装字段，先沿用现有 `success_response` / `error_response` 风格。
- 需要计算逻辑时，优先放进 `backend/business_logic/` 或 `backend/services/`，不要把复杂逻辑继续堆进路由里。
- 需要配置时，沿用 [backend/core/config.py](backend/core/config.py) 的优先级：环境变量 > `config.local.json` > `config.json`。
- 需要数据库变更时，把 SQL 放进 `backend/database/` 或 `backend/auth/` 的对应 schema 文件，说明初始化顺序是否受影响。

## 前端工作方式

- 页面优先落在 `frontend/src/views/`，共用交互放 `frontend/src/components/`。
- API 改动需要同步 `frontend/src/api/`；跨页面共享状态再考虑放 `frontend/src/stores/`。
- 新页面要补 `frontend/src/router/index.js`，并确认是否需要 `requiresAuth` 或 `requiresAdmin`。
- 不要手动给大多数请求补 `region`，项目里已经在 [frontend/src/api/index.js](frontend/src/api/index.js) 自动透传。
- 如果接口属于跳过名单，例如 `/auth`、`/admin`、`/users`、`/notifications`、`/subscriptions`、`/audit`，再单独判断是否要传 `region`。

## 必查约束

- 登录外的大部分页面默认都需要登录。
- 管理页需要管理员角色。
- 路由切换会自动记审计，新增页面时不要破坏这个机制。
- 地区切换走 `regionStore`，默认地区是 `sf`。
- 新增重复文案或中英文界面文案时，要看是否应同步到 `frontend/src/i18n/`。

## 推荐流程

1. 先定位需求属于哪条链路：基础 GTFS、实时、准点率、分析工具、用户体系、管理后台。
2. 先改后端契约，再改前端调用，再改页面展示。
3. 如果新增字段会影响列表、详情、导出、筛选，统一检查相关页面。
4. 如果改动已改变“当前完成情况”，同步更新 README，而不是只改代码。
5. 验证时跑最小闭环，不做无关重构。

## 验证基线

- 后端相关改动至少检查 `/api/health` 和受影响接口。
- 前端相关改动至少检查 `npm run build` 是否通过。
- 业务链路较大时，补跑 `backend/tests/test_api_quick.py` 或 `backend/tests/test_punctuality.py` 中最接近的脚本。

## 输出偏好

- 代码和注释保持简洁，中文注释只写必要信息。
- 变更说明优先说“影响范围、验证结果、剩余风险”。
- 如果需要提交信息，风格保持短中文主题，聚焦单一改动。
