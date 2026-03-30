# 历史数据回放 todo

## 1. 核心目标
基于已有实时车辆历史位置记录，实现“选择某天和时间范围，在地图上按时间轴回放车辆移动轨迹”的功能。

---

## 2. 当前可复用基础
- 车辆历史位置已存储于 `realtime_vehicle_positions`
- 后端已有实时车辆接口：`/api/realtime/vehicles`
- 前端已有地图页 `Map.vue` 和实时监控页 `RealtimeMonitor.vue`
- 表内已有 `position_timestamp` 字段，可直接作为回放时间轴基础

---

## 3. 后端实现 ToDo
- [ ] 在 `backend/api/app.py` 新增历史回放接口：
  - `GET /api/realtime/playback`
  - `GET /api/realtime/playback/summary`
- [ ] 请求参数建议包括：
  - `region`
  - `date`
  - `start_time`
  - `end_time`
  - `route_id`
  - `vehicle_id`
- [ ] 返回结构按时间排序，至少包含：
  - `vehicle_id`
  - `route_id`
  - `latitude`
  - `longitude`
  - `bearing`
  - `speed`
  - `position_timestamp`
- [ ] 增加汇总接口，先返回当日可回放时间范围和记录条数
- [ ] 若单次返回数据量过大，增加分页或时间切片参数

---

## 4. 前端实现 ToDo
- [ ] 新增页面 `frontend/src/views/Playback.vue`，或在 `Map.vue` 中增加“历史回放”模式
- [ ] 在 `frontend/src/api/` 下新增 `realtime.js` 或扩展现有实时接口封装
- [ ] 页面增加回放控制区：
  - 日期选择
  - 时间范围选择
  - 线路筛选
  - 播放 / 暂停 / 拖动时间轴
  - 播放速度切换
- [ ] 地图上按时间推进渲染车辆位置
- [ ] 可选展示车辆尾迹线，帮助观察移动路径
- [ ] 与 `regionStore` 联动，切换地区时重新拉取可回放数据

---

## 5. 性能与数据质量 ToDo
- [ ] 先确认 `realtime_vehicle_positions` 历史数据没有被服务清理掉
- [ ] 回放时不要一次性渲染全部点位，按时间窗口增量更新
- [ ] 对同一车辆相邻点位可做抽样，降低前端压力
- [ ] 若某些地区历史数据不足，页面要有空状态提示

---

## 6. 验收标准
- [ ] 用户可选择日期和时间范围进行回放
- [ ] 时间轴拖动时车辆位置能同步更新
- [ ] 按线路筛选后只展示对应车辆
- [ ] 页面在中等数据量下保持可操作，不出现明显卡顿

---

## 7. 建议开发顺序
1. 先做后端时间范围查询接口。
2. 再在地图上实现基础播放和暂停。
3. 最后补速度切换、尾迹线和筛选器。
