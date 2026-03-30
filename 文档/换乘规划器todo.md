# 换乘规划器 todo

## 1. 核心目标
基于现有 `stops`、`stop_times`、`trips`、`routes` 数据，实现“输入起点站和终点站后返回候选换乘方案”的功能，优先支持最少换乘和最短预计时间两种排序。

---

## 2. 当前可复用基础
- 后端已提供站点、线路、班次、时刻表接口：`/api/stops`、`/api/routes/<route_id>/stops`、`/api/trips`、`/api/trips/<trip_id>/stop_times`
- 前端已有站点列表、线路详情和地图页面：`frontend/src/views/Stops.vue`、`frontend/src/views/RouteDetail.vue`、`frontend/src/views/Map.vue`
- 数据库已有路径计算所需核心表：`stops`、`trips`、`stop_times`、`routes`

---

## 3. 后端实现 ToDo
- [ ] 在 `backend/api/app.py` 新增 `GET /api/planner/transfer` 接口
- [ ] 设计请求参数：`from_stop_id`、`to_stop_id`、`region`、`strategy=min_transfer|min_time`
- [ ] 先实现基础版路径搜索：
  - 以站点为节点
  - 以同一班次相邻站点为边
  - 记录当前所在线路，计算换乘次数
- [ ] 对首版搜索范围做约束，避免全图暴力搜索：
  - 限制最大换乘次数为 3
  - 限制最大展开节点数
  - 同地区内计算
- [ ] 返回统一结果结构：
  - 总耗时
  - 换乘次数
  - 分段步骤列表
  - 每段涉及线路、上下车站、经过站数
- [ ] 补一个辅助接口 `GET /api/planner/stops/search` 或直接复用现有 `/api/stops?search=`
- [ ] 为搜索逻辑抽出独立模块，建议放到 `backend/business_logic/transfer_planner.py`

---

## 4. 前端实现 ToDo
- [ ] 新增页面 `frontend/src/views/TransferPlanner.vue`
- [ ] 在 `frontend/src/router/index.js` 增加路由，例如 `/planner/transfer`
- [ ] 在 `frontend/src/api/` 下新增 `planner.js`，封装换乘规划接口
- [ ] 页面表单支持：
  - 起点站搜索选择
  - 终点站搜索选择
  - 策略切换
  - 地区跟随 `regionStore`
- [ ] 结果区展示多个候选方案卡片
- [ ] 每个方案展示步骤时间线：
  - 第几段乘坐哪条线路
  - 在哪个站换乘
  - 预计总时长和换乘次数
- [ ] 结果点击后联动地图页，后续可高亮相关站点和线路
- [ ] 在 `frontend/src/views/Home.vue` 增加功能入口

---

## 5. 数据与性能 ToDo
- [ ] 优先基于数据库查询预取候选边，而不是一次性把全量 `stop_times` 全读入内存
- [ ] 为高频查询确认索引可用：`stop_times(region, stop_id)`、`stop_times(region, trip_id)`、`trips(region, route_id)`
- [ ] 若首版响应慢，增加简单缓存：
  - 相同起终点 5 分钟缓存
  - 按 `region + from_stop_id + to_stop_id + strategy` 作为 key

---

## 6. 验收标准
- [ ] 能在同一区域内为任意两个存在连通关系的站点返回至少 1 条方案
- [ ] 返回结果能正确区分“直达”和“需要换乘”
- [ ] 最少换乘策略下，优先返回换乘次数更少的方案
- [ ] 页面能完整展示换乘步骤，且空结果时有明确提示

---

## 7. 建议开发顺序
1. 先做后端基础搜索接口，返回静态 JSON 结果。
2. 再做前端查询页和结果卡片。
3. 最后补排序优化、地图联动和缓存。
