#!/usr/bin/env python3
"""
站点可达性分析
"""

from typing import Any, Dict, List, Optional, Set

from core.db import execute_query, execute_query_one
from business_logic.transfer_planner import (
    _get_routes_through_stops,
    _get_stops_for_trips,
)


MAX_REACHABILITY_MINUTES = 90
MAX_TRIPS_PER_ROUND = 50
DEFAULT_BOARDING_WAIT_MINUTES = 2
DEFAULT_DEPART_TIME = '08:00:00'


def _time_to_seconds(time_text: str) -> int:
    if not time_text:
        raise ValueError('时间不能为空')

    parts = str(time_text).strip().split(':')
    if len(parts) == 2:
        hours, minutes = parts
        seconds = '0'
    elif len(parts) == 3:
        hours, minutes, seconds = parts
    else:
        raise ValueError(f'非法时间格式: {time_text}')

    return int(hours) * 3600 + int(minutes) * 60 + int(seconds)


def _seconds_to_minutes(seconds: int) -> int:
    return max(0, (seconds + 59) // 60)


def _elapsed_seconds(start_seconds: int, end_seconds: int) -> int:
    if end_seconds >= start_seconds:
        return end_seconds - start_seconds
    return (end_seconds + 24 * 3600) - start_seconds


def _normalize_time_for_sort(raw_seconds: int, baseline_seconds: int) -> int:
    if raw_seconds >= baseline_seconds:
        return raw_seconds
    return raw_seconds + 24 * 3600


def _get_stop_info(stop_id: str, region: str) -> Optional[Dict[str, Any]]:
    return execute_query_one(
        """
        SELECT stop_id, stop_name, stop_lat, stop_lon
        FROM stops
        WHERE stop_id = %s AND region = %s
        """,
        (stop_id, region)
    )


def _get_stop_locations(stop_ids: List[str], region: str) -> Dict[str, Dict[str, Any]]:
    if not stop_ids:
        return {}

    placeholders = ','.join(['%s'] * len(stop_ids))
    rows = execute_query(
        f"""
        SELECT stop_id, stop_name, stop_lat, stop_lon
        FROM stops
        WHERE stop_id IN ({placeholders}) AND region = %s
        """,
        tuple(stop_ids + [region])
    )
    return {row['stop_id']: row for row in rows}


def _build_layer_limits(max_minutes: int) -> List[int]:
    preset_limits = [15, 30, 45, 60, 75, 90]
    limits = [limit for limit in preset_limits if limit <= max_minutes]
    if not limits:
        limits = [min(15, max_minutes)]
    return limits


def _select_representative_trips(
    stop_routes: Dict[str, List[Dict[str, Any]]],
    depart_seconds: int
) -> Set[str]:
    trip_rows: Dict[str, Dict[str, Any]] = {}

    for routes in stop_routes.values():
        for route in routes:
            trip_id = route.get('trip_id')
            if not trip_id:
                continue

            depart_time = route.get('departure_time') or DEFAULT_DEPART_TIME
            try:
                sort_seconds = _normalize_time_for_sort(
                    _time_to_seconds(depart_time),
                    depart_seconds
                )
            except ValueError:
                sort_seconds = depart_seconds

            current = trip_rows.get(trip_id)
            if current is None or sort_seconds < current['sort_seconds']:
                trip_rows[trip_id] = {
                    'trip_id': trip_id,
                    'sort_seconds': sort_seconds
                }

    ordered = sorted(trip_rows.values(), key=lambda item: item['sort_seconds'])
    return {item['trip_id'] for item in ordered[:MAX_TRIPS_PER_ROUND]}


def find_reachable_stops(
    origin_stop_id: str,
    region: str,
    max_minutes: int = 60,
    depart_time: str = DEFAULT_DEPART_TIME,
    boarding_wait_minutes: int = DEFAULT_BOARDING_WAIT_MINUTES
) -> Dict[str, Any]:
    origin_stop = _get_stop_info(origin_stop_id, region)
    if not origin_stop:
        return {'error': f'起点站不存在: {origin_stop_id}'}

    depart_seconds = _time_to_seconds(depart_time)
    max_minutes = max(1, min(int(max_minutes), MAX_REACHABILITY_MINUTES))
    max_seconds = max_minutes * 60
    boarding_wait_seconds = max(0, boarding_wait_minutes) * 60

    dist_seconds: Dict[str, int] = {origin_stop_id: 0}
    frontier: Set[str] = {origin_stop_id}

    while frontier:
        frontier_ids = list(frontier)
        stop_routes = _get_routes_through_stops(frontier_ids, region)
        selected_trip_ids = _select_representative_trips(stop_routes, depart_seconds)

        if not selected_trip_ids:
            break

        trip_stops = _get_stops_for_trips(list(selected_trip_ids), region)
        new_frontier: Set[str] = set()

        for board_stop_id in frontier_ids:
            board_elapsed_seconds = dist_seconds.get(board_stop_id, max_seconds + 1)
            if board_elapsed_seconds > max_seconds:
                continue

            for route_info in stop_routes.get(board_stop_id, []):
                trip_id = route_info.get('trip_id')
                if trip_id not in selected_trip_ids:
                    continue

                board_sequence = route_info.get('stop_sequence') or 0
                board_departure_text = route_info.get('departure_time') or DEFAULT_DEPART_TIME
                try:
                    board_departure_seconds = _time_to_seconds(board_departure_text)
                except ValueError:
                    board_departure_seconds = depart_seconds

                for downstream_stop in trip_stops.get(trip_id, []):
                    if (downstream_stop.get('stop_sequence') or 0) <= board_sequence:
                        continue

                    stop_id = downstream_stop.get('stop_id')
                    if not stop_id or stop_id == board_stop_id:
                        continue

                    arrival_text = (
                        downstream_stop.get('arrival_time')
                        or downstream_stop.get('departure_time')
                        or board_departure_text
                    )
                    try:
                        arrival_seconds = _time_to_seconds(arrival_text)
                    except ValueError:
                        arrival_seconds = board_departure_seconds

                    travel_seconds = _elapsed_seconds(board_departure_seconds, arrival_seconds)
                    candidate_seconds = (
                        board_elapsed_seconds
                        + boarding_wait_seconds
                        + travel_seconds
                    )

                    if candidate_seconds > max_seconds:
                        continue

                    best_seconds = dist_seconds.get(stop_id)
                    if best_seconds is None or candidate_seconds < best_seconds:
                        dist_seconds[stop_id] = candidate_seconds
                        new_frontier.add(stop_id)

        frontier = new_frontier

    stop_locations = _get_stop_locations(list(dist_seconds.keys()), region)
    origin_data = stop_locations.get(origin_stop_id, origin_stop)
    layer_limits = _build_layer_limits(max_minutes)
    layers: Dict[int, List[str]] = {limit: [] for limit in layer_limits}
    reachable: List[Dict[str, Any]] = []

    reachable_rows = sorted(
        (
            (stop_id, seconds)
            for stop_id, seconds in dist_seconds.items()
            if stop_id != origin_stop_id
        ),
        key=lambda item: (item[1], item[0])
    )

    for stop_id, seconds in reachable_rows:
        stop_info = stop_locations.get(stop_id, {'stop_id': stop_id, 'stop_name': stop_id})
        minutes = _seconds_to_minutes(seconds)
        reachable.append({
            'stop_id': stop_id,
            'stop_name': stop_info.get('stop_name', stop_id),
            'stop_lat': stop_info.get('stop_lat'),
            'stop_lon': stop_info.get('stop_lon'),
            'minutes': minutes
        })

        for limit in layer_limits:
            if minutes <= limit:
                layers[limit].append(stop_id)
                break

    return {
        'origin': {
            'stop_id': origin_data.get('stop_id', origin_stop_id),
            'stop_name': origin_data.get('stop_name', origin_stop_id),
            'stop_lat': origin_data.get('stop_lat'),
            'stop_lon': origin_data.get('stop_lon')
        },
        'reachable': reachable,
        'layers': layers
    }
