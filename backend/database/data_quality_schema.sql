-- ============================================
-- 数据质量审查系统表结构
-- 功能：自动检查 GTFS 数据质量，记录检查结果
-- ============================================

-- 检查记录主表（每次检查生成一条记录）
CREATE TABLE IF NOT EXISTS data_quality_checks (
    id SERIAL PRIMARY KEY,                           -- 主键
    region VARCHAR(20) NOT NULL,                     -- 地区
    check_time TIMESTAMP NOT NULL DEFAULT NOW(),     -- 检查时间
    total_errors INTEGER DEFAULT 0,                  -- 错误数量
    total_warnings INTEGER DEFAULT 0,                -- 警告数量
    total_infos INTEGER DEFAULT 0,                   -- 信息数量
    quality_score DECIMAL(5,2) DEFAULT 100.00,       -- 综合质量分 0-100
    check_duration_ms INTEGER,                       -- 检查耗时（毫秒）
    feed_version VARCHAR(100)                        -- 对应 feed_info 版本
);
CREATE INDEX IF NOT EXISTS idx_dq_checks_region ON data_quality_checks(region);
CREATE INDEX IF NOT EXISTS idx_dq_checks_time ON data_quality_checks(check_time DESC);

-- 检查问题详情表
CREATE TABLE IF NOT EXISTS data_quality_issues (
    id SERIAL PRIMARY KEY,                           -- 主键
    check_id INTEGER REFERENCES data_quality_checks(id) ON DELETE CASCADE, -- 关联检查
    rule_code VARCHAR(50) NOT NULL,                  -- 规则编号（E001/W003/I001）
    severity VARCHAR(10) NOT NULL,                   -- 严重程度：ERROR/WARNING/INFO
    entity_type VARCHAR(20),                         -- 实体类型：route/stop/trip/shape/calendar
    entity_id VARCHAR(100),                          -- 实体ID
    description TEXT NOT NULL,                       -- 问题描述（中文）
    suggestion TEXT,                                 -- 修复建议
    affected_count INTEGER DEFAULT 1,                -- 影响条目数
    example_data JSONB                               -- 示例数据
);
CREATE INDEX IF NOT EXISTS idx_dq_issues_check ON data_quality_issues(check_id);
CREATE INDEX IF NOT EXISTS idx_dq_issues_severity ON data_quality_issues(severity);
