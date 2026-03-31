#!/usr/bin/env python3
"""
审计日志工具函数
提供统一的审计日志记录接口，用于记录管理员和用户的关键操作
"""

import json
from flask import request
from core.db import execute_write


def record_audit_log(user_id, username, action, target=None, detail=None):
    """
    记录一条审计日志

    Args:
        user_id:  操作用户ID，未登录操作传 None
        username: 操作用户名，未登录传 None
        action:   操作类型字符串，如 'login', 'create_user'
        target:   操作对象描述，如 'user:5', 'punctuality:sf'
        detail:   dict，操作详情，会序列化为 JSON 存储
    """
    ip = request.remote_addr or ''
    detail_json = json.dumps(detail, ensure_ascii=False) if detail else '{}'
    try:
        execute_write(
            """INSERT INTO audit_logs (user_id, username, action, target, detail, ip_address)
               VALUES (%s, %s, %s, %s, %s::jsonb, %s)""",
            (user_id, username, action, target, detail_json, ip)
        )
    except Exception as e:
        # 审计日志写入失败不应阻断业务流程，仅打印错误
        print(f"审计日志写入失败: {e}")
