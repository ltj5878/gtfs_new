# 准点率报告自动生成 todo

## 1. 核心目标
按周或按月汇总准点率数据，生成可下载的分析报告，内容包括整体趋势、TOP/BOTTOM 线路、时段分析和异常说明。

---

## 2. 当前可复用基础
- 准点率数据来源已具备：`route_daily_punctuality`、`hourly_punctuality_stats`、`stop_daily_punctuality`
- 后端已有概览和趋势接口：`/api/punctuality/overview`、`/api/punctuality/trends`
- 前端已有趋势和总览页面，可复用图表口径

---

## 3. 后端实现 ToDo
- [ ] 在 `backend/api/app.py` 新增报告接口：
  - `POST /api/reports/punctuality/generate`
  - `GET /api/reports/punctuality`
  - `GET /api/reports/punctuality/<report_id>/download`
- [ ] 新增报告任务表，建议命名 `punctuality_reports`
- [ ] 表字段至少包括：
  - `id`
  - `user_id`
  - `region`
  - `report_type`
  - `start_date`
  - `end_date`
  - `file_path`
  - `status`
  - `created_at`
- [ ] 报告内容聚合逻辑建议抽到 `backend/business_logic/report_generator.py`
- [ ] 首版生成内容：
  - 区间整体准点率
  - 每日趋势
  - 最优/最差线路 TOP5
  - 高峰与非高峰对比
  - 可选附录：站点维度 TOP5/BOTTOM5
- [ ] 使用 `reportlab` 生成 PDF
- [ ] 若暂时不做异步任务，首版可同步生成后返回下载地址

---

## 4. 前端实现 ToDo
- [ ] 新增页面 `frontend/src/views/PunctualityReport.vue`
- [ ] 在 `frontend/src/router/index.js` 增加路由，例如 `/punctuality/reports`
- [ ] 页面支持用户选择：
  - 周报 / 月报
  - 开始日期 / 结束日期
  - 地区
- [ ] 提交后展示生成状态和历史报告列表
- [ ] 历史报告支持下载和删除
- [ ] 在准点率概览页或趋势页增加“生成报告”入口

---

## 5. 存储与运维 ToDo
- [ ] 统一报告输出目录，例如 `backend/reports/` 或项目根目录下独立目录
- [ ] 文件命名加入时间戳，避免覆盖
- [ ] 增加简单清理策略，防止历史 PDF 累积过多
- [ ] 若目录不入库，需在 `.gitignore` 中保持忽略

---

## 6. 验收标准
- [ ] 用户能生成并下载指定时间范围的 PDF 报告
- [ ] 报告中的关键指标与系统页面展示口径一致
- [ ] 历史报告列表能正确展示生成时间和状态
- [ ] 生成失败时页面有明确错误信息

---

## 7. 建议开发顺序
1. 先做后端 PDF 生成和下载接口。
2. 再做前端发起生成与下载。
3. 最后补历史记录、异步状态和定时清理。
