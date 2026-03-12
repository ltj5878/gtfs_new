-- PostgreSQL GTFS 数据库架构
-- 此架构遵循 GTFS 规范，包含 SF Muni 扩展

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

-- 运营机构表：数据集中的公交运营机构
CREATE TABLE agency (
    agency_id TEXT PRIMARY KEY,
    agency_name TEXT NOT NULL,
    agency_url TEXT NOT NULL,
    agency_timezone TEXT NOT NULL,
    agency_lang TEXT,
    agency_phone TEXT,
    agency_fare_url TEXT,
    agency_email TEXT
);

-- 线路表：公交线路信息
CREATE TABLE routes (
    route_id TEXT PRIMARY KEY,
    agency_id TEXT REFERENCES agency(agency_id),
    route_short_name TEXT,
    route_long_name TEXT,
    route_desc TEXT,
    route_type INTEGER NOT NULL,
    route_url TEXT,
    route_color TEXT,
    route_text_color TEXT
);

-- 线路属性表（SF Muni 扩展）
CREATE TABLE route_attributes (
    route_id TEXT PRIMARY KEY REFERENCES routes(route_id),
    category TEXT,
    subcategory TEXT,
    running_way TEXT
);

-- 方向表（SF Muni 扩展）
CREATE TABLE directions (
    route_id TEXT REFERENCES routes(route_id),
    direction_id INTEGER,
    direction TEXT,
    PRIMARY KEY (route_id, direction_id)
);

-- 站点表：车辆接送乘客的具体位置
CREATE TABLE stops (
    stop_id TEXT PRIMARY KEY,
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
    platform_code TEXT
);

-- 日历表：定期运营的服务模式
CREATE TABLE calendar (
    service_id TEXT PRIMARY KEY,
    monday INTEGER NOT NULL,
    tuesday INTEGER NOT NULL,
    wednesday INTEGER NOT NULL,
    thursday INTEGER NOT NULL,
    friday INTEGER NOT NULL,
    saturday INTEGER NOT NULL,
    sunday INTEGER NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL
);

-- 日历属性表（SF Muni 扩展）
CREATE TABLE calendar_attributes (
    service_id TEXT PRIMARY KEY REFERENCES calendar(service_id),
    service_description TEXT
);

-- 日历日期表：日历中定义服务的例外情况
CREATE TABLE calendar_dates (
    service_id TEXT NOT NULL,
    date DATE NOT NULL,
    exception_type INTEGER NOT NULL,
    PRIMARY KEY (service_id, date)
);

-- 形状表：车辆行驶路径的地理轨迹
CREATE TABLE shapes (
    shape_id TEXT NOT NULL,
    shape_pt_lon DOUBLE PRECISION NOT NULL,
    shape_pt_lat DOUBLE PRECISION NOT NULL,
    shape_pt_sequence INTEGER NOT NULL,
    shape_dist_traveled DOUBLE PRECISION,
    PRIMARY KEY (shape_id, shape_pt_sequence)
);

-- 班次表：每条线路的班次信息
CREATE TABLE trips (
    trip_id TEXT PRIMARY KEY,
    route_id TEXT NOT NULL REFERENCES routes(route_id),
    service_id TEXT NOT NULL,
    trip_headsign TEXT,
    direction_id INTEGER,
    block_id TEXT,
    shape_id TEXT,
    trip_short_name TEXT,
    bikes_allowed INTEGER,
    wheelchair_accessible INTEGER
);

-- 站点时刻表：车辆到达和离开站点的时间
CREATE TABLE stop_times (
    trip_id TEXT NOT NULL REFERENCES trips(trip_id),
    arrival_time TEXT NOT NULL,
    departure_time TEXT NOT NULL,
    stop_id TEXT NOT NULL REFERENCES stops(stop_id),
    stop_sequence INTEGER NOT NULL,
    stop_headsign TEXT,
    pickup_type INTEGER,
    drop_off_type INTEGER,
    shape_dist_traveled DOUBLE PRECISION,
    timepoint INTEGER,
    PRIMARY KEY (trip_id, stop_sequence)
);

-- 乘客类别表（SF Muni 扩展）
CREATE TABLE rider_categories (
    rider_category_id TEXT PRIMARY KEY,
    rider_category_description TEXT
);

-- 票价属性表：票价信息
CREATE TABLE fare_attributes (
    fare_id TEXT PRIMARY KEY,
    price DOUBLE PRECISION NOT NULL,
    currency_type TEXT NOT NULL,
    payment_method INTEGER NOT NULL,
    transfers INTEGER,
    transfer_duration INTEGER
);

-- 票价乘客类别表（SF Muni 扩展）
CREATE TABLE fare_rider_categories (
    fare_id TEXT NOT NULL REFERENCES fare_attributes(fare_id),
    rider_category_id TEXT NOT NULL REFERENCES rider_categories(rider_category_id),
    price DOUBLE PRECISION NOT NULL,
    expiration_date DATE,
    commencement_date DATE,
    PRIMARY KEY (fare_id, rider_category_id)
);

-- 票价规则表：票价应用规则
CREATE TABLE fare_rules (
    fare_id TEXT NOT NULL REFERENCES fare_attributes(fare_id),
    route_id TEXT REFERENCES routes(route_id),
    origin_id TEXT,
    destination_id TEXT,
    contains_id TEXT,
    PRIMARY KEY (fare_id, route_id, origin_id, destination_id, contains_id)
);

-- 数据源信息表：数据集元数据
CREATE TABLE feed_info (
    feed_publisher_name TEXT NOT NULL,
    feed_publisher_url TEXT NOT NULL,
    feed_lang TEXT NOT NULL,
    feed_start_date DATE,
    feed_end_date DATE,
    feed_version TEXT
);

-- 归属表：数据集归属信息
CREATE TABLE attributions (
    organization_name TEXT NOT NULL,
    is_producer INTEGER,
    attribution_url TEXT,
    attribution_email TEXT
);

-- 创建索引以提高查询性能
CREATE INDEX idx_routes_agency_id ON routes(agency_id);
CREATE INDEX idx_routes_type ON routes(route_type);

CREATE INDEX idx_stops_location ON stops(stop_lat, stop_lon);
CREATE INDEX idx_stops_name ON stops(stop_name);

CREATE INDEX idx_trips_route_id ON trips(route_id);
CREATE INDEX idx_trips_service_id ON trips(service_id);
CREATE INDEX idx_trips_shape_id ON trips(shape_id);

CREATE INDEX idx_stop_times_trip_id ON stop_times(trip_id);
CREATE INDEX idx_stop_times_stop_id ON stop_times(stop_id);
CREATE INDEX idx_stop_times_departure ON stop_times(departure_time);

CREATE INDEX idx_calendar_dates_service_id ON calendar_dates(service_id);
CREATE INDEX idx_calendar_dates_date ON calendar_dates(date);

CREATE INDEX idx_shapes_shape_id ON shapes(shape_id);

CREATE INDEX idx_fare_rules_route_id ON fare_rules(route_id);

-- 为表添加注释
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
