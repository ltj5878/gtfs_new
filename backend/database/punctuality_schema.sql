-- 准点率分析系统数据库表结构
-- 这些表用于存储和分析公交准点率数据

-- 实时延误记录表
-- 存储从GTFS Realtime数据获取的延误记录
CREATE TABLE IF NOT EXISTS realtime_delay_records (
    id SERIAL PRIMARY KEY,
    trip_id TEXT NOT NULL,
    route_id TEXT NOT NULL,
    stop_id TEXT NOT NULL,
    stop_sequence INTEGER NOT NULL,
    vehicle_id TEXT,

    -- 时间信息
    scheduled_time TIMESTAMP NOT NULL,      -- 计划到达时间
    actual_time TIMESTAMP NOT NULL,         -- 实际到达时间
    record_timestamp TIMESTAMP NOT NULL,    -- 记录采集时间

    -- 延误信息（秒，正数为延误，负数为提前）
    arrival_delay INTEGER NOT NULL,         -- 到达延误
    departure_delay INTEGER DEFAULT 0,      -- 出发延误

    -- 数据来源和处理信息
    data_source TEXT DEFAULT 'GTFS_Realtime',  -- 数据来源
    processed BOOLEAN DEFAULT FALSE,           -- 是否已处理
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 外键约束
    FOREIGN KEY (route_id) REFERENCES routes(route_id),
    FOREIGN KEY (stop_id) REFERENCES stops(stop_id),
    FOREIGN KEY (trip_id) REFERENCES trips(trip_id)
);

-- 线路准点率日统计表
-- 按线路和日期聚合的准点率统计数据
CREATE TABLE IF NOT EXISTS route_daily_punctuality (
    id SERIAL PRIMARY KEY,
    route_id TEXT NOT NULL,
    stat_date DATE NOT NULL,

    -- 基础统计
    total_trips INTEGER DEFAULT 0,          -- 总班次
    on_time_trips INTEGER DEFAULT 0,        -- 准点班次
    early_trips INTEGER DEFAULT 0,          -- 提前班次
    late_trips INTEGER DEFAULT 0,           -- 延误班次
    very_late_trips INTEGER DEFAULT 0,      -- 严重延误班次

    -- 延误统计（秒）
    avg_arrival_delay DECIMAL(8,2) DEFAULT 0,   -- 平均到达延误
    max_arrival_delay INTEGER DEFAULT 0,        -- 最大到达延误
    min_arrival_delay INTEGER DEFAULT 0,        -- 最小到达延误（负值表示提前）

    -- 准点率指标（百分比）
    punctuality_rate DECIMAL(5,2) DEFAULT 0,     -- 准点率
    early_rate DECIMAL(5,2) DEFAULT 0,           -- 提前率
    late_rate DECIMAL(5,2) DEFAULT 0,            -- 延误率
    very_late_rate DECIMAL(5,2) DEFAULT 0,       -- 严重延误率

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 唯一约束
    UNIQUE(route_id, stat_date),
    FOREIGN KEY (route_id) REFERENCES routes(route_id)
);

-- 站点准点率日统计表
-- 按站点和日期聚合的准点率统计数据
CREATE TABLE IF NOT EXISTS stop_daily_punctuality (
    id SERIAL PRIMARY KEY,
    stop_id TEXT NOT NULL,
    stat_date DATE NOT NULL,

    -- 基础统计
    total_visits INTEGER DEFAULT 0,        -- 总到站次数
    on_time_visits INTEGER DEFAULT 0,      -- 准点到站
    early_visits INTEGER DEFAULT 0,        -- 提前到站
    late_visits INTEGER DEFAULT 0,         -- 延误到站
    very_late_visits INTEGER DEFAULT 0,    -- 严重延误到站

    -- 延误统计
    avg_arrival_delay DECIMAL(8,2) DEFAULT 0,
    max_arrival_delay INTEGER DEFAULT 0,
    min_arrival_delay INTEGER DEFAULT 0,

    -- 准点率指标
    punctuality_rate DECIMAL(5,2) DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(stop_id, stat_date),
    FOREIGN KEY (stop_id) REFERENCES stops(stop_id)
);

-- 时段准点率统计表
-- 按小时时段统计的准点率数据
CREATE TABLE IF NOT EXISTS hourly_punctuality_stats (
    id SERIAL PRIMARY KEY,
    route_id TEXT,
    stop_id TEXT,
    hour_of_day INTEGER NOT NULL,           -- 小时（0-23）
    stat_date DATE NOT NULL,

    -- 基础统计
    total_trips INTEGER DEFAULT 0,
    on_time_trips INTEGER DEFAULT 0,

    -- 延误统计
    avg_arrival_delay DECIMAL(8,2) DEFAULT 0,
    max_arrival_delay INTEGER DEFAULT 0,

    -- 准点率
    punctuality_rate DECIMAL(5,2) DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(route_id, stop_id, hour_of_day, stat_date),
    FOREIGN KEY (route_id) REFERENCES routes(route_id),
    FOREIGN KEY (stop_id) REFERENCES stops(stop_id)
);

-- 实时车辆位置表
-- 存储实时车辆位置信息（用于速度计算和轨迹分析）
CREATE TABLE IF NOT EXISTS realtime_vehicle_positions (
    id SERIAL PRIMARY KEY,
    vehicle_id TEXT NOT NULL,
    trip_id TEXT,
    route_id TEXT,

    -- 位置信息
    latitude DECIMAL(10,8) NOT NULL,
    longitude DECIMAL(11,8) NOT NULL,
    bearing DECIMAL(5,2),                   -- 方向角（度）
    speed DECIMAL(5,2),                     -- 速度（km/h，如果GPS提供）

    -- 时间信息
    position_timestamp TIMESTAMP NOT NULL,  -- GPS时间戳
    record_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 记录时间

    -- 状态信息
    current_status INTEGER,                 -- 车辆状态（INCOMING_AT, STOPPED_AT, IN_TRANSIT_TO）
    stop_id TEXT,                          -- 当前/下一站ID

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (route_id) REFERENCES routes(route_id),
    FOREIGN KEY (trip_id) REFERENCES trips(trip_id),
    FOREIGN KEY (stop_id) REFERENCES stops(stop_id)
);

-- 系统准点率概览表
-- 存储系统级别的准点率统计摘要
CREATE TABLE IF NOT EXISTS system_punctuality_overview (
    id SERIAL PRIMARY KEY,
    stat_date DATE NOT NULL,

    -- 系统整体统计
    total_routes INTEGER DEFAULT 0,
    total_trips INTEGER DEFAULT 0,
    system_punctuality_rate DECIMAL(5,2) DEFAULT 0,
    system_avg_delay_minutes DECIMAL(8,2) DEFAULT 0,

    -- 线路排名（JSON格式存储）
    best_performing_routes JSON,            -- 准点率最高的线路
    worst_performing_routes JSON,           -- 准点率最低的线路

    -- 时段统计
    morning_peak_rate DECIMAL(5,2) DEFAULT 0,    -- 早高峰准点率（7:00-9:00）
    evening_peak_rate DECIMAL(5,2) DEFAULT 0,    -- 晚高峰准点率（17:00-19:00）
    off_peak_rate DECIMAL(5,2) DEFAULT 0,        -- 非高峰时段准点率

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(stat_date)
);

-- 准点率分析配置表
-- 存储准点率分析的配置参数
CREATE TABLE IF NOT EXISTS punctuality_config (
    id SERIAL PRIMARY KEY,
    config_key TEXT UNIQUE NOT NULL,
    config_value TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 插入默认配置
INSERT INTO punctuality_config (config_key, config_value, description) VALUES
('early_threshold_seconds', '60', '提前多少秒算提前到达'),
('on_time_threshold_seconds', '120', '延误多少秒内算准点'),
('very_late_threshold_seconds', '300', '延误多少秒算严重延误'),
('morning_peak_start_hour', '7', '早高峰开始时间'),
('morning_peak_end_hour', '9', '早高峰结束时间'),
('evening_peak_start_hour', '17', '晚高峰开始时间'),
('evening_peak_end_hour', '19', '晚高峰结束时间'),
('data_retention_days', '90', '数据保留天数'),
('analysis_batch_size', '1000', '批量分析处理大小')
ON CONFLICT (config_key) DO NOTHING;

-- 创建索引以提高查询性能

-- 实时延误记录索引
CREATE INDEX IF NOT EXISTS idx_delay_records_route_time ON realtime_delay_records(route_id, scheduled_time);
CREATE INDEX IF NOT EXISTS idx_delay_records_stop_time ON realtime_delay_records(stop_id, scheduled_time);
CREATE INDEX IF NOT EXISTS idx_delay_records_trip ON realtime_delay_records(trip_id);
CREATE INDEX IF NOT EXISTS idx_delay_records_timestamp ON realtime_delay_records(record_timestamp);
CREATE INDEX IF NOT EXISTS idx_delay_records_processed ON realtime_delay_records(processed);

-- 线路日统计索引
CREATE INDEX IF NOT EXISTS idx_route_daily_date ON route_daily_punctuality(stat_date);
CREATE INDEX IF NOT EXISTS idx_route_daily_route ON route_daily_punctuality(route_id);

-- 站点日统计索引
CREATE INDEX IF NOT EXISTS idx_stop_daily_date ON stop_daily_punctuality(stat_date);
CREATE INDEX IF NOT EXISTS idx_stop_daily_stop ON stop_daily_punctuality(stop_id);

-- 时段统计索引
CREATE INDEX IF NOT EXISTS idx_hourly_date_hour ON hourly_punctuality_stats(stat_date, hour_of_day);
CREATE INDEX IF NOT EXISTS idx_hourly_route ON hourly_punctuality_stats(route_id);

-- 实时车辆位置索引
CREATE INDEX IF NOT EXISTS idx_vehicle_pos_vehicle ON realtime_vehicle_positions(vehicle_id);
CREATE INDEX IF NOT EXISTS idx_vehicle_pos_trip ON realtime_vehicle_positions(trip_id);
CREATE INDEX IF NOT EXISTS idx_vehicle_pos_timestamp ON realtime_vehicle_positions(position_timestamp);
CREATE INDEX IF NOT EXISTS idx_vehicle_pos_location ON realtime_vehicle_positions(latitude, longitude);

-- 系统概览索引
CREATE INDEX IF NOT EXISTS idx_system_overview_date ON system_punctuality_overview(stat_date);

-- 创建视图以简化常用查询

-- 线路准点率详细视图
CREATE OR REPLACE VIEW route_punctuality_detail AS
SELECT
    r.route_id,
    r.route_short_name,
    r.route_long_name,
    r.route_type,
    COALESCE(rdp.total_trips, 0) as total_trips,
    COALESCE(rdp.punctuality_rate, 0) as punctuality_rate,
    COALESCE(rdp.avg_arrival_delay, 0) / 60 as avg_delay_minutes,
    COALESCE(rdp.on_time_trips, 0) as on_time_trips,
    COALESCE(rdp.late_trips, 0) as late_trips,
    COALESCE(rdp.very_late_trips, 0) as very_late_trips,
    rdp.stat_date
FROM routes r
LEFT JOIN route_daily_punctuality rdp ON r.route_id = rdp.route_id
WHERE rdp.stat_date = CURRENT_DATE OR rdp.stat_date IS NULL;

-- 站点准点率详细视图
CREATE OR REPLACE VIEW stop_punctuality_detail AS
SELECT
    s.stop_id,
    s.stop_name,
    s.stop_lat,
    s.stop_lon,
    COALESCE(sdp.total_visits, 0) as total_visits,
    COALESCE(sdp.punctuality_rate, 0) as punctuality_rate,
    COALESCE(sdp.avg_arrival_delay, 0) / 60 as avg_delay_minutes,
    sdp.stat_date
FROM stops s
LEFT JOIN stop_daily_punctuality sdp ON s.stop_id = sdp.stop_id
WHERE sdp.stat_date = CURRENT_DATE OR sdp.stat_date IS NULL;

-- 实时延误汇总视图
CREATE OR REPLACE VIEW realtime_delay_summary AS
SELECT
    route_id,
    COUNT(*) as total_records,
    COUNT(CASE WHEN arrival_delay >= 0 THEN 1 END) as delayed_count,
    COUNT(CASE WHEN arrival_delay < 0 THEN 1 END) as early_count,
    COUNT(CASE WHEN ABS(arrival_delay) <= 120 THEN 1 END) as on_time_count,
    AVG(arrival_delay) / 60 as avg_delay_minutes,
    MAX(arrival_delay) / 60 as max_delay_minutes,
    MIN(arrival_delay) / 60 as min_delay_minutes,
    DATE(record_timestamp) as stat_date
FROM realtime_delay_records
WHERE record_timestamp >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY route_id, DATE(record_timestamp);

-- 创建自动更新时间戳的触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为相关表创建触发器
CREATE TRIGGER update_route_daily_punctuality_updated_at
    BEFORE UPDATE ON route_daily_punctuality
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_stop_daily_punctuality_updated_at
    BEFORE UPDATE ON stop_daily_punctuality
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_hourly_punctuality_stats_updated_at
    BEFORE UPDATE ON hourly_punctuality_stats
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_system_punctuality_overview_updated_at
    BEFORE UPDATE ON system_punctuality_overview
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_punctuality_config_updated_at
    BEFORE UPDATE ON punctuality_config
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();