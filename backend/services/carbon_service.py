#!/usr/bin/env python3
"""
碳排放计算与演示数据服务
"""

from __future__ import annotations

import math
import random
from datetime import date, timedelta

from core.db import execute_query, execute_query_one, execute_write


EMISSION_FACTORS = {
    0: 0.041,
    1: 0.041,
    2: 0.041,
    3: 0.089,
    4: 0.120,
    5: 0.041,
    6: 0.020,
    7: 0.020,
}
CAR_EMISSION = 0.271


def get_route_summary(route_id: str, region: str) -> dict | None:
    """获取线路基础信息。"""
    route = execute_query_one("""
        SELECT
            route_id,
            route_short_name,
            route_long_name,
            route_type
        FROM routes
        WHERE route_id = %s AND region = %s
        LIMIT 1
    """, (route_id, region))
    return dict(route) if route else None


def calc_shape_distance(points) -> float:
    """计算 shape 点序列总长度。"""
    total = 0.0
    for i in range(len(points) - 1):
        lat1 = float(points[i]['shape_pt_lat'])
        lon1 = float(points[i]['shape_pt_lon'])
        lat2 = float(points[i + 1]['shape_pt_lat'])
        lon2 = float(points[i + 1]['shape_pt_lon'])

        radius = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(dlon / 2) ** 2
        )
        total += radius * (2 * math.asin(math.sqrt(a)))
    return total


def get_route_distance_km(route_id: str, region: str) -> float:
    """获取线路里程，优先缓存。"""
    dist = execute_query_one(
        "SELECT distance_km FROM route_distances WHERE route_id = %s AND region = %s LIMIT 1",
        (route_id, region),
    )
    if dist and dist['distance_km']:
        return float(dist['distance_km'])

    shape_row = execute_query_one("""
        SELECT t.shape_id
        FROM trips t
        WHERE t.route_id = %s
          AND t.region = %s
          AND t.shape_id IS NOT NULL
        LIMIT 1
    """, (route_id, region))

    if shape_row and shape_row['shape_id']:
        points = execute_query("""
            SELECT shape_pt_lat, shape_pt_lon
            FROM shapes
            WHERE shape_id = %s AND region = %s
            ORDER BY shape_pt_sequence
        """, (shape_row['shape_id'], region))
        distance_km = calc_shape_distance(points)
    else:
        stop_count_row = execute_query_one("""
            SELECT COUNT(DISTINCT st.stop_id) as cnt
            FROM stop_times st
            JOIN trips t ON st.trip_id = t.trip_id AND st.region = t.region
            WHERE t.route_id = %s AND t.region = %s
        """, (route_id, region))
        stop_count = int(stop_count_row['cnt'] or 0) if stop_count_row else 0
        distance_km = max(2.0, stop_count * 0.8)

    if distance_km > 0:
        execute_write("""
            INSERT INTO route_distances (route_id, region, direction_id, distance_km)
            VALUES (%s, %s, 0, %s)
            ON CONFLICT (route_id, region, direction_id)
            DO UPDATE SET
                distance_km = EXCLUDED.distance_km,
                calculated_at = NOW()
        """, (route_id, region, round(distance_km, 3)))

    return distance_km


def calculate_route_carbon(route_id: str, region: str) -> dict:
    """计算线路碳排放对比。"""
    route = get_route_summary(route_id, region)
    if not route:
        raise ValueError('线路不存在')

    route_type = int(route['route_type']) if route['route_type'] is not None else 3

    distance_km = get_route_distance_km(route_id, region)
    transit_factor = EMISSION_FACTORS.get(route_type, 0.089)
    transit_emission = round(distance_km * transit_factor, 4)
    car_emission = round(distance_km * CAR_EMISSION, 4)
    carbon_saved = round(car_emission - transit_emission, 4)

    return {
        'route_id': route_id,
        'route_short_name': route.get('route_short_name') or route_id,
        'route_long_name': route.get('route_long_name') or '',
        'distance_km': round(distance_km, 2),
        'route_type': route_type,
        'transit_emission_kg': transit_emission,
        'car_emission_kg': car_emission,
        'carbon_saved_kg': carbon_saved,
        'saving_percent': round((1 - transit_emission / max(car_emission, 0.001)) * 100, 1),
        'trees_equivalent_yearly': round(carbon_saved / 21.77 * 365, 1),
        'fuel_saved_liters': round(distance_km / 8.5, 2),
    }


def build_trip_carbon_record(route_id: str, region: str, ride_count: int = 1, ride_distance_km: float | None = None) -> dict:
    """按用户录入的线路与次数生成一条碳排放记录。"""
    route_metrics = calculate_route_carbon(route_id, region)
    ride_count = max(1, min(int(ride_count or 1), 50))

    default_distance = float(route_metrics['distance_km'])
    try:
        parsed_distance = float(ride_distance_km) if ride_distance_km not in (None, '') else None
    except (TypeError, ValueError) as exc:
        raise ValueError('实际乘坐距离格式错误') from exc
    single_distance = parsed_distance if parsed_distance and parsed_distance > 0 else default_distance
    single_distance = round(max(0.5, min(single_distance, 200.0)), 2)

    route_type = int(route_metrics['route_type'])
    transit_factor = EMISSION_FACTORS.get(route_type, 0.089)
    single_transit = round(single_distance * transit_factor, 4)
    single_car = round(single_distance * CAR_EMISSION, 4)
    single_saved = round(single_car - single_transit, 4)

    total_distance = round(single_distance * ride_count, 2)
    total_transit = round(single_transit * ride_count, 4)
    total_car = round(single_car * ride_count, 4)
    total_saved = round(single_saved * ride_count, 4)

    return {
        'route_id': route_id,
        'region': region,
        'route_short_name': route_metrics.get('route_short_name') or route_id,
        'route_long_name': route_metrics.get('route_long_name') or '',
        'ride_count': ride_count,
        'single_distance_km': single_distance,
        'distance_km': total_distance,
        'transit_emission': total_transit,
        'car_emission': total_car,
        'carbon_saved': total_saved,
        'single_transit_emission': single_transit,
        'single_car_emission': single_car,
        'single_carbon_saved': single_saved,
        'saving_percent': route_metrics['saving_percent'],
    }


def ensure_demo_carbon_data(region: str, force_refresh: bool = False) -> None:
    """当用户尚无记录时，生成一组可演示的合理碳减排数据。"""
    if force_refresh:
        execute_write(
            "DELETE FROM user_carbon_records WHERE region = %s AND record_source = 'demo'",
            (region,),
        )

    total_row = execute_query_one(
        "SELECT COUNT(*) as cnt FROM user_carbon_records WHERE region = %s",
        (region,),
    )
    total_count = int(total_row['cnt'] or 0) if total_row else 0
    if total_count > 0 and not force_refresh:
        return

    users = execute_query("""
        SELECT id, username
        FROM users
        WHERE is_active = TRUE
        ORDER BY id
        LIMIT 8
    """)
    if not users:
        return

    routes = execute_query("""
        SELECT
            r.route_id,
            r.route_type,
            COALESCE(r.route_short_name, r.route_id) as route_short_name,
            COALESCE(rdp.punctuality_rate, 80) as punctuality_rate
        FROM routes r
        LEFT JOIN route_daily_punctuality rdp
            ON r.route_id = rdp.route_id
           AND r.region = rdp.region
           AND rdp.stat_date = (
                SELECT MAX(stat_date)
                FROM route_daily_punctuality
                WHERE region = %s
           )
        WHERE r.region = %s
        ORDER BY punctuality_rate DESC NULLS LAST, route_short_name
        LIMIT 40
    """, (region, region))
    if not routes:
        return

    seed_marker = date.today().toordinal()
    if force_refresh:
        seed_marker += random.randint(1, 10000)

    distance_cache = {}
    today = date.today()

    for user in users:
        rng = random.Random(f"{region}:{user['id']}:{seed_marker}")
        trip_total = rng.randint(8, 18)

        for trip_index in range(trip_total):
            route = routes[(trip_index + user['id']) % len(routes)]
            route_id = route['route_id']
            route_type = int(route['route_type']) if route['route_type'] is not None else 3

            if route_id not in distance_cache:
                distance_cache[route_id] = calculate_route_carbon(route_id, region)
            metrics = distance_cache[route_id]

            distance_multiplier = rng.uniform(0.45, 0.95)
            distance_km = round(max(2.0, metrics['distance_km'] * distance_multiplier), 2)
            transit_emission = round(distance_km * EMISSION_FACTORS.get(route_type, 0.089), 4)
            car_emission = round(distance_km * CAR_EMISSION, 4)
            carbon_saved = round(car_emission - transit_emission, 4)

            weekday_bias = rng.randint(0, 20)
            if weekday_bias <= 14:
                trip_date = today - timedelta(days=rng.randint(0, 13))
            else:
                trip_date = today - timedelta(days=rng.randint(14, 27))

            execute_write("""
                INSERT INTO user_carbon_records
                    (user_id, route_id, region, trip_date, ride_count, distance_km,
                     transit_emission, car_emission, carbon_saved, record_source)
                VALUES (%s, %s, %s, %s, 1, %s, %s, %s, %s, 'demo')
            """, (
                user['id'],
                route_id,
                region,
                trip_date,
                distance_km,
                transit_emission,
                car_emission,
                carbon_saved,
            ))
