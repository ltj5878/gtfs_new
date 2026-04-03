#!/usr/bin/env python3
"""
站点客流预测服务
"""

from __future__ import annotations

from datetime import datetime

from core.db import execute_query, execute_write


_DAY_FILTERS = {
    'weekday': "(c.monday = 1 OR c.tuesday = 1 OR c.wednesday = 1 OR c.thursday = 1 OR c.friday = 1)",
    'weekend': "(c.saturday = 1 OR c.sunday = 1)",
}


def _normalize_prediction_rows(rows):
    normalized = []
    for row in rows:
        normalized.append({
            'hour_of_day': int(row['hour_of_day']),
            'scheduled_trips': int(row['scheduled_trips'] or 0),
            'predicted_flow_index': round(float(row['predicted_flow_index'] or 0), 2),
        })
    return normalized


def _day_filter(day_type: str) -> str:
    return _DAY_FILTERS.get(day_type, _DAY_FILTERS['weekday'])


def compute_stop_flow(stop_id: str, region: str, day_type: str = 'weekday', persist: bool = False):
    """实时计算站点 24 小时客流指数。"""
    rows = execute_query(f"""
        SELECT
            MOD(EXTRACT(HOUR FROM st.departure_time::interval)::int, 24) as hour_of_day,
            COUNT(*) as trip_count
        FROM stop_times st
        JOIN trips t ON st.trip_id = t.trip_id AND st.region = t.region
        JOIN calendar c ON t.service_id = c.service_id AND t.region = c.region
        WHERE st.stop_id = %s
          AND st.region = %s
          AND ({_day_filter(day_type)})
          AND st.departure_time IS NOT NULL
        GROUP BY hour_of_day
        ORDER BY hour_of_day
    """, (stop_id, region))

    if not rows:
        return []

    counts = {int(r['hour_of_day']): int(r['trip_count']) for r in rows}
    avg_count = sum(counts.values()) / max(len(counts), 1)

    result = []
    for hour in range(24):
        trip_count = counts.get(hour, 0)
        flow_index = round(trip_count / max(avg_count, 1) * 100, 2) if avg_count > 0 else 0
        result.append({
            'hour_of_day': hour,
            'scheduled_trips': trip_count,
            'predicted_flow_index': flow_index,
        })

    if persist:
        for item in result:
            execute_write("""
                INSERT INTO stop_flow_predictions
                    (stop_id, region, day_type, hour_of_day, scheduled_trips, predicted_flow_index, computed_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (stop_id, region, day_type, hour_of_day)
                DO UPDATE SET
                    scheduled_trips = EXCLUDED.scheduled_trips,
                    predicted_flow_index = EXCLUDED.predicted_flow_index,
                    computed_at = NOW()
            """, (
                stop_id,
                region,
                day_type,
                item['hour_of_day'],
                item['scheduled_trips'],
                item['predicted_flow_index'],
            ))

    return result


def get_stop_flow_prediction_data(stop_id: str, region: str, day_type: str = 'weekday', refresh: bool = False):
    """优先读取缓存，不足时实时计算并回填。"""
    if not refresh:
        cached = execute_query("""
            SELECT hour_of_day, scheduled_trips, predicted_flow_index
            FROM stop_flow_predictions
            WHERE stop_id = %s AND region = %s AND day_type = %s
            ORDER BY hour_of_day
        """, (stop_id, region, day_type))
        if len(cached) == 24:
            return _normalize_prediction_rows(cached)

    return compute_stop_flow(stop_id, region, day_type, persist=True)


def get_flow_heatmap_data(region: str, hour: int | None = None, day_type: str = 'weekday', limit: int = 500):
    """按当前时刻实时计算所有站点的客流热力图。"""
    if hour is None:
        hour = datetime.now().hour

    rows = execute_query(f"""
        WITH hourly_counts AS (
            SELECT
                st.stop_id,
                COUNT(*) as trip_count
            FROM stop_times st
            JOIN trips t ON st.trip_id = t.trip_id AND st.region = t.region
            JOIN calendar c ON t.service_id = c.service_id AND t.region = c.region
            WHERE st.region = %s
              AND MOD(EXTRACT(HOUR FROM st.departure_time::interval)::int, 24) = %s
              AND ({_day_filter(day_type)})
              AND st.departure_time IS NOT NULL
            GROUP BY st.stop_id
        ),
        scored AS (
            SELECT
                hc.stop_id,
                hc.trip_count,
                ROUND(hc.trip_count * 100.0 / NULLIF(AVG(hc.trip_count) OVER (), 0), 2) as predicted_flow_index
            FROM hourly_counts hc
        )
        SELECT
            s.stop_id,
            s.stop_name,
            s.stop_lat,
            s.stop_lon,
            sc.trip_count as scheduled_trips,
            sc.predicted_flow_index
        FROM scored sc
        JOIN stops s ON sc.stop_id = s.stop_id AND s.region = %s
        WHERE sc.trip_count > 0
        ORDER BY sc.predicted_flow_index DESC, sc.trip_count DESC
        LIMIT %s
    """, (region, hour, region, limit))

    result = []
    for row in rows:
        result.append({
            'stop_id': row['stop_id'],
            'stop_name': row['stop_name'],
            'stop_lat': float(row['stop_lat']),
            'stop_lon': float(row['stop_lon']),
            'scheduled_trips': int(row['scheduled_trips'] or 0),
            'predicted_flow_index': round(float(row['predicted_flow_index'] or 0), 2),
        })
    return result
