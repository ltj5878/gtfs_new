#!/usr/bin/env python3
"""
生成示例准点率数据脚本
为测试和演示目的生成模拟的准点率数据
"""

import random
import sys
import os
from datetime import datetime, timedelta
from core.db import Database, execute_query, execute_query_one, execute_count

def generate_sample_routes():
    """生成示例线路准点率数据"""
    print("正在生成示例线路准点率数据...")

    try:
        conn = Database.get_connection()
        cursor = conn.cursor()

        # 获取现有线路
        routes_query = "SELECT route_id, route_short_name, route_long_name FROM routes LIMIT 20"
        routes = execute_query(routes_query)

        if not routes:
            print("警告：没有找到线路数据，请先导入GTFS数据")
            return False

        # 清空现有的示例数据
        cursor.execute("DELETE FROM route_daily_punctuality WHERE stat_date >= CURRENT_DATE - INTERVAL '7 days'")

        # 为每条线路生成过去7天的数据
        for route in routes:
            route_id = route['route_id']

            for days_ago in range(7, 0, -1):
                stat_date = datetime.now().date() - timedelta(days=days_ago)

                # 生成随机的准点率数据
                base_punctuality_rate = random.uniform(70, 95)  # 基础准点率70-95%

                # 根据线路类型调整准点率
                if 'Rapid' in route.get('route_long_name', '') or route.get('route_short_name', '').startswith('R'):
                    base_punctuality_rate += random.uniform(-5, 10)  # 快速线路可能准点率略高

                if 'Express' in route.get('route_long_name', '') or 'X' in route.get('route_short_name', ''):
                    base_punctuality_rate += random.uniform(-3, 8)   # 快车可能准点率略高

                punctuality_rate = min(98, max(60, base_punctuality_rate))  # 限制在60-98%

                # 生成班次数据
                total_trips = random.randint(80, 300)  # 每天80-300班次

                # 根据准点率生成延误分布
                on_time_percentage = punctuality_rate / 100
                early_percentage = random.uniform(0.05, 0.15)  # 5-15%提前
                late_percentage = (1 - on_time_percentage - early_percentage) * 0.7  # 大部分剩余为延误
                very_late_percentage = (1 - on_time_percentage - early_percentage) * 0.3  # 少量严重延误

                on_time_trips = int(total_trips * on_time_percentage)
                early_trips = int(total_trips * early_percentage)
                late_trips = int(total_trips * late_percentage)
                very_late_trips = total_trips - on_time_trips - early_trips - late_trips

                # 生成延误时间数据
                avg_delay_minutes = random.uniform(1.0, 8.0) if on_time_percentage < 0.9 else random.uniform(0.5, 3.0)
                max_delay_minutes = avg_delay_minutes * random.uniform(2.5, 5.0)

                # 插入数据
                cursor.execute("""
                    INSERT INTO route_daily_punctuality
                    (route_id, stat_date, total_trips, on_time_trips, early_trips,
                     late_trips, very_late_trips, avg_arrival_delay, max_arrival_delay,
                     min_arrival_delay, punctuality_rate, early_rate, late_rate, very_late_rate)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    route_id, stat_date, total_trips, on_time_trips, early_trips,
                    late_trips, very_late_trips, avg_delay_minutes * 60,  # 转换为秒
                    max_delay_minutes * 60, random.randint(-120, -30),  # 最小延误（提前30-120秒）
                    punctuality_rate, early_percentage * 100, late_percentage * 100, very_late_percentage * 100
                ))

        conn.commit()
        conn.close()

        print(f"已为 {len(routes)} 条线路生成过去7天的准点率数据")
        return True

    except Exception as e:
        print(f"生成线路数据时发生错误: {e}")
        return False

def generate_sample_stops():
    """生成示例站点准点率数据"""
    print("正在生成示例站点准点率数据...")

    try:
        conn = Database.get_connection()
        cursor = conn.cursor()

        # 获取现有站点
        stops_query = """
            SELECT DISTINCT s.stop_id, s.stop_name
            FROM stops s
            JOIN stop_times st ON s.stop_id = st.stop_id
            LIMIT 50
        """
        stops = execute_query(stops_query)

        if not stops:
            print("警告：没有找到站点数据")
            return False

        # 清空现有的示例数据
        cursor.execute("DELETE FROM stop_daily_punctuality WHERE stat_date >= CURRENT_DATE - INTERVAL '7 days'")

        # 为每个站点生成过去7天的数据
        for stop in stops:
            stop_id = stop['stop_id']

            for days_ago in range(7, 0, -1):
                stat_date = datetime.now().date() - timedelta(days=days_ago)

                # 生成随机但合理的站点准点率数据
                base_punctuality_rate = random.uniform(65, 92)

                # 站点类型调整（这里简化处理）
                if 'Station' in stop.get('stop_name', '') or 'Terminal' in stop.get('stop_name', ''):
                    base_punctuality_rate += random.uniform(-3, 5)  # 枢纽站可能更准时

                punctuality_rate = min(96, max(55, base_punctuality_rate))

                # 生成访问数据
                total_visits = random.randint(100, 800)  # 站点访问次数比线路班次多

                # 生成延误分布
                on_time_percentage = punctuality_rate / 100
                early_percentage = random.uniform(0.08, 0.18)
                late_percentage = (1 - on_time_percentage - early_percentage) * 0.75
                very_late_percentage = (1 - on_time_percentage - early_percentage) * 0.25

                on_time_visits = int(total_visits * on_time_percentage)
                early_visits = int(total_visits * early_percentage)
                late_visits = int(total_visits * late_percentage)
                very_late_visits = total_visits - on_time_visits - early_visits - late_visits

                # 生成延误数据
                avg_delay_minutes = random.uniform(1.2, 6.5)
                max_delay_minutes = avg_delay_minutes * random.uniform(2.0, 4.0)

                cursor.execute("""
                    INSERT INTO stop_daily_punctuality
                    (stop_id, stat_date, total_visits, on_time_visits, early_visits,
                     late_visits, very_late_visits, avg_arrival_delay, max_arrival_delay,
                     min_arrival_delay, punctuality_rate)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    stop_id, stat_date, total_visits, on_time_visits, early_visits,
                    late_visits, very_late_visits, avg_delay_minutes * 60,
                    max_delay_minutes * 60, random.randint(-120, -30),
                    punctuality_rate
                ))

        conn.commit()
        conn.close()

        print(f"已为 {len(stops)} 个站点生成过去7天的准点率数据")
        return True

    except Exception as e:
        print(f"生成站点数据时发生错误: {e}")
        return False

def generate_sample_realtime_data():
    """生成示例实时数据"""
    print("正在生成示例实时数据...")

    try:
        conn = Database.get_connection()
        cursor = conn.cursor()

        # 清空现有实时数据
        cursor.execute("DELETE FROM realtime_delay_records")
        cursor.execute("DELETE FROM realtime_vehicle_positions")
        cursor.execute("DELETE FROM system_punctuality_overview")

        # 获取一些示例行程和站点
        cursor.execute("""
            SELECT DISTINCT r.route_id, t.trip_id, st.stop_id, s.stop_name, st.stop_sequence
            FROM routes r
            JOIN trips t ON r.route_id = t.route_id
            JOIN stop_times st ON t.trip_id = st.trip_id
            JOIN stops s ON st.stop_id = s.stop_id
            WHERE st.stop_sequence <= 5
            LIMIT 50
        """)

        trip_stops = cursor.fetchall()

        if not trip_stops:
            print("警告：没有找到行程站点数据")
            return False

        # 生成实时延误记录
        current_time = datetime.now()

        for record in trip_stops:
            # 生成随机延误时间（最近1-2小时）
            minutes_ago = random.randint(1, 120)
            record_timestamp = current_time - timedelta(minutes=minutes_ago)
            scheduled_time = record_timestamp - timedelta(minutes=random.randint(-2, 15))

            # 随机生成延误
            delay_seconds = random.randint(-180, 600)  # -3分钟到10分钟

            cursor.execute("""
                INSERT INTO realtime_delay_records
                (trip_id, route_id, stop_id, stop_sequence, vehicle_id,
                 scheduled_time, actual_time, record_timestamp,
                 arrival_delay, departure_delay, data_source, processed)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                record['trip_id'], record['route_id'], record['stop_id'], record['stop_sequence'],
                f"VEH_{record['route_id']}_{random.randint(100, 999)}",
                scheduled_time, record_timestamp, record_timestamp,
                delay_seconds, 0, 'GTFS_Realtime', False
            ))

        # 生成实时车辆位置数据
        for record in trip_stops[:20]:  # 生成20个车辆位置
            # 随机生成位置（在旧金山湾区范围内）
            lat = random.uniform(37.70, 37.80)
            lng = random.uniform(-122.50, -122.35)

            minutes_ago = random.randint(1, 10)
            position_timestamp = current_time - timedelta(minutes=minutes_ago)

            cursor.execute("""
                INSERT INTO realtime_vehicle_positions
                (vehicle_id, trip_id, route_id, latitude, longitude,
                 position_timestamp, record_timestamp, current_status, stop_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                f"VEH_{record['route_id']}_{random.randint(100, 999)}",
                record['trip_id'], record['route_id'], lat, lng,
                position_timestamp, current_time, random.choice([0, 1, 2]), record['stop_id']
            ))

        # 生成系统概览数据
        cursor.execute("""
            INSERT INTO system_punctuality_overview
            (stat_date, total_routes, total_trips, system_punctuality_rate,
             system_avg_delay_minutes, morning_peak_rate, evening_peak_rate, off_peak_rate)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            current_time.date(),
            execute_count("SELECT COUNT(DISTINCT route_id) FROM routes"),
            execute_count("SELECT COUNT(*) FROM stop_times"),
            78.5,  # 系统准点率
            3.2,   # 平均延误分钟
            75.8,  # 早高峰准点率
            72.3,  # 晚高峰准点率
            81.2   # 非高峰准点率
        ))

        conn.commit()
        conn.close()

        print(f"已生成 {len(trip_stops)} 条实时延误记录和 20 个车辆位置")
        return True

    except Exception as e:
        print(f"生成实时数据时发生错误: {e}")
        return False

def generate_hourly_stats():
    """生成时段统计数据"""
    print("正在生成时段统计数据...")

    try:
        conn = Database.get_connection()
        cursor = conn.cursor()

        # 清空现有时段数据
        cursor.execute("DELETE FROM hourly_punctuality_stats WHERE stat_date = CURRENT_DATE")

        # 获取今天的线路数据
        cursor.execute("""
            SELECT DISTINCT route_id FROM route_daily_punctuality
            WHERE stat_date = CURRENT_DATE
            LIMIT 10
        """)
        routes = cursor.fetchall()

        if not routes:
            print("警告：没有找到今天的线路数据")
            return False

        for route in routes:
            route_id = route['route_id']

            # 为每个小时生成数据
            for hour in range(24):
                # 根据时段调整准点率（早高峰7-9点和晚高峰17-19点准点率较低）
                if 7 <= hour <= 9 or 17 <= hour <= 19:
                    base_rate = random.uniform(65, 85)
                elif 22 <= hour or hour <= 5:  # 深夜准点率较高
                    base_rate = random.uniform(85, 95)
                else:  # 其他时段
                    base_rate = random.uniform(75, 90)

                total_trips = random.randint(5, 30)
                on_time_trips = int(total_trips * (base_rate / 100))
                avg_delay = random.uniform(1.0, 5.0)

                cursor.execute("""
                    INSERT INTO hourly_punctuality_stats
                    (route_id, hour_of_day, stat_date, total_trips,
                     on_time_trips, avg_arrival_delay, max_arrival_delay, punctuality_rate)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    route_id, hour, datetime.now().date(),
                    total_trips, on_time_trips, avg_delay * 60,
                    avg_delay * random.uniform(2, 4), base_rate
                ))

        conn.commit()
        conn.close()

        print(f"已为 {len(routes)} 条线路生成24小时时段统计数据")
        return True

    except Exception as e:
        print(f"生成时段数据时发生错误: {e}")
        return False

def main():
    print("=" * 50)
    print("开始生成示例准点率数据")
    print("=" * 50)

    # 初始化数据库连接池
    Database.initialize()

    success_count = 0
    total_tasks = 5

    # 检查数据库连接
    try:
        execute_count("SELECT 1")
        print("✅ 数据库连接正常")
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        sys.exit(1)

    # 检查是否有GTFS数据
    routes_count = execute_count("SELECT COUNT(*) FROM routes")
    if routes_count == 0:
        print("❌ 没有GTFS数据，请先运行: python gtfs_importer.py --zip gtfs_data/gtfs_SF_20251119.zip")
        sys.exit(1)

    print(f"✅ 找到 {routes_count} 条线路数据")

    # 生成各种示例数据
    if generate_sample_routes():
        success_count += 1
        print("✅ 线路准点率数据生成成功")
    else:
        print("❌ 线路准点率数据生成失败")

    if generate_sample_stops():
        success_count += 1
        print("✅ 站点准点率数据生成成功")
    else:
        print("❌ 站点准点率数据生成失败")

    if generate_sample_realtime_data():
        success_count += 1
        print("✅ 实时数据生成成功")
    else:
        print("❌ 实时数据生成失败")

    if generate_hourly_stats():
        success_count += 1
        print("✅ 时段统计数据生成成功")
    else:
        print("❌ 时段统计数据生成失败")

    print("=" * 50)
    print(f"数据生成完成: {success_count}/{total_tasks} 个任务成功")

    if success_count == total_tasks:
        print("🎉 所有示例数据生成成功！")
        print("现在可以访问前端页面查看准点率分析功能:")
        print("- 准点率概览: http://localhost:5175/punctuality")
        print("- 线路准点率: http://localhost:5175/punctuality/routes")
        print("- 站点准点率: http://localhost:5175/punctuality/stops")
        print("- 实时监控: http://localhost:5175/punctuality/realtime")
    else:
        print("⚠️  部分数据生成失败，可能影响页面显示效果")

    print("=" * 50)

if __name__ == "__main__":
    main()