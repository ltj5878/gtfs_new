#!/usr/bin/env python3
"""
生成简单实时数据脚本
"""

import random
from datetime import datetime, timedelta
from db import Database, execute_count

def main():
    print("正在生成实时数据...")

    Database.initialize()
    conn = Database.get_connection()
    cursor = conn.cursor()

    # 清空现有实时数据
    cursor.execute("DELETE FROM realtime_delay_records")
    cursor.execute("DELETE FROM realtime_vehicle_positions")
    cursor.execute("DELETE FROM system_punctuality_overview")

    current_time = datetime.now()

    # 生成一些实时延误记录
    for i in range(50):
        # 随机选择一条线路
        cursor.execute("SELECT route_id FROM routes ORDER BY RANDOM() LIMIT 1")
        route = cursor.fetchone()
        if not route:
            break

        route_id = route['route_id']
        delay_seconds = random.randint(-120, 600)  # -2分钟到10分钟

        minutes_ago = random.randint(1, 60)
        record_timestamp = current_time - timedelta(minutes=minutes_ago)

        cursor.execute("""
            INSERT INTO realtime_delay_records
            (trip_id, route_id, stop_id, stop_sequence, vehicle_id,
             scheduled_time, actual_time, record_timestamp,
             arrival_delay, departure_delay, data_source, processed)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            f"TRIP_{route_id}_{i}", route_id, f"STOP_{i}", i,
            f"VEH_{route_id}_{i}", record_timestamp, record_timestamp,
            record_timestamp, delay_seconds, 0, 'GTFS_Realtime', True
        ))

    # 生成一些车辆位置
    for i in range(20):
        cursor.execute("SELECT route_id FROM routes ORDER BY RANDOM() LIMIT 1")
        route = cursor.fetchone()
        if not route:
            break

        route_id = route['route_id']
        # 旧金山湾区坐标范围
        lat = random.uniform(37.70, 37.80)
        lng = random.uniform(-122.50, -122.35)

        minutes_ago = random.randint(1, 5)
        position_timestamp = current_time - timedelta(minutes=minutes_ago)

        cursor.execute("""
            INSERT INTO realtime_vehicle_positions
            (vehicle_id, trip_id, route_id, latitude, longitude,
             position_timestamp, record_timestamp, current_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            f"VEH_{route_id}_{i}", f"TRIP_{route_id}_{i}", route_id,
            lat, lng, position_timestamp, current_time, 1
        ))

    # 更新系统概览
    cursor.execute("""
        INSERT INTO system_punctuality_overview
        (stat_date, total_routes, total_trips, system_punctuality_rate,
         system_avg_delay_minutes, morning_peak_rate, evening_peak_rate, off_peak_rate)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        current_time.date(),
        execute_count("SELECT COUNT(*) FROM routes"),
        execute_count("SELECT COUNT(*) FROM stop_times"),
        82.56,  # 使用之前计算的系统准点率
        3.94,   # 使用之前计算的平均延误
        75.8,  # 早高峰准点率
        72.3,  # 晚高峰准点率
        81.2   # 非高峰准点率
    ))

    conn.commit()
    conn.close()

    print("✅ 实时数据生成完成!")
    print(f"- 生成了 50 条延误记录")
    print(f"- 生成了 20 个车辆位置")
    print(f"- 更新了系统概览数据")

if __name__ == "__main__":
    main()