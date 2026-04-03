"""
API 共享辅助函数
"""

from flask import request, jsonify
from auth.models import verify_token
from typing import Dict, Any


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


def is_truthy_param(value) -> bool:
    """判断请求参数是否为真值"""
    return str(value).strip().lower() in ('1', 'true', 'yes', 'y', 'on')


def get_current_user():
    """从请求头提取当前登录用户信息，未登录返回 None"""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None
    token = auth_header[7:]
    return verify_token(token)


def require_admin():
    """校验当前用户是否为管理员，返回 (user, error_response)"""
    user = get_current_user()
    if not user:
        return None, (jsonify(error_response("请先登录", 401)), 401)
    if user.get('role') != 'admin':
        return None, (jsonify(error_response("权限不足，仅管理员可访问", 403)), 403)
    return user, None


def normalize_health_score_row(row):
    """规范化健康度评分行数据"""
    if not row:
        return None
    data = dict(row)
    for key in (
        'punctuality_score',
        'frequency_score',
        'coverage_score',
        'delay_dist_score',
        'total_score',
    ):
        if data.get(key) is not None:
            data[key] = round(float(data[key]), 2)
    return data
