"""
分析功能 API 路由（换乘规划/可达性分析/客流预测/智能推荐）
Blueprint prefix: /api
"""

from flask import Blueprint, jsonify, request
from core.db import execute_query, execute_query_one
from api.helpers import success_response, error_response, get_current_user, is_truthy_param

analysis_bp = Blueprint('analysis', __name__, url_prefix='/api')

@analysis_bp.route('/planner/transfer', methods=['GET'])
def plan_transfer():
    """换乘规划接口：根据起终点站返回候选换乘方案"""
    from_stop_id = request.args.get('from_stop_id', '').strip()
    to_stop_id = request.args.get('to_stop_id', '').strip()
    region = request.args.get('region', 'sf').strip()
    strategy = request.args.get('strategy', 'min_transfer').strip()

    if not from_stop_id or not to_stop_id:
        return jsonify(error_response("缺少必要参数：from_stop_id 和 to_stop_id", 400)), 400

    if strategy not in ('min_transfer', 'min_time'):
        strategy = 'min_transfer'

    try:
        from business_logic.transfer_planner import find_transfer_plans
        result = find_transfer_plans(from_stop_id, to_stop_id, region, strategy)

        if 'error' in result:
            return jsonify(error_response(result['error'], 400)), 400

        return jsonify(success_response(result))
    except Exception as e:
        return jsonify(error_response(f"换乘规划失败: {str(e)}", 500)), 500


@analysis_bp.route('/analysis/reachability', methods=['GET'])
def get_stop_reachability():
    """站点可达性分析接口"""
    stop_id = request.args.get('stop_id', '').strip()
    region = request.args.get('region', '').strip()
    max_min = request.args.get('max_min', 60, type=int)
    depart = request.args.get('depart', '08:00:00').strip()

    if not stop_id:
        return jsonify(error_response('缺少必要参数：stop_id', 400)), 400
    if not region:
        return jsonify(error_response('缺少必要参数：region', 400)), 400

    if max_min is None:
        max_min = 60

    try:
        from business_logic.reachability import find_reachable_stops
        result = find_reachable_stops(
            origin_stop_id=stop_id,
            region=region,
            max_minutes=max_min,
            depart_time=depart
        )

        if 'error' in result:
            return jsonify(error_response(result['error'], 400)), 400

        return jsonify(success_response(result))
    except ValueError as e:
        return jsonify(error_response(f'参数错误: {str(e)}', 400)), 400
    except Exception as e:
        return jsonify(error_response(f'站点可达性分析失败: {str(e)}', 500)), 500


# ==================== 数据质量审查接口 ====================
@analysis_bp.route('/stops/<stop_id>/flow-prediction', methods=['GET'])
def get_stop_flow_prediction(stop_id):
    """获取站点全天客流预测"""
    region = request.args.get('region', 'sf')
    day_type = request.args.get('day_type', 'weekday')
    try:
        from services.flow_prediction_service import get_stop_flow_prediction_data
        rows = get_stop_flow_prediction_data(
            stop_id,
            region,
            day_type,
            refresh=is_truthy_param(request.args.get('refresh'))
        )
        return jsonify(success_response(rows))
    except Exception as e:
        return jsonify(error_response(f"获取客流预测失败: {str(e)}", 500)), 500

@analysis_bp.route('/stops/<stop_id>/best-time', methods=['GET'])
def get_stop_best_time(stop_id):
    """推荐最佳到站时间（低客流时段）"""
    region = request.args.get('region', 'sf')
    day_type = request.args.get('day_type', 'weekday')
    try:
        from services.flow_prediction_service import get_stop_flow_prediction_data
        predictions = get_stop_flow_prediction_data(
            stop_id,
            region,
            day_type,
            refresh=is_truthy_param(request.args.get('refresh'))
        )
        if not predictions:
            return jsonify(success_response([]))

        # 找出有班次的时段中客流指数最低的 top 3
        with_service = [p for p in predictions if p['scheduled_trips'] > 0]
        with_service.sort(key=lambda x: x['predicted_flow_index'])
        best = with_service[:3] if with_service else []

        return jsonify(success_response(best))
    except Exception as e:
        return jsonify(error_response(f"获取最佳时间失败: {str(e)}", 500)), 500


@analysis_bp.route('/stops/flow-heatmap', methods=['GET'])
def get_stops_flow_heatmap():
    """获取所有站点当前时刻客流热力图数据"""
    region = request.args.get('region', 'sf')
    hour = request.args.get('hour', None, type=int)
    day_type = request.args.get('day_type', 'weekday')
    try:
        from services.flow_prediction_service import get_flow_heatmap_data
        rows = get_flow_heatmap_data(region, hour=hour, day_type=day_type)
        return jsonify(success_response(rows))
    except Exception as e:
        return jsonify(error_response(f"获取热力图数据失败: {str(e)}", 500)), 500


# ==================== 智能行程推荐接口 ====================
@analysis_bp.route('/recommendations', methods=['GET'])
def get_recommendations():
    """获取个性化行程推荐"""
    user = get_current_user()
    if not user:
        return jsonify(error_response("请先登录", 401)), 401
    region = request.args.get('region', 'sf')
    limit = request.args.get('limit', 5, type=int)
    try:
        # 从收藏中获取偏好线路
        fav_routes = execute_query("""
            SELECT item_id
            FROM user_favorites
            WHERE user_id = %s AND item_type = 'route' AND region = %s
        """, (user['user_id'], region))
        fav_ids = [f['item_id'] for f in fav_routes]

        # 从审计日志获取高频访问线路
        freq_routes = execute_query("""
            SELECT target as route_path, COUNT(*) as freq
            FROM audit_logs
            WHERE user_id = %s AND action = 'page_visit'
              AND target LIKE '/routes/%%'
              AND created_at > NOW() - INTERVAL '30 days'
            GROUP BY target ORDER BY freq DESC LIMIT 10
        """, (user['user_id'],))

        # 提取路由ID
        candidate_ids = set(fav_ids)
        for fr in freq_routes:
            path = fr['route_path']
            if path.startswith('/routes/'):
                rid = path.replace('/routes/', '').split('?')[0]
                candidate_ids.add(rid)

        if not candidate_ids:
            # 没有个性化数据时推荐准点率最高的线路
            top_routes = execute_query("""
                SELECT r.route_id, r.route_short_name, r.route_long_name, r.route_type,
                       rdp.punctuality_rate
                FROM routes r
                LEFT JOIN route_daily_punctuality rdp ON r.route_id = rdp.route_id
                    AND r.region = rdp.region AND rdp.stat_date = (
                        SELECT MAX(stat_date) FROM route_daily_punctuality WHERE region = %s
                    )
                WHERE r.region = %s
                ORDER BY rdp.punctuality_rate DESC NULLS LAST
                LIMIT %s
            """, (region, region, limit))
            recommendations = []
            for r in top_routes:
                recommendations.append({
                    'route_id': r['route_id'],
                    'route_short_name': r['route_short_name'],
                    'route_long_name': r['route_long_name'],
                    'route_type': r['route_type'],
                    'punctuality_rate': float(r['punctuality_rate']) if r['punctuality_rate'] else None,
                    'reason': '准点率表现优秀',
                    'score': float(r['punctuality_rate']) if r['punctuality_rate'] else 0
                })
            return jsonify(success_response(recommendations[:limit]))

        # 查询候选线路的详情和准点率
        placeholders = ','.join(['%s'] * len(candidate_ids))
        candidates = execute_query(f"""
            SELECT r.route_id, r.route_short_name, r.route_long_name, r.route_type,
                   rdp.punctuality_rate, rdp.total_trips,
                   CASE WHEN r.route_id = ANY(%s::text[]) THEN 20 ELSE 0 END as fav_bonus
            FROM routes r
            LEFT JOIN route_daily_punctuality rdp ON r.route_id = rdp.route_id
                AND r.region = rdp.region AND rdp.stat_date = (
                    SELECT MAX(stat_date) FROM route_daily_punctuality WHERE region = %s
                )
            WHERE r.region = %s AND r.route_id IN ({placeholders})
        """, (list(fav_ids), region, region) + tuple(candidate_ids))

        recommendations = []
        for c in candidates:
            rate = float(c['punctuality_rate']) if c['punctuality_rate'] else 70
            fav_bonus = c['fav_bonus'] or 0
            score = rate + fav_bonus
            reason = '已收藏线路' if c['route_id'] in fav_ids else '近期常浏览'
            if rate >= 90:
                reason += '，准点率优秀'
            recommendations.append({
                'route_id': c['route_id'],
                'route_short_name': c['route_short_name'],
                'route_long_name': c['route_long_name'],
                'route_type': c['route_type'],
                'punctuality_rate': rate,
                'reason': reason,
                'score': score
            })

        recommendations.sort(key=lambda x: x['score'], reverse=True)
        return jsonify(success_response(recommendations[:limit]))
    except Exception as e:
        return jsonify(error_response(f"获取推荐失败: {str(e)}", 500)), 500

