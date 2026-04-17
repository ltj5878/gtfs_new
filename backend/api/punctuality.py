"""
准点率分析 API 路由
Blueprint prefix: /api/punctuality
"""

import os
import sys
from flask import Blueprint, jsonify, request
from core.db import Database, execute_query, execute_query_one, execute_count, execute_write
from core.audit import record_audit_log
from api.helpers import success_response, error_response, get_current_user

punctuality_bp = Blueprint('punctuality', __name__, url_prefix='/api/punctuality')

@punctuality_bp.route('/routes', methods=['GET'])
def get_route_punctuality():
    """获取线路准点率统计"""
    try:
        route_id = request.args.get('route_id')
        date = request.args.get('date')
        region = request.args.get('region')
        start_date = request.args.get('startDate')
        end_date = request.args.get('endDate')
        days = min(int(request.args.get('days', 7)), 90)
        limit = min(int(request.args.get('limit', 20)), 1000)

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


@punctuality_bp.route('/stops', methods=['GET'])
def get_stop_punctuality():
    """获取站点准点率统计"""
    try:
        stop_id = request.args.get('stop_id')
        date = request.args.get('date')
        region = request.args.get('region')
        days = min(int(request.args.get('days', 7)), 90)
        limit = min(int(request.args.get('limit', 20)), 10000)

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


@punctuality_bp.route('/overview', methods=['GET'])
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


@punctuality_bp.route('/hourly', methods=['GET'])
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


@punctuality_bp.route('/config', methods=['GET', 'PUT'])
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

            for key, value in configs.items():
                query = """
                    UPDATE punctuality_config
                    SET config_value = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE config_key = %s
                """
                execute_query(query, (str(value), key))

            return jsonify(success_response({"message": "配置更新成功"}))

    except Exception as e:
        return jsonify(error_response(f"操作失败: {str(e)}", 500)), 500


@punctuality_bp.route('/refresh', methods=['POST'])
def refresh_punctuality_data():
    """刷新准点率数据 — 为所有线路和站点生成当天的模拟准点率数据"""
    import time as _t
    import random as _rand
    from datetime import datetime as _dt

    region = request.args.get('region', 'sf')
    today = _dt.now().date()

    try:
        conn = Database.get_connection()
        cursor = conn.cursor()

        # --- 生成线路准点率数据 ---
        routes = execute_query(
            "SELECT route_id, route_short_name, route_long_name FROM routes WHERE region = %s",
            (region,)
        )

        for route in routes:
            route_id = route['route_id']
            base_rate = _rand.uniform(70, 95)
            if 'Rapid' in (route.get('route_long_name') or '') or (route.get('route_short_name') or '').startswith('R'):
                base_rate += _rand.uniform(-5, 10)
            if 'Express' in (route.get('route_long_name') or '') or 'X' in (route.get('route_short_name') or ''):
                base_rate += _rand.uniform(-3, 8)
            punctuality_rate = min(98, max(60, base_rate))
            total_trips = _rand.randint(80, 300)
            on_time_pct = punctuality_rate / 100
            early_pct = _rand.uniform(0.05, 0.15)
            remaining_pct = max(0, 1 - on_time_pct - early_pct)
            late_pct = remaining_pct * 0.7
            very_late_pct = remaining_pct * 0.3
            on_time_trips = int(total_trips * on_time_pct)
            early_trips = int(total_trips * early_pct)
            late_trips = max(0, int(total_trips * late_pct))
            very_late_trips = max(0, total_trips - on_time_trips - early_trips - late_trips)
            avg_delay = _rand.uniform(1.0, 8.0) if on_time_pct < 0.9 else _rand.uniform(0.5, 3.0)
            max_delay = avg_delay * _rand.uniform(2.5, 5.0)

            cursor.execute("""
                INSERT INTO route_daily_punctuality
                (region, route_id, stat_date, total_trips, on_time_trips, early_trips,
                 late_trips, very_late_trips, avg_arrival_delay, max_arrival_delay,
                 min_arrival_delay, punctuality_rate, early_rate, late_rate, very_late_rate)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (region, route_id, stat_date) DO UPDATE SET
                    total_trips = EXCLUDED.total_trips,
                    on_time_trips = EXCLUDED.on_time_trips,
                    early_trips = EXCLUDED.early_trips,
                    late_trips = EXCLUDED.late_trips,
                    very_late_trips = EXCLUDED.very_late_trips,
                    avg_arrival_delay = EXCLUDED.avg_arrival_delay,
                    max_arrival_delay = EXCLUDED.max_arrival_delay,
                    punctuality_rate = EXCLUDED.punctuality_rate,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                region, route_id, today, total_trips, on_time_trips, early_trips,
                late_trips, very_late_trips, avg_delay * 60, max_delay * 60,
                _rand.randint(-120, -30), punctuality_rate,
                early_pct * 100, late_pct * 100, very_late_pct * 100
            ))

        # --- 生成站点准点率数据 ---
        stops = execute_query("""
            SELECT DISTINCT s.stop_id, s.stop_name
            FROM stops s
            JOIN stop_times st ON s.stop_id = st.stop_id AND s.region = st.region
            WHERE s.region = %s
        """, (region,))

        for stop in stops:
            stop_id = stop['stop_id']
            base_rate = _rand.uniform(65, 92)
            if 'Station' in (stop.get('stop_name') or '') or 'Terminal' in (stop.get('stop_name') or ''):
                base_rate += _rand.uniform(-3, 5)
            punctuality_rate = min(96, max(55, base_rate))
            total_visits = _rand.randint(100, 800)
            on_time_pct = punctuality_rate / 100
            early_pct = _rand.uniform(0.08, 0.18)
            remaining_pct = max(0, 1 - on_time_pct - early_pct)
            late_pct = remaining_pct * 0.75
            very_late_pct = remaining_pct * 0.25
            on_time_visits = int(total_visits * on_time_pct)
            early_visits = int(total_visits * early_pct)
            late_visits = max(0, int(total_visits * late_pct))
            very_late_visits = max(0, total_visits - on_time_visits - early_visits - late_visits)
            avg_delay = _rand.uniform(1.2, 6.5)
            max_delay = avg_delay * _rand.uniform(2.0, 4.0)

            cursor.execute("""
                INSERT INTO stop_daily_punctuality
                (region, stop_id, stat_date, total_visits, on_time_visits, early_visits,
                 late_visits, very_late_visits, avg_arrival_delay, max_arrival_delay,
                 min_arrival_delay, punctuality_rate)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (region, stop_id, stat_date) DO UPDATE SET
                    total_visits = EXCLUDED.total_visits,
                    on_time_visits = EXCLUDED.on_time_visits,
                    early_visits = EXCLUDED.early_visits,
                    late_visits = EXCLUDED.late_visits,
                    very_late_visits = EXCLUDED.very_late_visits,
                    avg_arrival_delay = EXCLUDED.avg_arrival_delay,
                    max_arrival_delay = EXCLUDED.max_arrival_delay,
                    punctuality_rate = EXCLUDED.punctuality_rate,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                region, stop_id, today, total_visits, on_time_visits, early_visits,
                late_visits, very_late_visits, avg_delay * 60, max_delay * 60,
                _rand.randint(-120, -30), punctuality_rate
            ))

        conn.commit()
        Database.return_connection(conn)

        # 模拟数据采集耗时
        _t.sleep(3)

        # 记录审计日志
        current_user = get_current_user()
        if current_user:
            record_audit_log(current_user['user_id'], current_user['username'], 'refresh_punctuality', f'punctuality:{region}', {'region': region, 'routes_count': len(routes), 'stops_count': len(stops)})

        return jsonify(success_response({
            "routes_count": len(routes),
            "stops_count": len(stops),
            "stat_date": str(today),
            "region": region
        }))
    except Exception as e:
        return jsonify(error_response(f"刷新数据失败: {str(e)}", 500)), 500


@punctuality_bp.route('/routes/<route_id>/timetable', methods=['GET'])
def get_route_timetable(route_id):
    """获取线路时刻表 — 含模拟的实际到站时间"""
    import random as _rand
    try:
        region = request.args.get('region')
        limit = min(int(request.args.get('limit', 10)), 30)

        # 获取线路信息
        route_query = """
            SELECT route_id, route_short_name, route_long_name, route_type
            FROM routes WHERE route_id = %s
        """
        route_params = [route_id]
        if region:
            route_query += " AND region = %s"
            route_params.append(region)
        route_info = execute_query_one(route_query, tuple(route_params))
        if not route_info:
            return jsonify(error_response("线路不存在", 404)), 404

        # 获取该线路的班次
        trip_query = """
            SELECT trip_id, trip_headsign, direction_id, service_id
            FROM trips WHERE route_id = %s
        """
        trip_params = [route_id]
        if region:
            trip_query += " AND region = %s"
            trip_params.append(region)
        trip_query += " ORDER BY trip_id LIMIT %s"
        trip_params.append(limit)
        trips = execute_query(trip_query, tuple(trip_params))

        # 为每个班次获取站点时刻表并生成模拟实际到站时间
        result_trips = []
        for trip in trips:
            trip_id_val = trip['trip_id']
            st_query = """
                SELECT st.stop_id, st.stop_sequence, st.arrival_time, st.departure_time,
                       s.stop_name, s.stop_lat, s.stop_lon
                FROM stop_times st
                JOIN stops s ON st.region = s.region AND st.stop_id = s.stop_id
                WHERE st.trip_id = %s
            """
            st_params = [trip_id_val]
            if region:
                st_query += " AND st.region = %s"
                st_params.append(region)
            st_query += " ORDER BY st.stop_sequence"
            stop_times = execute_query(st_query, tuple(st_params))

            stops_with_actual = []
            for st in stop_times:
                # 用 seeded random 生成一致的模拟延误
                seed = hash(f"{route_id}_{trip_id_val}_{st['stop_id']}")
                rng = _rand.Random(seed)
                delay_seconds = rng.randint(-120, 600)

                # 计算实际到站时间
                scheduled = st['arrival_time'] or st['departure_time'] or ''
                actual_time = scheduled
                if scheduled:
                    try:
                        parts = scheduled.split(':')
                        total_sec = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                        total_sec += delay_seconds
                        h, remainder = divmod(max(0, total_sec), 3600)
                        m, s = divmod(remainder, 60)
                        actual_time = f"{h:02d}:{m:02d}:{s:02d}"
                    except (ValueError, IndexError):
                        actual_time = scheduled

                stops_with_actual.append({
                    'stop_id': st['stop_id'],
                    'stop_name': st['stop_name'],
                    'stop_sequence': st['stop_sequence'],
                    'scheduled_time': scheduled,
                    'actual_time': actual_time,
                    'delay_seconds': delay_seconds,
                    'stop_lat': st['stop_lat'],
                    'stop_lon': st['stop_lon']
                })

            result_trips.append({
                'trip_id': trip_id_val,
                'trip_headsign': trip.get('trip_headsign', ''),
                'direction_id': trip.get('direction_id'),
                'stops': stops_with_actual
            })

        return jsonify(success_response({
            'route_info': dict(route_info),
            'trips': result_trips
        }))
    except Exception as e:
        return jsonify(error_response(f"查询失败: {str(e)}", 500)), 500


@punctuality_bp.route('/stops/<stop_id>/timetable', methods=['GET'])
def get_stop_timetable(stop_id):
    """获取站点时刻表 — 含模拟的实际到站时间"""
    import random as _rand
    try:
        region = request.args.get('region')
        limit = min(int(request.args.get('limit', 50)), 200)

        # 获取站点信息
        stop_query = """
            SELECT stop_id, stop_name, stop_lat, stop_lon
            FROM stops WHERE stop_id = %s
        """
        stop_params = [stop_id]
        if region:
            stop_query += " AND region = %s"
            stop_params.append(region)
        stop_info = execute_query_one(stop_query, tuple(stop_params))
        if not stop_info:
            return jsonify(error_response("站点不存在", 404)), 404

        # 获取经过该站点的时刻表记录
        records_query = """
            SELECT st.trip_id, st.arrival_time, st.departure_time, st.stop_sequence,
                   t.route_id, t.trip_headsign, t.direction_id,
                   r.route_short_name, r.route_long_name
            FROM stop_times st
            JOIN trips t ON st.region = t.region AND st.trip_id = t.trip_id
            JOIN routes r ON t.region = r.region AND t.route_id = r.route_id
            WHERE st.stop_id = %s
        """
        rec_params = [stop_id]
        if region:
            records_query += " AND st.region = %s"
            rec_params.append(region)
        records_query += " ORDER BY st.arrival_time LIMIT %s"
        rec_params.append(limit)
        records = execute_query(records_query, tuple(rec_params))

        result_records = []
        for rec in records:
            seed = hash(f"{rec['route_id']}_{rec['trip_id']}_{stop_id}")
            rng = _rand.Random(seed)
            delay_seconds = rng.randint(-120, 600)

            scheduled = rec['arrival_time'] or rec['departure_time'] or ''
            actual_time = scheduled
            if scheduled:
                try:
                    parts = scheduled.split(':')
                    total_sec = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                    total_sec += delay_seconds
                    h, remainder = divmod(max(0, total_sec), 3600)
                    m, s = divmod(remainder, 60)
                    actual_time = f"{h:02d}:{m:02d}:{s:02d}"
                except (ValueError, IndexError):
                    actual_time = scheduled

            result_records.append({
                'trip_id': rec['trip_id'],
                'route_id': rec['route_id'],
                'route_short_name': rec.get('route_short_name', ''),
                'route_long_name': rec.get('route_long_name', ''),
                'trip_headsign': rec.get('trip_headsign', ''),
                'direction_id': rec.get('direction_id'),
                'scheduled_time': scheduled,
                'actual_time': actual_time,
                'delay_seconds': delay_seconds
            })

        return jsonify(success_response({
            'stop_info': dict(stop_info),
            'records': result_records
        }))
    except Exception as e:
        return jsonify(error_response(f"查询失败: {str(e)}", 500)), 500


@punctuality_bp.route('/trends', methods=['GET'])
def get_punctuality_trends():
    """获取准点率趋势数据（每日时间序列）"""
    try:
        days = min(int(request.args.get('days', 30)), 90)
        region = request.args.get('region')
        route_id = request.args.get('route_id')
        stop_id = request.args.get('stop_id')

        region_clause = ""
        region_params = []
        if region:
            region_clause = " AND rdp.region = %s"
            region_params = [region]

        result = {}

        # 1. 系统每日准点率趋势
        sys_query = """
            SELECT
                rdp.stat_date,
                AVG(rdp.punctuality_rate) as avg_punctuality_rate,
                SUM(rdp.total_trips) as total_trips,
                AVG(ABS(rdp.avg_arrival_delay)) / 60 as avg_delay_minutes,
                SUM(rdp.on_time_trips) as on_time_trips,
                SUM(rdp.early_trips) as early_trips,
                SUM(rdp.late_trips) as late_trips,
                SUM(rdp.very_late_trips) as very_late_trips
            FROM route_daily_punctuality rdp
            WHERE rdp.stat_date >= CURRENT_DATE - INTERVAL '%s days'
            %s
            GROUP BY rdp.stat_date
            ORDER BY rdp.stat_date
        """ % (days, region_clause)
        result['daily_trends'] = execute_query(sys_query, tuple(region_params) if region_params else None)

        # 2. 线路 TOP5 / BOTTOM5
        route_rank_query = """
            SELECT
                rdp.route_id, r.route_short_name, r.route_long_name,
                AVG(rdp.punctuality_rate) as avg_punctuality_rate,
                SUM(rdp.total_trips) as total_trips,
                AVG(ABS(rdp.avg_arrival_delay)) / 60 as avg_delay_minutes
            FROM route_daily_punctuality rdp
            JOIN routes r ON rdp.region = r.region AND rdp.route_id = r.route_id
            WHERE rdp.stat_date >= CURRENT_DATE - INTERVAL '%s days'
            %s
            GROUP BY rdp.route_id, r.route_short_name, r.route_long_name
            HAVING SUM(rdp.total_trips) >= 10
            ORDER BY avg_punctuality_rate DESC
        """ % (days, region_clause)
        all_routes = execute_query(route_rank_query, tuple(region_params) if region_params else None)
        result['top_routes'] = all_routes[:5] if all_routes else []
        result['bottom_routes'] = list(reversed(all_routes[-5:])) if all_routes else []

        # 3. 站点 TOP5 / BOTTOM5
        stop_rank_query = """
            SELECT
                sdp.stop_id, s.stop_name,
                AVG(sdp.punctuality_rate) as avg_punctuality_rate,
                SUM(sdp.total_visits) as total_visits,
                AVG(ABS(sdp.avg_arrival_delay)) / 60 as avg_delay_minutes
            FROM stop_daily_punctuality sdp
            JOIN stops s ON sdp.region = s.region AND sdp.stop_id = s.stop_id
            WHERE sdp.stat_date >= CURRENT_DATE - INTERVAL '%s days'
            %s
        """ % (days, region_clause.replace('rdp.', 'sdp.'))
        stop_rank_query += """
            GROUP BY sdp.stop_id, s.stop_name
            HAVING SUM(sdp.total_visits) >= 10
            ORDER BY avg_punctuality_rate DESC
        """
        all_stops = execute_query(stop_rank_query, tuple(region_params) if region_params else None)
        result['top_stops'] = all_stops[:5] if all_stops else []
        result['bottom_stops'] = list(reversed(all_stops[-5:])) if all_stops else []

        # 4. 单条线路趋势（可选）
        if route_id:
            route_trend_query = """
                SELECT
                    rdp.stat_date, rdp.route_id, r.route_short_name,
                    rdp.punctuality_rate, rdp.total_trips,
                    rdp.avg_arrival_delay / 60 as avg_delay_minutes,
                    rdp.on_time_trips, rdp.early_trips, rdp.late_trips, rdp.very_late_trips
                FROM route_daily_punctuality rdp
                JOIN routes r ON rdp.region = r.region AND rdp.route_id = r.route_id
                WHERE rdp.route_id = %s
                AND rdp.stat_date >= CURRENT_DATE - INTERVAL '%s days'
            """ % ('%s', days)
            rt_params = [route_id]
            if region:
                route_trend_query += " AND rdp.region = %s"
                rt_params.append(region)
            route_trend_query += " ORDER BY rdp.stat_date"
            result['route_trend'] = execute_query(route_trend_query, tuple(rt_params))

        # 5. 单个站点趋势（可选）
        if stop_id:
            stop_trend_query = """
                SELECT
                    sdp.stat_date, sdp.stop_id, s.stop_name,
                    sdp.punctuality_rate, sdp.total_visits,
                    sdp.avg_arrival_delay / 60 as avg_delay_minutes,
                    sdp.on_time_visits, sdp.early_visits, sdp.late_visits, sdp.very_late_visits
                FROM stop_daily_punctuality sdp
                JOIN stops s ON sdp.region = s.region AND sdp.stop_id = s.stop_id
                WHERE sdp.stop_id = %s
                AND sdp.stat_date >= CURRENT_DATE - INTERVAL '%s days'
            """ % ('%s', days)
            st_params = [stop_id]
            if region:
                stop_trend_query += " AND sdp.region = %s"
                st_params.append(region)
            stop_trend_query += " ORDER BY sdp.stat_date"
            result['stop_trend'] = execute_query(stop_trend_query, tuple(st_params))

        # 6. 高峰/非高峰时段对比
        peak_query = """
            SELECT
                CASE
                    WHEN hps.hour_of_day BETWEEN 7 AND 9 THEN '早高峰(7-9时)'
                    WHEN hps.hour_of_day BETWEEN 17 AND 19 THEN '晚高峰(17-19时)'
                    ELSE '非高峰时段'
                END as period,
                AVG(hps.punctuality_rate) as avg_punctuality_rate,
                SUM(hps.total_trips) as total_trips,
                AVG(ABS(hps.avg_arrival_delay)) / 60 as avg_delay_minutes
            FROM hourly_punctuality_stats hps
            WHERE hps.stat_date >= CURRENT_DATE - INTERVAL '%s days'
        """ % days
        if region:
            peak_query += " AND hps.region = %s"
        peak_query += """
            GROUP BY period
            ORDER BY period
        """
        result['peak_comparison'] = execute_query(peak_query, (region,) if region else None)

        result['days'] = days
        result['data_available'] = bool(result['daily_trends'])

        return jsonify(success_response(result))
    except Exception as e:
        return jsonify(error_response(f"查询失败: {str(e)}", 500)), 500


@punctuality_bp.route('/collect', methods=['POST'])
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
