"""
用户功能 API 路由（收藏/订阅/通知）
Blueprint prefix: /api
"""

from flask import Blueprint, jsonify, request
from core.db import Database, execute_query, execute_query_one, execute_count, execute_write
from core.audit import record_audit_log
from api.helpers import success_response, error_response, get_current_user, require_admin

user_features_bp = Blueprint('user_features', __name__, url_prefix='/api')

@user_features_bp.route('/favorites', methods=['GET'])
def get_favorites():
    """获取当前用户的所有收藏"""
    user = get_current_user()
    if not user:
        return jsonify(error_response("请先登录", 401)), 401
    rows = execute_query(
        "SELECT id, region, item_type, item_id, item_name, created_at FROM user_favorites WHERE user_id = %s ORDER BY created_at DESC",
        (user['user_id'],)
    )
    return jsonify(success_response(rows))


@user_features_bp.route('/favorites', methods=['POST'])
def add_favorite():
    """添加收藏"""
    user = get_current_user()
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


@user_features_bp.route('/favorites', methods=['DELETE'])
def remove_favorite():
    """取消收藏"""
    user = get_current_user()
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


# ==================== 订阅相关接口 ====================

@user_features_bp.route('/subscriptions', methods=['GET'])
def get_subscriptions():
    """获取当前用户的所有线路订阅"""
    user = get_current_user()
    if not user:
        return jsonify(error_response("请先登录", 401)), 401
    rows = execute_query(
        """SELECT s.id, s.route_id, s.region, s.threshold, s.created_at,
                  r.route_short_name, r.route_long_name
           FROM user_subscriptions s
           LEFT JOIN routes r ON s.route_id = r.route_id AND s.region = r.region
           WHERE s.user_id = %s ORDER BY s.created_at DESC""",
        (user['user_id'],)
    )
    return jsonify(success_response(rows))


@user_features_bp.route('/subscriptions', methods=['POST'])
def add_subscription():
    """添加或更新线路订阅"""
    user = get_current_user()
    if not user:
        return jsonify(error_response("请先登录", 401)), 401
    data = request.get_json() or {}
    region = data.get('region', '').strip()
    route_id = data.get('route_id', '').strip()
    threshold = min(100, max(0, float(data.get('threshold', 80))))
    if not region or not route_id:
        return jsonify(error_response("缺少 region 或 route_id", 400)), 400
    try:
        row = execute_write(
            """INSERT INTO user_subscriptions (user_id, region, route_id, threshold)
               VALUES (%s, %s, %s, %s)
               ON CONFLICT (user_id, region, route_id)
               DO UPDATE SET threshold = EXCLUDED.threshold, updated_at = CURRENT_TIMESTAMP
               RETURNING id""",
            (user['user_id'], region, route_id, threshold)
        )
        return jsonify(success_response({"id": row['id'] if row else None, "message": "订阅成功"}))
    except Exception as e:
        return jsonify(error_response(f"订阅失败: {str(e)}", 500)), 500


@user_features_bp.route('/subscriptions', methods=['DELETE'])
def remove_subscription():
    """取消线路订阅"""
    user = get_current_user()
    if not user:
        return jsonify(error_response("请先登录", 401)), 401
    region = request.args.get('region', '').strip()
    route_id = request.args.get('route_id', '').strip()
    if not region or not route_id:
        return jsonify(error_response("缺少 region 或 route_id", 400)), 400
    execute_write(
        "DELETE FROM user_subscriptions WHERE user_id = %s AND region = %s AND route_id = %s",
        (user['user_id'], region, route_id)
    )
    return jsonify(success_response({"message": "已取消订阅"}))


@user_features_bp.route('/subscriptions/check', methods=['GET'])
def check_subscription():
    """检查当前用户是否订阅了某条线路"""
    user = get_current_user()
    if not user:
        return jsonify(success_response({"subscribed": False, "threshold": None}))
    region = request.args.get('region', '').strip()
    route_id = request.args.get('route_id', '').strip()
    if not region or not route_id:
        return jsonify(success_response({"subscribed": False, "threshold": None}))
    row = execute_query_one(
        "SELECT threshold FROM user_subscriptions WHERE user_id = %s AND region = %s AND route_id = %s",
        (user['user_id'], region, route_id)
    )
    if row:
        return jsonify(success_response({"subscribed": True, "threshold": float(row['threshold'])}))
    return jsonify(success_response({"subscribed": False, "threshold": None}))


# ==================== 通知相关接口 ====================

@user_features_bp.route('/notifications', methods=['GET'])
def get_notifications():
    """获取当前用户的通知列表（分页）"""
    user = get_current_user()
    if not user:
        return jsonify(error_response("请先登录", 401)), 401
    page = max(1, int(request.args.get('page', 1)))
    page_size = min(100, max(1, int(request.args.get('page_size', 20))))
    offset = (page - 1) * page_size
    uid = user['user_id']
    total = execute_count("SELECT COUNT(*) FROM notifications WHERE user_id = %s", (uid,))
    unread_count = execute_count("SELECT COUNT(*) FROM notifications WHERE user_id = %s AND is_read = FALSE", (uid,))
    rows = execute_query(
        """SELECT id, type, title, content, route_id, region, is_read, created_at
           FROM notifications WHERE user_id = %s
           ORDER BY created_at DESC LIMIT %s OFFSET %s""",
        (uid, page_size, offset)
    )
    for row in rows:
        if row.get('created_at'):
            row['created_at'] = row['created_at'].isoformat()
    return jsonify(success_response({"items": rows, "unread_count": unread_count, "total": total}))


@user_features_bp.route('/notifications/unread-count', methods=['GET'])
def get_unread_count():
    """获取未读通知数量（轻量级，供前端轮询）"""
    user = get_current_user()
    if not user:
        return jsonify(success_response({"unread_count": 0}))
    count = execute_count("SELECT COUNT(*) FROM notifications WHERE user_id = %s AND is_read = FALSE", (user['user_id'],))
    return jsonify(success_response({"unread_count": count}))


@user_features_bp.route('/notifications/read', methods=['PATCH'])
def mark_notifications_read():
    """标记通知为已读（单条或全部）"""
    user = get_current_user()
    if not user:
        return jsonify(error_response("请先登录", 401)), 401
    data = request.get_json() or {}
    uid = user['user_id']
    if data.get('all'):
        execute_write("UPDATE notifications SET is_read = TRUE WHERE user_id = %s AND is_read = FALSE", (uid,))
        return jsonify(success_response({"message": "已全部标记为已读"}))
    nid = data.get('id')
    if nid:
        execute_write("UPDATE notifications SET is_read = TRUE WHERE id = %s AND user_id = %s", (nid, uid))
        return jsonify(success_response({"message": "已标记为已读"}))
    return jsonify(error_response("缺少 id 或 all 参数", 400)), 400


@user_features_bp.route('/notifications/announcement', methods=['POST'])
def publish_announcement():
    """管理员发布系统公告（为每个活跃用户创建一条通知）"""
    admin_user, err = require_admin()
    if err:
        return err
    data = request.get_json() or {}
    title = data.get('title', '').strip()
    content = data.get('content', '').strip()
    if not title:
        return jsonify(error_response("公告标题不能为空", 400)), 400
    try:
        conn = Database.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO notifications (user_id, type, title, content)
               SELECT id, 'announcement', %s, %s FROM users WHERE is_active = TRUE""",
            (title, content)
        )
        count = cursor.rowcount
        conn.commit()
        Database.return_connection(conn)
        record_audit_log(admin_user['user_id'], admin_user['username'], 'publish_announcement', f'announcement:{title[:50]}', {'title': title, 'user_count': count})
        return jsonify(success_response({"message": f"公告已发布给 {count} 位用户", "count": count}))
    except Exception as e:
        return jsonify(error_response(f"发布失败: {str(e)}", 500)), 500


@user_features_bp.route('/notifications/check-punctuality', methods=['POST'])
def check_punctuality_alerts():
    """检查准点率并为订阅用户生成告警通知"""
    user = get_current_user()
    if not user:
        return jsonify(error_response("请先登录", 401)), 401
    try:
        conn = Database.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO notifications (user_id, type, title, content, route_id, region)
            SELECT
                s.user_id,
                'alert',
                '线路准点率告警: ' || COALESCE(r.route_short_name, s.route_id),
                '线路 ' || COALESCE(r.route_long_name, s.route_id)
                    || ' 在 ' || rdp.stat_date
                    || ' 的准点率为 ' || ROUND(rdp.punctuality_rate, 1) || '%%'
                    || '，低于您设定的阈值 ' || s.threshold || '%%',
                s.route_id,
                s.region
            FROM user_subscriptions s
            JOIN route_daily_punctuality rdp
                ON s.region = rdp.region AND s.route_id = rdp.route_id
            LEFT JOIN routes r
                ON s.region = r.region AND s.route_id = r.route_id
            WHERE rdp.stat_date = (
                SELECT MAX(stat_date) FROM route_daily_punctuality rdp2
                WHERE rdp2.region = s.region AND rdp2.route_id = s.route_id
            )
            AND rdp.punctuality_rate < s.threshold
            AND NOT EXISTS (
                SELECT 1 FROM notifications n
                WHERE n.user_id = s.user_id
                  AND n.type = 'alert'
                  AND n.route_id = s.route_id
                  AND n.region = s.region
                  AND n.created_at::date = rdp.stat_date
            )
        """)
        count = cursor.rowcount
        conn.commit()
        Database.return_connection(conn)
        return jsonify(success_response({"new_alerts": count, "message": f"检查完成，新增 {count} 条告警"}))
    except Exception as e:
        return jsonify(error_response(f"检查失败: {str(e)}", 500)), 500

