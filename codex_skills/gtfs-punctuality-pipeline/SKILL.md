---
name: gtfs-punctuality-pipeline
description: 在 gtfs_new 仓库中处理实时监控、准点率、历史回放、GTFS-Realtime 采集、采集服务、延误计算或相关数据库结构时使用。适用于改动 fetcher、service、calculator、API、前端准点率页面以及配置和降级逻辑。
---

# GTFS Punctuality Pipeline

这个 skill 只针对项目里最容易牵一发动全身的那条链路：实时数据获取 -> 延误计算 -> 入库/汇总 -> API -> 前端展示。

## 先认清边界

- Flask API 不是唯一主体，准点率服务是独立运行的。
- 真正的关键点通常分散在：
  - `backend/data_acquisition/`
  - `backend/services/punctuality_service.py`
  - `backend/business_logic/punctuality_calculator.py`
  - `backend/database/punctuality_schema.sql`
  - `backend/scripts/start_punctuality_service.py`
  - `frontend/src/api/punctuality.js`
  - `frontend/src/views/Punctuality*.vue`

## 默认约束

- 保留真实数据失败时的降级思路，不要轻易去掉 mock fallback。
- 按地区处理 fetcher 和数据，不把 `sf`、`sydney` 的逻辑混成单一路径。
- `nyc` 继续视为预留，不因为顺手改服务就当成已支持完成。
- 配置优先级跟随后端现有规则，不自行发明新入口。

## 修改顺序

1. 先确定改动落在哪一层：采集、计算、存储、接口还是展示。
2. 如果改了数据结构，先更新 schema 和写入逻辑，再更新查询接口。
3. 如果改了接口返回字段，补看前端概览、排行、趋势、详情页是否一起受影响。
4. 如果改了服务行为，检查是否影响 API 健康统计、重试、降级和日志。
5. 如果改动会改变系统“当前已完成能力”，同步 README。

## 计算与数据侧重点

- 区分线路、站点、小时分布、趋势、明细等不同粒度，不混用统计口径。
- 当接口空数据时，优先确认是采集问题、计算问题还是展示问题。
- 历史回放、实时监控、准点率排行虽然都依赖实时数据，但不是同一份视图，改字段时要分别检查。

## 验证基线

- 至少跑一次 [backend/tests/test_punctuality.py](backend/tests/test_punctuality.py) 中相关部分。
- 至少检查健康接口和一个准点率接口，例如 `/api/punctuality/overview` 或 `/api/punctuality/routes`。
- 如果涉及实时数据入口，再补看 `/api/realtime/summary` 或车辆接口。
- 如果改动前端展示，最后再做一次前端构建检查。

## 常见错误模式

- 只改 API 不改服务，导致数据库里根本没有新字段或新口径。
- 只改计算器不改前端解释文案，页面含义和数据口径错位。
- 把配置写死在代码里，绕过 `config.json` / 环境变量。
- 在一个地区验证通过后，忘了另一主用地区也要过最基本检查。
