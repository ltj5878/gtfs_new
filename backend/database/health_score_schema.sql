-- ============================================
-- 线路健康度评分系统表结构
-- 功能：多维度线路健康度评分与历史记录
-- ============================================

-- 线路健康度评分表
CREATE TABLE IF NOT EXISTS route_health_scores (
    id SERIAL PRIMARY KEY,                           -- 主键
    route_id VARCHAR(50) NOT NULL,                   -- 线路ID
    region VARCHAR(20) NOT NULL,                     -- 地区
    score_date DATE NOT NULL DEFAULT CURRENT_DATE,   -- 评分日期
    punctuality_score DECIMAL(5,2),                  -- 准点率得分（0-100）
    frequency_score DECIMAL(5,2),                    -- 频率稳定性得分（0-100）
    coverage_score DECIMAL(5,2),                     -- 覆盖度得分（0-100）
    delay_dist_score DECIMAL(5,2),                   -- 延误分布得分（0-100）
    total_score DECIMAL(5,2),                        -- 综合得分（0-100）
    score_detail JSONB,                              -- 详细计算参数
    created_at TIMESTAMP DEFAULT NOW(),              -- 创建时间
    UNIQUE(route_id, region, score_date)
);
CREATE INDEX IF NOT EXISTS idx_health_region_date ON route_health_scores(region, score_date);
CREATE INDEX IF NOT EXISTS idx_health_total ON route_health_scores(total_score DESC);
