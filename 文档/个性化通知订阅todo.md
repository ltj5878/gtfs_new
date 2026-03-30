# 个性化通知订阅 todo

## 1. 核心目标
允许登录用户订阅关注线路的准点率阈值，当某线路低于阈值时生成站内通知，并在页面顶部显示未读数。

---

## 2. 当前可复用基础
- 项目已有登录认证体系：`backend/auth`、`verify_token`
- 后端已有 `_get_current_user()` 和收藏功能相关认证写法
- 准点率数据已在 `route_daily_punctuality` 中具备
- 前端已有用户态、收藏页、首页入口体系

---

## 3. 数据库实现 ToDo
- [ ] 在 `backend/database/` 新增通知相关 SQL，例如 `notification_schema.sql`
- [ ] 创建 `user_subscriptions` 表：
  - `id`
  - `user_id`
  - `region`
  - `route_id`
  - `threshold`
  - `is_active`
  - `created_at`
- [ ] 创建 `user_notifications` 表：
  - `id`
  - `user_id`
  - `region`
  - `route_id`
  - `title`
  - `content`
  - `is_read`
  - `created_at`
- [ ] 增加唯一约束，避免同一用户重复订阅同一线路

---

## 4. 后端实现 ToDo
- [ ] 在 `backend/api/app.py` 增加订阅接口：
  - `GET /api/notifications/subscriptions`
  - `POST /api/notifications/subscriptions`
  - `DELETE /api/notifications/subscriptions/<id>`
- [ ] 增加通知接口：
  - `GET /api/notifications`
  - `POST /api/notifications/<id>/read`
  - `POST /api/notifications/read-all`
- [ ] 复用 `_get_current_user()` 做鉴权
- [ ] 新增检测逻辑：
  - 遍历 `user_subscriptions`
  - 查询对应线路最近一天或最近一周准点率
  - 低于阈值则写入 `user_notifications`
- [ ] 首版可做手动触发接口或简单脚本，后续再挂到定时任务
- [ ] 做去重策略，避免同一天重复写入同一告警

---

## 5. 前端实现 ToDo
- [ ] 新增 `frontend/src/api/notifications.js`
- [ ] 新增 `frontend/src/stores/notificationStore.js`
- [ ] 在导航栏或 `App.vue` 增加通知角标和下拉面板
- [ ] 在线路详情页、线路准点率详情页增加“订阅此线路”按钮
- [ ] 新增通知中心页面 `frontend/src/views/Notifications.vue`
- [ ] 支持：
  - 查看未读/全部通知
  - 标记已读
  - 删除订阅
  - 修改阈值

---

## 6. 交互与规则 ToDo
- [ ] 未登录用户点击订阅时跳转登录页
- [ ] 阈值输入限制在合理区间，例如 `0-100`
- [ ] 通知文案明确标识地区、线路和触发日期
- [ ] 顶部未读数在登录后自动拉取

---

## 7. 验收标准
- [ ] 用户可以新增、查看、取消线路订阅
- [ ] 当线路准点率低于阈值时，系统能生成站内通知
- [ ] 未读数、通知列表和已读状态能正确联动
- [ ] 不同用户之间的订阅和通知互相隔离

---

## 8. 建议开发顺序
1. 先补数据库表和基础接口。
2. 再做线路订阅入口与通知列表。
3. 最后补自动检测任务和未读角标联动。
