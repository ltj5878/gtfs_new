#!/usr/bin/env python3
"""
异常告警生成服务
"""

from __future__ import annotations

import json
from datetime import datetime, time, timedelta

from core.db import execute_query, execute_query_one, execute_write
from services.flow_prediction_service import get_flow_heatmap_data


_GENERATED_SOURCE = 'system_generated'


def _route_severity(punctuality_rate: float, avg_delay_seconds: float) -> str:
    if punctuality_rate < 60 or avg_delay_seconds >= 420:
        return 'critical'
    if punctuality_rate < 70 or avg_delay_seconds >= 300:
        return 'high'
    if punctuality_rate < 80 or avg_delay_seconds >= 180:
        return 'medium'
    return 'low'


def _insert_alert(alert: dict) -> None:
    execute_write("""
        INSERT INTO anomaly_alerts
            (region, alert_type, entity_type, entity_id, entity_name, severity,
             title, alert_data, triggered_at, resolved_at, notified)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s)
    """, (
        alert['region'],
        alert['alert_type'],
        alert['entity_type'],
        alert['entity_id'],
        alert.get('entity_name'),
        alert['severity'],
        alert['title'],
        json.dumps(alert.get('alert_data') or {}, ensure_ascii=False),
        alert['triggered_at'],
        alert.get('resolved_at'),
        alert.get('notified', False),
    ))


def _build_vehicle_alert(region: str):
    row = execute_query_one("""
        SELECT
            vp.vehicle_id,
            vp.route_id,
            COALESCE(r.route_short_name, vp.route_id) as route_name,
            COUNT(*) as sample_count,
            EXTRACT(EPOCH FROM MAX(vp.position_timestamp) - MIN(vp.position_timestamp)) as span_seconds
        FROM realtime_vehicle_positions vp
        LEFT JOIN routes r ON vp.route_id = r.route_id AND vp.region = r.region
        WHERE vp.region = %s
        GROUP BY vp.vehicle_id, vp.route_id, route_name
        HAVING COUNT(*) >= 5
        ORDER BY span_seconds DESC NULLS LAST, sample_count DESC
        LIMIT 1
    """, (region,))
    if not row:
        return None

    span_seconds = float(row['span_seconds'] or 0)
    severity = 'high' if span_seconds >= 600 else 'medium'
    return {
        'region': region,
        'alert_type': 'vehicle_stall',
        'entity_type': 'vehicle',
        'entity_id': row['vehicle_id'],
        'entity_name': f"{row['route_name']} / {row['vehicle_id']}",
        'severity': severity,
        'title': f"车辆 {row['vehicle_id']} 疑似长时间滞留",
        'alert_data': {
            'source': _GENERATED_SOURCE,
            'route_id': row['route_id'],
            'sample_count': int(row['sample_count'] or 0),
            'stall_span_seconds': round(span_seconds, 1),
        },
        'triggered_at': datetime.now() - timedelta(minutes=10),
        'resolved_at': None,
        'notified': False,
    }


def _build_route_alerts(region: str):
    latest_date_row = execute_query_one(
        "SELECT MAX(stat_date) as stat_date FROM route_daily_punctuality WHERE region = %s",
        (region,),
    )
    if not latest_date_row or not latest_date_row['stat_date']:
        return []

    stat_date = latest_date_row['stat_date']
    route_rows = execute_query("""
        SELECT
            rdp.route_id,
            COALESCE(r.route_short_name, rdp.route_id) as route_short_name,
            r.route_long_name,
            COALESCE(rdp.punctuality_rate, 0) as punctuality_rate,
            COALESCE(rdp.avg_arrival_delay, 0) as avg_arrival_delay
        FROM route_daily_punctuality rdp
        JOIN routes r ON rdp.route_id = r.route_id AND rdp.region = r.region
        WHERE rdp.region = %s
          AND rdp.stat_date = %s
        ORDER BY rdp.punctuality_rate ASC, rdp.avg_arrival_delay DESC
        LIMIT 4
    """, (region, stat_date))

    alerts = []
    for idx, row in enumerate(route_rows):
        punctuality_rate = float(row['punctuality_rate'] or 0)
        avg_delay = float(row['avg_arrival_delay'] or 0)
        if idx == 0:
            alert_type = 'route_delay'
            title = f"线路 {row['route_short_name']} 准点率偏低"
        else:
            alert_type = 'segment_slow'
            title = f"线路 {row['route_short_name']} 区间运行偏慢"

        alerts.append({
            'region': region,
            'alert_type': alert_type,
            'entity_type': 'route',
            'entity_id': row['route_id'],
            'entity_name': row['route_long_name'] or row['route_short_name'],
            'severity': _route_severity(punctuality_rate, avg_delay),
            'title': title,
            'alert_data': {
                'source': _GENERATED_SOURCE,
                'stat_date': str(stat_date),
                'punctuality_rate': round(punctuality_rate, 2),
                'avg_arrival_delay_seconds': round(avg_delay, 2),
            },
            'triggered_at': datetime.now() - timedelta(minutes=20 + idx * 6),
            'resolved_at': None,
            'notified': False,
        })
    return alerts


def _build_stop_alert(region: str):
    heatmap = get_flow_heatmap_data(region, limit=8)
    if not heatmap:
        return None

    top_stop = heatmap[0]
    severity = 'critical' if top_stop['predicted_flow_index'] >= 180 else 'high'
    return {
        'region': region,
        'alert_type': 'stop_congestion',
        'entity_type': 'stop',
        'entity_id': top_stop['stop_id'],
        'entity_name': top_stop['stop_name'],
        'severity': severity,
        'title': f"站点 {top_stop['stop_name']} 客流明显拥挤",
        'alert_data': {
            'source': _GENERATED_SOURCE,
            'predicted_flow_index': top_stop['predicted_flow_index'],
            'scheduled_trips': top_stop['scheduled_trips'],
        },
        'triggered_at': datetime.now() - timedelta(minutes=5),
        'resolved_at': None,
        'notified': False,
    }


def _build_history_alerts(region: str):
    history_days = execute_query("""
        SELECT DISTINCT stat_date
        FROM route_daily_punctuality
        WHERE region = %s
        ORDER BY stat_date DESC
        LIMIT 7
    """, (region,))

    alerts = []
    for day_index, item in enumerate(history_days[1:], start=1):
        stat_date = item['stat_date']
        route_row = execute_query_one("""
            SELECT
                rdp.route_id,
                COALESCE(r.route_short_name, rdp.route_id) as route_short_name,
                r.route_long_name,
                COALESCE(rdp.punctuality_rate, 0) as punctuality_rate,
                COALESCE(rdp.avg_arrival_delay, 0) as avg_arrival_delay
            FROM route_daily_punctuality rdp
            JOIN routes r ON rdp.route_id = r.route_id AND rdp.region = r.region
            WHERE rdp.region = %s
              AND rdp.stat_date = %s
            ORDER BY rdp.punctuality_rate ASC, rdp.avg_arrival_delay DESC
            LIMIT 1
        """, (region, stat_date))
        if not route_row:
            continue

        punctuality_rate = float(route_row['punctuality_rate'] or 0)
        avg_delay = float(route_row['avg_arrival_delay'] or 0)
        triggered_at = datetime.combine(stat_date, time(8 + (day_index % 4), 15))
        resolved_at = triggered_at + timedelta(hours=2 + (day_index % 3))
        alerts.append({
            'region': region,
            'alert_type': 'route_delay' if day_index % 2 else 'segment_slow',
            'entity_type': 'route',
            'entity_id': route_row['route_id'],
            'entity_name': route_row['route_long_name'] or route_row['route_short_name'],
            'severity': _route_severity(punctuality_rate, avg_delay),
            'title': f"线路 {route_row['route_short_name']} 历史运行异常",
            'alert_data': {
                'source': _GENERATED_SOURCE,
                'stat_date': str(stat_date),
                'punctuality_rate': round(punctuality_rate, 2),
                'avg_arrival_delay_seconds': round(avg_delay, 2),
            },
            'triggered_at': triggered_at,
            'resolved_at': resolved_at,
            'notified': True,
        })
    return alerts


def build_generated_alerts(region: str):
    alerts = []

    vehicle_alert = _build_vehicle_alert(region)
    if vehicle_alert:
        alerts.append(vehicle_alert)

    alerts.extend(_build_route_alerts(region))

    stop_alert = _build_stop_alert(region)
    if stop_alert:
        alerts.append(stop_alert)

    alerts.extend(_build_history_alerts(region))
    return alerts


def ensure_alert_data(region: str, force_refresh: bool = False) -> None:
    """为空表或刷新动作补充系统生成告警。"""
    total_row = execute_query_one(
        "SELECT COUNT(*) as cnt FROM anomaly_alerts WHERE region = %s",
        (region,),
    )
    total_count = int(total_row['cnt'] or 0) if total_row else 0

    if not force_refresh and total_count > 0:
        return

    execute_write("""
        DELETE FROM anomaly_alerts
        WHERE region = %s
          AND COALESCE(alert_data->>'source', '') = %s
    """, (region, _GENERATED_SOURCE))

    remaining_row = execute_query_one(
        "SELECT COUNT(*) as cnt FROM anomaly_alerts WHERE region = %s",
        (region,),
    )
    remaining_count = int(remaining_row['cnt'] or 0) if remaining_row else 0
    if remaining_count > 0 and not force_refresh:
        return

    for alert in build_generated_alerts(region):
        _insert_alert(alert)
