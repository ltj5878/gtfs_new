#!/usr/bin/env python3
"""
GTFS 数据 RESTful API 服务
提供查询 PostgreSQL 中 GTFS 数据的 HTTP 接口
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from db import Database, execute_query, execute_query_one, execute_count
from typing import Dict, Any
import os

app = Flask(__name__)
CORS(app)


@app.before_request
def before_first_request():
    """初始化数据库连接池"""
    if Database._connection_pool is None:
        Database.initialize()


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


@app.route('/api/agencies', methods=['GET'])
def get_agencies():
    """获取所有运营机构"""
    try:
        query = """
            SELECT agency_id, agency_name, agency_url, agency_timezone,
                   agency_lang, agency_phone, agency_fare_url, agency_email
            FROM agency
            ORDER BY agency_name
        """
        agencies = execute_query(query)
        return jsonify(success_response(agencies))
    except Exception as e:
        return jsonify(error_response(f"查询失败: {str(e)}", 500)), 500


@app.route('/api/agencies/<agency_id>', methods=['GET'])
def get_agency(agency_id):
    """获取指定运营机构详情"""
    try:
        query = """
            SELECT agency_id, agency_name, agency_url, agency_timezone,
                   agency_lang, agency_phone, agency_fare_url, agency_email
            FROM agency
            WHERE agency_id = %s
        """
        agency = execute_query_one(query, (agency_id,))
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

        offset = (page - 1) * page_size

        where_clauses = []
        params = []

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
            SELECT r.route_id, r.agency_id, r.route_short_name, r.route_long_name,
                   r.route_desc, r.route_type, r.route_url, r.route_color, r.route_text_color,
                   ra.category, ra.subcategory, ra.running_way
            FROM routes r
            LEFT JOIN route_attributes ra ON r.route_id = ra.route_id
            WHERE {where_sql}
            ORDER BY r.route_short_name, r.route_long_name
            LIMIT %s OFFSET %s
        """
        params.extend([page_size, offset])

        routes = execute_query(query, tuple(params))

        return jsonify(success_response({
            "routes": routes,
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
        query = """
            SELECT r.route_id, r.agency_id, r.route_short_name, r.route_long_name,
                   r.route_desc, r.route_type, r.route_url, r.route_color, r.route_text_color,
                   ra.category, ra.subcategory, ra.running_way
            FROM routes r
            LEFT JOIN route_attributes ra ON r.route_id = ra.route_id
            WHERE r.route_id = %s
        """
        route = execute_query_one(query, (route_id,))
        if route:
            return jsonify(success_response(route))
        return jsonify(error_response("线路不存在", 404)), 404
    except Exception as e:
        return jsonify(error_response(f"查询失败: {str(e)}", 500)), 500


@app.route('/api/routes/<route_id>/directions', methods=['GET'])
def get_route_directions(route_id):
    """获取线路的所有方向"""
    try:
        query = """
            SELECT route_id, direction_id, direction
            FROM directions
            WHERE route_id = %s
            ORDER BY direction_id
        """
        directions = execute_query(query, (route_id,))
        return jsonify(success_response(directions))
    except Exception as e:
        return jsonify(error_response(f"查询失败: {str(e)}", 500)), 500


@app.route('/api/routes/<route_id>/stops', methods=['GET'])
def get_route_stops(route_id):
    """获取线路的所有站点"""
    try:
        direction_id = request.args.get('direction_id', type=int)

        where_clause = "r.route_id = %s"
        params = [route_id]

        if direction_id is not None:
            where_clause += " AND t.direction_id = %s"
            params.append(direction_id)

        query = f"""
            SELECT DISTINCT s.stop_id, s.stop_code, s.stop_name,
                   s.stop_lat, s.stop_lon, s.stop_desc,
                   MIN(st.stop_sequence) as min_sequence
            FROM stops s
            JOIN stop_times st ON s.stop_id = st.stop_id
            JOIN trips t ON st.trip_id = t.trip_id
            JOIN routes r ON t.route_id = r.route_id
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

        offset = (page - 1) * page_size

        where_clauses = []
        params = []

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
            SELECT stop_id, stop_code, stop_name, stop_lat, stop_lon,
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
        query = """
            SELECT stop_id, stop_code, stop_name, stop_lat, stop_lon,
                   zone_id, stop_desc, stop_url, location_type,
                   parent_station, stop_timezone, wheelchair_boarding, platform_code
            FROM stops
            WHERE stop_id = %s
        """
        stop = execute_query_one(query, (stop_id,))
        if stop:
            return jsonify(success_response(stop))
        return jsonify(error_response("站点不存在", 404)), 404
    except Exception as e:
        return jsonify(error_response(f"查询失败: {str(e)}", 500)), 500


@app.route('/api/stops/<stop_id>/routes', methods=['GET'])
def get_stop_routes(stop_id):
    """获取经过指定站点的所有线路"""
    try:
        query = """
            SELECT DISTINCT r.route_id, r.route_short_name, r.route_long_name,
                   r.route_type, r.route_color, r.route_text_color
            FROM routes r
            JOIN trips t ON r.route_id = t.route_id
            JOIN stop_times st ON t.trip_id = st.trip_id
            WHERE st.stop_id = %s
            ORDER BY r.route_short_name, r.route_long_name
        """
        routes = execute_query(query, (stop_id,))
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
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)

        offset = (page - 1) * page_size

        where_clauses = []
        params = []

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
            SELECT trip_id, route_id, service_id, trip_headsign,
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
        query = """
            SELECT trip_id, route_id, service_id, trip_headsign,
                   trip_short_name, direction_id, block_id, shape_id,
                   wheelchair_accessible, bikes_allowed
            FROM trips
            WHERE trip_id = %s
        """
        trip = execute_query_one(query, (trip_id,))
        if trip:
            return jsonify(success_response(trip))
        return jsonify(error_response("班次不存在", 404)), 404
    except Exception as e:
        return jsonify(error_response(f"查询失败: {str(e)}", 500)), 500


@app.route('/api/trips/<trip_id>/stop_times', methods=['GET'])
def get_trip_stop_times(trip_id):
    """获取班次的所有站点时刻表"""
    try:
        query = """
            SELECT st.trip_id, st.arrival_time, st.departure_time,
                   st.stop_id, st.stop_sequence, st.stop_headsign,
                   st.pickup_type, st.drop_off_type, st.shape_dist_traveled,
                   s.stop_name, s.stop_lat, s.stop_lon
            FROM stop_times st
            JOIN stops s ON st.stop_id = s.stop_id
            WHERE st.trip_id = %s
            ORDER BY st.stop_sequence
        """
        stop_times = execute_query(query, (trip_id,))
        return jsonify(success_response(stop_times))
    except Exception as e:
        return jsonify(error_response(f"查询失败: {str(e)}", 500)), 500


@app.route('/api/routes/<route_id>/shapes', methods=['GET'])
def get_route_shapes(route_id):
    """获取指定线路的所有轨迹"""
    try:
        direction_id = request.args.get('direction_id', type=int)

        # 根据trips表获取该线路的所有shape_id
        query = """
            SELECT DISTINCT t.shape_id, d.direction_id
            FROM trips t
            LEFT JOIN directions d ON t.route_id = d.route_id AND t.direction_id = d.direction_id
            WHERE t.route_id = %s
        """
        params = [route_id]

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
                ORDER BY shape_pt_sequence
            """
            shape_points = execute_query(shape_query, (shape_id,))

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
        query = """
            SELECT shape_id, shape_pt_lat, shape_pt_lon,
                   shape_pt_sequence, shape_dist_traveled
            FROM shapes
            WHERE shape_id = %s
            ORDER BY shape_pt_sequence
        """
        shape_points = execute_query(query, (shape_id,))
        if shape_points:
            return jsonify(success_response(shape_points))
        return jsonify(error_response("轨迹不存在", 404)), 404
    except Exception as e:
        return jsonify(error_response(f"查询失败: {str(e)}", 500)), 500


@app.route('/api/calendar', methods=['GET'])
def get_calendar():
    """获取服务日历"""
    try:
        query = """
            SELECT c.service_id, c.monday, c.tuesday, c.wednesday,
                   c.thursday, c.friday, c.saturday, c.sunday,
                   c.start_date, c.end_date, ca.service_description
            FROM calendar c
            LEFT JOIN calendar_attributes ca ON c.service_id = ca.service_id
            ORDER BY c.service_id
        """
        calendar = execute_query(query)
        return jsonify(success_response(calendar))
    except Exception as e:
        return jsonify(error_response(f"查询失败: {str(e)}", 500)), 500


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """获取数据统计信息"""
    try:
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
        # 获取查询参数
        route_id = request.args.get('route_id')
        limit = min(int(request.args.get('limit', 100)), 500)  # 最大500条

        # 构建查询语句
        base_query = """
            SELECT vehicle_id, trip_id, route_id, latitude, longitude,
                   bearing, speed, position_timestamp, current_status, stop_id
            FROM realtime_vehicle_positions
            WHERE position_timestamp >= NOW() - INTERVAL '10 minutes'
        """

        params = []
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
        # 获取查询参数
        route_id = request.args.get('route_id')
        stop_id = request.args.get('stop_id')
        hours = min(int(request.args.get('hours', 2)), 24)  # 最多24小时
        limit = min(int(request.args.get('limit', 200)), 1000)

        # 构建查询语句
        base_query = """
            SELECT rdr.trip_id, rdr.route_id, rdr.stop_id, rdr.vehicle_id,
                   rdr.scheduled_time, rdr.actual_time, rdr.arrival_delay,
                   rdr.departure_delay, rdr.record_timestamp,
                   r.route_short_name, r.route_long_name,
                   s.stop_name
            FROM realtime_delay_records rdr
            LEFT JOIN routes r ON rdr.route_id = r.route_id
            LEFT JOIN stops s ON rdr.stop_id = s.stop_id
            WHERE record_timestamp >= NOW() - INTERVAL '%s hours'
        """ % hours

        params = []
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
        summary = {
            "active_vehicles": execute_count("""
                SELECT COUNT(DISTINCT vehicle_id)
                FROM realtime_vehicle_positions
                WHERE position_timestamp >= NOW() - INTERVAL '10 minutes'
            """),
            "recent_delays": execute_count("""
                SELECT COUNT(*)
                FROM realtime_delay_records
                WHERE record_timestamp >= NOW() - INTERVAL '1 hour'
            """),
            "routes_with_delays": execute_count("""
                SELECT COUNT(DISTINCT route_id)
                FROM realtime_delay_records
                WHERE record_timestamp >= NOW() - INTERVAL '1 hour'
            """),
            "avg_delay_minutes": execute_query_one("""
                SELECT COALESCE(AVG(arrival_delay) / 60, 0) as avg_delay
                FROM realtime_delay_records
                WHERE record_timestamp >= NOW() - INTERVAL '1 hour'
            """)['avg_delay']
        }
        return jsonify(success_response(summary))
    except Exception as e:
        return jsonify(error_response(f"查询失败: {str(e)}", 500)), 500


@app.route('/api/punctuality/routes', methods=['GET'])
def get_route_punctuality():
    """获取线路准点率统计"""
    try:
        # 获取查询参数
        route_id = request.args.get('route_id')
        date = request.args.get('date')
        days = min(int(request.args.get('days', 7)), 90)  # 最多90天
        limit = min(int(request.args.get('limit', 20)), 100)

        # 构建查询语句
        if route_id:
            # 查询特定线路
            query = """
                SELECT
                    rdp.route_id, r.route_short_name, r.route_long_name,
                    rdp.stat_date, rdp.total_trips, rdp.punctuality_rate,
                    rdp.avg_arrival_delay / 60 as avg_delay_minutes,
                    rdp.on_time_trips, rdp.late_trips, rdp.very_late_trips
                FROM route_daily_punctuality rdp
                JOIN routes r ON rdp.route_id = r.route_id
                WHERE rdp.route_id = %s
            """
            params = [route_id]

            if date:
                query += " AND rdp.stat_date = %s"
                params.append(date)
            else:
                query += " AND rdp.stat_date >= CURRENT_DATE - INTERVAL '%s days'" % days

            query += " ORDER BY rdp.stat_date DESC"
            results = execute_query(query, params)
        else:
            # 查询所有线路的汇总
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
                JOIN routes r ON rdp.route_id = r.route_id
                WHERE rdp.stat_date >= CURRENT_DATE - INTERVAL '%s days'
            """ % days
            query += " GROUP BY rdp.route_id, r.route_short_name, r.route_long_name"
            query += " ORDER BY avg_punctuality_rate DESC LIMIT %s"
            params = [limit]
            results = execute_query(query, params)

        return jsonify(success_response(results))
    except Exception as e:
        return jsonify(error_response(f"查询失败: {str(e)}", 500)), 500


@app.route('/api/punctuality/stops', methods=['GET'])
def get_stop_punctuality():
    """获取站点准点率统计"""
    try:
        # 获取查询参数
        stop_id = request.args.get('stop_id')
        date = request.args.get('date')
        days = min(int(request.args.get('days', 7)), 90)
        limit = min(int(request.args.get('limit', 20)), 100)

        if stop_id:
            # 查询特定站点
            query = """
                SELECT
                    sdp.stop_id, s.stop_name, s.stop_lat, s.stop_lon,
                    sdp.stat_date, sdp.total_visits, sdp.punctuality_rate,
                    sdp.avg_arrival_delay / 60 as avg_delay_minutes
                FROM stop_daily_punctuality sdp
                JOIN stops s ON sdp.stop_id = s.stop_id
                WHERE sdp.stop_id = %s
            """
            params = [stop_id]

            if date:
                query += " AND sdp.stat_date = %s"
                params.append(date)
            else:
                query += " AND sdp.stat_date >= CURRENT_DATE - INTERVAL '%s days'" % days

            query += " ORDER BY sdp.stat_date DESC"
            results = execute_query(query, params)
        else:
            # 查询所有站点的汇总
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
                JOIN stops s ON sdp.stop_id = s.stop_id
                WHERE sdp.stat_date >= CURRENT_DATE - INTERVAL '%s days'
            """ % days
            query += " GROUP BY sdp.stop_id, s.stop_name, s.stop_lat, s.stop_lon"
            query += " ORDER BY avg_punctuality_rate DESC LIMIT %s"
            params = [limit]
            results = execute_query(query, params)

        return jsonify(success_response(results))
    except Exception as e:
        return jsonify(error_response(f"查询失败: {str(e)}", 500)), 500


@app.route('/api/punctuality/overview', methods=['GET'])
def get_system_punctuality_overview():
    """获取系统准点率概览"""
    try:
        # 获取查询参数
        days = min(int(request.args.get('days', 7)), 90)

        # 查询系统概览
        query = """
            SELECT
                COUNT(DISTINCT rdp.route_id) as total_routes,
                SUM(rdp.total_trips) as total_trips,
                AVG(rdp.punctuality_rate) as system_punctuality_rate,
                AVG(rdp.avg_arrival_delay) / 60 as system_avg_delay_minutes,
                MAX(rdp.stat_date) as latest_data_date
            FROM route_daily_punctuality rdp
            WHERE rdp.stat_date >= CURRENT_DATE - INTERVAL '%s days'
        """ % days

        system_stats = execute_query_one(query)

        if not system_stats or system_stats['total_routes'] == 0:
            # 如果没有统计数据，返回默认值
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

        # 获取最佳和最差线路
        best_routes_query = """
            SELECT
                rdp.route_id, r.route_short_name, r.route_long_name,
                AVG(rdp.punctuality_rate) as avg_punctuality_rate,
                SUM(rdp.total_trips) as total_trips
            FROM route_daily_punctuality rdp
            JOIN routes r ON rdp.route_id = r.route_id
            WHERE rdp.stat_date >= CURRENT_DATE - INTERVAL '%s days'
            GROUP BY rdp.route_id, r.route_short_name, r.route_long_name
            ORDER BY avg_punctuality_rate DESC
            LIMIT 5
        """ % days

        worst_routes_query = """
            SELECT
                rdp.route_id, r.route_short_name, r.route_long_name,
                AVG(rdp.punctuality_rate) as avg_punctuality_rate,
                SUM(rdp.total_trips) as total_trips
            FROM route_daily_punctuality rdp
            JOIN routes r ON rdp.route_id = r.route_id
            WHERE rdp.stat_date >= CURRENT_DATE - INTERVAL '%s days'
            AND rdp.total_trips >= 10  -- 至少10个班次
            GROUP BY rdp.route_id, r.route_short_name, r.route_long_name
            ORDER BY avg_punctuality_rate ASC
            LIMIT 5
        """ % days

        best_routes = execute_query(best_routes_query)
        worst_routes = execute_query(worst_routes_query)

        # 构建返回结果
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
        # 获取查询参数
        route_id = request.args.get('route_id')
        date = request.args.get('date')

        if not date:
            date = 'CURRENT_DATE'

        # 构建查询语句
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
