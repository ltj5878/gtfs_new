# 站点可达性分析 TODO

功能：选择一个起点站，展示在指定时间内（15/30/45/60 分钟）可到达的所有站点，在地图上用不同颜色的多边形绘制等时圈。

---

## 后端

### 1. 新建算法文件 `backend/business_logic/reachability.py`

核心逻辑：从起点站做 BFS 扩展，按到达时间分层。

**复用 `transfer_planner.py` 的两个查询函数（直接 import，不改动原文件）：**
- `_get_routes_through_stops(stop_ids, region)` — 查当前 frontier 各站经过哪些线路
- `_get_stops_for_trips(trip_ids, region)` — 查这些 trip 的完整站点序列

**算法步骤：**

```
输入: origin_stop_id, region, max_minutes=60, depart_time="08:00:00"

1. 初始化:
   dist = { origin_stop_id: 0 }    # 到达各站的最短分钟数
   frontier = { origin_stop_id }

2. BFS 循环（最多扩展到 max_minutes 分钟）:
   a. 查 frontier 各站经过的所有线路（每线路取1个代表 trip，复用现有函数）
   b. 对每个代表 trip，遍历其 boarding_stop 之后的站点：
      - travel_time = arrival_time(下游站) - departure_time(boarding站) （秒转分钟）
      - candidate_time = dist[boarding_stop] + boarding_wait + travel_time
        （boarding_wait 固定用 2 分钟估算，可配置）
      - 若 candidate_time <= max_minutes 且 < dist.get(stop_id, inf)：
          更新 dist[stop_id] = candidate_time
          将 stop_id 加入 new_frontier
   c. frontier = new_frontier（仅包含本轮新发现的站点）
   d. 若 frontier 为空则退出

3. 查询所有可达站点的经纬度:
   SELECT stop_id, stop_name, stop_lat, stop_lon FROM stops
   WHERE stop_id IN (...) AND region = %s

4. 返回结构:
   {
     origin: { stop_id, stop_name, stop_lat, stop_lon },
     reachable: [
       { stop_id, stop_name, stop_lat, stop_lon, minutes: 12 },
       ...
     ],
     layers: {
       15:  [stop_id, ...],   # 0~15 分钟可达
       30:  [stop_id, ...],   # 15~30 分钟可达
       45:  [stop_id, ...],   # 30~45 分钟可达
       60:  [stop_id, ...],   # 45~60 分钟可达
     }
   }
```

**性能控制：**
- 每轮 BFS 最多展开 50 条 trip（按 departure_time 最早的取前 50）
- max_minutes 上限为 90，防止请求过慢
- 查询超时：后端 60 秒

---

### 2. 新增 API 路由（`backend/api/app.py`）

在换乘规划接口附近新增（不修改任何已有路由）：

```python
GET /api/analysis/reachability
参数:
  stop_id   string  必填，起点站 ID
  region    string  必填（由 axios 拦截器自动附加）
  max_min   int     可选，默认 60，最大 90
  depart    string  可选，出发时间 HH:MM:SS，默认 08:00:00

响应:
  { origin, reachable: [...], layers: { 15:[], 30:[], 45:[], 60:[] } }
```

---

## 前端

### 3. 新增 API 模块 `frontend/src/api/analysis.js`

```javascript
export const getReachability = (params) =>
  apiClient.get('/analysis/reachability', { params })
```

### 4. 新增页面 `frontend/src/views/StopReachability.vue`

布局：左侧控制面板 + 右侧 Leaflet 地图（复用 Map.vue 的地图初始化方式）

**控制面板：**
- 站点搜索框（复用 SearchBar.vue 或 el-autocomplete）
- 出发时间选择（el-time-picker，默认 08:00）
- 最大时间滑块（el-slider，15/30/45/60，步进 15）
- "分析"按钮，触发 API 请求

**地图渲染：**

等时圈用 **凸包（Convex Hull）**：对每层的站点坐标计算凸包，用 `L.polygon` 绘制，不同层用不同颜色填充。

颜色方案（由内到外，浅到深）：
- 0~15 分钟：`#4ade80`（浅绿）
- 15~30 分钟：`#facc15`（黄）
- 30~45 分钟：`#fb923c`（橙）
- 45~60 分钟：`#f87171`（红）

各层叠加顺序：先画最外层（60min），再画内层，保证内层不被遮挡。

起点站用醒目的蓝色圆圈标记，可达站点用小圆点标记（颜色与所属层一致）。

**凸包算法：** 前端用 Leaflet 扩展或手写 Graham Scan（只需十几行 JS），不引入新依赖。

### 5. 注册路由（`frontend/src/router/index.js`）

```javascript
{
  path: '/analysis/reachability',
  name: 'stop-reachability',
  component: () => import('@/views/StopReachability.vue'),
  meta: { requiresAuth: true }
}
```

### 6. 国际化（`zh-CN.js` / `en.js`）

在 `analysis` key 下新增：

```javascript
// zh-CN
reachability: {
  title: '站点可达性分析',
  subtitle: '从指定站点出发，分析各时间段内可到达的站点范围',
  selectStop: '选择起点站',
  departTime: '出发时间',
  maxMinutes: '最大时间（分钟）',
  analyze: '开始分析',
  legend: '图例',
  min15: '15 分钟内',
  min30: '30 分钟内',
  min45: '45 分钟内',
  min60: '60 分钟内',
  reachableCount: '可达站点数',
  noResult: '未找到可达站点，请尝试其他站点或延长时间',
}
```

---

## 实现顺序

1. `backend/business_logic/reachability.py` — 核心 BFS 算法
2. `backend/api/app.py` — 新增 GET /api/analysis/reachability
3. 用 curl 测试 API 返回数据正确性
4. `frontend/src/api/analysis.js`
5. `frontend/src/views/StopReachability.vue` — 地图 + 控制面板
6. 注册路由
7. 更新 i18n

---

## 不影响现有功能的约束

- 新算法文件独立，仅 import transfer_planner 中的私有函数（`_get_routes_through_stops`、`_get_stops_for_trips`），不修改 transfer_planner.py
- 新 API 路由追加在 app.py 末尾，不修改任何现有路由
- 新页面和路由不触碰 Map.vue、TransferPlanner.vue 等已有组件
- 无新依赖（凸包手写，不引入新 npm 包）
