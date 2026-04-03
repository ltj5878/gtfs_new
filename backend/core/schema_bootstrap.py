#!/usr/bin/env python3
"""
新增功能表结构兜底初始化
"""

from __future__ import annotations

import os
import threading

from core.db import Database


_LOCK = threading.Lock()
_ENSURED = False

_SCHEMA_FILES = [
    os.path.join('database', 'data_quality_schema.sql'),
    os.path.join('database', 'health_score_schema.sql'),
    os.path.join('database', 'alert_schema.sql'),
    os.path.join('database', 'carbon_schema.sql'),
    os.path.join('database', 'flow_prediction_schema.sql'),
]

_EXTRA_MIGRATIONS = [
    "ALTER TABLE user_carbon_records ADD COLUMN IF NOT EXISTS record_source VARCHAR(20) DEFAULT 'user'",
    "ALTER TABLE user_carbon_records ADD COLUMN IF NOT EXISTS ride_count INTEGER DEFAULT 1",
    "UPDATE user_carbon_records SET ride_count = 1 WHERE ride_count IS NULL",
]


def ensure_feature_schemas() -> None:
    """确保六个新增功能依赖的表结构和补充字段存在。"""
    global _ENSURED

    if _ENSURED:
        return

    with _LOCK:
        if _ENSURED:
            return

        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        conn = Database.get_connection()

        try:
            with conn.cursor() as cursor:
                for rel_path in _SCHEMA_FILES:
                    schema_path = os.path.join(backend_dir, rel_path)
                    with open(schema_path, 'r', encoding='utf-8') as f:
                        cursor.execute(f.read())

                for sql in _EXTRA_MIGRATIONS:
                    cursor.execute(sql)

            conn.commit()
            _ENSURED = True
        except Exception:
            conn.rollback()
            raise
        finally:
            Database.return_connection(conn)
