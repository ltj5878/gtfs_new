#!/usr/bin/env python3
"""检查数据库详细数据"""

import psycopg2
import json

DB_CONFIG = {
    'dbname': 'gtfs_db',
    'user': 'lvtongjie.1',
    'password': '',
    'host': 'localhost',
    'port': 5432
}

def check_route_punctuality():
    """检查线路准点率数据"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    print("=" * 80)
    print("检查 route_daily_punctuality 表结构和数据")
    print("=" * 80)

    # 查看表结构
    cur.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'route_daily_punctuality'
        ORDER BY ordinal_position
    """)
    columns = cur.fetchall()
    print("\n表字段:")
    for col in columns:
        print(f"  - {col[0]}: {col[1]}")

    # 查看示例数据
    cur.execute("""
        SELECT *
        FROM route_daily_punctuality
        LIMIT 3
    """)
    rows = cur.fetchall()
    col_names = [desc[0] for desc in cur.description]

    print("\n示例数据:")
    for row in rows:
        data = dict(zip(col_names, row))
        print(json.dumps(data, indent=2, default=str))
        print("-" * 40)

    cur.close()
    conn.close()

def check_stop_punctuality():
    """检查站点准点率数据"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    print("\n" + "=" * 80)
    print("检查 stop_daily_punctuality 表结构和数据")
    print("=" * 80)

    # 查看表结构
    cur.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'stop_daily_punctuality'
        ORDER BY ordinal_position
    """)
    columns = cur.fetchall()
    print("\n表字段:")
    for col in columns:
        print(f"  - {col[0]}: {col[1]}")

    # 查看示例数据
    cur.execute("""
        SELECT *
        FROM stop_daily_punctuality
        LIMIT 3
    """)
    rows = cur.fetchall()
    col_names = [desc[0] for desc in cur.description]

    print("\n示例数据:")
    for row in rows:
        data = dict(zip(col_names, row))
        print(json.dumps(data, indent=2, default=str))
        print("-" * 40)

    cur.close()
    conn.close()

def check_realtime_delays():
    """检查实时延误数据"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    print("\n" + "=" * 80)
    print("检查 realtime_delay_records 表结构和数据")
    print("=" * 80)

    # 查看表结构
    cur.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'realtime_delay_records'
        ORDER BY ordinal_position
    """)
    columns = cur.fetchall()
    print("\n表字段:")
    for col in columns:
        print(f"  - {col[0]}: {col[1]}")

    # 查看示例数据
    cur.execute("""
        SELECT *
        FROM realtime_delay_records
        LIMIT 5
    """)
    rows = cur.fetchall()
    col_names = [desc[0] for desc in cur.description]

    print("\n示例数据:")
    for row in rows:
        data = dict(zip(col_names, row))
        print(json.dumps(data, indent=2, default=str))
        print("-" * 40)

    cur.close()
    conn.close()

if __name__ == '__main__':
    try:
        check_route_punctuality()
        check_stop_punctuality()
        check_realtime_delays()
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
