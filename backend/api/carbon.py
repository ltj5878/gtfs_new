"""
碳排放 API 路由
Blueprint prefix: /api/carbon
"""

from flask import Blueprint, jsonify, request
from core.db import execute_query, execute_query_one, execute_write
from core.audit import record_audit_log
from api.helpers import success_response, error_response, get_current_user, is_truthy_param

carbon_bp = Blueprint('carbon', __name__, url_prefix='/api/carbon')

@carbon_bp.route('/route/<route_id>', methods=['GET'])
def get_route_carbon(route_id):
    """计算某条线路的碳排放对比数据"""
    region = request.args.get('region', 'sf')
    try:
        from services.carbon_service import calculate_route_carbon
        return jsonify(success_response(calculate_route_carbon(route_id, region)))
    except ValueError as e:
        return jsonify(error_response(str(e), 404)), 404
    except Exception as e:
        return jsonify(error_response(f"碳排放计算失败: {str(e)}", 500)), 500

@carbon_bp.route('/record', methods=['POST'])
def record_carbon_trip():
    """用户记录一次绿色出行"""
    user = get_current_user()
    if not user:
        return jsonify(error_response("请先登录", 401)), 401
    data = request.get_json() or {}
    route_id = data.get('route_id')
    region = data.get('region', 'sf')
    if not route_id:
        return jsonify(error_response("缺少线路ID", 400)), 400

    try:
        ride_count = int(data.get('ride_count', 1) or 1)
    except (TypeError, ValueError):
        return jsonify(error_response("乘坐次数格式错误", 400)), 400
    if ride_count < 1 or ride_count > 50:
        return jsonify(error_response("乘坐次数需在 1 到 50 之间", 400)), 400

    trip_date_raw = str(data.get('trip_date') or '').strip()
    if trip_date_raw:
        try:
            from datetime import date as _date
            trip_date = _date.fromisoformat(trip_date_raw)
        except ValueError:
            return jsonify(error_response("出行日期格式错误，应为 YYYY-MM-DD", 400)), 400
    else:
        from datetime import date as _date
        trip_date = _date.today()

    distance_input = data.get('distance_km')
    try:
        from services.carbon_service import build_trip_carbon_record

        metrics = build_trip_carbon_record(
            route_id,
            region,
            ride_count=ride_count,
            ride_distance_km=distance_input,
        )
        execute_write("""
            INSERT INTO user_carbon_records
                (user_id, route_id, region, trip_date, ride_count, distance_km,
                 transit_emission, car_emission, carbon_saved, record_source)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'user')
            RETURNING id
        """, (
            user['user_id'],
            route_id,
            region,
            trip_date,
            metrics['ride_count'],
            metrics['distance_km'],
            metrics['transit_emission'],
            metrics['car_emission'],
            metrics['carbon_saved'],
        ))
        record_audit_log(
            user['user_id'],
            user['username'],
            'record_carbon_trip',
            f'carbon:{route_id}',
            {
                'region': region,
                'trip_date': trip_date.isoformat(),
                'ride_count': metrics['ride_count'],
                'distance_km': metrics['distance_km'],
                'carbon_saved': metrics['carbon_saved'],
            }
        )
        return jsonify(success_response({
            'message': '绿色出行已记录',
            'trip_date': trip_date.isoformat(),
            **metrics,
        }))
    except ValueError as e:
        return jsonify(error_response(str(e), 400)), 400
    except Exception as e:
        return jsonify(error_response(f"记录失败: {str(e)}", 500)), 500


@carbon_bp.route('/my-stats', methods=['GET'])
def get_carbon_my_stats():
    """获取当前用户碳排放统计"""
    user = get_current_user()
    if not user:
        return jsonify(error_response("请先登录", 401)), 401
    try:
        region = request.args.get('region', '').strip()
        region_sql = " AND region = %s" if region else ""
        region_params = (region,) if region else ()
        source_sql = " AND record_source = 'user'"
        stats = execute_query_one("""
            SELECT
                COALESCE(SUM(ride_count), 0) as total_trips,
                COALESCE(SUM(distance_km), 0) as total_distance,
                COALESCE(SUM(carbon_saved), 0) as total_saved,
                COALESCE(SUM(transit_emission), 0) as total_transit,
                COALESCE(SUM(car_emission), 0) as total_car
            FROM user_carbon_records
            WHERE user_id = %s
        """ + source_sql + region_sql, (user['user_id'],) + region_params)

        # 本周统计
        week_stats = execute_query_one("""
            SELECT COALESCE(SUM(carbon_saved), 0) as week_saved, COALESCE(SUM(ride_count), 0) as week_trips
            FROM user_carbon_records
            WHERE user_id = %s AND trip_date >= (CURRENT_DATE - INTERVAL '7 days')
        """ + source_sql + region_sql, (user['user_id'],) + region_params)

        # 本月统计
        month_stats = execute_query_one("""
            SELECT COALESCE(SUM(carbon_saved), 0) as month_saved, COALESCE(SUM(ride_count), 0) as month_trips
            FROM user_carbon_records
            WHERE user_id = %s AND trip_date >= DATE_TRUNC('month', CURRENT_DATE)
        """ + source_sql + region_sql, (user['user_id'],) + region_params)

        # 每日趋势（最近30天）
        daily = execute_query("""
            SELECT trip_date, SUM(carbon_saved) as saved, COALESCE(SUM(ride_count), 0) as trips
            FROM user_carbon_records
            WHERE user_id = %s AND trip_date >= (CURRENT_DATE - INTERVAL '30 days')
        """ + source_sql + region_sql + """
            GROUP BY trip_date ORDER BY trip_date
        """, (user['user_id'],) + region_params)

        total_saved = float(stats['total_saved']) if stats else 0
        return jsonify(success_response({
            'total_trips': stats['total_trips'] if stats else 0,
            'total_distance_km': round(float(stats['total_distance']) if stats else 0, 2),
            'total_saved_kg': round(total_saved, 2),
            'week_saved_kg': round(float(week_stats['week_saved']) if week_stats else 0, 2),
            'week_trips': week_stats['week_trips'] if week_stats else 0,
            'month_saved_kg': round(float(month_stats['month_saved']) if month_stats else 0, 2),
            'month_trips': month_stats['month_trips'] if month_stats else 0,
            'trees_equivalent': round(total_saved / 21.77, 1),
            'fuel_saved_liters': round(float(stats['total_distance']) / 8.5 if stats and stats['total_distance'] else 0, 1),
            'daily_trend': [dict(r) for r in daily]
        }))
    except Exception as e:
        return jsonify(error_response(f"获取统计失败: {str(e)}", 500)), 500


@carbon_bp.route('/my-records', methods=['GET'])
def get_my_carbon_records():
    """获取当前用户手动录入的绿色出行记录。"""
    user = get_current_user()
    if not user:
        return jsonify(error_response("请先登录", 401)), 401

    region = request.args.get('region', '').strip()
    limit = request.args.get('limit', 10, type=int)
    limit = min(max(limit, 1), 50)
    try:
        region_sql = " AND c.region = %s" if region else ""
        params = (user['user_id'], region, limit) if region else (user['user_id'], limit)
        rows = execute_query("""
            SELECT
                c.id,
                c.route_id,
                c.region,
                c.trip_date,
                COALESCE(c.ride_count, 1) as ride_count,
                c.distance_km,
                c.transit_emission,
                c.car_emission,
                c.carbon_saved,
                c.created_at,
                COALESCE(r.route_short_name, c.route_id) as route_short_name,
                COALESCE(r.route_long_name, '') as route_long_name
            FROM user_carbon_records c
            LEFT JOIN routes r
              ON c.route_id = r.route_id
             AND c.region = r.region
            WHERE c.user_id = %s
              AND c.record_source = 'user'
        """ + region_sql + """
            ORDER BY c.trip_date DESC, c.created_at DESC
            LIMIT %s
        """, params)
        return jsonify(success_response([dict(r) for r in rows]))
    except Exception as e:
        return jsonify(error_response(f"获取个人记录失败: {str(e)}", 500)), 500


@carbon_bp.route('/records/<int:record_id>', methods=['DELETE'])
def delete_carbon_record(record_id):
    """删除当前用户的一条手动录入记录。"""
    user = get_current_user()
    if not user:
        return jsonify(error_response("请先登录", 401)), 401

    try:
        record = execute_query_one("""
            SELECT id, route_id
            FROM user_carbon_records
            WHERE id = %s
              AND user_id = %s
              AND record_source = 'user'
        """, (record_id, user['user_id']))
        if not record:
            return jsonify(error_response("记录不存在", 404)), 404

        execute_write("""
            DELETE FROM user_carbon_records
            WHERE id = %s
              AND user_id = %s
              AND record_source = 'user'
        """, (record_id, user['user_id']))
        record_audit_log(
            user['user_id'],
            user['username'],
            'delete_carbon_trip',
            f"carbon:{record.get('route_id') or record_id}",
            {'record_id': record_id}
        )
        return jsonify(success_response({'id': record_id, 'message': '记录已删除'}))
    except Exception as e:
        return jsonify(error_response(f"删除失败: {str(e)}", 500)), 500


@carbon_bp.route('/leaderboard', methods=['GET'])
def get_carbon_leaderboard():
    """绿色出行排行榜"""
    region = request.args.get('region', '').strip()
    limit = request.args.get('limit', 10, type=int)
    try:
        refresh = is_truthy_param(request.args.get('refresh'))
        user_region_sql = " AND region = %s" if region else ""
        user_count_row = execute_query_one("""
            SELECT COUNT(*) as cnt
            FROM user_carbon_records
            WHERE record_source = 'user'
        """ + user_region_sql, (region,) if region else None)
        user_count = int(user_count_row['cnt'] or 0) if user_count_row else 0

        source_clause = "c.record_source = 'user'"
        if user_count == 0:
            from services.carbon_service import ensure_demo_carbon_data
            ensure_demo_carbon_data(region or 'sf', force_refresh=refresh)
            source_clause = "1 = 1"

        region_sql = " AND c.region = %s" if region else ""
        params = (region, limit) if region else (limit,)
        rows = execute_query("""
            SELECT u.username, COALESCE(SUM(c.ride_count), 0) as trip_count,
                   ROUND(COALESCE(SUM(c.carbon_saved), 0)::numeric, 2) as total_saved
            FROM user_carbon_records c
            JOIN users u ON c.user_id = u.id
            WHERE """ + source_clause + region_sql + """
            GROUP BY u.username
            ORDER BY total_saved DESC
            LIMIT %s
        """, params)
        return jsonify(success_response([dict(r) for r in rows]))
    except Exception as e:
        return jsonify(error_response(f"获取排行榜失败: {str(e)}", 500)), 500

