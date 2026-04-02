---
name: gtfs-punctuality-pipeline
description: 在 gtfs_new 仓库中处理实时监控、准点率分析、历史回放、GTFS-Realtime 采集或相关数据库结构时使用。适用于改动 fetcher、service、calculator、API、历史轨迹、管理端配置，以及前端准点率与实时页面。
---

# GTFS Punctuality Pipeline

这个 skill 只服务于项目里最核心、也最容易牵一发动全身的链路: 实时数据获取 -> 延误计算 -> 入库汇总 -> API -> 前端展示 -> 管理端配置。

## 先认清边界

- Flask API 不是唯一主体，准点率服务是独立运行的。
- 真正关键的文件通常分散在:
  - `backend/data_acquisition/`
  - `backend/services/punctuality_service.py`
  - `backend/business_logic/punctuality_calculator.py`
  - `backend/database/punctuality_schema.sql`
  - `backend/scripts/start_punctuality_service.py`
  - `frontend/src/api/punctuality.js`
  - `frontend/src/views/Punctuality*.vue`
  - `frontend/src/views/VehiclePlayback.vue`

## 默认约束

- 保留真实数据失败时的降级思路，不要轻易去掉 mock fallback。
- 按地区处理 fetcher 和数据，不把 `sf`、`sydney` 混成单一路径。
- `nyc` 继续视为预留，不因为顺手改服务就写成已完整支持。
- 配置入口跟随后端现有规则，不自行新增平行配置源。

## 修改顺序

1. 先确定改动落在哪一层: 采集、计算、存储、接口、回放还是展示。
2. 如果改了数据结构，先更新 schema 和写入逻辑，再更新查询接口。
3. 如果改了接口字段，补看概览、排行、趋势、详情、回放、管理端配置是否一起受影响。
4. 如果改了服务行为，检查是否影响健康统计、重试、降级、日志和手动刷新。
5. 如果改动改变当前完成能力，同步 README。

## 数据和口径

- 区分线路、站点、小时分布、趋势、明细、实时摘要等不同统计粒度，不混用口径。
- 页面空数据时，先判断是采集问题、计算问题、表结构问题还是展示接线问题。
- 历史回放、实时监控、准点率排行都依赖实时数据，但不是同一份视图，改字段时要分别检查。

## 验证基线

- 至少检查一个健康接口和一个准点率接口，例如 `/api/punctuality/overview`。
- 涉及实时入口时，再补看 `/api/realtime/summary` 或车辆接口。
- 至少跑一次 `backend/tests/test_punctuality.py` 中最接近的脚本。
- 如果改了前端展示，最后补一次 `cd frontend && npm run build`。

## 常见错误模式

- 只改 API，不改服务或写库逻辑，导致数据库口径和接口口径脱节。
- 只改计算器，不改前端文案和图表解释，导致页面含义错位。
- 把配置写死在代码里，绕过 `config.json` 或环境变量。
- 只在一个地区验证通过，就默认另一主用地区也没问题。
