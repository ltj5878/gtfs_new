"""
基础 GTFS 数据查询 API 路由
Blueprint prefix: /api
"""

from flask import Blueprint, jsonify, request
from core.db import execute_query, execute_query_one, execute_count
from core.route_mappings import enrich_route_attributes
from api.helpers import success_response, error_response

gtfs_bp = Blueprint('gtfs', __name__, url_prefix='/api')

@gtfs_bp.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    try:
        result = execute_query_one("SELECT 1 as status")
        if result:
            return jsonify(success_response({"status": "healthy", "database": "connected"}))
        return jsonify(error_response("数据库连接失败", 500)), 500
    except Exception as e:
        return jsonify(error_response(f"健康检查失败: {str(e)}", 500)), 500


@gtfs_bp.route('/regions', methods=['GET'])
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


@gtfs_bp.route('/agencies', methods=['GET'])
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


@gtfs_bp.route('/agencies/<agency_id>', methods=['GET'])
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


@gtfs_bp.route('/routes', methods=['GET'])
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


@gtfs_bp.route('/routes/<route_id>', methods=['GET'])
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


@gtfs_bp.route('/routes/<route_id>/directions', methods=['GET'])
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


@gtfs_bp.route('/routes/<route_id>/stops', methods=['GET'])
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


@gtfs_bp.route('/stops', methods=['GET'])
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


@gtfs_bp.route('/stops/<stop_id>', methods=['GET'])
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


@gtfs_bp.route('/stops/<stop_id>/routes', methods=['GET'])
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


@gtfs_bp.route('/stops/frequency', methods=['GET'])
def get_stop_frequency():
    """获取各站点的服务频率（班次密度），用于热力图展示"""
    try:
        region = request.args.get('region', 'sf')
        period = request.args.get('period', 'all').strip()
        route_type = request.args.get('route_type', '').strip()

        where_clauses = ["s.region = %s"]
        params = [region]

        # 时段筛选
        if period == 'morning':
            where_clauses.append("st.departure_time >= '06:00:00' AND st.departure_time < '09:00:00'")
        elif period == 'evening':
            where_clauses.append("st.departure_time >= '17:00:00' AND st.departure_time < '20:00:00'")

        # 线路类型筛选
        join_routes = ""
        if route_type != '':
            join_routes = "JOIN routes r ON t.region = r.region AND t.route_id = r.route_id"
            where_clauses.append("r.route_type = %s")
            params.append(int(route_type))

        where_sql = " AND ".join(where_clauses)

        query = f"""
            SELECT s.stop_id, s.stop_name, s.stop_lat, s.stop_lon, COUNT(*) AS frequency
            FROM stops s
            JOIN stop_times st ON s.region = st.region AND s.stop_id = st.stop_id
            JOIN trips t ON st.region = t.region AND st.trip_id = t.trip_id
            {join_routes}
            WHERE {where_sql}
            GROUP BY s.stop_id, s.stop_name, s.stop_lat, s.stop_lon
            ORDER BY frequency DESC
        """
        rows = execute_query(query, tuple(params))
        return jsonify(success_response(rows))
    except Exception as e:
        return jsonify(error_response(f"查询失败: {str(e)}", 500)), 500


@gtfs_bp.route('/trips', methods=['GET'])
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


@gtfs_bp.route('/trips/<trip_id>', methods=['GET'])
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


@gtfs_bp.route('/trips/<trip_id>/stop_times', methods=['GET'])
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


@gtfs_bp.route('/routes/schedule-summary', methods=['GET'])
def get_routes_schedule_summary():
    """获取所有线路的运营时间摘要（首末班 + 班次数 + 高峰密度）"""
    try:
        region = request.args.get('region', 'sf')
        rows = execute_query("""
            SELECT
                t.route_id,
                r.route_short_name,
                r.route_long_name,
                MIN(st.departure_time) AS first_departure,
                MAX(st.departure_time) AS last_departure,
                COUNT(DISTINCT st.trip_id) AS total_trips,
                COUNT(DISTINCT st.trip_id) FILTER (
                    WHERE CAST(SPLIT_PART(st.departure_time, ':', 1) AS INTEGER) %% 24 BETWEEN 7 AND 9
                ) AS morning_peak_trips,
                COUNT(DISTINCT st.trip_id) FILTER (
                    WHERE CAST(SPLIT_PART(st.departure_time, ':', 1) AS INTEGER) %% 24 BETWEEN 17 AND 19
                ) AS evening_peak_trips
            FROM stop_times st
            JOIN trips t ON st.region = t.region AND st.trip_id = t.trip_id
            JOIN routes r ON t.region = r.region AND t.route_id = r.route_id
            WHERE t.region = %s AND st.stop_sequence = 1
            GROUP BY t.route_id, r.route_short_name, r.route_long_name
            ORDER BY total_trips DESC
        """, (region,))
        return jsonify(success_response(rows))
    except Exception as e:
        return jsonify(error_response(f"查询失败: {str(e)}", 500)), 500


@gtfs_bp.route('/routes/<route_id>/schedule-analysis', methods=['GET'])
def get_route_schedule_analysis(route_id):
    """获取单条线路运营时间分析：首末班、24小时班次分布"""
    try:
        region = request.args.get('region', 'sf')

        # 各小时班次分布（用 %% 24 处理超过24小时的 GTFS 时间）
        rows = execute_query("""
            SELECT
                CAST(SPLIT_PART(st.departure_time, ':', 1) AS INTEGER) %% 24 AS hour,
                COUNT(DISTINCT st.trip_id) AS trip_count
            FROM stop_times st
            JOIN trips t ON st.region = t.region AND st.trip_id = t.trip_id
            WHERE t.route_id = %s AND t.region = %s AND st.stop_sequence = 1
            GROUP BY hour ORDER BY hour
        """, (route_id, region))

        # 首末班时间
        first_last = execute_query_one("""
            SELECT
                MIN(st.departure_time) AS first_departure,
                MAX(st.departure_time) AS last_departure,
                COUNT(DISTINCT st.trip_id) AS total_trips
            FROM stop_times st
            JOIN trips t ON st.region = t.region AND st.trip_id = t.trip_id
            WHERE t.route_id = %s AND t.region = %s AND st.stop_sequence = 1
        """, (route_id, region))

        # 构建 24 小时分布
        hourly = {}
        for r in rows:
            h = int(r['hour']) if r['hour'] is not None else 0
            hourly[h] = r['trip_count']

        distribution = [{'hour': h, 'trip_count': hourly.get(h, 0)} for h in range(24)]

        morning_peak = sum(hourly.get(h, 0) for h in range(7, 10))
        evening_peak = sum(hourly.get(h, 0) for h in range(17, 20))
        total = first_last['total_trips'] or 0

        return jsonify(success_response({
            'first_departure': first_last['first_departure'] if first_last else None,
            'last_departure': first_last['last_departure'] if first_last else None,
            'total_trips': total,
            'morning_peak': morning_peak,
            'evening_peak': evening_peak,
            'off_peak': max(0, total - morning_peak - evening_peak),
            'hourly_distribution': distribution,
        }))
    except Exception as e:
        return jsonify(error_response(f"查询失败: {str(e)}", 500)), 500


@gtfs_bp.route('/routes/<route_id>/shapes', methods=['GET'])
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


@gtfs_bp.route('/routes/<route_id>/fares', methods=['GET'])
def get_route_fares(route_id):
    """获取指定线路的票价信息（含各乘客类别差异价）"""
    try:
        region = request.args.get('region')

        # 查询该线路关联的所有票价
        fare_query = """
            SELECT DISTINCT fa.fare_id, fa.price, fa.currency_type,
                   fa.payment_method, fa.transfers, fa.transfer_duration
            FROM fare_attributes fa
            JOIN fare_rules fr ON fa.region = fr.region AND fa.fare_id = fr.fare_id
            WHERE fr.route_id = %s
        """
        params = [route_id]
        if region:
            fare_query += " AND fa.region = %s"
            params.append(region)
        fare_query += " ORDER BY fa.price"

        fares = execute_query(fare_query, tuple(params))
        if not fares:
            return jsonify(success_response({'route_id': route_id, 'fares': []}))

        # 收集所有 fare_id，批量查询乘客类别票价
        fare_ids = [f['fare_id'] for f in fares]
        cat_query = """
            SELECT frc.fare_id, frc.rider_category_id,
                   rc.rider_category_description, frc.price
            FROM fare_rider_categories frc
            JOIN rider_categories rc ON frc.region = rc.region
              AND frc.rider_category_id = rc.rider_category_id
            WHERE frc.fare_id IN %s
        """
        cat_params = [tuple(fare_ids)]
        if region:
            cat_query += " AND frc.region = %s"
            cat_params.append(region)
        cat_query += " ORDER BY frc.fare_id, frc.price"

        categories = execute_query(cat_query, tuple(cat_params))

        # 按 fare_id 分组乘客类别
        cat_map = {}
        for c in categories:
            fid = c['fare_id']
            if fid not in cat_map:
                cat_map[fid] = []
            cat_map[fid].append({
                'rider_category_id': c['rider_category_id'],
                'description': c['rider_category_description'],
                'price': float(c['price'])
            })

        result = {
            'route_id': route_id,
            'fares': [{
                'fare_id': f['fare_id'],
                'price': float(f['price']),
                'currency_type': f['currency_type'],
                'payment_method': f['payment_method'],
                'transfers': f['transfers'],
                'transfer_duration': f['transfer_duration'],
                'rider_categories': cat_map.get(f['fare_id'], [])
            } for f in fares]
        }
        return jsonify(success_response(result))
    except Exception as e:
        return jsonify(error_response(f"查询票价失败: {str(e)}", 500)), 500


@gtfs_bp.route('/shapes/<shape_id>', methods=['GET'])
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


@gtfs_bp.route('/calendar', methods=['GET'])
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


@gtfs_bp.route('/stats', methods=['GET'])
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

