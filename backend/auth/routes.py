"""
认证相关 API 路由
Blueprint prefix: /api/auth
"""

from flask import Blueprint, request, jsonify
from auth.models import get_user_by_username, verify_password, generate_token, verify_token, revoke_token, create_user
from core.audit import record_audit_log

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


def _ok(data):
    return jsonify({"code": 200, "message": "success", "data": data})


def _err(msg, code=400):
    return jsonify({"code": code, "message": msg, "data": None}), code


@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录，返回 token 和角色信息"""
    body = request.get_json(silent=True) or {}
    username = body.get('username', '').strip()
    password = body.get('password', '')

    if not username or not password:
        return _err("用户名和密码不能为空")

    user = get_user_by_username(username)
    if not user:
        record_audit_log(None, username, 'login_failed', f'user:{username}', {'reason': '账号不存在'})
        return _err("账号不存在", 404)
    if not verify_password(password, user['password_hash']):
        record_audit_log(user['id'], username, 'login_failed', f'user:{user["id"]}', {'reason': '密码错误'})
        return _err("密码错误", 401)
    if not user.get('is_active', True):
        record_audit_log(user['id'], username, 'login_failed', f'user:{user["id"]}', {'reason': '账号已停用'})
        return _err("账号已停用，请联系管理员", 403)

    role = user.get('role', 'user')
    token = generate_token(user['id'], user['username'], role)
    record_audit_log(user['id'], user['username'], 'login', f'user:{user["id"]}', {'username': user['username']})
    return _ok({"token": token, "username": user['username'], "role": role})


@auth_bp.route('/register', methods=['POST'])
def register():
    """用户注册（普通用户）"""
    body = request.get_json(silent=True) or {}
    username = body.get('username', '').strip()
    password = body.get('password', '')

    if not username or not password:
        return _err("用户名和密码不能为空")
    if not (4 <= len(username) <= 20):
        return _err("用户名长度须在 4-20 个字符之间")
    if len(password) < 6:
        return _err("密码长度不能少于 6 位")

    if get_user_by_username(username):
        return _err("用户名已存在", 409)

    create_user(username, password, role='user')
    record_audit_log(None, username, 'register', f'user:{username}', {'username': username})
    return _ok({"message": "注册成功"})


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """退出登录，使 token 失效"""
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
        user_info = verify_token(token)
        revoke_token(token)
        if user_info:
            record_audit_log(user_info['user_id'], user_info['username'], 'logout', f'user:{user_info["user_id"]}', {'username': user_info['username']})
    return _ok({"message": "已退出登录"})


@auth_bp.route('/me', methods=['GET'])
def me():
    """获取当前登录用户信息（含角色）"""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return _err("未登录", 401)

    token = auth_header[7:]
    user_info = verify_token(token)
    if not user_info:
        return _err("token 无效或已过期", 401)

    return _ok({
        "user_id": user_info['user_id'],
        "username": user_info['username'],
        "role": user_info.get('role', 'user')
    })
