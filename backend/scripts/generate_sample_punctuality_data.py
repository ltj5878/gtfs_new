#!/usr/bin/env python3
"""
生成示例准点率数据脚本
为测试和演示目的生成模拟的准点率数据
支持 --region sf|nyc|sydney 参数
"""

import random
import sys
import os
import argparse
from datetime import datetime, timedelta

# 将 backend 目录加入 sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.db import Database, execute_query, execute_query_one, execute_count


def generate_sample_routes(region):
    """生成示例线路准点率数据"""
    print(f"正在生成示例线路准点率数据 (region={region})...")

    try:
        conn = Database.get_connection()
        cursor = conn.cursor()

        # 获取现有线路
        routes_query = "SELECT route_id, route_short_name, route_long_name FROM routes WHERE region = %s LIMIT 20"
        routes = execute_query(routes_query, (region,))

        if not routes:
            print(f"警告：没有找到 {region} 的线路数据，请先导入GTFS数据")
            return False

        # 清空现有的示例数据
        cursor.execute(
            "DELETE FROM route_daily_punctuality WHERE region = %s AND stat_date >= CURRENT_DATE - INTERVAL '7 days'",
            (region,)
        )

        # 为每条线路生成过去7天的数据
        for route in routes:
            route_id = route['route_id']

            for days_ago in range(7, 0, -1):
                stat_date = datetime.now().date() - timedelta(days=days_ago)

                base_punctuality_rate = random.uniform(70, 95)

                if 'Rapid' in route.get('route_long_name', '') or route.get('route_short_name', '').startswith('R'):
                    base_punctuality_rate += random.uniform(-5, 10)

                if 'Express' in route.get('route_long_name', '') or 'X' in route.get('route_short_name', ''):
                    base_punctuality_rate += random.uniform(-3, 8)

                punctuality_rate = min(98, max(60, base_punctuality_rate))

                total_trips = random.randint(80, 300)

                on_time_percentage = punctuality_rate / 100
                early_percentage = random.uniform(0.05, 0.15)
                late_percentage = (1 - on_time_percentage - early_percentage) * 0.7
                very_late_percentage = (1 - on_time_percentage - early_percentage) * 0.3

                on_time_trips = int(total_trips * on_time_percentage)
                early_trips = int(total_trips * early_percentage)
                late_trips = int(total_trips * late_percentage)
                very_late_trips = total_trips - on_time_trips - early_trips - late_trips

                avg_delay_minutes = random.uniform(1.0, 8.0) if on_time_percentage < 0.9 else random.uniform(0.5, 3.0)
                max_delay_minutes = avg_delay_minutes * random.uniform(2.5, 5.0)

                cursor.execute("""
                    INSERT INTO route_daily_punctuality
                    (region, route_id, stat_date, total_trips, on_time_trips, early_trips,
                     late_trips, very_late_trips, avg_arrival_delay, max_arrival_delay,
                     min_arrival_delay, punctuality_rate, early_rate, late_rate, very_late_rate)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (region, route_id, stat_date) DO UPDATE SET
                        total_trips = EXCLUDED.total_trips,
                        on_time_trips = EXCLUDED.on_time_trips,
                        punctuality_rate = EXCLUDED.punctuality_rate,
                        updated_at = CURRENT_TIMESTAMP
                """, (
                    region, route_id, stat_date, total_trips, on_time_trips, early_trips,
                    late_trips, very_late_trips, avg_delay_minutes * 60,
                    max_delay_minutes * 60, random.randint(-120, -30),
                    punctuality_rate, early_percentage * 100, late_percentage * 100, very_late_percentage * 100
                ))

        conn.commit()
        Database.return_connection(conn)

        print(f"已为 {len(routes)} 条线路生成过去7天的准点率数据")
        return True

    except Exception as e:
        print(f"生成线路数据时发生错误: {e}")
        import traceback; traceback.print_exc()
        return False


def generate_sample_stops(region):
    """生成示例站点准点率数据"""
    print(f"正在生成示例站点准点率数据 (region={region})...")

    try:
        conn = Database.get_connection()
        cursor = conn.cursor()

        stops_query = """
            SELECT DISTINCT s.stop_id, s.stop_name
            FROM stops s
            JOIN stop_times st ON s.stop_id = st.stop_id AND s.region = st.region
            WHERE s.region = %s
            LIMIT 50
        """
        stops = execute_query(stops_query, (region,))

        if not stops:
            print(f"警告：没有找到 {region} 的站点数据")
            return False

        cursor.execute(
            "DELETE FROM stop_daily_punctuality WHERE region = %s AND stat_date >= CURRENT_DATE - INTERVAL '7 days'",
            (region,)
        )

        for stop in stops:
            stop_id = stop['stop_id']

            for days_ago in range(7, 0, -1):
                stat_date = datetime.now().date() - timedelta(days=days_ago)

                base_punctuality_rate = random.uniform(65, 92)

                if 'Station' in stop.get('stop_name', '') or 'Terminal' in stop.get('stop_name', ''):
                    base_punctuality_rate += random.uniform(-3, 5)

                punctuality_rate = min(96, max(55, base_punctuality_rate))

                total_visits = random.randint(100, 800)

                on_time_percentage = punctuality_rate / 100
                early_percentage = random.uniform(0.08, 0.18)
                late_percentage = (1 - on_time_percentage - early_percentage) * 0.75
                very_late_percentage = (1 - on_time_percentage - early_percentage) * 0.25

                on_time_visits = int(total_visits * on_time_percentage)
                early_visits = int(total_visits * early_percentage)
                late_visits = int(total_visits * late_percentage)
                very_late_visits = total_visits - on_time_visits - early_visits - late_visits

                avg_delay_minutes = random.uniform(1.2, 6.5)
                max_delay_minutes = avg_delay_minutes * random.uniform(2.0, 4.0)

                cursor.execute("""
                    INSERT INTO stop_daily_punctuality
                    (region, stop_id, stat_date, total_visits, on_time_visits, early_visits,
                     late_visits, very_late_visits, avg_arrival_delay, max_arrival_delay,
                     min_arrival_delay, punctuality_rate)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (region, stop_id, stat_date) DO UPDATE SET
                        total_visits = EXCLUDED.total_visits,
                        punctuality_rate = EXCLUDED.punctuality_rate,
                        updated_at = CURRENT_TIMESTAMP
                """, (
                    region, stop_id, stat_date, total_visits, on_time_visits, early_visits,
                    late_visits, very_late_visits, avg_delay_minutes * 60,
                    max_delay_minutes * 60, random.randint(-120, -30),
                    punctuality_rate
                ))

        conn.commit()
        Database.return_connection(conn)

        print(f"已为 {len(stops)} 个站点生成过去7天的准点率数据")
        return True

    except Exception as e:
        print(f"生成站点数据时发生错误: {e}")
        import traceback; traceback.print_exc()
        return False


def generate_sample_realtime_data(region):
    """生成示例实时数据"""
    print(f"正在生成示例实时数据 (region={region})...")

    try:
        conn = Database.get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM realtime_delay_records WHERE region = %s", (region,))
        cursor.execute("DELETE FROM realtime_vehicle_positions WHERE region = %s", (region,))
        cursor.execute("DELETE FROM system_punctuality_overview WHERE region = %s", (region,))

        cursor.execute("""
            SELECT DISTINCT r.route_id, t.trip_id, st.stop_id, s.stop_name, st.stop_sequence
            FROM routes r
            JOIN trips t ON r.route_id = t.route_id AND r.region = t.region
            JOIN stop_times st ON t.trip_id = st.trip_id AND t.region = st.region
            JOIN stops s ON st.stop_id = s.stop_id AND st.region = s.region
            WHERE r.region = %s AND st.stop_sequence <= 5
            LIMIT 50
        """, (region,))

        trip_stops = cursor.fetchall()

        if not trip_stops:
            print(f"警告：没有找到 {region} 的行程站点数据")
            return False

        current_time = datetime.now()

        for record in trip_stops:
            minutes_ago = random.randint(1, 120)
            record_timestamp = current_time - timedelta(minutes=minutes_ago)
            scheduled_time = record_timestamp - timedelta(minutes=random.randint(-2, 15))
            delay_seconds = random.randint(-180, 600)

            cursor.execute("""
                INSERT INTO realtime_delay_records
                (region, trip_id, route_id, stop_id, stop_sequence, vehicle_id,
                 scheduled_time, actual_time, record_timestamp,
                 arrival_delay, departure_delay, data_source, processed)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                region, record[1], record[0], record[2], record[4],
                f"VEH_{record[0]}_{random.randint(100, 999)}",
                scheduled_time, record_timestamp, record_timestamp,
                delay_seconds, 0, 'GTFS_Realtime', False
            ))

        # 地区坐标范围
        coord_ranges = {
            'sf':     (37.70, 37.80, -122.50, -122.35),
            'nyc':    (40.60, 40.80, -74.05, -73.85),
            'sydney': (-33.95, -33.75, 151.00, 151.25),
        }
        lat_min, lat_max, lng_min, lng_max = coord_ranges.get(region, (37.70, 37.80, -122.50, -122.35))

        for record in trip_stops[:20]:
            lat = random.uniform(lat_min, lat_max)
            lng = random.uniform(lng_min, lng_max)
            minutes_ago = random.randint(1, 10)
            position_timestamp = current_time - timedelta(minutes=minutes_ago)

            cursor.execute("""
                INSERT INTO realtime_vehicle_positions
                (region, vehicle_id, trip_id, route_id, latitude, longitude,
                 position_timestamp, record_timestamp, current_status, stop_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                region, f"VEH_{record[0]}_{random.randint(100, 999)}",
                record[1], record[0], lat, lng,
                position_timestamp, current_time, random.choice([0, 1, 2]), record[2]
            ))

        route_count = execute_count("SELECT COUNT(DISTINCT route_id) FROM routes WHERE region = %s", (region,))
        trip_count = execute_count(
            "SELECT COUNT(*) FROM stop_times st JOIN trips t ON st.trip_id = t.trip_id AND st.region = t.region WHERE t.region = %s",
            (region,)
        )

        cursor.execute("""
            INSERT INTO system_punctuality_overview
            (region, stat_date, total_routes, total_trips, system_punctuality_rate,
             system_avg_delay_minutes, morning_peak_rate, evening_peak_rate, off_peak_rate)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (region, stat_date) DO UPDATE SET
                system_punctuality_rate = EXCLUDED.system_punctuality_rate,
                updated_at = CURRENT_TIMESTAMP
        """, (
            region, current_time.date(),
            route_count, trip_count,
            78.5, 3.2, 75.8, 72.3, 81.2
        ))

        conn.commit()
        Database.return_connection(conn)

        print(f"已生成 {len(trip_stops)} 条实时延误记录和 20 个车辆位置")
        return True

    except Exception as e:
        print(f"生成实时数据时发生错误: {e}")
        import traceback; traceback.print_exc()
        return False


def generate_hourly_stats(region):
    """生成时段统计数据"""
    print(f"正在生成时段统计数据 (region={region})...")

    try:
        conn = Database.get_connection()
        cursor = conn.cursor()

        # 使用今天日期，并为今天生成数据
        today = datetime.now().date()
        cursor.execute(
            "DELETE FROM hourly_punctuality_stats WHERE region = %s AND stat_date = %s",
            (region, today)
        )

        # 取最近有数据的线路（不限于今天）
        cursor.execute("""
            SELECT DISTINCT route_id FROM route_daily_punctuality
            WHERE region = %s
            ORDER BY route_id
            LIMIT 10
        """, (region,))
        routes = cursor.fetchall()

        if not routes:
            print(f"警告：没有找到 {region} 的线路数据")
            return False

        for route in routes:
            route_id = route[0]

            for hour in range(24):
                if 7 <= hour <= 9 or 17 <= hour <= 19:
                    base_rate = random.uniform(65, 85)
                elif 22 <= hour or hour <= 5:
                    base_rate = random.uniform(85, 95)
                else:
                    base_rate = random.uniform(75, 90)

                total_trips = random.randint(5, 30)
                on_time_trips = int(total_trips * (base_rate / 100))
                avg_delay = random.uniform(1.0, 5.0)

                cursor.execute("""
                    INSERT INTO hourly_punctuality_stats
                    (region, route_id, hour_of_day, stat_date, total_trips,
                     on_time_trips, avg_arrival_delay, max_arrival_delay, punctuality_rate)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    region, route_id, hour, today,
                    total_trips, on_time_trips, avg_delay * 60,
                    avg_delay * random.uniform(2, 4), base_rate
                ))

        conn.commit()
        Database.return_connection(conn)

        print(f"已为 {len(routes)} 条线路生成24小时时段统计数据")
        return True

    except Exception as e:
        print(f"生成时段数据时发生错误: {e}")
        import traceback; traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(description='生成示例准点率数据')
    parser.add_argument('--region', default='sf', choices=['sf', 'nyc', 'sydney'],
                        help='地区代码 (默认: sf)')
    args = parser.parse_args()
    region = args.region

    print("=" * 50)
    print(f"开始生成示例准点率数据 (region={region})")
    print("=" * 50)

    Database.initialize()

    try:
        execute_count("SELECT 1")
        print("✅ 数据库连接正常")
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        sys.exit(1)

    routes_count = execute_count("SELECT COUNT(*) FROM routes WHERE region = %s", (region,))
    if routes_count == 0:
        print(f"❌ 没有 {region} 的GTFS数据，请先导入")
        sys.exit(1)

    print(f"✅ 找到 {routes_count} 条线路数据")

    success_count = 0

    if generate_sample_routes(region):
        success_count += 1
        print("✅ 线路准点率数据生成成功")
    else:
        print("❌ 线路准点率数据生成失败")

    if generate_sample_stops(region):
        success_count += 1
        print("✅ 站点准点率数据生成成功")
    else:
        print("❌ 站点准点率数据生成失败")

    if generate_sample_realtime_data(region):
        success_count += 1
        print("✅ 实时数据生成成功")
    else:
        print("❌ 实时数据生成失败")

    if generate_hourly_stats(region):
        success_count += 1
        print("✅ 时段统计数据生成成功")
    else:
        print("❌ 时段统计数据生成失败")

    print("=" * 50)
    print(f"数据生成完成: {success_count}/4 个任务成功")
    print("=" * 50)


if __name__ == "__main__":
    main()
