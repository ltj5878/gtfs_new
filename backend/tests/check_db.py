#!/usr/bin/env python3
"""检查数据库表和数据"""

import psycopg2

# 数据库连接配置
DB_CONFIG = {
    'dbname': 'gtfs_db',
    'user': 'lvtongjie.1',
    'password': '',
    'host': 'localhost',
    'port': 5432
}

def check_tables():
    """检查准点率和实时数据相关的表"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    print("=" * 80)
    print("检查准点率相关的表")
    print("=" * 80)

    # 检查准点率相关的表
    cur.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name LIKE '%punctuality%'
        ORDER BY table_name
    """)
    punctuality_tables = cur.fetchall()

    if punctuality_tables:
        print(f"\n找到 {len(punctuality_tables)} 个准点率相关的表:")
        for table in punctuality_tables:
            print(f"  - {table[0]}")

            # 检查每个表的数据量
            cur.execute(f"SELECT COUNT(*) FROM {table[0]}")
            count = cur.fetchone()[0]
            print(f"    数据量: {count} 条")
    else:
        print("\n❌ 未找到准点率相关的表!")

    print("\n" + "=" * 80)
    print("检查实时数据相关的表")
    print("=" * 80)

    # 检查实时数据相关的表
    cur.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name LIKE '%realtime%'
        ORDER BY table_name
    """)
    realtime_tables = cur.fetchall()

    if realtime_tables:
        print(f"\n找到 {len(realtime_tables)} 个实时数据相关的表:")
        for table in realtime_tables:
            print(f"  - {table[0]}")

            # 检查每个表的数据量
            cur.execute(f"SELECT COUNT(*) FROM {table[0]}")
            count = cur.fetchone()[0]
            print(f"    数据量: {count} 条")
    else:
        print("\n❌ 未找到实时数据相关的表!")

    print("\n" + "=" * 80)
    print("检查所有表")
    print("=" * 80)

    # 列出所有表
    cur.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)
    all_tables = cur.fetchall()

    print(f"\n数据库中共有 {len(all_tables)} 个表:")
    for table in all_tables:
        cur.execute(f"SELECT COUNT(*) FROM {table[0]}")
        count = cur.fetchone()[0]
        print(f"  - {table[0]}: {count} 条数据")

    cur.close()
    conn.close()

if __name__ == '__main__':
    try:
        check_tables()
    except Exception as e:
        print(f"\n❌ 错误: {e}")
