# Beta 功能规划文档

> 分支：`dev_0403_beta`  
> 创建日期：2026-04-03  
> 目标：在不破坏现有功能的前提下，新增六个复杂度较高的增强功能

---

## 功能一：智能行程推荐引擎（基于现有数据，无需新数据）

### 功能概述

基于用户的收藏路线、历史浏览记录（审计日志）、当前时间段和准点率数据，构建一套个性化行程推荐引擎。在首页展示"今日推荐出行方案"卡片，推荐最优路线、预测到站时间、提示拥挤时段。

### 技术原理

- 利用现有 `audit_logs` 表分析用户常用路线、高频访问站点
- 结合 `favorites` 表的收藏数据权重加成
- 利用 `punctuality` 数据按时段计算最佳出发时间窗口
- 利用 `stop_times` 推算当前时刻距离下一班车的剩余时间
- 前端实现基于时段的推荐分数排序算法（无需 AI API）

### 实现步骤

#### 后端（backend/api/app.py）

1. **新增路由 `GET /api/recommendations`**
   - 参数：`region`, `user_id`（从 session 获取）, `limit`（默认 5）
   - 查询逻辑：
     ```sql
     -- Step 1: 从审计日志提取用户高频路线（最近 30 天）
     SELECT entity_id, COUNT(*) as freq
     FROM audit_logs
     WHERE user_id = :uid AND entity_type = 'route' AND created_at > NOW() - INTERVAL '30 days'
     GROUP BY entity_id ORDER BY freq DESC LIMIT 20;
     
     -- Step 2: 合并收藏权重（收藏的路线 freq * 2）
     -- Step 3: 查询这些路线的当前时段准点率
     -- Step 4: 计算下一班车时间（基于 stop_times）
     ```
   - 返回字段：`route_id`, `route_name`, `next_departure`, `punctuality_score`, `recommendation_score`, `reason`（推荐理由文案）

2. **新增路由 `GET /api/recommendations/best-time`**
   - 给定路线 ID，返回当天各时段的推荐指数（基于准点率历史）
   - 返回按小时粒度的推荐分数数组

#### 前端

3. **新建 `src/views/Recommendations.vue`**
   - 顶部：今日推荐卡片轮播（基于当前时间动态更新）
   - 中部：各推荐路线的"今日最佳出行时段"柱状图（ECharts）
   - 底部：基于收藏的"快速出行"面板，显示下班车倒计时

4. **新建 `src/api/recommendations.js`**

5. **新建 `src/stores/recommendationStore.js`**
   - 缓存推荐结果，每 5 分钟自动刷新
   - 记录用户点击的推荐条目（用于隐式反馈改善推荐质量）

6. **在 `Home.vue` 首页** 嵌入推荐摘要组件（最多展示 3 条）

7. **更新 `router/index.js`** 添加 `/recommendations` 路由

8. **更新 `i18n/zh-CN.js` 和 `i18n/en.js`** 添加所有新增文案

---

## 功能二：多维度线路健康度评分系统（基于现有数据）

### 功能概述

为每条线路生成一个综合"健康度评分"（0-100分），整合准点率、运营频率稳定性、覆盖站点数、历史延误分布等多个维度，并在线路列表和线路详情页直观展示。还提供跨线路横向对比的评分雷达图。

### 技术原理

- **准点率维度**：从 `punctuality` 表获取近 7 天平均准点率（权重 40%）
- **频率稳定性**：计算 `stop_times` 中班次间隔的标准差，标准差越小分数越高（权重 25%）
- **覆盖度维度**：站点数量、方向数对比该地区平均水平（权重 15%）
- **延误分布维度**：延误集中在轻度（<5min）vs 严重延误（>15min）的比例（权重 20%）
- 评分结果缓存到 Redis 或 PostgreSQL 的 `route_health_scores` 扩展表（每日计算一次）

### 实现步骤

#### 数据库

1. **新建扩展表 `backend/database/health_score_schema.sql`**
   ```sql
   CREATE TABLE route_health_scores (
       id SERIAL PRIMARY KEY,
       route_id VARCHAR(50) NOT NULL,
       region VARCHAR(20) NOT NULL,
       score_date DATE NOT NULL DEFAULT CURRENT_DATE,
       punctuality_score DECIMAL(5,2),  -- 准点率得分
       frequency_score DECIMAL(5,2),   -- 频率稳定性得分
       coverage_score DECIMAL(5,2),    -- 覆盖度得分
       delay_dist_score DECIMAL(5,2),  -- 延误分布得分
       total_score DECIMAL(5,2),       -- 综合得分
       score_detail JSONB,             -- 详细计算参数
       created_at TIMESTAMP DEFAULT NOW(),
       UNIQUE(route_id, region, score_date)
   );
   CREATE INDEX idx_health_scores_region_date ON route_health_scores(region, score_date);
   ```

#### 后端

2. **新建 `backend/scripts/calculate_health_scores.py`**
   - 实现各维度评分计算逻辑
   - 支持命令行参数 `--region sf --date 2026-04-03`
   - 计算结果写入 `route_health_scores` 表

3. **在 `app.py` 新增路由**：
   - `GET /api/routes/<route_id>/health-score` — 单条线路健康度详情
   - `GET /api/routes/health-scores` — 批量返回所有线路评分（支持排序/过滤）
   - `POST /api/admin/recalculate-health-scores` — 管理员触发重新计算

#### 前端

4. **`Routes.vue` 改造**：
   - 线路卡片增加健康度分数徽章（颜色区分：绿>80、黄60-80、红<60）
   - 增加"按健康度排序"选项

5. **`RouteDetail.vue` 改造**：
   - 在基本信息区增加健康度雷达图（ECharts radar chart）
   - 展示各维度得分及说明

6. **新建 `src/views/HealthScoreRanking.vue`**：
   - 全地区线路健康度排行榜
   - 支持筛选维度（只看准点率维度排名 / 综合排名）
   - 折线图展示某条线路健康度的历史趋势

7. **更新 `router/index.js`、`i18n` 文件**

---

## 功能三：实时异常检测与告警系统（基于现有数据 + WebSocket）

### 功能概述

对实时车辆位置数据进行连续监控，当检测到异常情况（如车辆长时间停留、区间严重拥堵、多条线路同时大面积延误、某站点车辆堆积）时，自动触发系统告警，推送到通知中心，并在监控地图上高亮标记异常区域。

### 技术原理

- 后端定时任务（每 60 秒）扫描 `realtime_vehicle_positions` 最新数据
- 异常检测规则引擎（基于规则，无需 ML）：
  - 规则 1：同一车辆 10 分钟内位移 < 200 米 → "车辆疑似停滞"
  - 规则 2：某线路 >50% 车辆同时延误 >10 分钟 → "线路大面积延误"
  - 规则 3：某站点 3 辆以上车辆在 500 米内聚集 → "车辆堆积"
  - 规则 4：区间行驶速度 < 正常速度 30% → "区间严重拥堵"
- 告警去重（相同类型+对象 30 分钟内只告警一次）
- 通过现有 `notifications` 表推送告警通知

### 实现步骤

#### 数据库

1. **新建 `backend/database/alert_schema.sql`**
   ```sql
   CREATE TABLE anomaly_alerts (
       id SERIAL PRIMARY KEY,
       region VARCHAR(20) NOT NULL,
       alert_type VARCHAR(50) NOT NULL,  -- vehicle_stall/route_delay/stop_congestion/segment_congestion
       entity_type VARCHAR(20) NOT NULL, -- route/stop/vehicle/segment
       entity_id VARCHAR(50) NOT NULL,
       severity VARCHAR(10) NOT NULL,    -- low/medium/high/critical
       alert_data JSONB,                 -- 告警详情（延误分钟数、涉及车辆列表等）
       triggered_at TIMESTAMP NOT NULL DEFAULT NOW(),
       resolved_at TIMESTAMP,
       notified BOOLEAN DEFAULT FALSE,
       UNIQUE(region, alert_type, entity_id, triggered_at::DATE)  -- 去重约束
   );
   ```

2. **新建 `backend/scripts/anomaly_detector.py`**
   - 实现四条检测规则
   - 调用现有 `notifications` 写入接口推送告警
   - 支持作为后台守护进程运行：`python3 anomaly_detector.py --region sf --interval 60`

3. **在 `app.py` 新增路由**：
   - `GET /api/alerts/active` — 当前活跃告警列表
   - `GET /api/alerts/history` — 历史告警记录（支持分页和时间范围）
   - `PATCH /api/alerts/<id>/resolve` — 手动标记告警为已解决
   - `GET /api/alerts/rules` — 查看告警规则配置
   - `PUT /api/alerts/rules` — 管理员修改告警规则阈值

#### 前端

4. **`RealtimeMonitor.vue` 改造**：
   - 地图上增加告警图层：异常区域显示闪烁红色标记
   - 右侧增加"实时告警面板"侧边栏，列出当前活跃告警
   - 点击告警条目，地图自动定位到异常位置

5. **新建 `src/views/AlertCenter.vue`**：
   - 告警中心页面，显示活跃告警和历史告警
   - 支持按严重程度、类型、线路筛选
   - 告警趋势图（按天/周统计各类告警数量）

6. **`NotificationBell.vue` 改造**：
   - 高优先级告警（severity=critical）显示红色数字徽章
   - 点击展开时优先显示未解决告警

7. **更新路由、国际化**

---

## 功能四：出行碳排放计算器（基于现有数据 + 公开排放因子）

### 功能概述

基于 GTFS 路线数据和公开的公共交通碳排放因子，为用户提供公交出行 vs 私家车出行的碳排放对比计算，展示用户选择公交节省的碳排放量，并记录用户的"绿色出行"积累数据，生成个人碳排放报告。

### 数据来源

排放因子使用 IPCC/EPA 公开数据（硬编码常量，无需外部 API）：
- 公共汽车：0.089 kg CO₂/乘客公里
- 轨道交通：0.041 kg CO₂/乘客公里
- 私家车：0.271 kg CO₂/公里（平均）

行驶距离从现有 `shapes` 表计算（Haversine 公式累计路段长度）。

### 实现步骤

#### 数据库

1. **新建 `backend/database/carbon_schema.sql`**
   ```sql
   CREATE TABLE user_carbon_records (
       id SERIAL PRIMARY KEY,
       user_id INTEGER REFERENCES users(id),
       route_id VARCHAR(50),
       region VARCHAR(20),
       trip_date DATE DEFAULT CURRENT_DATE,
       distance_km DECIMAL(8,3),       -- 行程距离
       transit_emission DECIMAL(8,4),  -- 公交排放 kg CO₂
       car_emission DECIMAL(8,4),      -- 等效私家车排放
       carbon_saved DECIMAL(8,4),      -- 节省 kg CO₂
       created_at TIMESTAMP DEFAULT NOW()
   );
   
   CREATE TABLE route_distances (  -- 缓存每条线路的距离
       route_id VARCHAR(50),
       region VARCHAR(20),
       direction_id INTEGER,
       distance_km DECIMAL(8,3),
       calculated_at TIMESTAMP DEFAULT NOW(),
       PRIMARY KEY (route_id, region, direction_id)
   );
   ```

2. **在 `app.py` 新增路由**：
   - `GET /api/carbon/route/<route_id>` — 计算某条线路的碳排放对比数据
   - `POST /api/carbon/record` — 用户记录一次绿色出行
   - `GET /api/carbon/my-stats` — 用户个人碳排放统计（本周/月/年节省量）
   - `GET /api/carbon/leaderboard` — 绿色出行排行榜（匿名）
   - `GET /api/carbon/routes/ranking` — 线路环保指数排名

#### 前端

3. **`RouteDetail.vue` 改造**：
   - 新增"绿色出行"Tab 页
   - 展示本线路 vs 私家车的排放对比（横向进度条可视化）
   - "记录本次乘坐"按钮（登录用户可点击积累碳积分）

4. **新建 `src/views/CarbonFootprint.vue`**：
   - 个人碳排放统计中心
   - 环形图展示：累计节省量 / 等效植树棵数 / 等效减少燃油升数
   - 日历热力图展示每天的绿色出行记录
   - 月度趋势折线图

5. **在首页 `Home.vue`** 增加"绿色出行"快速统计小组件

6. **更新路由、国际化**

---

## 功能五：站点客流预测模型（基于现有 stop_times 数据）

### 功能概述

基于 GTFS `stop_times` 数据中的计划班次密度（班次越密集表明该时段预期客流越大），结合实际准点率、历史延误数据，构建每个站点的分时段客流预测模型。在站点详情页展示"全天预测客流热力图"，并提供"最佳到站时间"推荐（避开拥挤时段）。

### 技术原理

- 使用 `stop_times` 中某站某小时的班次数作为客流代理指标（班次数 × 平均载客系数）
- 叠加准点率修正：延误率高的时段实际客流积压效应更强
- 使用指数平滑（Exponential Smoothing）对工作日 vs 周末分别建模
- 结果缓存到扩展表，按需查询无需实时计算

### 实现步骤

#### 数据库

1. **新建 `backend/database/flow_prediction_schema.sql`**
   ```sql
   CREATE TABLE stop_flow_predictions (
       id SERIAL PRIMARY KEY,
       stop_id VARCHAR(50) NOT NULL,
       region VARCHAR(20) NOT NULL,
       day_type VARCHAR(10) NOT NULL,   -- weekday/weekend
       hour_of_day SMALLINT NOT NULL,   -- 0-23
       predicted_flow_index DECIMAL(8,2), -- 相对客流指数（100 = 该站平均水平）
       confidence DECIMAL(4,3),         -- 预测置信度 0-1
       model_version VARCHAR(20),
       computed_at TIMESTAMP DEFAULT NOW(),
       UNIQUE(stop_id, region, day_type, hour_of_day)
   );
   ```

2. **新建 `backend/scripts/compute_flow_predictions.py`**
   - 读取 `stop_times` 计算每站每小时班次数
   - 结合 `punctuality` 数据做延误修正
   - 计算 7 天滚动平均，区分工作日/周末
   - 将结果写入 `stop_flow_predictions` 表

3. **在 `app.py` 新增路由**：
   - `GET /api/stops/<stop_id>/flow-prediction` — 站点全天客流预测
   - `GET /api/stops/<stop_id>/best-time` — 推荐最佳到站时间（返回低峰时段列表）
   - `GET /api/stops/flow-heatmap` — 全站点当前时刻客流热力图数据（用于地图叠层）

#### 前端

4. **`StopDetail.vue` 改造**：
   - 新增"客流预测"Tab 页
   - 展示全天 24 小时客流指数折线图（工作日 vs 周末双线对比）
   - "最佳到站时间"高亮标注（绿色区间）
   - 当前时刻的实时拥挤度指示器（基于预测值）

5. **`StopHeatmap.vue` 改造**：
   - 现有热力图增加"预测模式"切换
   - 切换后热力图权重改用 `flow_prediction` 数据而非实际延误数据
   - 增加时间滑块，可查看"预测中"的未来 6 小时热力分布

6. **`Map.vue` 改造**：
   - 新增"客流叠层"图层开关
   - 开启后各站点图标大小随预测客流指数动态缩放

7. **更新路由、国际化**

---

## 功能六：GTFS 数据质量审查仪表板（基于现有数据，运营向功能）

### 功能概述

自动检查已导入的 GTFS 数据质量问题，包括：缺失数据、时刻表逻辑错误（如到站时间早于发车时间）、孤立停靠点、无效的 shape 坐标、过期的日历条目等。生成数据质量报告，并在管理员仪表板中可视化展示质量得分历史趋势。

### 技术原理

- 纯 SQL + Python 逻辑，不依赖任何外部工具
- 参考 MobilityData 的 GTFS Validator 规则集，选取 20+ 条可在本地 SQL 实现的规则
- 按严重程度分级：ERROR（数据错误）、WARNING（质量隐患）、INFO（建议优化）
- 支持增量检查（只对上次检查后更新的数据运行规则）

### 检查规则示例

```
ERROR 类：
- stop_times 中 arrival_time > departure_time（到达晚于出发）
- shapes 中连续点间距 > 50km（坐标异常跳变）
- trips 引用了不存在的 route_id / calendar service_id
- 站点经纬度超出对应地区合理范围

WARNING 类：
- 路线无 shape 数据（无法绘制地图轨迹）
- stop_times 中相邻站间隔 < 30 秒（时刻表过密）
- 日历 end_date 早于今日（过期服务）
- 线路只有一个方向（可能缺失回程数据）

INFO 类：
- 路线未设置颜色代码
- 站点缺少无障碍设施信息（wheelchair_boarding）
- 班次未关联 block_id（无法进行跨线路连续行程分析）
```

### 实现步骤

#### 数据库

1. **新建 `backend/database/data_quality_schema.sql`**
   ```sql
   CREATE TABLE data_quality_checks (
       id SERIAL PRIMARY KEY,
       region VARCHAR(20) NOT NULL,
       check_time TIMESTAMP NOT NULL DEFAULT NOW(),
       total_errors INTEGER DEFAULT 0,
       total_warnings INTEGER DEFAULT 0,
       total_infos INTEGER DEFAULT 0,
       quality_score DECIMAL(5,2),    -- 综合质量分 0-100
       check_duration_ms INTEGER,
       feed_version VARCHAR(100)      -- 对应的 feed_info 版本
   );
   
   CREATE TABLE data_quality_issues (
       id SERIAL PRIMARY KEY,
       check_id INTEGER REFERENCES data_quality_checks(id) ON DELETE CASCADE,
       rule_code VARCHAR(50) NOT NULL,    -- 规则编号，如 E001/W003
       severity VARCHAR(10) NOT NULL,    -- ERROR/WARNING/INFO
       entity_type VARCHAR(20),          -- route/stop/trip/shape
       entity_id VARCHAR(100),
       description TEXT NOT NULL,         -- 问题描述（中文）
       suggestion TEXT,                   -- 修复建议
       example_data JSONB                 -- 示例数据（最多5条）
   );
   ```

2. **新建 `backend/scripts/data_quality_checker.py`**
   - 实现 20+ 条检查规则（纯 SQL 查询）
   - 计算综合质量分（ERROR 每个 -5 分，WARNING 每个 -1 分，满分 100）
   - 写入 `data_quality_checks` 和 `data_quality_issues` 表
   - 命令行：`python3 data_quality_checker.py --region sf`

3. **在 `app.py` 新增路由**：
   - `GET /api/admin/data-quality/latest` — 最新检查结果摘要
   - `GET /api/admin/data-quality/issues` — 问题详情列表（支持分页、按严重程度筛选）
   - `GET /api/admin/data-quality/history` — 质量分数历史趋势
   - `POST /api/admin/data-quality/run` — 触发新一轮检查（异步执行）
   - `GET /api/admin/data-quality/rules` — 查看所有检查规则说明

#### 前端

4. **`AdminDashboard.vue` 改造**：
   - 新增"数据质量"卡片：显示当前质量分数 + 颜色（红/黄/绿）
   - 点击跳转到详情页

5. **新建 `src/views/DataQualityDashboard.vue`**（仅管理员可访问）：
   - 顶部：综合质量分仪表盘（ECharts gauge 组件）
   - 质量分历史趋势折线图（可查看多个地区的趋势对比）
   - 问题列表（按 ERROR/WARNING/INFO 分 Tab）
     - 每条问题展示：规则编号、描述、影响实体数、示例数据、修复建议
   - "运行检查"按钮（需管理员权限，显示进度条）

6. **更新 `router/index.js`**（添加管理员路由守卫）、**国际化文件**

---

## 实施建议与注意事项

### 优先级建议

| 功能 | 优先级 | 复杂度 | 依赖现有数据 | 是否需要新数据/外部依赖 |
|------|--------|--------|------------|------------------------|
| 功能六：数据质量审查 | 高 | 中 | 是 | 否 |
| 功能二：健康度评分 | 高 | 中 | 是 | 否 |
| 功能三：异常检测告警 | 高 | 高 | 是 | 否 |
| 功能五：客流预测 | 中 | 高 | 是 | 否 |
| 功能四：碳排放计算 | 中 | 低 | 是 | 排放因子常量（硬编码）|
| 功能一：推荐引擎 | 低 | 中 | 是 | 否 |

### 开发规范提醒

1. **数据库**：所有新建 SQL 文件放入 `backend/database/`，表名使用小写下划线，字段添加中文注释
2. **后端**：新增路由统一追加到 `backend/api/app.py` 末尾，函数名使用 snake_case，添加中文 docstring
3. **前端**：新建页面放入 `frontend/src/views/`，新建 store 放入 `frontend/src/stores/`，所有文案同步更新 `i18n/zh-CN.js` 和 `i18n/en.js`
4. **region 过滤**：所有新增查询接口必须支持 `region` 参数过滤（前端 Axios 拦截器自动附加）
5. **不破坏现有功能**：新增路由使用新的 URL 路径，新建数据库表不修改现有表结构，新建前端页面不修改现有页面的核心逻辑

### 建议开发顺序

```
第一阶段：基础设施
└── 功能六（数据质量）→ 功能二（健康度评分）→ 数据库脚本验证

第二阶段：监控增强  
└── 功能三（异常检测）→ 集成到现有通知系统

第三阶段：用户价值
└── 功能五（客流预测）→ 功能四（碳排放）→ 功能一（推荐引擎）
```
