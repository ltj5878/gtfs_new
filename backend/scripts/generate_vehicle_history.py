#!/usr/bin/env python3
"""
生成模拟车辆历史位置数据
基于 GTFS 静态数据（routes + stops + stop_times）生成沿途位置序列
用于历史数据回放功能

优化策略：
- 覆盖全天运营时段（6:00-23:00），按小时分桶选取 trip
- 每个小时至少选 15 个 trip，确保任何一分钟都有 10+ 辆车在线
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


def generate_history(region, date_str, trips_per_hour=15):
    """为指定地区和日期生成车辆历史位置数据

    策略：将 6:00-23:00 按小时分桶，每个小时随机选取 trips_per_hour 个 trip，
    确保全天每个时刻都有足够车辆在线。
    """
    Database.initialize()
    target_date = datetime.strptime(date_str, '%Y-%m-%d').date()

    print(f"正在为 {region} 地区生成 {date_str} 的车辆历史数据（每小时 {trips_per_hour} 个 trip）...")

    # 按小时分桶选取 trip，确保全天覆盖
    all_trips = []
    for hour in range(6, 23):
        hour_start = f"{hour:02d}:00:00"
        hour_end = f"{hour + 1:02d}:00:00"
        trips = execute_query("""
            WITH trip_first_dep AS (
                SELECT t.trip_id, t.route_id,
                       MIN(st.departure_time) AS first_dep
                FROM trips t
                JOIN stop_times st ON t.region = st.region AND t.trip_id = st.trip_id
                JOIN stops s ON st.region = s.region AND st.stop_id = s.stop_id
                WHERE t.region = %s AND s.stop_lat IS NOT NULL AND s.stop_lon IS NOT NULL
                GROUP BY t.trip_id, t.route_id
            )
            SELECT trip_id, route_id FROM trip_first_dep
            WHERE first_dep >= %s AND first_dep < %s
            ORDER BY random()
            LIMIT %s
        """, (region, hour_start, hour_end, trips_per_hour))
        all_trips.extend(trips)
        if trips:
            print(f"  {hour:02d}:00 时段选取了 {len(trips)} 个 trip")

    if not all_trips:
        print("未找到可用的 trip 数据")
        return

    print(f"共选取 {len(all_trips)} 个 trip，开始生成位置数据...")

    conn = Database.get_connection()
    cursor = conn.cursor()
    total_points = 0

    for idx, trip in enumerate(all_trips):
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

        if (idx + 1) % 20 == 0:
            conn.commit()
            print(f"  已处理 {idx + 1}/{len(all_trips)} 个 trip，累计 {total_points} 个位置点")

    conn.commit()
    Database.return_connection(conn)
    print(f"完成！共生成 {total_points} 个车辆位置点")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='生成模拟车辆历史位置数据')
    parser.add_argument('--region', default='sf', help='地区代码 (sf/nyc/sydney)')
    parser.add_argument('--date', default=datetime.now().strftime('%Y-%m-%d'), help='日期 (YYYY-MM-DD)')
    parser.add_argument('--trips-per-hour', type=int, default=15, help='每小时选取的 trip 数')
    parser.add_argument('--clean', action='store_true', help='清除已有数据后重新生成')
    args = parser.parse_args()

    if args.clean:
        Database.initialize()
        conn = Database.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM realtime_vehicle_positions WHERE region = %s", (args.region,))
        deleted = cursor.rowcount
        conn.commit()
        Database.return_connection(conn)
        print(f"已清除 {args.region} 的 {deleted} 条历史数据")

    generate_history(args.region, args.date, args.trips_per_hour)
