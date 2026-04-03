"""
健康度评分与异常告警 API 路由
Blueprint prefix: /api
"""

from flask import Blueprint, jsonify, request
from core.db import execute_query, execute_query_one, execute_write
from core.audit import record_audit_log
from api.helpers import success_response, error_response, require_admin, is_truthy_param, normalize_health_score_row

health_alerts_bp = Blueprint('health_alerts', __name__, url_prefix='/api')

@health_alerts_bp.route('/routes/health-scores', methods=['GET'])
def get_route_health_scores():
    """获取所有线路的健康度评分"""
    region = request.args.get('region', 'sf')
    sort_by = request.args.get('sort_by', 'total_score')
    order = request.args.get('order', 'desc')
    limit = request.args.get('limit', 50, type=int)
    try:
        if is_truthy_param(request.args.get('refresh')):
            from scripts.calculate_health_scores import calculate_scores
            calculate_scores(region)

        order_dir = 'DESC' if order == 'desc' else 'ASC'
        sort_col = sort_by if sort_by in ('total_score', 'punctuality_score', 'frequency_score',
                                           'coverage_score', 'delay_dist_score') else 'total_score'
        rows = execute_query(f"""
            SELECT hs.route_id, r.route_short_name, r.route_long_name, r.route_type,
                   hs.score_date, hs.punctuality_score, hs.frequency_score,
                   hs.coverage_score, hs.delay_dist_score, hs.total_score
            FROM route_health_scores hs
            JOIN routes r ON hs.route_id = r.route_id AND hs.region = r.region
            WHERE hs.region = %s AND hs.score_date = (
                SELECT MAX(score_date) FROM route_health_scores WHERE region = %s
            )
            ORDER BY hs.{sort_col} {order_dir} NULLS LAST
            LIMIT %s
        """, (region, region, limit))

        if not rows:
            from scripts.calculate_health_scores import calculate_scores
            calculate_scores(region)
            rows = execute_query(f"""
                SELECT hs.route_id, r.route_short_name, r.route_long_name, r.route_type,
                       hs.score_date, hs.punctuality_score, hs.frequency_score,
                       hs.coverage_score, hs.delay_dist_score, hs.total_score
                FROM route_health_scores hs
                JOIN routes r ON hs.route_id = r.route_id AND hs.region = r.region
                WHERE hs.region = %s AND hs.score_date = (
                    SELECT MAX(score_date) FROM route_health_scores WHERE region = %s
                )
                ORDER BY hs.{sort_col} {order_dir} NULLS LAST
                LIMIT %s
            """, (region, region, limit))
        return jsonify(success_response([normalize_health_score_row(r) for r in rows]))
    except Exception as e:
        return jsonify(error_response(f"获取健康度评分失败: {str(e)}", 500)), 500


@health_alerts_bp.route('/routes/<route_id>/health-score', methods=['GET'])
def get_route_health_score_detail(route_id):
    """获取单条线路的健康度详情"""
    region = request.args.get('region', 'sf')
    try:
        # 最新评分
        latest = execute_query_one("""
            SELECT * FROM route_health_scores
            WHERE route_id = %s AND region = %s
            ORDER BY score_date DESC LIMIT 1
        """, (route_id, region))
        # 历史趋势（最近30天）
        history = execute_query("""
            SELECT score_date, total_score, punctuality_score, frequency_score,
                   coverage_score, delay_dist_score
            FROM route_health_scores
            WHERE route_id = %s AND region = %s
            ORDER BY score_date DESC LIMIT 30
        """, (route_id, region))

        if len(history) < 2:
            from scripts.calculate_health_scores import calculate_score_history
            calculate_score_history(region, days=14, route_ids=[route_id])
            latest = execute_query_one("""
                SELECT * FROM route_health_scores
                WHERE route_id = %s AND region = %s
                ORDER BY score_date DESC LIMIT 1
            """, (route_id, region))
            history = execute_query("""
                SELECT score_date, total_score, punctuality_score, frequency_score,
                       coverage_score, delay_dist_score
                FROM route_health_scores
                WHERE route_id = %s AND region = %s
                ORDER BY score_date DESC LIMIT 30
            """, (route_id, region))

        return jsonify(success_response({
            'latest': normalize_health_score_row(latest),
            'history': [normalize_health_score_row(r) for r in history]
        }))
    except Exception as e:
        return jsonify(error_response(f"获取健康度详情失败: {str(e)}", 500)), 500


@health_alerts_bp.route('/admin/recalculate-health-scores', methods=['POST'])
def recalculate_health_scores():
    """管理员触发重新计算健康度评分"""
    admin_user, err = require_admin()
    if err:
        return err
    region = request.args.get('region', 'sf')
    try:
        from scripts.calculate_health_scores import calculate_scores
        calculate_scores(region)
        record_audit_log(admin_user['user_id'], admin_user['username'],
                        'recalculate_health', f'region:{region}', {})
        return jsonify(success_response({'message': '健康度评分计算完成'}))
    except Exception as e:
        return jsonify(error_response(f"计算失败: {str(e)}", 500)), 500


# ==================== 异常检测与告警接口 ====================

@health_alerts_bp.route('/alerts/active', methods=['GET'])
def get_active_alerts():
    """获取当前活跃告警列表"""
    region = request.args.get('region', 'sf')
    try:
        from services.alert_service import ensure_alert_data
        ensure_alert_data(region, force_refresh=is_truthy_param(request.args.get('refresh')))

        rows = execute_query("""
            SELECT id, region, alert_type, entity_type, entity_id, entity_name,
                   severity, title, alert_data, triggered_at
            FROM anomaly_alerts
            WHERE region = %s AND resolved_at IS NULL
            ORDER BY
                CASE severity WHEN 'critical' THEN 1 WHEN 'high' THEN 2
                              WHEN 'medium' THEN 3 ELSE 4 END,
                triggered_at DESC
        """, (region,))
        return jsonify(success_response([dict(r) for r in rows]))
    except Exception as e:
        return jsonify(error_response(f"获取活跃告警失败: {str(e)}", 500)), 500


@health_alerts_bp.route('/alerts/history', methods=['GET'])
def get_alert_history():
    """获取历史告警记录"""
    region = request.args.get('region', 'sf')
    days = request.args.get('days', 7, type=int)
    alert_type = request.args.get('type', '')
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    try:
        from services.alert_service import ensure_alert_data
        ensure_alert_data(region, force_refresh=is_truthy_param(request.args.get('refresh')))

        where = "WHERE region = %s AND triggered_at >= (NOW() - INTERVAL '%s days')"
        params = [region, days]
        if alert_type:
            where += " AND alert_type = %s"
            params.append(alert_type)

        total_row = execute_query_one(
            f"SELECT COUNT(*) as cnt FROM anomaly_alerts {where}", tuple(params))
        total = total_row['cnt'] if total_row else 0

        rows = execute_query(f"""
            SELECT id, alert_type, entity_type, entity_id, entity_name,
                   severity, title, alert_data, triggered_at, resolved_at
            FROM anomaly_alerts {where}
            ORDER BY triggered_at DESC
            LIMIT %s OFFSET %s
        """, tuple(params) + (page_size, (page - 1) * page_size))

        return jsonify(success_response({
            'items': [dict(r) for r in rows],
            'total': total
        }))
    except Exception as e:
        return jsonify(error_response(f"获取告警历史失败: {str(e)}", 500)), 500


@health_alerts_bp.route('/alerts/<int:alert_id>/resolve', methods=['PATCH'])
def resolve_alert(alert_id):
    """手动标记告警为已解决"""
    admin_user, err = require_admin()
    if err:
        return err
    try:
        execute_write(
            "UPDATE anomaly_alerts SET resolved_at = NOW() WHERE id = %s",
            (alert_id,))
        return jsonify(success_response({'message': '告警已解决'}))
    except Exception as e:
        return jsonify(error_response(f"操作失败: {str(e)}", 500)), 500


@health_alerts_bp.route('/alerts/stats', methods=['GET'])
def get_alert_stats():
    """获取告警统计摘要"""
    region = request.args.get('region', 'sf')
    try:
        from services.alert_service import ensure_alert_data
        ensure_alert_data(region, force_refresh=is_truthy_param(request.args.get('refresh')))

        # 活跃告警计数
        active = execute_query_one(
            "SELECT COUNT(*) as cnt FROM anomaly_alerts WHERE region = %s AND resolved_at IS NULL",
            (region,))
        # 今日新增
        today = execute_query_one("""
            SELECT COUNT(*) as cnt FROM anomaly_alerts
            WHERE region = %s AND triggered_at >= CURRENT_DATE
        """, (region,))
        # 按类型统计（最近7天）
        by_type = execute_query("""
            SELECT alert_type, severity, COUNT(*) as cnt
            FROM anomaly_alerts
            WHERE region = %s AND triggered_at >= (NOW() - INTERVAL '7 days')
            GROUP BY alert_type, severity ORDER BY cnt DESC
        """, (region,))
        # 按天统计（最近7天）
        by_day = execute_query("""
            SELECT triggered_at::DATE as day, COUNT(*) as cnt
            FROM anomaly_alerts
            WHERE region = %s AND triggered_at >= (NOW() - INTERVAL '7 days')
            GROUP BY day ORDER BY day
        """, (region,))
        return jsonify(success_response({
            'active_count': active['cnt'] if active else 0,
            'today_count': today['cnt'] if today else 0,
            'by_type': [dict(r) for r in by_type],
            'by_day': [dict(r) for r in by_day]
        }))
    except Exception as e:
        return jsonify(error_response(f"获取告警统计失败: {str(e)}", 500)), 500

