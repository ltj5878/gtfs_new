-- API 调用日志表（记录第三方 API 调用质量）
CREATE TABLE IF NOT EXISTS api_call_logs (
    id SERIAL PRIMARY KEY,
    region TEXT NOT NULL,
    api_name TEXT NOT NULL,         -- '511_SF_BAY', 'MTA_NYC', 'TFNSW_SYDNEY'
    endpoint TEXT NOT NULL,         -- 接口路径
    latency_ms INTEGER NOT NULL,    -- 响应时长（毫秒）
    status_code INTEGER NOT NULL,   -- HTTP 状态码
    error_msg TEXT,                 -- 错误信息
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_api_logs_time ON api_call_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_api_logs_region ON api_call_logs(region);

-- 数据更新追踪表（记录 GTFS 静态数据导入历史）
CREATE TABLE IF NOT EXISTS data_update_logs (
    id SERIAL PRIMARY KEY,
    region TEXT NOT NULL,
    file_version TEXT,              -- 文件版本/文件名
    records_imported INTEGER,       -- 导入记录数
    duration_ms INTEGER,            -- 导入耗时（毫秒）
    status TEXT NOT NULL,           -- 'success' / 'failed'
    error_msg TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_update_logs_region ON data_update_logs(region);
CREATE INDEX IF NOT EXISTS idx_update_logs_time ON data_update_logs(created_at);
