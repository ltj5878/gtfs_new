-- PostgreSQL GTFS 数据库架构
-- 此架构遵循 GTFS 规范，包含 SF Muni 扩展
-- 支持多地区数据隔离（region 字段）

-- 删除已存在的表
DROP TABLE IF EXISTS stop_times CASCADE;
DROP TABLE IF EXISTS trips CASCADE;
DROP TABLE IF EXISTS fare_rules CASCADE;
DROP TABLE IF EXISTS fare_rider_categories CASCADE;
DROP TABLE IF EXISTS fare_attributes CASCADE;
DROP TABLE IF EXISTS rider_categories CASCADE;
DROP TABLE IF EXISTS calendar_dates CASCADE;
DROP TABLE IF EXISTS calendar CASCADE;
DROP TABLE IF EXISTS calendar_attributes CASCADE;
DROP TABLE IF EXISTS shapes CASCADE;
DROP TABLE IF EXISTS stops CASCADE;
DROP TABLE IF EXISTS routes CASCADE;
DROP TABLE IF EXISTS route_attributes CASCADE;
DROP TABLE IF EXISTS directions CASCADE;
DROP TABLE IF EXISTS agency CASCADE;
DROP TABLE IF EXISTS feed_info CASCADE;
DROP TABLE IF EXISTS attributions CASCADE;
DROP TABLE IF EXISTS regions CASCADE;

-- 地区配置表：支持多地区数据源
CREATE TABLE regions (
    region_id TEXT PRIMARY KEY,
    region_name TEXT NOT NULL,
    country TEXT NOT NULL,
    timezone TEXT NOT NULL,
    api_type TEXT NOT NULL,
    api_base_url TEXT,
    gtfs_static_url TEXT,
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 插入初始地区数据
INSERT INTO regions (region_id, region_name, country, timezone, api_type, api_base_url, gtfs_static_url) VALUES
('sf', '旧金山湾区', 'US', 'America/Los_Angeles', 'sf_511', 'https://api.511.org/transit', NULL),
('nyc', '纽约', 'US', 'America/New_York', 'mta', 'https://api-endpoint.mta.info', 'http://web.mta.info/developers/data/nyct/subway/google_transit.zip'),
('sydney', '悉尼', 'AU', 'Australia/Sydney', 'tfnsw', 'https://api.transport.nsw.gov.au/v1/gtfs', 'https://api.transport.nsw.gov.au/v1/gtfs/schedule/buses');

-- 运营机构表：数据集中的公交运营机构
CREATE TABLE agency (
    region TEXT NOT NULL DEFAULT 'sf',
    agency_id TEXT NOT NULL,
    agency_name TEXT NOT NULL,
    agency_url TEXT NOT NULL,
    agency_timezone TEXT NOT NULL,
    agency_lang TEXT,
    agency_phone TEXT,
    agency_fare_url TEXT,
    agency_email TEXT,
    PRIMARY KEY (region, agency_id),
    FOREIGN KEY (region) REFERENCES regions(region_id)
);

-- 线路表：公交线路信息
CREATE TABLE routes (
    region TEXT NOT NULL DEFAULT 'sf',
    route_id TEXT NOT NULL,
    agency_id TEXT,
    route_short_name TEXT,
    route_long_name TEXT,
    route_desc TEXT,
    route_type INTEGER NOT NULL,
    route_url TEXT,
    route_color TEXT,
    route_text_color TEXT,
    PRIMARY KEY (region, route_id),
    FOREIGN KEY (region, agency_id) REFERENCES agency(region, agency_id)
);

-- 线路属性表（SF Muni 扩展）
CREATE TABLE route_attributes (
    region TEXT NOT NULL DEFAULT 'sf',
    route_id TEXT NOT NULL,
    category TEXT,
    subcategory TEXT,
    running_way TEXT,
    PRIMARY KEY (region, route_id),
    FOREIGN KEY (region, route_id) REFERENCES routes(region, route_id)
);

-- 方向表（SF Muni 扩展）
CREATE TABLE directions (
    region TEXT NOT NULL DEFAULT 'sf',
    route_id TEXT NOT NULL,
    direction_id INTEGER NOT NULL,
    direction TEXT,
    PRIMARY KEY (region, route_id, direction_id),
    FOREIGN KEY (region, route_id) REFERENCES routes(region, route_id)
);

-- 站点表：车辆接送乘客的具体位置
CREATE TABLE stops (
    region TEXT NOT NULL DEFAULT 'sf',
    stop_id TEXT NOT NULL,
    stop_code TEXT,
    stop_name TEXT NOT NULL,
    stop_lat DOUBLE PRECISION NOT NULL,
    stop_lon DOUBLE PRECISION NOT NULL,
    zone_id TEXT,
    stop_desc TEXT,
    stop_url TEXT,
    location_type INTEGER,
    parent_station TEXT,
    stop_timezone TEXT,
    wheelchair_boarding INTEGER,
    platform_code TEXT,
    PRIMARY KEY (region, stop_id),
    FOREIGN KEY (region) REFERENCES regions(region_id)
);

-- 日历表：定期运营的服务模式
CREATE TABLE calendar (
    region TEXT NOT NULL DEFAULT 'sf',
    service_id TEXT NOT NULL,
    monday INTEGER NOT NULL,
    tuesday INTEGER NOT NULL,
    wednesday INTEGER NOT NULL,
    thursday INTEGER NOT NULL,
    friday INTEGER NOT NULL,
    saturday INTEGER NOT NULL,
    sunday INTEGER NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    PRIMARY KEY (region, service_id),
    FOREIGN KEY (region) REFERENCES regions(region_id)
);

-- 日历属性表（SF Muni 扩展）
CREATE TABLE calendar_attributes (
    region TEXT NOT NULL DEFAULT 'sf',
    service_id TEXT NOT NULL,
    service_description TEXT,
    PRIMARY KEY (region, service_id),
    FOREIGN KEY (region, service_id) REFERENCES calendar(region, service_id)
);

-- 日历日期表：日历中定义服务的例外情况
CREATE TABLE calendar_dates (
    region TEXT NOT NULL DEFAULT 'sf',
    service_id TEXT NOT NULL,
    date DATE NOT NULL,
    exception_type INTEGER NOT NULL,
    PRIMARY KEY (region, service_id, date),
    FOREIGN KEY (region) REFERENCES regions(region_id)
);

-- 形状表：车辆行驶路径的地理轨迹
CREATE TABLE shapes (
    region TEXT NOT NULL DEFAULT 'sf',
    shape_id TEXT NOT NULL,
    shape_pt_lon DOUBLE PRECISION NOT NULL,
    shape_pt_lat DOUBLE PRECISION NOT NULL,
    shape_pt_sequence INTEGER NOT NULL,
    shape_dist_traveled DOUBLE PRECISION,
    PRIMARY KEY (region, shape_id, shape_pt_sequence),
    FOREIGN KEY (region) REFERENCES regions(region_id)
);

-- 班次表：每条线路的班次信息
CREATE TABLE trips (
    region TEXT NOT NULL DEFAULT 'sf',
    trip_id TEXT NOT NULL,
    route_id TEXT NOT NULL,
    service_id TEXT NOT NULL,
    trip_headsign TEXT,
    direction_id INTEGER,
    block_id TEXT,
    shape_id TEXT,
    trip_short_name TEXT,
    bikes_allowed INTEGER,
    wheelchair_accessible INTEGER,
    PRIMARY KEY (region, trip_id),
    FOREIGN KEY (region, route_id) REFERENCES routes(region, route_id)
);

-- 站点时刻表：车辆到达和离开站点的时间
CREATE TABLE stop_times (
    region TEXT NOT NULL DEFAULT 'sf',
    trip_id TEXT NOT NULL,
    arrival_time TEXT NOT NULL,
    departure_time TEXT NOT NULL,
    stop_id TEXT NOT NULL,
    stop_sequence INTEGER NOT NULL,
    stop_headsign TEXT,
    pickup_type INTEGER,
    drop_off_type INTEGER,
    shape_dist_traveled DOUBLE PRECISION,
    timepoint INTEGER,
    PRIMARY KEY (region, trip_id, stop_sequence),
    FOREIGN KEY (region, trip_id) REFERENCES trips(region, trip_id),
    FOREIGN KEY (region, stop_id) REFERENCES stops(region, stop_id)
);

-- 乘客类别表（SF Muni 扩展）
CREATE TABLE rider_categories (
    region TEXT NOT NULL DEFAULT 'sf',
    rider_category_id TEXT NOT NULL,
    rider_category_description TEXT,
    PRIMARY KEY (region, rider_category_id),
    FOREIGN KEY (region) REFERENCES regions(region_id)
);

-- 票价属性表：票价信息
CREATE TABLE fare_attributes (
    region TEXT NOT NULL DEFAULT 'sf',
    fare_id TEXT NOT NULL,
    price DOUBLE PRECISION NOT NULL,
    currency_type TEXT NOT NULL,
    payment_method INTEGER NOT NULL,
    transfers INTEGER,
    transfer_duration INTEGER,
    PRIMARY KEY (region, fare_id),
    FOREIGN KEY (region) REFERENCES regions(region_id)
);

-- 票价乘客类别表（SF Muni 扩展）
CREATE TABLE fare_rider_categories (
    region TEXT NOT NULL DEFAULT 'sf',
    fare_id TEXT NOT NULL,
    rider_category_id TEXT NOT NULL,
    price DOUBLE PRECISION NOT NULL,
    expiration_date DATE,
    commencement_date DATE,
    PRIMARY KEY (region, fare_id, rider_category_id),
    FOREIGN KEY (region, fare_id) REFERENCES fare_attributes(region, fare_id),
    FOREIGN KEY (region, rider_category_id) REFERENCES rider_categories(region, rider_category_id)
);

-- 票价规则表：票价应用规则
CREATE TABLE fare_rules (
    region TEXT NOT NULL DEFAULT 'sf',
    fare_id TEXT NOT NULL,
    route_id TEXT,
    origin_id TEXT,
    destination_id TEXT,
    contains_id TEXT,
    FOREIGN KEY (region, fare_id) REFERENCES fare_attributes(region, fare_id),
    FOREIGN KEY (region, route_id) REFERENCES routes(region, route_id)
);

-- 数据源信息表：数据集元数据
CREATE TABLE feed_info (
    region TEXT NOT NULL DEFAULT 'sf',
    feed_publisher_name TEXT NOT NULL,
    feed_publisher_url TEXT NOT NULL,
    feed_lang TEXT NOT NULL,
    feed_start_date DATE,
    feed_end_date DATE,
    feed_version TEXT,
    FOREIGN KEY (region) REFERENCES regions(region_id)
);

-- 归属表：数据集归属信息
CREATE TABLE attributions (
    region TEXT NOT NULL DEFAULT 'sf',
    organization_name TEXT NOT NULL,
    is_producer INTEGER,
    attribution_url TEXT,
    attribution_email TEXT,
    FOREIGN KEY (region) REFERENCES regions(region_id)
);

-- 创建索引以提高查询性能
CREATE INDEX idx_routes_agency_id ON routes(region, agency_id);
CREATE INDEX idx_routes_type ON routes(region, route_type);
CREATE INDEX idx_routes_region ON routes(region);

CREATE INDEX idx_stops_location ON stops(stop_lat, stop_lon);
CREATE INDEX idx_stops_name ON stops(region, stop_name);
CREATE INDEX idx_stops_region ON stops(region);

CREATE INDEX idx_trips_route_id ON trips(region, route_id);
CREATE INDEX idx_trips_service_id ON trips(region, service_id);
CREATE INDEX idx_trips_shape_id ON trips(region, shape_id);
CREATE INDEX idx_trips_region ON trips(region);

CREATE INDEX idx_stop_times_trip_id ON stop_times(region, trip_id);
CREATE INDEX idx_stop_times_stop_id ON stop_times(region, stop_id);
CREATE INDEX idx_stop_times_departure ON stop_times(departure_time);

CREATE INDEX idx_calendar_dates_service_id ON calendar_dates(region, service_id);
CREATE INDEX idx_calendar_dates_date ON calendar_dates(date);

CREATE INDEX idx_shapes_shape_id ON shapes(region, shape_id);

CREATE INDEX idx_fare_rules_route_id ON fare_rules(region, route_id);

-- 为表添加注释
COMMENT ON TABLE regions IS '地区配置表，支持多地区数据源';
COMMENT ON TABLE agency IS '数据集中的公交运营机构';
COMMENT ON TABLE routes IS '公交线路信息';
COMMENT ON TABLE stops IS '车辆接送乘客的具体位置';
COMMENT ON TABLE trips IS '每条线路的班次信息';
COMMENT ON TABLE stop_times IS '车辆到达和离开站点的时间';
COMMENT ON TABLE calendar IS '定期运营的服务模式';
COMMENT ON TABLE calendar_dates IS '日历中定义服务的例外情况';
COMMENT ON TABLE shapes IS '车辆行驶路径的地理轨迹';
COMMENT ON TABLE fare_attributes IS '公交机构的票价信息';
COMMENT ON TABLE fare_rules IS '票价应用规则';
COMMENT ON TABLE feed_info IS '数据集元数据';
