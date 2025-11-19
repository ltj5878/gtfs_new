-- GTFS Database Schema for PostgreSQL
-- This schema follows the GTFS specification with additional SF Muni extensions

-- Drop existing tables if they exist
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

-- Agency table: Transit agencies with service represented in this dataset
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

-- Routes table: Transit routes
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

-- Route attributes table (SF Muni extension)
CREATE TABLE route_attributes (
    route_id TEXT PRIMARY KEY REFERENCES routes(route_id),
    category TEXT,
    subcategory TEXT,
    running_way TEXT
);

-- Directions table (SF Muni extension)
CREATE TABLE directions (
    route_id TEXT REFERENCES routes(route_id),
    direction_id INTEGER,
    direction TEXT,
    PRIMARY KEY (route_id, direction_id)
);

-- Stops table: Individual locations where vehicles pick up or drop off riders
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

-- Calendar table: Service patterns that operate recurringly
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

-- Calendar attributes table (SF Muni extension)
CREATE TABLE calendar_attributes (
    service_id TEXT PRIMARY KEY REFERENCES calendar(service_id),
    service_description TEXT
);

-- Calendar dates table: Exceptions for the services defined in calendar
CREATE TABLE calendar_dates (
    service_id TEXT NOT NULL,
    date DATE NOT NULL,
    exception_type INTEGER NOT NULL,
    PRIMARY KEY (service_id, date)
);

-- Shapes table: Rules for mapping vehicle travel paths
CREATE TABLE shapes (
    shape_id TEXT NOT NULL,
    shape_pt_lon DOUBLE PRECISION NOT NULL,
    shape_pt_lat DOUBLE PRECISION NOT NULL,
    shape_pt_sequence INTEGER NOT NULL,
    shape_dist_traveled DOUBLE PRECISION,
    PRIMARY KEY (shape_id, shape_pt_sequence)
);

-- Trips table: Trips for each route
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

-- Stop times table: Times that a vehicle arrives at and departs from stops
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

-- Rider categories table (SF Muni extension)
CREATE TABLE rider_categories (
    rider_category_id TEXT PRIMARY KEY,
    rider_category_description TEXT
);

-- Fare attributes table: Fare information
CREATE TABLE fare_attributes (
    fare_id TEXT PRIMARY KEY,
    price DOUBLE PRECISION NOT NULL,
    currency_type TEXT NOT NULL,
    payment_method INTEGER NOT NULL,
    transfers INTEGER,
    transfer_duration INTEGER
);

-- Fare rider categories table (SF Muni extension)
CREATE TABLE fare_rider_categories (
    fare_id TEXT NOT NULL REFERENCES fare_attributes(fare_id),
    rider_category_id TEXT NOT NULL REFERENCES rider_categories(rider_category_id),
    price DOUBLE PRECISION NOT NULL,
    expiration_date DATE,
    commencement_date DATE,
    PRIMARY KEY (fare_id, rider_category_id)
);

-- Fare rules table: Rules for applying fares
CREATE TABLE fare_rules (
    fare_id TEXT NOT NULL REFERENCES fare_attributes(fare_id),
    route_id TEXT REFERENCES routes(route_id),
    origin_id TEXT,
    destination_id TEXT,
    contains_id TEXT,
    PRIMARY KEY (fare_id, route_id, origin_id, destination_id, contains_id)
);

-- Feed info table: Dataset metadata
CREATE TABLE feed_info (
    feed_publisher_name TEXT NOT NULL,
    feed_publisher_url TEXT NOT NULL,
    feed_lang TEXT NOT NULL,
    feed_start_date DATE,
    feed_end_date DATE,
    feed_version TEXT
);

-- Attributions table: Dataset attributions
CREATE TABLE attributions (
    organization_name TEXT NOT NULL,
    is_producer INTEGER,
    attribution_url TEXT,
    attribution_email TEXT
);

-- Create indexes for better query performance
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

-- Add comments to tables
COMMENT ON TABLE agency IS 'Transit agencies with service represented in this dataset';
COMMENT ON TABLE routes IS 'Transit routes';
COMMENT ON TABLE stops IS 'Individual locations where vehicles pick up or drop off riders';
COMMENT ON TABLE trips IS 'Trips for each route';
COMMENT ON TABLE stop_times IS 'Times that a vehicle arrives at and departs from stops';
COMMENT ON TABLE calendar IS 'Service patterns that operate recurringly';
COMMENT ON TABLE calendar_dates IS 'Exceptions for the services defined in calendar';
COMMENT ON TABLE shapes IS 'Rules for mapping vehicle travel paths';
COMMENT ON TABLE fare_attributes IS 'Fare information for a transit agency';
COMMENT ON TABLE fare_rules IS 'Rules for applying fares';
COMMENT ON TABLE feed_info IS 'Dataset metadata';
