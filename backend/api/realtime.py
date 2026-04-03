"""
实时数据 API 路由
Blueprint prefix: /api/realtime
"""

import os
import sys
from flask import Blueprint, jsonify, request
from core.db import Database, execute_query, execute_query_one, execute_count, execute_write
from core.audit import record_audit_log
from api.helpers import success_response, error_response, get_current_user

realtime_bp = Blueprint('realtime', __name__, url_prefix='/api/realtime')

@realtime_bp.route('/vehicles', methods=['GET'])
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


@realtime_bp.route('/vehicles/dates', methods=['GET'])
def get_vehicle_history_dates():
    """获取有历史车辆位置数据的日期列表"""
    try:
        region = request.args.get('region', 'sf')
        rows = execute_query(
            """SELECT DISTINCT DATE(position_timestamp) AS date
               FROM realtime_vehicle_positions
               WHERE region = %s
               ORDER BY date DESC""",
            (region,)
        )
        dates = [str(r['date']) for r in rows]
        return jsonify(success_response(dates))
    except Exception as e:
        return jsonify(error_response(f"查询失败: {str(e)}", 500)), 500


@realtime_bp.route('/vehicles/history', methods=['GET'])
def get_vehicle_history():
    """获取指定日期的车辆历史位置数据（用于回放）"""
    try:
        region = request.args.get('region', 'sf')
        date = request.args.get('date', '').strip()
        if not date:
            return jsonify(error_response("缺少 date 参数", 400)), 400

        rows = execute_query(
            """SELECT vehicle_id, route_id, latitude, longitude, bearing, speed,
                      position_timestamp
               FROM realtime_vehicle_positions
               WHERE region = %s AND DATE(position_timestamp) = %s
               ORDER BY position_timestamp""",
            (region, date)
        )
        for r in rows:
            if r.get('position_timestamp'):
                r['position_timestamp'] = r['position_timestamp'].isoformat()
            if r.get('latitude'):
                r['latitude'] = float(r['latitude'])
            if r.get('longitude'):
                r['longitude'] = float(r['longitude'])
            if r.get('bearing'):
                r['bearing'] = float(r['bearing'])
            if r.get('speed'):
                r['speed'] = float(r['speed'])
        return jsonify(success_response(rows))
    except Exception as e:
        return jsonify(error_response(f"查询失败: {str(e)}", 500)), 500


@realtime_bp.route('/vehicles/sync', methods=['POST'])
def sync_vehicle_history():
    """同步车辆历史数据：为当前地区生成前一天的模拟位置数据"""
    import subprocess
    from datetime import datetime, timedelta
    try:
        region = request.args.get('region', 'sf')
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

        # 检查前一天是否已有数据
        count = execute_query(
            """SELECT COUNT(*) AS cnt FROM realtime_vehicle_positions
               WHERE region = %s AND DATE(position_timestamp) = %s""",
            (region, yesterday)
        )
        if count and count[0]['cnt'] > 0:
            return jsonify(success_response({
                'message': f'{yesterday} 已有数据，无需重复生成',
                'date': yesterday,
                'total_points': count[0]['cnt'],
                'skipped': True
            }))

        # 调用生成脚本
        script_path = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'generate_vehicle_history.py')
        result = subprocess.run(
            [sys.executable, script_path, '--region', region, '--date', yesterday, '--trips-per-hour', '20'],
            capture_output=True, text=True, timeout=120
        )

        if result.returncode != 0:
            return jsonify(error_response(f"生成失败: {result.stderr}", 500)), 500

        # 查询生成的数据量
        count = execute_query(
            """SELECT COUNT(*) AS cnt FROM realtime_vehicle_positions
               WHERE region = %s AND DATE(position_timestamp) = %s""",
            (region, yesterday)
        )
        total = count[0]['cnt'] if count else 0

        # 记录同步操作审计日志
        user = get_current_user()
        if user:
            record_audit_log(
                user_id=user['user_id'], username=user['username'],
                action='sync_data', target=f'vehicles:{region}',
                detail={'date': yesterday, 'total_points': total}
            )

        return jsonify(success_response({
            'message': f'成功生成 {yesterday} 的车辆历史数据',
            'date': yesterday,
            'total_points': total,
            'skipped': False
        }))
    except subprocess.TimeoutExpired:
        return jsonify(error_response("生成超时，请稍后重试", 500)), 500
    except Exception as e:
        return jsonify(error_response(f"同步失败: {str(e)}", 500)), 500


@realtime_bp.route('/delays', methods=['GET'])
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


@realtime_bp.route('/summary', methods=['GET'])
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

