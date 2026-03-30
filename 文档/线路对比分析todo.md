# 线路对比分析 todo

## 1. 核心目标
支持用户同时选择 2 到 4 条线路，横向对比准点率、总班次、平均延误、高峰时段表现、覆盖站点数等指标。

---

## 2. 当前可复用基础
- 已有线路准点率接口：`/api/punctuality/routes`
- 已有时段统计接口：`/api/punctuality/hourly`
- 已有线路站点接口：`/api/routes/<route_id>/stops`
- 前端已有准点率相关页面和图表风格：`RoutePunctuality.vue`、`RoutePunctualityDetail.vue`、`PunctualityTrends.vue`

---

## 3. 后端实现 ToDo
- [ ] 在 `backend/api/app.py` 新增 `GET /api/punctuality/routes/compare`
- [ ] 设计参数：
  - `route_ids=1,2,3`
  - `region`
  - `days` 或 `startDate/endDate`
- [ ] 汇总每条线路的核心指标：
  - 平均准点率
  - 总班次数
  - 平均延误分钟
  - 最大延误分钟
  - 覆盖站点数
  - 早高峰/晚高峰平均准点率
- [ ] 复用 `route_daily_punctuality` 和 `hourly_punctuality_stats`，避免重复造表
- [ ] 若接口返回图表直接可用的数据结构更方便，可同步返回：
  - 雷达图指标数组
  - 柱状图系列数据
- [ ] 做输入校验：
  - 至少 2 条线路
  - 最多 4 条线路
  - 线路必须属于同一 `region`

---

## 4. 前端实现 ToDo
- [ ] 新增页面 `frontend/src/views/RouteCompare.vue`
- [ ] 在 `frontend/src/router/index.js` 增加路由，例如 `/punctuality/routes/compare`
- [ ] 在 `frontend/src/api/punctuality.js` 增加 compare 方法
- [ ] 增加线路多选组件，数据源复用 `routes` 接口
- [ ] 图表展示至少包括：
  - 指标对比卡片
  - 柱状图：平均准点率、总班次数
  - 折线图或分组柱图：高峰时段表现
  - 表格：各线路指标明细
- [ ] 支持从 `RoutePunctuality.vue` 勾选线路后跳转到对比页
- [ ] 在首页或准点率菜单区增加入口

---

## 5. 交互细节 ToDo
- [ ] 默认选中最近浏览或收藏的线路可作为增强项
- [ ] 线路数量不足 2 条时禁用“开始对比”
- [ ] 切换地区时清空已选线路，避免跨地区混选
- [ ] 图表数值统一保留 2 位小数

---

## 6. 验收标准
- [ ] 能稳定对比 2 到 4 条线路
- [ ] 后端返回的各项指标与单线路详情页口径一致
- [ ] 页面在桌面端和窄屏下都能清晰展示结果
- [ ] 切换日期范围后结果能实时刷新

---

## 7. 建议开发顺序
1. 先补后端聚合接口。
2. 再做前端多选与表格展示。
3. 最后补图表和从其他页面跳转的联动入口。
