#!/usr/bin/env python3
"""
线路健康度评分计算脚本
基于准点率、频率稳定性、覆盖度、延误分布四个维度评分
"""

import sys
import os
import json
import argparse
import math
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.db import Database, execute_query, execute_query_one, execute_write


def calculate_scores(region: str, score_date: str = None):
    """计算指定地区所有线路的健康度评分"""
    if score_date is None:
        score_date = date.today().isoformat()

    # 获取该地区所有线路
    routes = execute_query("""
        SELECT route_id, route_short_name, route_long_name, route_type
        FROM routes WHERE region = %s
    """, (region,))

    if not routes:
        print(f"⚠️ 地区 {region} 无线路数据")
        return

    # 预计算该地区的平均站点数（用于覆盖度维度）
    avg_stops_row = execute_query_one("""
        SELECT AVG(stop_count) as avg_stops FROM (
            SELECT t.route_id, COUNT(DISTINCT st.stop_id) as stop_count
            FROM trips t
            JOIN stop_times st ON t.trip_id = st.trip_id AND t.region = st.region
            WHERE t.region = %s
            GROUP BY t.route_id
        ) sub
    """, (region,))
    avg_stops = float(avg_stops_row['avg_stops']) if avg_stops_row and avg_stops_row['avg_stops'] else 10

    # 预计算该地区平均方向数
    avg_dirs_row = execute_query_one("""
        SELECT AVG(dir_count) as avg_dirs FROM (
            SELECT route_id, COUNT(DISTINCT direction_id) as dir_count
            FROM trips WHERE region = %s GROUP BY route_id
        ) sub
    """, (region,))
    avg_dirs = float(avg_dirs_row['avg_dirs']) if avg_dirs_row and avg_dirs_row['avg_dirs'] else 1.5

    scored = 0
    for route in routes:
        route_id = route['route_id']
        detail = {}

        # ====== 维度一：准点率（权重 40%）======
        punct_row = execute_query_one("""
            SELECT AVG(punctuality_rate) as avg_rate
            FROM route_daily_punctuality
            WHERE route_id = %s AND region = %s
              AND stat_date >= (CURRENT_DATE - INTERVAL '7 days')
        """, (route_id, region))
        avg_rate = float(punct_row['avg_rate']) if punct_row and punct_row['avg_rate'] else None

        if avg_rate is not None:
            punctuality_score = min(100, avg_rate)
        else:
            punctuality_score = 70.0  # 无数据给默认分
        detail['avg_punctuality_rate'] = avg_rate

        # ====== 维度二：频率稳定性（权重 25%）======
        # 计算班次间隔的标准差，标准差越小越稳定
        freq_rows = execute_query("""
            SELECT departure_time FROM stop_times
            WHERE trip_id IN (
                SELECT trip_id FROM trips WHERE route_id = %s AND region = %s LIMIT 200
            ) AND region = %s AND stop_sequence = 1
            ORDER BY departure_time
        """, (route_id, region, region))

        if len(freq_rows) >= 3:
            times = []
            for r in freq_rows:
                dt = r['departure_time']
                if dt:
                    # departure_time 是字符串如 "07:30:00"
                    parts = str(dt).split(':')
                    if len(parts) >= 2:
                        try:
                            minutes = int(parts[0]) * 60 + int(parts[1])
                            times.append(minutes)
                        except ValueError:
                            pass
            times.sort()
            if len(times) >= 3:
                intervals = [times[i+1] - times[i] for i in range(len(times)-1) if times[i+1] > times[i]]
                if intervals:
                    mean_interval = sum(intervals) / len(intervals)
                    variance = sum((x - mean_interval) ** 2 for x in intervals) / len(intervals)
                    std_dev = math.sqrt(variance)
                    # 标准差越小分数越高，标准差=0 得100分，标准差=30 得50分
                    frequency_score = max(0, min(100, 100 - std_dev * 1.67))
                    detail['interval_std_dev'] = round(std_dev, 2)
                    detail['mean_interval_min'] = round(mean_interval, 2)
                else:
                    frequency_score = 50.0
            else:
                frequency_score = 50.0
        else:
            frequency_score = 50.0

        # ====== 维度三：覆盖度（权重 15%）======
        coverage_row = execute_query_one("""
            SELECT COUNT(DISTINCT st.stop_id) as stop_count,
                   COUNT(DISTINCT t.direction_id) as dir_count
            FROM trips t
            JOIN stop_times st ON t.trip_id = st.trip_id AND t.region = st.region
            WHERE t.route_id = %s AND t.region = %s
        """, (route_id, region))

        if coverage_row:
            stop_count = coverage_row['stop_count'] or 0
            dir_count = coverage_row['dir_count'] or 0
            # 站点覆盖度：与平均值比较
            stop_ratio = min(2.0, stop_count / max(1, avg_stops))
            dir_ratio = min(2.0, dir_count / max(1, avg_dirs))
            coverage_score = min(100, (stop_ratio * 60 + dir_ratio * 40))
            detail['stop_count'] = stop_count
            detail['dir_count'] = dir_count
        else:
            coverage_score = 50.0

        # ====== 维度四：延误分布（权重 20%）======
        delay_row = execute_query_one("""
            SELECT
                COUNT(*) FILTER (WHERE avg_arrival_delay <= 120) as light_delay,
                COUNT(*) FILTER (WHERE avg_arrival_delay > 120 AND avg_arrival_delay <= 300) as mid_delay,
                COUNT(*) FILTER (WHERE avg_arrival_delay > 300) as severe_delay,
                COUNT(*) as total
            FROM route_daily_punctuality
            WHERE route_id = %s AND region = %s
              AND stat_date >= (CURRENT_DATE - INTERVAL '7 days')
        """, (route_id, region))

        if delay_row and delay_row['total'] and delay_row['total'] > 0:
            total = delay_row['total']
            light = delay_row['light_delay'] or 0
            severe = delay_row['severe_delay'] or 0
            # 轻度延误比例高得分高，严重延误比例高得分低
            delay_dist_score = min(100, (light / total) * 100 - (severe / total) * 50)
            delay_dist_score = max(0, delay_dist_score)
            detail['light_delay_pct'] = round(light / total * 100, 1)
            detail['severe_delay_pct'] = round(severe / total * 100, 1)
        else:
            delay_dist_score = 70.0

        # ====== 综合得分 ======
        total_score = round(
            punctuality_score * 0.40 +
            frequency_score * 0.25 +
            coverage_score * 0.15 +
            delay_dist_score * 0.20, 2
        )

        # 写入数据库
        execute_write("""
            INSERT INTO route_health_scores
                (route_id, region, score_date, punctuality_score, frequency_score,
                 coverage_score, delay_dist_score, total_score, score_detail)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
            ON CONFLICT (route_id, region, score_date)
            DO UPDATE SET
                punctuality_score = EXCLUDED.punctuality_score,
                frequency_score = EXCLUDED.frequency_score,
                coverage_score = EXCLUDED.coverage_score,
                delay_dist_score = EXCLUDED.delay_dist_score,
                total_score = EXCLUDED.total_score,
                score_detail = EXCLUDED.score_detail,
                created_at = NOW()
        """, (route_id, region, score_date,
              round(punctuality_score, 2), round(frequency_score, 2),
              round(coverage_score, 2), round(delay_dist_score, 2),
              total_score, json.dumps(detail, default=str)))

        scored += 1

    print(f"✅ 健康度评分完成 [{region}] {score_date}")
    print(f"   共计算 {scored} 条线路")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='线路健康度评分计算')
    parser.add_argument('--region', default='sf', help='地区 (sf/nyc/sydney)')
    parser.add_argument('--date', default=None, help='评分日期 (YYYY-MM-DD)')
    args = parser.parse_args()

    Database.initialize()
    calculate_scores(args.region, args.date)
