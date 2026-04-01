#!/usr/bin/env python3
"""
生成模拟车辆历史位置数据
基于 GTFS 静态数据（routes + stops + stop_times）生成沿途位置序列
用于历史数据回放功能
"""

import sys
import os
import argparse
import random
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from core.db import Database, execute_query


def parse_gtfs_time(time_str):
    """解析 GTFS 时间格式（可能超过 24:00:00）"""
    parts = time_str.strip().split(':')
    h, m, s = int(parts[0]), int(parts[1]), int(parts[2]) if len(parts) > 2 else 0
    return h * 3600 + m * 60 + s


def interpolate(lat1, lon1, lat2, lon2, ratio):
    """线性插值两点间的经纬度"""
    return lat1 + (lat2 - lat1) * ratio, lon1 + (lon2 - lon1) * ratio


def calc_bearing(lat1, lon1, lat2, lon2):
    """简单方向角计算"""
    import math
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    angle = math.degrees(math.atan2(dlon, dlat))
    return (angle + 360) % 360


def generate_history(region, date_str, max_trips=50):
    """为指定地区和日期生成车辆历史位置数据"""
    Database.initialize()
    target_date = datetime.strptime(date_str, '%Y-%m-%d').date()

    print(f"正在为 {region} 地区生成 {date_str} 的车辆历史数据...")

    # 获取有站点坐标的 trip + stop_times 数据
    trips = execute_query("""
        SELECT DISTINCT t.trip_id, t.route_id
        FROM trips t
        JOIN stop_times st ON t.region = st.region AND t.trip_id = st.trip_id
        JOIN stops s ON st.region = s.region AND st.stop_id = s.stop_id
        WHERE t.region = %s AND s.stop_lat IS NOT NULL AND s.stop_lon IS NOT NULL
        LIMIT %s
    """, (region, max_trips))

    if not trips:
        print("未找到可用的 trip 数据")
        return

    print(f"找到 {len(trips)} 个 trip，开始生成位置数据...")

    conn = Database.get_connection()
    cursor = conn.cursor()
    total_points = 0

    for idx, trip in enumerate(trips):
        trip_id = trip['trip_id']
        route_id = trip['route_id']
        vehicle_id = f"V_{region}_{idx:04d}"

        # 获取该 trip 的站点序列（含坐标和时间）
        stops = execute_query("""
            SELECT st.stop_id, st.departure_time, s.stop_lat, s.stop_lon, st.stop_sequence
            FROM stop_times st
            JOIN stops s ON st.region = s.region AND st.stop_id = s.stop_id
            WHERE st.region = %s AND st.trip_id = %s
              AND s.stop_lat IS NOT NULL AND s.stop_lon IS NOT NULL
            ORDER BY st.stop_sequence
        """, (region, trip_id))

        if len(stops) < 2:
            continue

        # 在相邻站点间每分钟插值一个位置点
        for i in range(len(stops) - 1):
            s1, s2 = stops[i], stops[i + 1]
            t1 = parse_gtfs_time(s1['departure_time'])
            t2 = parse_gtfs_time(s2['departure_time'])

            if t2 <= t1:
                continue

            duration = t2 - t1
            steps = max(1, duration // 60)  # 每分钟一个点

            lat1, lon1 = float(s1['stop_lat']), float(s1['stop_lon'])
            lat2, lon2 = float(s2['stop_lat']), float(s2['stop_lon'])
            bearing = calc_bearing(lat1, lon1, lat2, lon2)

            for step in range(steps):
                ratio = step / steps
                lat, lon = interpolate(lat1, lon1, lat2, lon2, ratio)

                # 添加微小随机偏移模拟真实 GPS
                lat += random.uniform(-0.0001, 0.0001)
                lon += random.uniform(-0.0001, 0.0001)

                seconds = t1 + int(duration * ratio)
                hours = (seconds // 3600) % 24
                minutes = (seconds % 3600) // 60
                secs = seconds % 60
                ts = datetime(target_date.year, target_date.month, target_date.day,
                              hours, minutes, secs)

                speed = random.uniform(10, 45)

                cursor.execute("""
                    INSERT INTO realtime_vehicle_positions
                    (region, vehicle_id, trip_id, route_id, latitude, longitude,
                     bearing, speed, position_timestamp, current_status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (region, vehicle_id, trip_id, route_id,
                      round(lat, 8), round(lon, 8),
                      round(bearing, 2), round(speed, 2),
                      ts, 2))
                total_points += 1

        if (idx + 1) % 10 == 0:
            conn.commit()
            print(f"  已处理 {idx + 1}/{len(trips)} 个 trip，累计 {total_points} 个位置点")

    conn.commit()
    Database.return_connection(conn)
    print(f"完成！共生成 {total_points} 个车辆位置点")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='生成模拟车辆历史位置数据')
    parser.add_argument('--region', default='sf', help='地区代码 (sf/nyc/sydney)')
    parser.add_argument('--date', default=datetime.now().strftime('%Y-%m-%d'), help='日期 (YYYY-MM-DD)')
    parser.add_argument('--max-trips', type=int, default=50, help='最大 trip 数量')
    args = parser.parse_args()

    generate_history(args.region, args.date, args.max_trips)
