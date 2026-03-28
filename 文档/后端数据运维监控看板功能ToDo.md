# 后端数据运维监控看板 (System Admin & Data Dashboard) 实现 ToDo 列表

## 1. 核心目标
为系统管理员提供一个深度监控平台，用于实时查看 PostgreSQL 数据库的存储健康状况、第三方 API（511 SF Bay, MTA, TfNSW）的调用质量，以及多地区 GTFS 数据集的更新时效。该功能不仅增加毕业设计的工作量，还能显著提升系统的专业度。

---

## 2. 数据库设计 (Database Layer)
在不破坏现有 GTFS 业务表的前提下，新增运维专用日志表。

- [ ] **创建 API 调用日志表 (`api_call_logs`)**：
```sql
CREATE TABLE IF NOT EXISTS api_call_logs (
    id SERIAL PRIMARY KEY,
    region TEXT NOT NULL,
    api_name TEXT NOT NULL,         -- '511_SF_BAY', 'MTA_NYC', 'TFNSW_SYDNEY'
    endpoint TEXT NOT NULL,         -- 接口路径
    latency_ms INTEGER NOT NULL,    -- 响应时长
    status_code INTEGER NOT NULL,   -- HTTP 状态码
    error_msg TEXT,                 -- 错误信息记录
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_api_logs_time ON api_call_logs(created_at);
```

- [ ] **创建数据更新追踪表 (`data_update_logs`)**：
  - 记录每次 `gtfs_importer.py` 的执行，包括地区、文件版本、导入时长和入库记录数。

---

## 3. 后端接口实现 (Backend Layer)
在 `backend/api/app.py` 中新增 `admin` 命名空间下的接口。

- [ ] **数据库健康度接口 (`GET /api/admin/db-stats`)**：
  - **关键 SQL**：查询 `pg_total_relation_size` 和 `pg_stat_user_tables` 以获取各表的物理空间占用和当前记录数。
- [ ] **API 服务质量接口 (`GET /api/admin/api-health`)**：
  - 汇总 `api_call_logs`，返回 24 小时内的平均延迟、成功率分布。
- [ ] **数据时效性接口 (`GET /api/admin/data-freshness`)**：
  - 返回各地区 GTFS 静态数据的版本信息和上次同步时间。

---

## 4. 前端监控视图 (Frontend Layer)
在 `frontend/src/views/AdminDashboard.vue` 实现可视化展示。

- [ ] **仪表盘布局**：
  - **核心指标卡片**：展示 DB 总大小、百万级数据表记录数、API 实时异常数。
  - **可视化图表 (ECharts)**：
    - 数据库存储分配饼图（展示哪些表最占空间）。
    - 外部 API 延迟趋势折线图。
  - **运维操作台**：支持手动触发数据清理或重新拉取指定地区的实时数据流。

---

## 5. 关键逻辑点
- **零干扰集成**：通过 Python 装饰器或日志中间件自动捕获 API 调用信息，不影响原业务逻辑。
- **性能优化**：数据库统计接口增加 15 分钟的内存缓存，避免频繁扫描系统目录。
- **安全性**：在路由配置中增加鉴权守卫，确保只有管理员可访问此页面。

---

## 6. 验收标准
1. [ ] **数据驱动**：看板能真实反映数据库中 `stop_times` 等千万级记录的物理分布。
2. [ ] **异常感知**：当第三方 API 出现 429（限流）或 5xx 错误时，看板能迅速以红色告警显示。
3. [ ] **多地区覆盖**：能同时监控 SF、NYC 和 Sydney 三个地区的数据流状态。
4. [ ] **代码质量**：新增代码遵循项目的中文注释和 Python 类型提示规范。
