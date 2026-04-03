"""
管理后台 API 路由（运维监控/用户管理/审计追踪/数据质量）
Blueprint prefix: /api
"""

import time as _time
from flask import Blueprint, jsonify, request
from core.db import Database, execute_query, execute_query_one, execute_count, execute_write
from core.audit import record_audit_log
from auth.models import create_user as _create_user, hash_password as _hash_password, get_user_by_username as _get_user_by_username
from api.helpers import success_response, error_response, get_current_user, require_admin, is_truthy_param

admin_bp = Blueprint('admin', __name__, url_prefix='/api')

# 数据库统计缓存
_db_stats_cache = {'data': None, 'ts': 0}
_DB_STATS_CACHE_TTL = 900  # 15分钟

@admin_bp.route('/admin/db-stats', methods=['GET'])
def admin_db_stats():
    """获取数据库各表存储统计（带15分钟缓存）"""
    user, err = require_admin()
    if err:
        return err

    force_refresh = str(request.args.get('force_refresh', '')).strip().lower() in ('1', 'true', 'yes')
    now = _time.time()
    if (not force_refresh and _db_stats_cache.get('data')
            and now - _db_stats_cache.get('ts', 0) < _DB_STATS_CACHE_TTL):
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


@admin_bp.route('/admin/api-health', methods=['GET'])
def admin_api_health():
    """获取过去24小时第三方 API 调用健康度统计"""
    user, err = require_admin()
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


@admin_bp.route('/admin/data-freshness', methods=['GET'])
def admin_data_freshness():
    """获取各地区 GTFS 数据时效性信息"""
    user, err = require_admin()
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


@admin_bp.route('/admin/log-api-call', methods=['POST'])
def admin_log_api_call():
    """记录一次第三方 API 调用日志（内部接口）"""
    user, err = require_admin()
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


# ==================== 审计日志查询接口（仅管理员）====================

@admin_bp.route('/admin/audit-logs', methods=['GET'])
def admin_audit_logs():
    """获取审计日志列表（支持筛选和分页）"""
    _, err = require_admin()
    if err:
        return err

    # 分页参数
    page = max(1, int(request.args.get('page', 1)))
    page_size = min(100, max(1, int(request.args.get('page_size', 20))))

    # 筛选参数
    action = request.args.get('action', '').strip()
    username_filter = request.args.get('username', '').strip()
    start_time = request.args.get('start_time', '').strip()
    end_time = request.args.get('end_time', '').strip()

    where_clauses = []
    params = []

    if action:
        where_clauses.append("action = %s")
        params.append(action)
    if username_filter:
        where_clauses.append("username LIKE %s")
        params.append(f"%{username_filter}%")
    if start_time:
        where_clauses.append("created_at >= %s")
        params.append(start_time)
    if end_time:
        where_clauses.append("created_at <= %s")
        params.append(end_time)

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    try:
        # 总数
        total = execute_count(f"SELECT COUNT(*) FROM audit_logs WHERE {where_sql}", tuple(params))

        # 分页查询
        offset = (page - 1) * page_size
        rows = execute_query(
            f"""SELECT id, user_id, username, action, target, detail, ip_address, created_at
                FROM audit_logs WHERE {where_sql}
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s""",
            tuple(params) + (page_size, offset)
        )

        # 序列化 datetime
        for row in rows:
            if row.get('created_at'):
                row['created_at'] = row['created_at'].isoformat()

        return jsonify(success_response({
            "total": total,
            "page": page,
            "page_size": page_size,
            "list": rows
        }))
    except Exception as e:
        return jsonify(error_response(f"查询审计日志失败: {str(e)}", 500)), 500


# ==================== 用户管理接口（仅管理员）====================


@admin_bp.route('/users', methods=['GET'])
def list_users():
    """获取所有用户列表"""
    _, err = require_admin()
    if err:
        return err
    try:
        users = execute_query(
            "SELECT id, username, role, is_active, created_at FROM users ORDER BY id"
        )
        return jsonify(success_response([dict(u) for u in users]))
    except Exception as e:
        return jsonify(error_response(f"获取用户列表失败: {str(e)}", 500)), 500


@admin_bp.route('/users', methods=['POST'])
def create_user_api():
    """创建新普通用户"""
    admin_user, err = require_admin()
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
        record_audit_log(admin_user['user_id'], admin_user['username'], 'create_user', f'user:{new_id}', {'username': username, 'role': 'user'})
        return jsonify(success_response({"id": new_id, "username": username, "role": "user"}))
    except Exception as e:
        return jsonify(error_response(f"创建用户失败: {str(e)}", 500)), 500


@admin_bp.route('/users/<int:user_id>', methods=['PATCH'])
def update_user_api(user_id: int):
    """更新用户状态（启用/停用）"""
    admin_user, err = require_admin()
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
        record_audit_log(admin_user['user_id'], admin_user['username'], 'toggle_user', f'user:{user_id}', {'is_active': bool(is_active)})
        return jsonify(success_response({"message": "更新成功"}))
    except Exception as e:
        return jsonify(error_response(f"更新失败: {str(e)}", 500)), 500


@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user_api(user_id: int):
    """删除用户（不能删除自己）"""
    admin_user, err = require_admin()
    if err:
        return err
    if admin_user['user_id'] == user_id:
        return jsonify(error_response("不能删除自己", 400)), 400
    try:
        # 先查询用户名，删除后无法获取
        target_user = execute_query_one("SELECT username FROM users WHERE id = %s", (user_id,))
        target_username = target_user['username'] if target_user else str(user_id)
        execute_write("DELETE FROM users WHERE id = %s", (user_id,))
        record_audit_log(admin_user['user_id'], admin_user['username'], 'delete_user', f'user:{user_id}', {'username': target_username})
        return jsonify(success_response({"message": "删除成功"}))
    except Exception as e:
        return jsonify(error_response(f"删除失败: {str(e)}", 500)), 500


@admin_bp.route('/users/<int:user_id>/password', methods=['GET'])
def get_user_password(user_id: int):
    """查看用户密码（管理员专用，返回明文密码哈希前缀用于展示，实际返回重置后的临时密码）"""
    admin_user, err = require_admin()
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
        record_audit_log(admin_user['user_id'], admin_user['username'], 'reset_password', f'user:{user_id}', {'username': user['username']})
        return jsonify(success_response({"temp_password": temp_password, "username": user['username']}))
    except Exception as e:
        return jsonify(error_response(f"操作失败: {str(e)}", 500)), 500


@admin_bp.route('/users/<int:user_id>/password', methods=['PUT'])
def update_user_password(user_id: int):
    """修改用户密码（管理员专用）"""
    admin_user, err = require_admin()
    if err:
        return err
    data = request.get_json() or {}
    new_password = data.get('password', '')
    if len(new_password) < 6:
        return jsonify(error_response("密码长度不能少于 6 位", 400)), 400
    try:
        user = execute_query_one("SELECT id, username, role FROM users WHERE id = %s", (user_id,))
        if not user:
            return jsonify(error_response("用户不存在", 404)), 404
        if user['role'] == 'admin':
            return jsonify(error_response("不能修改管理员密码", 403)), 403
        from auth.models import hash_password as _hp
        execute_write("UPDATE users SET password_hash = %s WHERE id = %s", (_hp(new_password), user_id))
        record_audit_log(admin_user['user_id'], admin_user['username'], 'change_password', f'user:{user_id}', {'username': user['username']})
        return jsonify(success_response({"message": "密码修改成功"}))
    except Exception as e:
        return jsonify(error_response(f"修改失败: {str(e)}", 500)), 500


# ==================== 前端行为追踪接口 ====================

@admin_bp.route('/audit/track', methods=['POST'])
def audit_track():
    """前端行为追踪接口（页面访问、数据导出等）"""
    user = get_current_user()
    if not user:
        return jsonify(error_response('未登录', 401)), 401
    data = request.get_json() or {}
    action = data.get('action')
    # 只允许特定 action 类型，防止滥用
    allowed = ('page_visit', 'export_data')
    if action not in allowed:
        return jsonify(error_response('不支持的操作类型', 400)), 400
    record_audit_log(
        user_id=user['user_id'],
        username=user['username'],
        action=action,
        target=data.get('target'),
        detail=data.get('detail')
    )
    return jsonify(success_response(None))


# ==================== 换乘规划接口 ====================
@admin_bp.route('/admin/data-quality/latest', methods=['GET'])
def get_data_quality_latest():
    """获取最新数据质量检查结果"""
    admin_user, err = require_admin()
    if err:
        return err
    region = request.args.get('region', 'sf')
    try:
        check = execute_query_one("""
            SELECT id, region, check_time, total_errors, total_warnings,
                   total_infos, quality_score, check_duration_ms, feed_version
            FROM data_quality_checks
            WHERE region = %s ORDER BY check_time DESC LIMIT 1
        """, (region,))
        if not check:
            return jsonify(success_response(None))
        # 获取该次检查的问题摘要
        issues = execute_query("""
            SELECT rule_code, severity, entity_type, description, affected_count
            FROM data_quality_issues WHERE check_id = %s ORDER BY severity, rule_code
        """, (check['id'],))
        check['issues'] = [dict(i) for i in issues]
        return jsonify(success_response(dict(check)))
    except Exception as e:
        return jsonify(error_response(f"获取数据质量检查失败: {str(e)}", 500)), 500


@admin_bp.route('/admin/data-quality/issues', methods=['GET'])
def get_data_quality_issues():
    """获取数据质量问题详情列表"""
    admin_user, err = require_admin()
    if err:
        return err
    region = request.args.get('region', 'sf')
    severity = request.args.get('severity', '')
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    try:
        # 获取最新检查ID
        check = execute_query_one(
            "SELECT id FROM data_quality_checks WHERE region = %s ORDER BY check_time DESC LIMIT 1",
            (region,))
        if not check:
            return jsonify(success_response({'items': [], 'total': 0}))
        check_id = check['id']

        where_clause = "WHERE check_id = %s"
        params = [check_id]
        if severity:
            where_clause += " AND severity = %s"
            params.append(severity)

        total_row = execute_query_one(
            f"SELECT COUNT(*) as cnt FROM data_quality_issues {where_clause}", tuple(params))
        total = total_row['cnt'] if total_row else 0

        items = execute_query(f"""
            SELECT id, rule_code, severity, entity_type, entity_id,
                   description, suggestion, affected_count, example_data
            FROM data_quality_issues {where_clause}
            ORDER BY severity, rule_code
            LIMIT %s OFFSET %s
        """, tuple(params) + (page_size, (page - 1) * page_size))

        return jsonify(success_response({
            'items': [dict(i) for i in items],
            'total': total
        }))
    except Exception as e:
        return jsonify(error_response(f"获取问题详情失败: {str(e)}", 500)), 500


@admin_bp.route('/admin/data-quality/history', methods=['GET'])
def get_data_quality_history():
    """获取数据质量分数历史趋势"""
    admin_user, err = require_admin()
    if err:
        return err
    region = request.args.get('region', 'sf')
    limit = request.args.get('limit', 30, type=int)
    try:
        rows = execute_query("""
            SELECT id, check_time, total_errors, total_warnings, total_infos,
                   quality_score, check_duration_ms
            FROM data_quality_checks WHERE region = %s
            ORDER BY check_time DESC LIMIT %s
        """, (region, limit))
        return jsonify(success_response([dict(r) for r in rows]))
    except Exception as e:
        return jsonify(error_response(f"获取质量历史失败: {str(e)}", 500)), 500


@admin_bp.route('/admin/data-quality/run', methods=['POST'])
def run_data_quality_check():
    """触发数据质量检查"""
    admin_user, err = require_admin()
    if err:
        return err
    data = request.get_json(silent=True) or {}
    region = request.args.get('region', data.get('region', 'sf'))
    try:
        from scripts.data_quality_checker import run_check
        result = run_check(region)
        record_audit_log(admin_user['user_id'], admin_user['username'],
                        'run_quality_check', f'region:{region}', result)
        return jsonify(success_response(result))
    except Exception as e:
        return jsonify(error_response(f"质量检查执行失败: {str(e)}", 500)), 500


@admin_bp.route('/admin/data-quality/rules', methods=['GET'])
def get_data_quality_rules():
    """获取所有数据质量检查规则说明"""
    rules = [
        {'code': 'E001', 'severity': 'ERROR', 'description': '到站时间晚于发车时间', 'category': '时刻表'},
        {'code': 'E002', 'severity': 'ERROR', 'description': '行程引用不存在的线路ID', 'category': '引用完整性'},
        {'code': 'E003', 'severity': 'ERROR', 'description': '站点坐标超出地区合理范围', 'category': '地理数据'},
        {'code': 'E004', 'severity': 'ERROR', 'description': '行程引用不存在的服务日历ID', 'category': '引用完整性'},
        {'code': 'E005', 'severity': 'ERROR', 'description': '轨迹坐标异常跳变（>50km）', 'category': '地理数据'},
        {'code': 'W001', 'severity': 'WARNING', 'description': '线路缺少轨迹数据', 'category': '数据完整性'},
        {'code': 'W002', 'severity': 'WARNING', 'description': '相邻站点间隔时间过短', 'category': '时刻表'},
        {'code': 'W003', 'severity': 'WARNING', 'description': '服务日历已过期', 'category': '日历'},
        {'code': 'W004', 'severity': 'WARNING', 'description': '线路仅有单向数据', 'category': '数据完整性'},
        {'code': 'W005', 'severity': 'WARNING', 'description': '孤立站点（无班次经过）', 'category': '数据完整性'},
        {'code': 'W006', 'severity': 'WARNING', 'description': '线路无任何班次', 'category': '数据完整性'},
        {'code': 'I001', 'severity': 'INFO', 'description': '线路未设置颜色代码', 'category': '展示优化'},
        {'code': 'I002', 'severity': 'INFO', 'description': '站点缺少无障碍信息', 'category': '无障碍'},
        {'code': 'I003', 'severity': 'INFO', 'description': '班次未关联 block_id', 'category': '数据完整性'},
        {'code': 'I004', 'severity': 'INFO', 'description': '线路缺少长名称', 'category': '展示优化'},
    ]
    return jsonify(success_response(rules))

