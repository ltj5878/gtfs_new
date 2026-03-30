# 时刻表导出 todo

## 1. 核心目标
在线路详情页或站点详情页支持将时刻表导出为 CSV，后续再补 PDF，优先保证首版可稳定下载和复用现有接口数据。

---

## 2. 当前可复用基础
- 后端已有班次时刻表接口：`/api/trips/<trip_id>/stop_times`
- 后端已有线路时刻表接口：`/api/punctuality/routes/<route_id>/timetable`
- 后端已有站点时刻表接口：`/api/punctuality/stops/<stop_id>/timetable`
- 前端已有页面：`RoutePunctualityDetail.vue`、`StopPunctualityDetail.vue`、`RouteDetail.vue`、`StopDetail.vue`

---

## 3. 后端实现 ToDo
- [ ] 首版可不新增复杂导出服务，直接复用现有查询接口
- [ ] 新增轻量导出接口：
  - `GET /api/export/route-timetable`
  - `GET /api/export/stop-timetable`
- [ ] 导出接口支持 `format=csv|pdf`，其中首批先落地 `csv`
- [ ] 明确导出字段：
  - 线路/站点名称
  - 班次 ID
  - 方向
  - 计划时间
  - 实际时间
  - 延误秒数
- [ ] 若实现 PDF，可在后端使用 `reportlab` 统一生成
- [ ] 补文件名规则，例如 `route_{route_id}_timetable_2026-03-30.csv`

---

## 4. 前端实现 ToDo
- [ ] 在相关详情页增加“导出 CSV”“导出 PDF”按钮
- [ ] 在 `frontend/src/api/` 新建 `export.js`
- [ ] 首版前端可直接把接口返回 JSON 转为 CSV Blob 下载
- [ ] 若后端直接返回文件流，前端需处理 `blob` 响应并触发下载
- [ ] 导出前允许用户选择：
  - 导出对象是线路还是站点
  - 导出最近多少条记录
  - 是否包含模拟实际到站时间

---

## 5. 实现策略建议
- [ ] 第一阶段只做 CSV，尽快完成闭环
- [ ] 第二阶段再补 PDF 排版，避免一开始把工作量压在格式渲染上
- [ ] 导出逻辑尽量共用一套字段转换方法，避免页面各自拼装

---

## 6. 验收标准
- [ ] 用户能在详情页一键下载 CSV 文件
- [ ] CSV 能被 Excel/WPS 正常打开且中文不乱码
- [ ] 导出数据和页面展示数据一致
- [ ] 无数据时按钮禁用或给出明确提示

---

## 7. 建议开发顺序
1. 先在前端基于现有接口实现 CSV 下载。
2. 再视需要补后端统一导出接口。
3. 最后增加 PDF 和导出参数面板。
