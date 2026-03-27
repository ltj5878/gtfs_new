#!/usr/bin/env python3
"""
GTFS 数据 RESTful API 服务
提供查询 PostgreSQL 中 GTFS 数据的 HTTP 接口
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from core.db import Database, execute_query, execute_query_one, execute_count, execute_write
from core.route_mappings import enrich_route_attributes
from typing import Dict, Any, List
import os
import sys

# 将 backend 目录加入 sys.path，确保 auth 模块可被导入
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth.routes import auth_bp
from auth.models import init_default_user, verify_token

app = Flask(__name__)
CORS(app)
app.register_blueprint(auth_bp)


@app.before_request
def before_first_request():
    """初始化数据库连接池"""
    if Database._connection_pool is None:
        Database.initialize()
        init_default_user()


@app.teardown_appcontext
def shutdown_session(exception=None):
    """请求结束时的清理工作"""
    pass


def success_response(data: Any, message: str = "success") -> Dict:
    """成功响应格式"""
    return {
        "code": 200,
        "message": message,
        "data": data
    }


def error_response(message: str, code: int = 400) -> Dict:
    """错误响应格式"""
    return {
        "code": code,
        "message": message,
        "data": None
    }


@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    try:
        result = execute_query_one("SELECT 1 as status")
        if result:
            return jsonify(success_response({"status": "healthy", "database": "connected"}))
        return jsonify(error_response("数据库连接失败", 500)), 500
    except Exception as e:
        return jsonify(error_response(f"健康检查失败: {str(e)}", 500)), 500


@app.route('/api/regions', methods=['GET'])
def get_regions():
    """获取所有可用地区列表"""
    try:
        query = """
            SELECT region_id, region_name, country, timezone, api_type,
                   api_base_url, gtfs_static_url, enabled
            FROM regions
            WHERE enabled = true
            ORDER BY region_id
        """
        regions = execute_query(query)
        return jsonify(success_response(regions))
    except Exception as e:
        return jsonify(error_response(f"查询失败: {str(e)}", 500)), 500


@app.route('/api/agencies', methods=['GET'])
def get_agencies():
    """获取所有运营机构"""
    try:
        region = request.args.get('region')
        where_clauses = []
        params = []

        if region:
            where_clauses.append("region = %s")
            params.append(region)

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        query = f"""
            SELECT region, agency_id, agency_name, agency_url, agency_timezone,
                   agency_lang, agency_phone, agency_fare_url, agency_email
            FROM agency
            WHERE {where_sql}
            ORDER BY agency_name
        """
        agencies = execute_query(query, tuple(params) if params else None)
        return jsonify(success_response(agencies))
    except Exception as e:
        return jsonify(error_response(f"查询失败: {str(e)}", 500)), 500


@app.route('/api/agencies/<agency_id>', methods=['GET'])
def get_agency(agency_id):
    """获取指定运营机构详情"""
    try:
        region = request.args.get('region')
        query = """
            SELECT region, agency_id, agency_name, agency_url, agency_timezone,
                   agency_lang, agency_phone, agency_fare_url, agency_email
            FROM agency
            WHERE agency_id = %s
        """
        params = [agency_id]
        if region:
            query += " AND region = %s"
            params.append(region)

        agency = execute_query_one(query, tuple(params))
        if agency:
            return jsonify(success_response(agency))
        return jsonify(error_response("运营机构不存在", 404)), 404
    except Exception as e:
        return jsonify(error_response(f"查询失败: {str(e)}", 500)), 500


@app.route('/api/routes', methods=['GET'])
def get_routes():
    """获取所有线路，支持分页和筛选"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        agency_id = request.args.get('agency_id', type=str)
        route_type = request.args.get('route_type', type=int)
        search = request.args.get('search', type=str)
        region = request.args.get('region', type=str)

        offset = (page - 1) * page_size

        where_clauses = []
        params = []

        if region:
            where_clauses.append("r.region = %s")
            params.append(region)

        if agency_id:
            where_clauses.append("r.agency_id = %s")
            params.append(agency_id)

        if route_type is not None:
            where_clauses.append("r.route_type = %s")
            params.append(route_type)

        if search:
            where_clauses.append(
                "(r.route_short_name ILIKE %s OR r.route_long_name ILIKE %s)"
            )
            search_pattern = f"%{search}%"
            params.extend([search_pattern, search_pattern])

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        count_query = f"SELECT COUNT(*) FROM routes r WHERE {where_sql}"
        total = execute_count(count_query, tuple(params))

        query = f"""
            SELECT r.region, r.route_id, r.agency_id, r.route_short_name, r.route_long_name,
                   r.route_desc, r.route_type, r.route_url, r.route_color, r.route_text_color,
                   ra.category, ra.subcategory, ra.running_way
            FROM routes r
            LEFT JOIN route_attributes ra ON r.region = ra.region AND r.route_id = ra.route_id
            WHERE {where_sql}
            ORDER BY r.route_short_name, r.route_long_name
            LIMIT %s OFFSET %s
        """
        params.extend([page_size, offset])

        routes = execute_query(query, tuple(params))

        # 为每条路线添加映射后的文本
        lang = request.args.get('lang', 'zh')
        enriched_routes = [enrich_route_attributes(route, lang) for route in routes]

        return jsonify(success_response({
            "routes": enriched_routes,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size
            }
        }))
    except Exception as e:
        return jsonify(error_response(f"查询失败: {str(e)}", 500)), 500


@app.route('/api/routes/<route_id>', methods=['GET'])
def get_route(route_id):
    """获取指定线路详情"""
    try:
        region = request.args.get('region')
        query = """
            SELECT r.region, r.route_id, r.agency_id, r.route_short_name, r.route_long_name,
                   r.route_desc, r.route_type, r.route_url, r.route_color, r.route_text_color,
                   ra.category, ra.subcategory, ra.running_way
            FROM routes r
            LEFT JOIN route_attributes ra ON r.region = ra.region AND r.route_id = ra.route_id
            WHERE r.route_id = %s
        """
        params = [route_id]
        if region:
            query += " AND r.region = %s"
            params.append(region)

        route = execute_query_one(query, tuple(params))
        if route:
            lang = request.args.get('lang', 'zh')
            enriched_route = enrich_route_attributes(route, lang)
            return jsonify(success_response(enriched_route))
        return jsonify(error_response("线路不存在", 404)), 404
    except Exception as e:
        return jsonify(error_response(f"查询失败: {str(e)}", 500)), 500


@app.route('/api/routes/<route_id>/directions', methods=['GET'])
def get_route_directions(route_id):
    """获取线路的所有方向"""
    try:
        region = request.args.get('region')
        query = """
            SELECT region, route_id, direction_id, direction
            FROM directions
            WHERE route_id = %s
        """
        params = [route_id]
        if region:
            query += " AND region = %s"
            params.append(region)
        query += " ORDER BY direction_id"

        directions = execute_query(query, tuple(params))
        return jsonify(success_response(directions))
    except Exception as e:
        return jsonify(error_response(f"查询失败: {str(e)}", 500)), 500


@app.route('/api/routes/<route_id>/stops', methods=['GET'])
def get_route_stops(route_id):
    """获取线路的所有站点"""
    try:
        direction_id = request.args.get('direction_id', type=int)
        region = request.args.get('region')

        where_clause = "r.route_id = %s"
        params = [route_id]

        if region:
            where_clause += " AND r.region = %s"
            params.append(region)

        if direction_id is not None:
            where_clause += " AND t.direction_id = %s"
            params.append(direction_id)

        query = f"""
            SELECT DISTINCT s.stop_id, s.stop_code, s.stop_name,
                   s.stop_lat, s.stop_lon, s.stop_desc,
                   MIN(st.stop_sequence) as min_sequence
            FROM stops s
            JOIN stop_times st ON s.region = st.region AND s.stop_id = st.stop_id
            JOIN trips t ON st.region = t.region AND st.trip_id = t.trip_id
            JOIN routes r ON t.region = r.region AND t.route_id = r.route_id
            WHERE {where_clause}
            GROUP BY s.stop_id, s.stop_code, s.stop_name, s.stop_lat, s.stop_lon, s.stop_desc
            ORDER BY min_sequence
        """
        stops = execute_query(query, tuple(params))
        return jsonify(success_response(stops))
    except Exception as e:
        return jsonify(error_response(f"查询失败: {str(e)}", 500)), 500


@app.route('/api/stops', methods=['GET'])
def get_stops():
    """获取所有站点，支持分页和地理位置筛选"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        search = request.args.get('search', type=str)
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        radius = request.args.get('radius', 1.0, type=float)
        region = request.args.get('region', type=str)
        agency_id = request.args.get('agency_id', type=str)

        offset = (page - 1) * page_size

        # 按运营机构筛选时需要 JOIN
        if agency_id:
            where_clauses = ["r.agency_id = %s"]
            params = [agency_id]
            if region:
                where_clauses.append("s.region = %s")
                params.append(region)
            if search:
                where_clauses.append("s.stop_name ILIKE %s")
                params.append(f"%{search}%")
            where_sql = " AND ".join(where_clauses)

            count_query = f"""
                SELECT COUNT(DISTINCT s.stop_id) FROM stops s
                JOIN stop_times st ON s.region = st.region AND s.stop_id = st.stop_id
                JOIN trips t ON st.region = t.region AND st.trip_id = t.trip_id
                JOIN routes r ON t.region = r.region AND t.route_id = r.route_id
                WHERE {where_sql}
            """
            total = execute_count(count_query, tuple(params))

            query = f"""
                SELECT DISTINCT s.region, s.stop_id, s.stop_code, s.stop_name, s.stop_lat, s.stop_lon,
                       s.zone_id, s.stop_desc, s.stop_url, s.location_type,
                       s.parent_station, s.stop_timezone, s.wheelchair_boarding, s.platform_code
                FROM stops s
                JOIN stop_times st ON s.region = st.region AND s.stop_id = st.stop_id
                JOIN trips t ON st.region = t.region AND st.trip_id = t.trip_id
                JOIN routes r ON t.region = r.region AND t.route_id = r.route_id
                WHERE {where_sql}
                ORDER BY s.stop_name
                LIMIT %s OFFSET %s
            """
            params.extend([page_size, offset])
        else:
            where_clauses = []
            params = []

            if region:
                where_clauses.append("region = %s")
                params.append(region)

            if search:
                where_clauses.append("stop_name ILIKE %s")
                params.append(f"%{search}%")

            if lat is not None and lon is not None:
                where_clauses.append("""
                    (6371 * acos(
                        cos(radians(%s)) * cos(radians(stop_lat)) *
                        cos(radians(stop_lon) - radians(%s)) +
                        sin(radians(%s)) * sin(radians(stop_lat))
                    )) <= %s
                """)
                params.extend([lat, lon, lat, radius])

            where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

            count_query = f"SELECT COUNT(*) FROM stops WHERE {where_sql}"
            total = execute_count(count_query, tuple(params))

            query = f"""
                SELECT region, stop_id, stop_code, stop_name, stop_lat, stop_lon,
                       zone_id, stop_desc, stop_url, location_type,
                       parent_station, stop_timezone, wheelchair_boarding, platform_code
                FROM stops
                WHERE {where_sql}
                ORDER BY stop_name
                LIMIT %s OFFSET %s
            """
            params.extend([page_size, offset])

        stops = execute_query(query, tuple(params))

        return jsonify(success_response({
            "stops": stops,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size
            }
        }))
    except Exception as e:
        return jsonify(error_response(f"查询失败: {str(e)}", 500)), 500


@app.route('/api/stops/<stop_id>', methods=['GET'])
def get_stop(stop_id):
    """获取指定站点详情"""
    try:
        region = request.args.get('region')
        query = """
            SELECT region, stop_id, stop_code, stop_name, stop_lat, stop_lon,
                   zone_id, stop_desc, stop_url, location_type,
                   parent_station, stop_timezone, wheelchair_boarding, platform_code
            FROM stops
            WHERE stop_id = %s
        """
        params = [stop_id]
        if region:
            query += " AND region = %s"
            params.append(region)

        stop = execute_query_one(query, tuple(params))
        if stop:
            return jsonify(success_response(stop))
        return jsonify(error_response("站点不存在", 404)), 404
    except Exception as e:
        return jsonify(error_response(f"查询失败: {str(e)}", 500)), 500


@app.route('/api/stops/<stop_id>/routes', methods=['GET'])
def get_stop_routes(stop_id):
    """获取经过指定站点的所有线路"""
    try:
        region = request.args.get('region')
        where_clause = "st.stop_id = %s"
        params = [stop_id]

        if region:
            where_clause += " AND r.region = %s"
            params.append(region)

        query = f"""
            SELECT DISTINCT r.region, r.route_id, r.route_short_name, r.route_long_name,
                   r.route_type, r.route_color, r.route_text_color
            FROM routes r
            JOIN trips t ON r.region = t.region AND r.route_id = t.route_id
            JOIN stop_times st ON t.region = st.region AND t.trip_id = st.trip_id
            WHERE {where_clause}
            ORDER BY r.route_short_name, r.route_long_name
        """
        routes = execute_query(query, tuple(params))
        return jsonify(success_response(routes))
    except Exception as e:
        return jsonify(error_response(f"查询失败: {str(e)}", 500)), 500


@app.route('/api/trips', methods=['GET'])
def get_trips():
    """获取班次信息，支持按线路筛选"""
    try:
        route_id = request.args.get('route_id', type=str)
        service_id = request.args.get('service_id', type=str)
        direction_id = request.args.get('direction_id', type=int)
        region = request.args.get('region', type=str)
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)

        offset = (page - 1) * page_size

        where_clauses = []
        params = []

        if region:
            where_clauses.append("region = %s")
            params.append(region)

        if route_id:
            where_clauses.append("route_id = %s")
            params.append(route_id)

        if service_id:
            where_clauses.append("service_id = %s")
            params.append(service_id)

        if direction_id is not None:
            where_clauses.append("direction_id = %s")
            params.append(direction_id)

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        count_query = f"SELECT COUNT(*) FROM trips WHERE {where_sql}"
        total = execute_count(count_query, tuple(params))

        query = f"""
            SELECT region, trip_id, route_id, service_id, trip_headsign,
                   trip_short_name, direction_id, block_id, shape_id,
                   wheelchair_accessible, bikes_allowed
            FROM trips
            WHERE {where_sql}
            ORDER BY trip_id
            LIMIT %s OFFSET %s
        """
        params.extend([page_size, offset])

        trips = execute_query(query, tuple(params))

        return jsonify(success_response({
            "trips": trips,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size
            }
        }))
    except Exception as e:
        return jsonify(error_response(f"查询失败: {str(e)}", 500)), 500


@app.route('/api/trips/<trip_id>', methods=['GET'])
def get_trip(trip_id):
    """获取指定班次详情"""
    try:
        region = request.args.get('region')
        query = """
            SELECT region, trip_id, route_id, service_id, trip_headsign,
                   trip_short_name, direction_id, block_id, shape_id,
                   wheelchair_accessible, bikes_allowed
            FROM trips
            WHERE trip_id = %s
        """
        params = [trip_id]
        if region:
            query += " AND region = %s"
            params.append(region)

        trip = execute_query_one(query, tuple(params))
        if trip:
            return jsonify(success_response(trip))
        return jsonify(error_response("班次不存在", 404)), 404
    except Exception as e:
        return jsonify(error_response(f"查询失败: {str(e)}", 500)), 500


@app.route('/api/trips/<trip_id>/stop_times', methods=['GET'])
def get_trip_stop_times(trip_id):
    """获取班次的所有站点时刻表"""
    try:
        region = request.args.get('region')
        query = """
            SELECT st.region, st.trip_id, st.arrival_time, st.departure_time,
                   st.stop_id, st.stop_sequence, st.stop_headsign,
                   st.pickup_type, st.drop_off_type, st.shape_dist_traveled,
                   s.stop_name, s.stop_lat, s.stop_lon
            FROM stop_times st
            JOIN stops s ON st.region = s.region AND st.stop_id = s.stop_id
            WHERE st.trip_id = %s
        """
        params = [trip_id]
        if region:
            query += " AND st.region = %s"
            params.append(region)
        query += " ORDER BY st.stop_sequence"

        stop_times = execute_query(query, tuple(params))
        return jsonify(success_response(stop_times))
    except Exception as e:
        return jsonify(error_response(f"查询失败: {str(e)}", 500)), 500


@app.route('/api/routes/<route_id>/shapes', methods=['GET'])
def get_route_shapes(route_id):
    """获取指定线路的所有轨迹"""
    try:
        direction_id = request.args.get('direction_id', type=int)
        region = request.args.get('region')

        # 根据trips表获取该线路的所有shape_id
        query = """
            SELECT DISTINCT t.shape_id, d.direction_id
            FROM trips t
            LEFT JOIN directions d ON t.region = d.region AND t.route_id = d.route_id AND t.direction_id = d.direction_id
            WHERE t.route_id = %s
        """
        params = [route_id]

        if region:
            query += " AND t.region = %s"
            params.append(region)

        if direction_id is not None:
            query += " AND t.direction_id = %s"
            params.append(direction_id)

        shape_ids = execute_query(query, tuple(params))

        if not shape_ids:
            return jsonify(success_response([]))

        # 获取所有shape的轨迹点
        all_shapes = []
        for shape_info in shape_ids:
            shape_id = shape_info['shape_id']
            shape_direction_id = shape_info.get('direction_id')

            shape_query = """
                SELECT shape_id, shape_pt_lat, shape_pt_lon,
                       shape_pt_sequence, shape_dist_traveled
                FROM shapes
                WHERE shape_id = %s
            """
            shape_params = [shape_id]
            if region:
                shape_query += " AND region = %s"
                shape_params.append(region)
            shape_query += " ORDER BY shape_pt_sequence"

            shape_points = execute_query(shape_query, tuple(shape_params))

            if shape_points:
                all_shapes.append({
                    'shape_id': shape_id,
                    'direction_id': shape_direction_id,
                    'points': shape_points
                })

        return jsonify(success_response(all_shapes))
    except Exception as e:
        return jsonify(error_response(f"查询失败: {str(e)}", 500)), 500


@app.route('/api/shapes/<shape_id>', methods=['GET'])
def get_shape(shape_id):
    """获取线路轨迹"""
    try:
        region = request.args.get('region')
        query = """
            SELECT shape_id, shape_pt_lat, shape_pt_lon,
                   shape_pt_sequence, shape_dist_traveled
            FROM shapes
            WHERE shape_id = %s
        """
        params = [shape_id]
        if region:
            query += " AND region = %s"
            params.append(region)
        query += " ORDER BY shape_pt_sequence"

        shape_points = execute_query(query, tuple(params))
        if shape_points:
            return jsonify(success_response(shape_points))
        return jsonify(error_response("轨迹不存在", 404)), 404
    except Exception as e:
        return jsonify(error_response(f"查询失败: {str(e)}", 500)), 500


@app.route('/api/calendar', methods=['GET'])
def get_calendar():
    """获取服务日历"""
    try:
        region = request.args.get('region')
        query = """
            SELECT c.region, c.service_id, c.monday, c.tuesday, c.wednesday,
                   c.thursday, c.friday, c.saturday, c.sunday,
                   c.start_date, c.end_date, ca.service_description
            FROM calendar c
            LEFT JOIN calendar_attributes ca ON c.region = ca.region AND c.service_id = ca.service_id
        """
        params = []
        if region:
            query += " WHERE c.region = %s"
            params.append(region)
        query += " ORDER BY c.service_id"

        calendar = execute_query(query, tuple(params) if params else None)
        return jsonify(success_response(calendar))
    except Exception as e:
        return jsonify(error_response(f"查询失败: {str(e)}", 500)), 500


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """获取数据统计信息"""
    try:
        region = request.args.get('region')

        if region:
            stats = {
                "agencies": execute_count("SELECT COUNT(*) FROM agency WHERE region = %s", (region,)),
                "routes": execute_count("SELECT COUNT(*) FROM routes WHERE region = %s", (region,)),
                "stops": execute_count("SELECT COUNT(*) FROM stops WHERE region = %s", (region,)),
                "trips": execute_count("SELECT COUNT(*) FROM trips WHERE region = %s", (region,)),
                "stop_times": execute_count("SELECT COUNT(*) FROM stop_times WHERE region = %s", (region,)),
                "shapes": execute_count("SELECT COUNT(DISTINCT shape_id) FROM shapes WHERE region = %s", (region,))
            }
        else:
            stats = {
                "agencies": execute_count("SELECT COUNT(*) FROM agency"),
                "routes": execute_count("SELECT COUNT(*) FROM routes"),
                "stops": execute_count("SELECT COUNT(*) FROM stops"),
                "trips": execute_count("SELECT COUNT(*) FROM trips"),
                "stop_times": execute_count("SELECT COUNT(*) FROM stop_times"),
                "shapes": execute_count("SELECT COUNT(DISTINCT shape_id) FROM shapes")
            }
        return jsonify(success_response(stats))
    except Exception as e:
        return jsonify(error_response(f"查询失败: {str(e)}", 500)), 500


# ===== 准点率和实时数据接口 =====

@app.route('/api/realtime/vehicles', methods=['GET'])
def get_realtime_vehicles():
    """获取实时车辆位置信息"""
    try:
        route_id = request.args.get('route_id')
        region = request.args.get('region')
        limit = min(int(request.args.get('limit', 100)), 500)

        base_query = """
            SELECT region, vehicle_id, trip_id, route_id, latitude, longitude,
                   bearing, speed, position_timestamp, current_status, stop_id
            FROM realtime_vehicle_positions
            WHERE position_timestamp >= NOW() - INTERVAL '10 minutes'
        """

        params = []
        if region:
            base_query += " AND region = %s"
            params.append(region)
        if route_id:
            base_query += " AND route_id = %s"
            params.append(route_id)

        base_query += " ORDER BY position_timestamp DESC LIMIT %s"
        params.append(limit)

        vehicles = execute_query(base_query, params)
        return jsonify(success_response(vehicles))
    except Exception as e:
        return jsonify(error_response(f"查询失败: {str(e)}", 500)), 500


@app.route('/api/realtime/delays', methods=['GET'])
def get_realtime_delays():
    """获取实时延误信息"""
    try:
        route_id = request.args.get('route_id')
        stop_id = request.args.get('stop_id')
        region = request.args.get('region')
        hours = min(int(request.args.get('hours', 2)), 24)
        limit = min(int(request.args.get('limit', 200)), 1000)

        base_query = """
            SELECT rdr.region, rdr.trip_id, rdr.route_id, rdr.stop_id, rdr.vehicle_id,
                   rdr.scheduled_time, rdr.actual_time, rdr.arrival_delay,
                   rdr.departure_delay, rdr.record_timestamp,
                   r.route_short_name, r.route_long_name,
                   s.stop_name
            FROM realtime_delay_records rdr
            LEFT JOIN routes r ON rdr.region = r.region AND rdr.route_id = r.route_id
            LEFT JOIN stops s ON rdr.region = s.region AND rdr.stop_id = s.stop_id
            WHERE record_timestamp >= NOW() - INTERVAL '%s hours'
        """ % hours

        params = []
        if region:
            base_query += " AND rdr.region = %s"
            params.append(region)
        if route_id:
            base_query += " AND rdr.route_id = %s"
            params.append(route_id)
        if stop_id:
            base_query += " AND rdr.stop_id = %s"
            params.append(stop_id)

        base_query += " ORDER BY rdr.record_timestamp DESC LIMIT %s"
        params.append(limit)

        delays = execute_query(base_query, params)
        return jsonify(success_response(delays))
    except Exception as e:
        return jsonify(error_response(f"查询失败: {str(e)}", 500)), 500


@app.route('/api/realtime/summary', methods=['GET'])
def get_realtime_summary():
    """获取实时数据汇总"""
    try:
        region = request.args.get('region')
        region_clause = ""
        params = []
        if region:
            region_clause = " AND region = %s"
            params = [region]

        summary = {
            "active_vehicles": execute_count(f"""
                SELECT COUNT(DISTINCT vehicle_id)
                FROM realtime_vehicle_positions
                WHERE position_timestamp >= NOW() - INTERVAL '10 minutes'
                {region_clause}
            """, tuple(params) if params else None),
            "recent_delays": execute_count(f"""
                SELECT COUNT(*)
                FROM realtime_delay_records
                WHERE record_timestamp >= NOW() - INTERVAL '1 hour'
                {region_clause}
            """, tuple(params) if params else None),
            "routes_with_delays": execute_count(f"""
                SELECT COUNT(DISTINCT route_id)
                FROM realtime_delay_records
                WHERE record_timestamp >= NOW() - INTERVAL '1 hour'
                {region_clause}
            """, tuple(params) if params else None),
            "avg_delay_minutes": execute_query_one(f"""
                SELECT COALESCE(AVG(ABS(arrival_delay)) / 60, 0) as avg_delay
                FROM realtime_delay_records
                WHERE record_timestamp >= NOW() - INTERVAL '1 hour'
                {region_clause}
            """, tuple(params) if params else None)['avg_delay']
        }
        return jsonify(success_response(summary))
    except Exception as e:
        return jsonify(error_response(f"查询失败: {str(e)}", 500)), 500


@app.route('/api/punctuality/routes', methods=['GET'])
def get_route_punctuality():
    """获取线路准点率统计"""
    try:
        route_id = request.args.get('route_id')
        date = request.args.get('date')
        region = request.args.get('region')
        start_date = request.args.get('startDate')
        end_date = request.args.get('endDate')
        days = min(int(request.args.get('days', 7)), 90)
        limit = min(int(request.args.get('limit', 20)), 100)

        if route_id:
            query = """
                SELECT
                    rdp.region, rdp.route_id, r.route_short_name, r.route_long_name,
                    rdp.stat_date, rdp.total_trips, rdp.punctuality_rate,
                    rdp.avg_arrival_delay / 60 as avg_delay_minutes,
                    rdp.on_time_trips, rdp.late_trips, rdp.very_late_trips
                FROM route_daily_punctuality rdp
                JOIN routes r ON rdp.region = r.region AND rdp.route_id = r.route_id
                WHERE rdp.route_id = %s
            """
            params = [route_id]

            if region:
                query += " AND rdp.region = %s"
                params.append(region)

            if date:
                query += " AND rdp.stat_date = %s"
                params.append(date)
            elif start_date and end_date:
                query += " AND rdp.stat_date >= %s AND rdp.stat_date <= %s"
                params.extend([start_date, end_date])
            else:
                query += " AND rdp.stat_date >= CURRENT_DATE - INTERVAL '%s days'" % days

            query += " ORDER BY rdp.stat_date DESC"
            results = execute_query(query, params)
        else:
            # 构建日期过滤条件
            date_clause = ""
            params = []
            if start_date and end_date:
                date_clause = "rdp.stat_date >= %s AND rdp.stat_date <= %s"
                params.extend([start_date, end_date])
            else:
                date_clause = "rdp.stat_date >= CURRENT_DATE - INTERVAL '%s days'" % days

            region_clause = ""
            if region:
                region_clause = " AND rdp.region = %s"
                params.append(region)

            query = """
                SELECT
                    rdp.route_id, r.route_short_name, r.route_long_name,
                    AVG(rdp.punctuality_rate) as avg_punctuality_rate,
                    SUM(rdp.total_trips) as total_trips,
                    AVG(rdp.avg_arrival_delay) / 60 as avg_delay_minutes,
                    MAX(rdp.max_arrival_delay) / 60 as max_delay_minutes,
                    SUM(rdp.on_time_trips) as on_time_trips,
                    SUM(rdp.early_trips) as early_trips,
                    SUM(rdp.late_trips) as late_trips,
                    SUM(rdp.very_late_trips) as very_late_trips,
                    MAX(rdp.stat_date) as last_stat_date
                FROM route_daily_punctuality rdp
                JOIN routes r ON rdp.region = r.region AND rdp.route_id = r.route_id
                WHERE %s
                %s
            """ % (date_clause, region_clause)
            query += " GROUP BY rdp.route_id, r.route_short_name, r.route_long_name"
            query += " ORDER BY avg_punctuality_rate DESC LIMIT %s"
            params.append(limit)
            results = execute_query(query, params)

        return jsonify(success_response(results))
    except Exception as e:
        return jsonify(error_response(f"查询失败: {str(e)}", 500)), 500


@app.route('/api/punctuality/stops', methods=['GET'])
def get_stop_punctuality():
    """获取站点准点率统计"""
    try:
        stop_id = request.args.get('stop_id')
        date = request.args.get('date')
        region = request.args.get('region')
        days = min(int(request.args.get('days', 7)), 90)
        limit = min(int(request.args.get('limit', 20)), 100)

        if stop_id:
            query = """
                SELECT
                    sdp.region, sdp.stop_id, s.stop_name, s.stop_lat, s.stop_lon,
                    sdp.stat_date, sdp.total_visits, sdp.punctuality_rate,
                    sdp.avg_arrival_delay / 60 as avg_delay_minutes
                FROM stop_daily_punctuality sdp
                JOIN stops s ON sdp.region = s.region AND sdp.stop_id = s.stop_id
                WHERE sdp.stop_id = %s
            """
            params = [stop_id]

            if region:
                query += " AND sdp.region = %s"
                params.append(region)

            if date:
                query += " AND sdp.stat_date = %s"
                params.append(date)
            else:
                query += " AND sdp.stat_date >= CURRENT_DATE - INTERVAL '%s days'" % days

            query += " ORDER BY sdp.stat_date DESC"
            results = execute_query(query, params)
        else:
            region_clause = ""
            params = []
            if region:
                region_clause = " AND sdp.region = %s"
                params.append(region)

            query = """
                SELECT
                    sdp.stop_id, s.stop_name, s.stop_lat, s.stop_lon,
                    AVG(sdp.punctuality_rate) as avg_punctuality_rate,
                    SUM(sdp.total_visits) as total_visits,
                    AVG(sdp.avg_arrival_delay) / 60 as avg_delay_minutes,
                    MAX(sdp.max_arrival_delay) / 60 as max_delay_minutes,
                    SUM(sdp.on_time_visits) as on_time_visits,
                    SUM(sdp.early_visits) as early_visits,
                    SUM(sdp.late_visits) as late_visits,
                    SUM(sdp.very_late_visits) as very_late_visits,
                    MAX(sdp.stat_date) as last_stat_date
                FROM stop_daily_punctuality sdp
                JOIN stops s ON sdp.region = s.region AND sdp.stop_id = s.stop_id
                WHERE sdp.stat_date >= CURRENT_DATE - INTERVAL '%s days'
                %s
            """ % (days, region_clause)
            query += " GROUP BY sdp.stop_id, s.stop_name, s.stop_lat, s.stop_lon"
            query += " ORDER BY avg_punctuality_rate DESC LIMIT %s"
            params.append(limit)
            results = execute_query(query, params)

        return jsonify(success_response(results))
    except Exception as e:
        return jsonify(error_response(f"查询失败: {str(e)}", 500)), 500


@app.route('/api/punctuality/overview', methods=['GET'])
def get_system_punctuality_overview():
    """获取系统准点率概览"""
    try:
        days = min(int(request.args.get('days', 7)), 90)
        region = request.args.get('region')

        region_clause = ""
        region_params = []
        if region:
            region_clause = " AND rdp.region = %s"
            region_params = [region]

        query = """
            SELECT
                COUNT(DISTINCT rdp.route_id) as total_routes,
                SUM(rdp.total_trips) as total_trips,
                AVG(rdp.punctuality_rate) as system_punctuality_rate,
                AVG(ABS(rdp.avg_arrival_delay)) / 60 as system_avg_delay_minutes,
                MAX(rdp.stat_date) as latest_data_date
            FROM route_daily_punctuality rdp
            WHERE rdp.stat_date >= CURRENT_DATE - INTERVAL '%s days'
            %s
        """ % (days, region_clause)

        system_stats = execute_query_one(query, tuple(region_params) if region_params else None)

        if not system_stats or system_stats['total_routes'] == 0:
            overview = {
                "total_routes": 0,
                "total_trips": 0,
                "system_punctuality_rate": 0,
                "system_avg_delay_minutes": 0,
                "latest_data_date": None,
                "best_routes": [],
                "worst_routes": [],
                "analysis_period": f"最近 {days} 天",
                "data_available": False
            }
            return jsonify(success_response(overview))

        best_routes_query = """
            SELECT
                rdp.route_id, r.route_short_name, r.route_long_name,
                AVG(rdp.punctuality_rate) as avg_punctuality_rate,
                SUM(rdp.total_trips) as total_trips
            FROM route_daily_punctuality rdp
            JOIN routes r ON rdp.region = r.region AND rdp.route_id = r.route_id
            WHERE rdp.stat_date >= CURRENT_DATE - INTERVAL '%s days'
            %s
            GROUP BY rdp.route_id, r.route_short_name, r.route_long_name
            ORDER BY avg_punctuality_rate DESC
            LIMIT 5
        """ % (days, region_clause)

        worst_routes_query = """
            SELECT
                rdp.route_id, r.route_short_name, r.route_long_name,
                AVG(rdp.punctuality_rate) as avg_punctuality_rate,
                SUM(rdp.total_trips) as total_trips
            FROM route_daily_punctuality rdp
            JOIN routes r ON rdp.region = r.region AND rdp.route_id = r.route_id
            WHERE rdp.stat_date >= CURRENT_DATE - INTERVAL '%s days'
            AND rdp.total_trips >= 10
            %s
            GROUP BY rdp.route_id, r.route_short_name, r.route_long_name
            ORDER BY avg_punctuality_rate ASC
            LIMIT 5
        """ % (days, region_clause)

        best_routes = execute_query(best_routes_query, tuple(region_params) if region_params else None)
        worst_routes = execute_query(worst_routes_query, tuple(region_params) if region_params else None)

        overview = {
            "total_routes": system_stats['total_routes'],
            "total_trips": system_stats['total_trips'],
            "system_punctuality_rate": round(float(system_stats['system_punctuality_rate'] or 0), 2),
            "system_avg_delay_minutes": round(float(system_stats['system_avg_delay_minutes'] or 0), 2),
            "latest_data_date": system_stats['latest_data_date'].strftime('%Y-%m-%d') if system_stats['latest_data_date'] else None,
            "best_routes": best_routes,
            "worst_routes": worst_routes,
            "analysis_period": f"最近 {days} 天",
            "data_available": True
        }

        return jsonify(success_response(overview))
    except Exception as e:
        return jsonify(error_response(f"查询失败: {str(e)}", 500)), 500


@app.route('/api/punctuality/hourly', methods=['GET'])
def get_hourly_punctuality():
    """获取时段准点率统计"""
    try:
        route_id = request.args.get('route_id')
        date = request.args.get('date')
        region = request.args.get('region')

        if not date:
            date = 'CURRENT_DATE'

        query = """
            SELECT
                hour_of_day,
                AVG(punctuality_rate) as avg_punctuality_rate,
                SUM(total_trips) as total_trips,
                AVG(avg_arrival_delay) / 60 as avg_delay_minutes
            FROM hourly_punctuality_stats
            WHERE stat_date = %s
        """ % ('CURRENT_DATE' if date == 'CURRENT_DATE' else f"'{date}'")

        params = []
        if region:
            query += " AND region = %s"
            params.append(region)
        if route_id:
            query += " AND route_id = %s"
            params.append(route_id)

        query += " GROUP BY hour_of_day ORDER BY hour_of_day"

        hourly_stats = execute_query(query, params)

        # 确保返回24小时的数据
        result = []
        hour_data = {stat['hour_of_day']: stat for stat in hourly_stats}

        for hour in range(24):
            if hour in hour_data:
                result.append({
                    'hour': hour,
                    'hour_label': f"{hour:02d}:00",
                    'punctuality_rate': round(float(hour_data[hour]['avg_punctuality_rate'] or 0), 2),
                    'total_trips': hour_data[hour]['total_trips'],
                    'avg_delay_minutes': round(float(hour_data[hour]['avg_delay_minutes'] or 0), 2)
                })
            else:
                result.append({
                    'hour': hour,
                    'hour_label': f"{hour:02d}:00",
                    'punctuality_rate': 0,
                    'total_trips': 0,
                    'avg_delay_minutes': 0
                })

        return jsonify(success_response(result))
    except Exception as e:
        return jsonify(error_response(f"查询失败: {str(e)}", 500)), 500


@app.route('/api/punctuality/config', methods=['GET', 'PUT'])
def punctuality_config():
    """获取或更新准点率配置"""
    try:
        if request.method == 'GET':
            # 获取配置
            query = "SELECT config_key, config_value, description FROM punctuality_config ORDER BY config_key"
            configs = execute_query(query)

            # 转换为字典格式
            config_dict = {}
            for config in configs:
                # 尝试转换为数值类型
                try:
                    if '.' in config['config_value']:
                        config_dict[config['config_key']] = float(config['config_value'])
                    else:
                        config_dict[config['config_key']] = int(config['config_value'])
                except ValueError:
                    config_dict[config['config_key']] = config['config_value']

            return jsonify(success_response(config_dict))

        else:  # PUT
            # 更新配置
            configs = request.get_json()
            if not configs:
                return jsonify(error_response("配置数据不能为空", 400)), 400

            for key, value in configs:
                query = """
                    UPDATE punctuality_config
                    SET config_value = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE config_key = %s
                """
                execute_query(query, (str(value), key))

            return jsonify(success_response({"message": "配置更新成功"}))

    except Exception as e:
        return jsonify(error_response(f"操作失败: {str(e)}", 500)), 500


@app.route('/api/punctuality/collect', methods=['POST'])
def trigger_punctuality_collection():
    """触发一次实时准点率数据收集"""
    import time
    region = request.args.get('region', 'sf')

    # 从环境变量读取 API Keys
    api_keys = {
        'sf':     os.getenv('SF_511_API_KEY', ''),
        'nyc':    os.getenv('MTA_API_KEY', ''),
        'sydney': os.getenv('TFNSW_API_KEY', ''),
    }
    api_key = api_keys.get(region, '')

    if not api_key:
        return jsonify(error_response(
            f"未设置 {region.upper()} 的 API Key 环境变量（SF_511_API_KEY / MTA_API_KEY / TFNSW_API_KEY）",
            400
        )), 400

    try:
        # 动态导入，避免循环依赖
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from services.punctuality_service import PunctualityDataService

        start_time = time.time()
        service = PunctualityDataService(api_key=api_key, region=region)
        records = service.collect_realtime_data()
        duration = round(time.time() - start_time, 2)

        return jsonify(success_response({
            "region": region,
            "records_collected": records if isinstance(records, int) else 0,
            "duration_seconds": duration
        }))
    except Exception as e:
        return jsonify(error_response(f"数据收集失败: {str(e)}", 500)), 500


# ==================== 收藏相关接口 ====================

def _get_current_user():
    """从请求头提取当前登录用户信息，未登录返回 None"""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None
    token = auth_header[7:]
    return verify_token(token)


def _require_admin():
    """校验当前用户是否为管理员，返回 (user, error_response)"""
    user = _get_current_user()
    if not user:
        return None, (jsonify(error_response("请先登录", 401)), 401)
    if user.get('role') != 'admin':
        return None, (jsonify(error_response("权限不足，仅管理员可访问", 403)), 403)
    return user, None


@app.route('/api/favorites', methods=['GET'])
def get_favorites():
    """获取当前用户的所有收藏"""
    user = _get_current_user()
    if not user:
        return jsonify(error_response("请先登录", 401)), 401
    rows = execute_query(
        "SELECT id, region, item_type, item_id, item_name, created_at FROM user_favorites WHERE user_id = %s ORDER BY created_at DESC",
        (user['user_id'],)
    )
    return jsonify(success_response(rows))


@app.route('/api/favorites', methods=['POST'])
def add_favorite():
    """添加收藏"""
    user = _get_current_user()
    if not user:
        return jsonify(error_response("请先登录", 401)), 401
    data = request.get_json() or {}
    region = data.get('region', '').strip()
    item_type = data.get('item_type', '').strip()
    item_id = data.get('item_id', '').strip()
    item_name = data.get('item_name', '').strip()
    if not region or not item_type or not item_id:
        return jsonify(error_response("缺少必要参数", 400)), 400
    if item_type not in ('route', 'stop'):
        return jsonify(error_response("item_type 必须为 route 或 stop", 400)), 400
    try:
        row = execute_write(
            """INSERT INTO user_favorites (user_id, region, item_type, item_id, item_name)
               VALUES (%s, %s, %s, %s, %s)
               ON CONFLICT (user_id, region, item_type, item_id) DO NOTHING
               RETURNING id""",
            (user['user_id'], region, item_type, item_id, item_name)
        )
        return jsonify(success_response({"id": row['id'] if row else None, "message": "收藏成功"}))
    except Exception as e:
        return jsonify(error_response(f"收藏失败: {str(e)}", 500)), 500


@app.route('/api/favorites', methods=['DELETE'])
def remove_favorite():
    """取消收藏"""
    user = _get_current_user()
    if not user:
        return jsonify(error_response("请先登录", 401)), 401
    region = request.args.get('region', '').strip()
    item_type = request.args.get('item_type', '').strip()
    item_id = request.args.get('item_id', '').strip()
    if not region or not item_type or not item_id:
        return jsonify(error_response("缺少必要参数", 400)), 400
    execute_write(
        "DELETE FROM user_favorites WHERE user_id = %s AND region = %s AND item_type = %s AND item_id = %s",
        (user['user_id'], region, item_type, item_id)
    )
    return jsonify(success_response({"message": "已取消收藏"}))


# ==================== 运维监控接口 ====================

import time as _time

# 数据库统计缓存（15分钟有效期）
_db_stats_cache: Dict[str, Any] = {}
_DB_STATS_CACHE_TTL = 900  # 15分钟


@app.route('/api/admin/db-stats', methods=['GET'])
def admin_db_stats():
    """获取数据库各表存储统计（带15分钟缓存）"""
    user, err = _require_admin()
    if err:
        return err

    now = _time.time()
    if _db_stats_cache.get('data') and now - _db_stats_cache.get('ts', 0) < _DB_STATS_CACHE_TTL:
        return jsonify(success_response(_db_stats_cache['data']))

    try:
        # 各表物理大小和行数（优先用统计信息，小表用精确 COUNT）
        table_stats = execute_query("""
            SELECT
                t.relname AS table_name,
                pg_total_relation_size(t.oid) AS total_bytes,
                pg_size_pretty(pg_total_relation_size(t.oid)) AS total_size,
                GREATEST(COALESCE(s.n_live_tup, 0), GREATEST(t.reltuples::bigint, 0)) AS row_estimate
            FROM pg_class t
            JOIN pg_namespace n ON n.oid = t.relnamespace
            LEFT JOIN pg_stat_user_tables s ON s.relname = t.relname
            WHERE n.nspname = 'public' AND t.relkind = 'r'
            ORDER BY total_bytes DESC
            LIMIT 20
        """)

        # 数据库总大小
        db_size = execute_query_one("SELECT pg_size_pretty(pg_database_size(current_database())) AS db_size, pg_database_size(current_database()) AS db_bytes")

        # 连接数
        conn_info = execute_query_one("SELECT count(*) AS active_connections FROM pg_stat_activity WHERE state = 'active'")

        result = {
            'db_size': db_size['db_size'] if db_size else 'N/A',
            'db_bytes': db_size['db_bytes'] if db_size else 0,
            'active_connections': conn_info['active_connections'] if conn_info else 0,
            'tables': [dict(r) for r in table_stats]
        }
        _db_stats_cache['data'] = result
        _db_stats_cache['ts'] = now
        return jsonify(success_response(result))
    except Exception as e:
        return jsonify(error_response(f"获取数据库统计失败: {str(e)}", 500)), 500


@app.route('/api/admin/api-health', methods=['GET'])
def admin_api_health():
    """获取过去24小时第三方 API 调用健康度统计"""
    user, err = _require_admin()
    if err:
        return err

    try:
        # 各 region+api_name 的调用统计
        stats = execute_query("""
            SELECT
                region,
                api_name,
                COUNT(*) AS total_calls,
                ROUND(AVG(latency_ms)) AS avg_latency_ms,
                SUM(CASE WHEN status_code >= 200 AND status_code < 300 THEN 1 ELSE 0 END) AS success_count,
                SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) AS error_count,
                MAX(latency_ms) AS max_latency_ms,
                MIN(latency_ms) AS min_latency_ms
            FROM api_call_logs
            WHERE created_at >= NOW() - INTERVAL '24 hours'
            GROUP BY region, api_name
            ORDER BY region, api_name
        """)

        # 最近10条错误记录
        recent_errors = execute_query("""
            SELECT region, api_name, endpoint, status_code, error_msg, created_at
            FROM api_call_logs
            WHERE status_code >= 400 AND created_at >= NOW() - INTERVAL '24 hours'
            ORDER BY created_at DESC
            LIMIT 10
        """)

        # 总调用次数
        total = execute_query_one("SELECT COUNT(*) AS cnt FROM api_call_logs WHERE created_at >= NOW() - INTERVAL '24 hours'")
        error_total = execute_query_one("SELECT COUNT(*) AS cnt FROM api_call_logs WHERE status_code >= 400 AND created_at >= NOW() - INTERVAL '24 hours'")

        result = {
            'total_calls_24h': total['cnt'] if total else 0,
            'error_calls_24h': error_total['cnt'] if error_total else 0,
            'stats': [dict(r) for r in stats],
            'recent_errors': [dict(r) for r in recent_errors]
        }
        return jsonify(success_response(result))
    except Exception as e:
        return jsonify(error_response(f"获取API健康度失败: {str(e)}", 500)), 500


@app.route('/api/admin/data-freshness', methods=['GET'])
def admin_data_freshness():
    """获取各地区 GTFS 数据时效性信息"""
    user, err = _require_admin()
    if err:
        return err

    try:
        regions = ['sf', 'nyc', 'sydney']
        freshness = []
        for region in regions:
            # 各地区主表记录数
            routes_count = execute_query_one("SELECT COUNT(*) AS cnt FROM routes WHERE region = %s", (region,))
            stops_count = execute_query_one("SELECT COUNT(*) AS cnt FROM stops WHERE region = %s", (region,))
            trips_count = execute_query_one("SELECT COUNT(*) AS cnt FROM trips WHERE region = %s", (region,))

            # 最新导入记录
            last_import = execute_query_one(
                "SELECT file_version, records_imported, duration_ms, status, created_at FROM data_update_logs WHERE region = %s ORDER BY created_at DESC LIMIT 1",
                (region,)
            )

            freshness.append({
                'region': region,
                'routes_count': routes_count['cnt'] if routes_count else 0,
                'stops_count': stops_count['cnt'] if stops_count else 0,
                'trips_count': trips_count['cnt'] if trips_count else 0,
                'last_import': dict(last_import) if last_import else None
            })

        return jsonify(success_response(freshness))
    except Exception as e:
        return jsonify(error_response(f"获取数据时效性失败: {str(e)}", 500)), 500


@app.route('/api/admin/log-api-call', methods=['POST'])
def admin_log_api_call():
    """记录一次第三方 API 调用日志（内部接口）"""
    user, err = _require_admin()
    if err:
        return err

    data = request.get_json() or {}
    region = data.get('region', '').strip()
    api_name = data.get('api_name', '').strip()
    endpoint = data.get('endpoint', '').strip()
    latency_ms = data.get('latency_ms', 0)
    status_code = data.get('status_code', 0)
    error_msg = data.get('error_msg', None)

    if not region or not api_name or not endpoint:
        return jsonify(error_response("缺少必要参数", 400)), 400

    try:
        execute_write(
            "INSERT INTO api_call_logs (region, api_name, endpoint, latency_ms, status_code, error_msg) VALUES (%s, %s, %s, %s, %s, %s)",
            (region, api_name, endpoint, int(latency_ms), int(status_code), error_msg)
        )
        return jsonify(success_response({"message": "记录成功"}))
    except Exception as e:
        return jsonify(error_response(f"记录失败: {str(e)}", 500)), 500


# ==================== 用户管理接口（仅管理员）====================

from auth.models import create_user as _create_user, hash_password as _hash_password, get_user_by_username as _get_user_by_username


@app.route('/api/users', methods=['GET'])
def list_users():
    """获取所有用户列表"""
    _, err = _require_admin()
    if err:
        return err
    try:
        users = execute_query(
            "SELECT id, username, role, is_active, created_at FROM users ORDER BY id"
        )
        return jsonify(success_response([dict(u) for u in users]))
    except Exception as e:
        return jsonify(error_response(f"获取用户列表失败: {str(e)}", 500)), 500


@app.route('/api/users', methods=['POST'])
def create_user_api():
    """创建新普通用户"""
    _, err = _require_admin()
    if err:
        return err
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')
    if not username or not password:
        return jsonify(error_response("用户名和密码不能为空", 400)), 400
    if not (4 <= len(username) <= 20):
        return jsonify(error_response("用户名长度须在 4-20 个字符之间", 400)), 400
    if len(password) < 6:
        return jsonify(error_response("密码长度不能少于 6 位", 400)), 400
    if _get_user_by_username(username):
        return jsonify(error_response("用户名已存在", 409)), 409
    try:
        new_id = _create_user(username, password, role='user')
        return jsonify(success_response({"id": new_id, "username": username, "role": "user"}))
    except Exception as e:
        return jsonify(error_response(f"创建用户失败: {str(e)}", 500)), 500


@app.route('/api/users/<int:user_id>', methods=['PATCH'])
def update_user_api(user_id: int):
    """更新用户状态（启用/停用）"""
    admin_user, err = _require_admin()
    if err:
        return err
    if admin_user['user_id'] == user_id:
        return jsonify(error_response("不能修改自己的状态", 400)), 400
    data = request.get_json() or {}
    is_active = data.get('is_active')
    if is_active is None:
        return jsonify(error_response("缺少 is_active 参数", 400)), 400
    try:
        execute_write(
            "UPDATE users SET is_active = %s WHERE id = %s",
            (bool(is_active), user_id)
        )
        return jsonify(success_response({"message": "更新成功"}))
    except Exception as e:
        return jsonify(error_response(f"更新失败: {str(e)}", 500)), 500


@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user_api(user_id: int):
    """删除用户（不能删除自己）"""
    admin_user, err = _require_admin()
    if err:
        return err
    if admin_user['user_id'] == user_id:
        return jsonify(error_response("不能删除自己", 400)), 400
    try:
        execute_write("DELETE FROM users WHERE id = %s", (user_id,))
        return jsonify(success_response({"message": "删除成功"}))
    except Exception as e:
        return jsonify(error_response(f"删除失败: {str(e)}", 500)), 500


@app.route('/api/users/<int:user_id>/password', methods=['GET'])
def get_user_password(user_id: int):
    """查看用户密码（管理员专用，返回明文密码哈希前缀用于展示，实际返回重置后的临时密码）"""
    _, err = _require_admin()
    if err:
        return err
    try:
        user = execute_query_one("SELECT id, username, role FROM users WHERE id = %s", (user_id,))
        if not user:
            return jsonify(error_response("用户不存在", 404)), 404
        if user['role'] == 'admin':
            return jsonify(error_response("不能查看管理员密码", 403)), 403
        # 生成临时密码并更新
        import secrets as _secrets
        temp_password = _secrets.token_urlsafe(8)
        from auth.models import hash_password as _hp
        execute_write("UPDATE users SET password_hash = %s WHERE id = %s", (_hp(temp_password), user_id))
        return jsonify(success_response({"temp_password": temp_password, "username": user['username']}))
    except Exception as e:
        return jsonify(error_response(f"操作失败: {str(e)}", 500)), 500


@app.route('/api/users/<int:user_id>/password', methods=['PUT'])
def update_user_password(user_id: int):
    """修改用户密码（管理员专用）"""
    _, err = _require_admin()
    if err:
        return err
    data = request.get_json() or {}
    new_password = data.get('password', '')
    if len(new_password) < 6:
        return jsonify(error_response("密码长度不能少于 6 位", 400)), 400
    try:
        user = execute_query_one("SELECT id, role FROM users WHERE id = %s", (user_id,))
        if not user:
            return jsonify(error_response("用户不存在", 404)), 404
        if user['role'] == 'admin':
            return jsonify(error_response("不能修改管理员密码", 403)), 403
        from auth.models import hash_password as _hp
        execute_write("UPDATE users SET password_hash = %s WHERE id = %s", (_hp(new_password), user_id))
        return jsonify(success_response({"message": "密码修改成功"}))
    except Exception as e:
        return jsonify(error_response(f"修改失败: {str(e)}", 500)), 500


@app.errorhandler(404)
def not_found(error):
    """404 错误处理"""
    return jsonify(error_response("接口不存在", 404)), 404


@app.errorhandler(500)
def internal_error(error):
    """500 错误处理"""
    return jsonify(error_response("服务器内部错误", 500)), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'True').lower() == 'true'

    print(f"启动 GTFS API 服务...")
    print(f"端口: {port}")
    print(f"调试模式: {debug}")
    print(f"API 文档: http://localhost:{port}/api/health")

    app.run(host='0.0.0.0', port=port, debug=debug)
