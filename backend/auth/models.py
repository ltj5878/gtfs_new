"""
用户认证模型和工具函数
使用标准库实现，无需额外依赖
"""

import hashlib
import secrets
import time
from core.db import execute_query_one, execute_query

# 内存中存储 token（重启后失效）
_token_store = {}


def hash_password(plain: str) -> str:
    """使用 pbkdf2_hmac 哈希密码"""
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac('sha256', plain.encode(), salt.encode(), 100000)
    return f"{salt}:{dk.hex()}"


def verify_password(plain: str, hashed: str) -> bool:
    """验证密码"""
    try:
        salt, dk_hex = hashed.split(':', 1)
        dk = hashlib.pbkdf2_hmac('sha256', plain.encode(), salt.encode(), 100000)
        return dk.hex() == dk_hex
    except Exception:
        return False


def get_user_by_username(username: str):
    """根据用户名查询用户"""
    return execute_query_one(
        "SELECT id, username, password_hash FROM users WHERE username = %s",
        (username,)
    )


def init_default_user():
    """若 users 表为空则插入默认 admin 账号"""
    try:
        count_row = execute_query_one("SELECT COUNT(*) as cnt FROM users")
        if count_row and count_row['cnt'] == 0:
            from core.db import Database
            conn = Database.get_connection()
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
                        ('admin', hash_password('admin'))
                    )
                conn.commit()
                print("已创建默认账号 admin/admin")
            finally:
                Database.return_connection(conn)
    except Exception as e:
        print(f"初始化默认用户失败: {e}")


def create_user(username: str, password: str) -> int:
    """创建新用户，返回新用户 id"""
    from core.db import Database
    conn = Database.get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO users (username, password_hash) VALUES (%s, %s) RETURNING id",
                (username, hash_password(password))
            )
            row = cur.fetchone()
        conn.commit()
        return row[0]
    finally:
        Database.return_connection(conn)


def generate_token(user_id: int, username: str) -> str:
    """生成 token 并存入内存"""
    token = secrets.token_urlsafe(32)
    _token_store[token] = {
        'user_id': user_id,
        'username': username,
        'created_at': time.time()
    }
    return token


def verify_token(token: str):
    """验证 token，返回用户信息或 None"""
    return _token_store.get(token)


def revoke_token(token: str):
    """使 token 失效"""
    _token_store.pop(token, None)
