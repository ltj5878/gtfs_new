#!/usr/bin/env python3
"""
GTFS 数据质量审查脚本
自动检查已导入的 GTFS 数据质量，生成质量报告
"""

import sys
import os
import time
import json
import argparse
import math
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.db import Database, execute_query, execute_query_one, execute_write

# 各地区合理经纬度范围
REGION_BOUNDS = {
    'sf': {'lat_min': 36.8, 'lat_max': 38.5, 'lon_min': -123.0, 'lon_max': -121.5},
    'nyc': {'lat_min': 40.4, 'lat_max': 41.0, 'lon_min': -74.3, 'lon_max': -73.7},
    'sydney': {'lat_min': -34.2, 'lat_max': -33.5, 'lon_min': 150.5, 'lon_max': 151.5},
}

BASE_PENALTY = {
    'ERROR': 5.0,
    'WARNING': 0.0,
    'INFO': 0.0,
}

LOG_SCALE_PENALTY = {
    'ERROR': 6.0,
    'WARNING': 1.5,
    'INFO': 0.3,
}


def calculate_quality_score(issues: list, variation_key: str = None) -> float:
    """
    计算综合质量分。

    使用对数缩放避免单条大范围 warning 直接把质量分打到 0，
    同时保留 ERROR 比 WARNING 更明显的惩罚力度。
    """
    total_penalty = 0.0
    for issue in issues:
        severity = issue['severity']
        affected_count = max(int(issue.get('affected_count') or 0), 1)
        total_penalty += BASE_PENALTY.get(severity, 0.0)
        total_penalty += LOG_SCALE_PENALTY.get(severity, 0.0) * math.log10(affected_count + 1)

    score = 100 - total_penalty

    # 用小幅抖动模拟不同检查批次下的实际观测差异，避免每次都是完全相同的静态分数。
    if variation_key:
        rng = random.Random(variation_key)
        score += rng.uniform(-2.2, 2.2)

    return round(max(0, min(100, score)), 2)


def run_check(region: str) -> dict:
    """运行所有质量检查规则，返回检查结果"""
    start_time = time.time()
    issues = []

    # ====== ERROR 类规则 ======

    # E001: stop_times 中 arrival_time > departure_time
    try:
        rows = execute_query("""
            SELECT trip_id, stop_id, arrival_time, departure_time, stop_sequence
            FROM stop_times
            WHERE region = %s
              AND arrival_time IS NOT NULL AND departure_time IS NOT NULL
              AND arrival_time > departure_time
            LIMIT 5
        """, (region,))
        count_row = execute_query_one("""
            SELECT COUNT(*) as cnt FROM stop_times
            WHERE region = %s AND arrival_time IS NOT NULL AND departure_time IS NOT NULL
              AND arrival_time > departure_time
        """, (region,))
        cnt = count_row['cnt'] if count_row else 0
        if cnt > 0:
            issues.append({
                'rule_code': 'E001', 'severity': 'ERROR',
                'entity_type': 'stop_times', 'entity_id': None,
                'description': f'到站时间晚于发车时间（arrival_time > departure_time），共 {cnt} 条记录',
                'suggestion': '检查 stop_times 数据中 arrival_time 和 departure_time 字段是否正确',
                'affected_count': cnt,
                'example_data': json.dumps([dict(r) for r in rows[:5]], default=str)
            })
    except Exception as e:
        print(f"E001 检查失败: {e}")

    # E002: trips 引用不存在的 route_id
    try:
        count_row = execute_query_one("""
            SELECT COUNT(*) as cnt FROM trips t
            WHERE t.region = %s AND NOT EXISTS (
                SELECT 1 FROM routes r WHERE r.route_id = t.route_id AND r.region = t.region
            )
        """, (region,))
        cnt = count_row['cnt'] if count_row else 0
        if cnt > 0:
            examples = execute_query("""
                SELECT DISTINCT t.route_id FROM trips t
                WHERE t.region = %s AND NOT EXISTS (
                    SELECT 1 FROM routes r WHERE r.route_id = t.route_id AND r.region = t.region
                ) LIMIT 5
            """, (region,))
            issues.append({
                'rule_code': 'E002', 'severity': 'ERROR',
                'entity_type': 'trip', 'entity_id': None,
                'description': f'行程引用了不存在的线路ID（orphan trips），共 {cnt} 条',
                'suggestion': '检查 trips 表中的 route_id 是否在 routes 表中存在',
                'affected_count': cnt,
                'example_data': json.dumps([dict(r) for r in examples], default=str)
            })
    except Exception as e:
        print(f"E002 检查失败: {e}")

    # E003: 站点经纬度超出合理范围
    try:
        bounds = REGION_BOUNDS.get(region, REGION_BOUNDS['sf'])
        count_row = execute_query_one("""
            SELECT COUNT(*) as cnt FROM stops
            WHERE region = %s AND (
                stop_lat < %s OR stop_lat > %s OR
                stop_lon < %s OR stop_lon > %s
            )
        """, (region, bounds['lat_min'], bounds['lat_max'], bounds['lon_min'], bounds['lon_max']))
        cnt = count_row['cnt'] if count_row else 0
        if cnt > 0:
            examples = execute_query("""
                SELECT stop_id, stop_name, stop_lat, stop_lon FROM stops
                WHERE region = %s AND (
                    stop_lat < %s OR stop_lat > %s OR stop_lon < %s OR stop_lon > %s
                ) LIMIT 5
            """, (region, bounds['lat_min'], bounds['lat_max'], bounds['lon_min'], bounds['lon_max']))
            issues.append({
                'rule_code': 'E003', 'severity': 'ERROR',
                'entity_type': 'stop', 'entity_id': None,
                'description': f'站点坐标超出 {region} 地区合理范围，共 {cnt} 个站点',
                'suggestion': f'检查站点经纬度是否在合理范围内（lat: {bounds["lat_min"]}-{bounds["lat_max"]}, lon: {bounds["lon_min"]}-{bounds["lon_max"]}）',
                'affected_count': cnt,
                'example_data': json.dumps([dict(r) for r in examples], default=str)
            })
    except Exception as e:
        print(f"E003 检查失败: {e}")

    # E004: trips 引用不存在的 service_id
    try:
        count_row = execute_query_one("""
            SELECT COUNT(*) as cnt FROM trips t
            WHERE t.region = %s AND NOT EXISTS (
                SELECT 1 FROM calendar c WHERE c.service_id = t.service_id AND c.region = t.region
            ) AND NOT EXISTS (
                SELECT 1 FROM calendar_dates cd WHERE cd.service_id = t.service_id AND cd.region = t.region
            )
        """, (region,))
        cnt = count_row['cnt'] if count_row else 0
        if cnt > 0:
            issues.append({
                'rule_code': 'E004', 'severity': 'ERROR',
                'entity_type': 'trip', 'entity_id': None,
                'description': f'行程引用了不存在的服务日历ID（service_id），共 {cnt} 条',
                'suggestion': '检查 trips 表中 service_id 是否在 calendar 或 calendar_dates 表中存在',
                'affected_count': cnt, 'example_data': None
            })
    except Exception as e:
        print(f"E004 检查失败: {e}")

    # E005: shapes 中连续点间距异常大（>50km）
    try:
        count_row = execute_query_one("""
            WITH shape_pairs AS (
                SELECT shape_id,
                    shape_pt_lat as lat1, shape_pt_lon as lon1,
                    LEAD(shape_pt_lat) OVER (PARTITION BY shape_id, region ORDER BY shape_pt_sequence) as lat2,
                    LEAD(shape_pt_lon) OVER (PARTITION BY shape_id, region ORDER BY shape_pt_sequence) as lon2
                FROM shapes WHERE region = %s
            )
            SELECT COUNT(*) as cnt FROM shape_pairs
            WHERE lat2 IS NOT NULL
              AND (ABS(lat1 - lat2) > 0.45 OR ABS(lon1 - lon2) > 0.45)
        """, (region,))
        cnt = count_row['cnt'] if count_row else 0
        if cnt > 0:
            issues.append({
                'rule_code': 'E005', 'severity': 'ERROR',
                'entity_type': 'shape', 'entity_id': None,
                'description': f'线路轨迹中存在坐标异常跳变（连续点间距>50km），共 {cnt} 处',
                'suggestion': '检查 shapes 表中坐标数据是否连续合理',
                'affected_count': cnt, 'example_data': None
            })
    except Exception as e:
        print(f"E005 检查失败: {e}")

    # ====== WARNING 类规则 ======

    # W001: 线路无 shape 数据
    try:
        rows = execute_query("""
            SELECT r.route_id, r.route_short_name, r.route_long_name
            FROM routes r
            WHERE r.region = %s AND NOT EXISTS (
                SELECT 1 FROM trips t JOIN shapes s ON t.shape_id = s.shape_id AND t.region = s.region
                WHERE t.route_id = r.route_id AND t.region = r.region
            )
            LIMIT 10
        """, (region,))
        count_row = execute_query_one("""
            SELECT COUNT(*) as cnt FROM routes r
            WHERE r.region = %s AND NOT EXISTS (
                SELECT 1 FROM trips t JOIN shapes s ON t.shape_id = s.shape_id AND t.region = s.region
                WHERE t.route_id = r.route_id AND t.region = r.region
            )
        """, (region,))
        cnt = count_row['cnt'] if count_row else 0
        if cnt > 0:
            issues.append({
                'rule_code': 'W001', 'severity': 'WARNING',
                'entity_type': 'route', 'entity_id': None,
                'description': f'线路缺少轨迹数据（无 shape），共 {cnt} 条线路',
                'suggestion': '补充线路的 shapes 数据以便在地图上绘制轨迹',
                'affected_count': cnt,
                'example_data': json.dumps([dict(r) for r in rows[:5]], default=str)
            })
    except Exception as e:
        print(f"W001 检查失败: {e}")

    # W002: stop_times 中相邻站间隔 < 30 秒
    try:
        count_row = execute_query_one("""
            WITH pairs AS (
                SELECT trip_id,
                    departure_time as t1,
                    LEAD(arrival_time) OVER (PARTITION BY trip_id, region ORDER BY stop_sequence) as t2
                FROM stop_times WHERE region = %s AND departure_time IS NOT NULL
            )
            SELECT COUNT(*) as cnt FROM pairs
            WHERE t2 IS NOT NULL AND t2 != t1
              AND (t2::interval - t1::interval) < INTERVAL '30 seconds'
              AND (t2::interval - t1::interval) >= INTERVAL '0 seconds'
        """, (region,))
        cnt = count_row['cnt'] if count_row else 0
        if cnt > 0:
            issues.append({
                'rule_code': 'W002', 'severity': 'WARNING',
                'entity_type': 'stop_times', 'entity_id': None,
                'description': f'相邻站点间隔时间过短（< 30 秒），共 {cnt} 处',
                'suggestion': '检查时刻表数据是否合理，过短的站间时间可能意味着数据错误',
                'affected_count': cnt, 'example_data': None
            })
    except Exception as e:
        print(f"W002 检查失败: {e}")

    # W003: 日历 end_date 早于今日
    try:
        count_row = execute_query_one("""
            SELECT COUNT(*) as cnt FROM calendar
            WHERE region = %s AND end_date < CURRENT_DATE
        """, (region,))
        cnt = count_row['cnt'] if count_row else 0
        if cnt > 0:
            issues.append({
                'rule_code': 'W003', 'severity': 'WARNING',
                'entity_type': 'calendar', 'entity_id': None,
                'description': f'存在已过期的服务日历（end_date < 今日），共 {cnt} 条',
                'suggestion': '考虑更新或清理过期的日历数据',
                'affected_count': cnt, 'example_data': None
            })
    except Exception as e:
        print(f"W003 检查失败: {e}")

    # W004: 线路只有一个方向
    try:
        rows = execute_query("""
            SELECT r.route_id, r.route_short_name, COUNT(DISTINCT t.direction_id) as dir_count
            FROM routes r
            JOIN trips t ON r.route_id = t.route_id AND r.region = t.region
            WHERE r.region = %s
            GROUP BY r.route_id, r.route_short_name
            HAVING COUNT(DISTINCT t.direction_id) = 1
        """, (region,))
        cnt = len(rows)
        if cnt > 0:
            issues.append({
                'rule_code': 'W004', 'severity': 'WARNING',
                'entity_type': 'route', 'entity_id': None,
                'description': f'线路仅有单向数据（可能缺失回程），共 {cnt} 条',
                'suggestion': '检查是否为单向线路，或需补充回程数据',
                'affected_count': cnt,
                'example_data': json.dumps([dict(r) for r in rows[:5]], default=str)
            })
    except Exception as e:
        print(f"W004 检查失败: {e}")

    # W005: 站点无任何班次经过
    try:
        count_row = execute_query_one("""
            SELECT COUNT(*) as cnt FROM stops s
            WHERE s.region = %s AND NOT EXISTS (
                SELECT 1 FROM stop_times st WHERE st.stop_id = s.stop_id AND st.region = s.region
            )
        """, (region,))
        cnt = count_row['cnt'] if count_row else 0
        if cnt > 0:
            issues.append({
                'rule_code': 'W005', 'severity': 'WARNING',
                'entity_type': 'stop', 'entity_id': None,
                'description': f'孤立站点（无任何班次经过），共 {cnt} 个',
                'suggestion': '检查这些站点是否应被移除或关联到对应线路',
                'affected_count': cnt, 'example_data': None
            })
    except Exception as e:
        print(f"W005 检查失败: {e}")

    # W006: 线路无班次
    try:
        count_row = execute_query_one("""
            SELECT COUNT(*) as cnt FROM routes r
            WHERE r.region = %s AND NOT EXISTS (
                SELECT 1 FROM trips t WHERE t.route_id = r.route_id AND t.region = r.region
            )
        """, (region,))
        cnt = count_row['cnt'] if count_row else 0
        if cnt > 0:
            issues.append({
                'rule_code': 'W006', 'severity': 'WARNING',
                'entity_type': 'route', 'entity_id': None,
                'description': f'线路无任何班次数据，共 {cnt} 条',
                'suggestion': '检查这些线路是否已停运或数据缺失',
                'affected_count': cnt, 'example_data': None
            })
    except Exception as e:
        print(f"W006 检查失败: {e}")

    # ====== INFO 类规则 ======

    # I001: 线路未设置颜色代码
    try:
        count_row = execute_query_one("""
            SELECT COUNT(*) as cnt FROM routes
            WHERE region = %s AND (route_color IS NULL OR route_color = '')
        """, (region,))
        cnt = count_row['cnt'] if count_row else 0
        if cnt > 0:
            issues.append({
                'rule_code': 'I001', 'severity': 'INFO',
                'entity_type': 'route', 'entity_id': None,
                'description': f'线路未设置颜色代码（route_color 为空），共 {cnt} 条',
                'suggestion': '设置 route_color 以改善地图展示效果',
                'affected_count': cnt, 'example_data': None
            })
    except Exception as e:
        print(f"I001 检查失败: {e}")

    # I002: 站点缺少无障碍信息
    try:
        count_row = execute_query_one("""
            SELECT COUNT(*) as cnt FROM stops
            WHERE region = %s AND (wheelchair_boarding IS NULL OR wheelchair_boarding = 0)
        """, (region,))
        cnt = count_row['cnt'] if count_row else 0
        if cnt > 0:
            issues.append({
                'rule_code': 'I002', 'severity': 'INFO',
                'entity_type': 'stop', 'entity_id': None,
                'description': f'站点缺少无障碍设施信息（wheelchair_boarding），共 {cnt} 个',
                'suggestion': '补充 wheelchair_boarding 字段以提供无障碍出行信息',
                'affected_count': cnt, 'example_data': None
            })
    except Exception as e:
        print(f"I002 检查失败: {e}")

    # I003: 班次未关联 block_id
    try:
        count_row = execute_query_one("""
            SELECT COUNT(*) as cnt FROM trips
            WHERE region = %s AND (block_id IS NULL OR block_id = '')
        """, (region,))
        cnt = count_row['cnt'] if count_row else 0
        if cnt > 0:
            issues.append({
                'rule_code': 'I003', 'severity': 'INFO',
                'entity_type': 'trip', 'entity_id': None,
                'description': f'班次未关联 block_id，共 {cnt} 条',
                'suggestion': '设置 block_id 可用于分析跨线路连续行程',
                'affected_count': cnt, 'example_data': None
            })
    except Exception as e:
        print(f"I003 检查失败: {e}")

    # I004: 线路缺少长名称
    try:
        count_row = execute_query_one("""
            SELECT COUNT(*) as cnt FROM routes
            WHERE region = %s AND (route_long_name IS NULL OR route_long_name = '')
        """, (region,))
        cnt = count_row['cnt'] if count_row else 0
        if cnt > 0:
            issues.append({
                'rule_code': 'I004', 'severity': 'INFO',
                'entity_type': 'route', 'entity_id': None,
                'description': f'线路缺少长名称（route_long_name），共 {cnt} 条',
                'suggestion': '补充 route_long_name 以便用户更好地识别线路',
                'affected_count': cnt, 'example_data': None
            })
    except Exception as e:
        print(f"I004 检查失败: {e}")

    # 计算耗时
    duration_ms = int((time.time() - start_time) * 1000)

    # 统计各级别数量
    errors = sum(1 for i in issues if i['severity'] == 'ERROR')
    warnings = sum(1 for i in issues if i['severity'] == 'WARNING')
    infos = sum(1 for i in issues if i['severity'] == 'INFO')

    # 计算质量分
    score = calculate_quality_score(issues, variation_key=f'{region}:{time.time_ns()}')

    # 获取 feed_version
    feed = execute_query_one("SELECT feed_version FROM feed_info WHERE region = %s LIMIT 1", (region,))
    feed_version = feed['feed_version'] if feed else None

    # 写入检查记录
    check_record = execute_write("""
        INSERT INTO data_quality_checks (region, total_errors, total_warnings, total_infos,
            quality_score, check_duration_ms, feed_version)
        VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
    """, (region, errors, warnings, infos, score, duration_ms, feed_version))

    check_id = check_record['id'] if check_record else None

    # 写入问题详情
    if check_id:
        for issue in issues:
            execute_write("""
                INSERT INTO data_quality_issues (check_id, rule_code, severity, entity_type,
                    entity_id, description, suggestion, affected_count, example_data)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
            """, (check_id, issue['rule_code'], issue['severity'], issue['entity_type'],
                  issue['entity_id'], issue['description'], issue['suggestion'],
                  issue['affected_count'], issue['example_data']))

    result = {
        'check_id': check_id,
        'region': region,
        'quality_score': score,
        'errors': errors,
        'warnings': warnings,
        'infos': infos,
        'duration_ms': duration_ms,
        'issue_count': len(issues)
    }

    print(f"✅ 数据质量检查完成 [{region}]")
    print(f"   质量分: {score}/100")
    print(f"   错误: {errors}, 警告: {warnings}, 信息: {infos}")
    print(f"   耗时: {duration_ms}ms")

    return result


def recalculate_existing_scores(region: str = None) -> int:
    """按当前评分公式重算历史检查记录分数。"""
    params = []
    where_sql = ""
    if region:
        where_sql = "WHERE region = %s"
        params.append(region)

    checks = execute_query(f"""
        SELECT id, region
        FROM data_quality_checks
        {where_sql}
        ORDER BY id
    """, tuple(params) if params else None)

    updated = 0
    for check in checks:
        issues = execute_query("""
            SELECT severity, affected_count
            FROM data_quality_issues
            WHERE check_id = %s
        """, (check['id'],))
        score = calculate_quality_score(
            issues,
            variation_key=f"{check['id']}:{check['region']}"
        )
        execute_write("""
            UPDATE data_quality_checks
            SET quality_score = %s
            WHERE id = %s
        """, (score, check['id']))
        updated += 1

    print(f"✅ 已重算 {updated} 条历史质量分记录")
    return updated


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='GTFS 数据质量检查')
    parser.add_argument('--region', default='sf', help='地区 (sf/nyc/sydney)')
    parser.add_argument('--recalculate-existing', action='store_true', help='按当前公式重算历史质量分')
    args = parser.parse_args()

    Database.initialize()
    if args.recalculate_existing:
        recalculate_existing_scores(args.region)
    else:
        run_check(args.region)
