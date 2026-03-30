#!/usr/bin/env python3
"""
换乘规划器
策略：按线路展开（每条线路只取1个代表trip），大幅减少数据量
"""

from collections import defaultdict
from typing import List, Dict, Any, Optional, Set, Tuple
from core.db import execute_query, execute_query_one


MAX_TRANSFERS = 3


def _time_to_seconds(t: str) -> int:
    try:
        parts = t.split(':')
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    except Exception:
        return 0


def _seconds_to_minutes(s: int) -> int:
    return max(0, (s + 59) // 60)


def _get_stop_info(stop_id: str, region: str) -> Optional[Dict]:
    return execute_query_one(
        "SELECT stop_id, stop_name FROM stops WHERE stop_id = %s AND region = %s",
        (stop_id, region)
    )


def _get_routes_through_stops(stop_ids: List[str], region: str) -> Dict[str, List[Dict]]:
    """
    查询经过指定站点的所有线路（每条线路取1个代表trip）。
    返回：{ stop_id -> [{route_id, trip_id, stop_sequence, departure_time, ...}] }
    """
    if not stop_ids:
        return {}
    placeholders = ','.join(['%s'] * len(stop_ids))
    # 每条线路每个变体（headsign）取1个代表trip
    # 同一线路同一方向可能有不同分支（headsign不同，站点序列不同）
    rows = execute_query(f"""
        SELECT DISTINCT ON (st.stop_id, t.route_id, COALESCE(t.trip_headsign, ''))
            st.stop_id,
            st.stop_sequence,
            st.departure_time,
            t.trip_id,
            t.route_id,
            t.direction_id,
            t.trip_headsign,
            r.route_short_name,
            r.route_long_name,
            r.route_color
        FROM stop_times st
        JOIN trips  t ON st.region = t.region AND st.trip_id  = t.trip_id
        JOIN routes r ON t.region  = r.region AND t.route_id  = r.route_id
        WHERE st.stop_id IN ({placeholders}) AND st.region = %s
        ORDER BY st.stop_id, t.route_id, COALESCE(t.trip_headsign, ''), st.departure_time
    """, stop_ids + [region])

    result: Dict[str, List[Dict]] = defaultdict(list)
    for row in rows:
        result[row['stop_id']].append(row)
    return result


def _get_stops_for_trips(trip_ids: List[str], region: str) -> Dict[str, List[Dict]]:
    """
    查询指定 trip 经过的所有站点。
    返回：{ trip_id -> [{stop_id, stop_name, stop_sequence, arrival_time, departure_time}] }
    """
    if not trip_ids:
        return {}
    placeholders = ','.join(['%s'] * len(trip_ids))
    rows = execute_query(f"""
        SELECT
            st.trip_id,
            st.stop_id,
            st.stop_sequence,
            st.arrival_time,
            st.departure_time,
            s.stop_name
        FROM stop_times st
        JOIN stops s ON st.region = s.region AND st.stop_id = s.stop_id
        WHERE st.trip_id IN ({placeholders}) AND st.region = %s
        ORDER BY st.trip_id, st.stop_sequence
    """, trip_ids + [region])

    result: Dict[str, List[Dict]] = defaultdict(list)
    for row in rows:
        result[row['trip_id']].append(row)
    return result


def find_transfer_plans(
    from_stop_id: str,
    to_stop_id: str,
    region: str,
    strategy: str = 'min_transfer'
) -> Dict[str, Any]:

    from_stop = _get_stop_info(from_stop_id, region)
    to_stop = _get_stop_info(to_stop_id, region)

    if not from_stop:
        return {"error": f"起点站不存在: {from_stop_id}"}
    if not to_stop:
        return {"error": f"终点站不存在: {to_stop_id}"}
    if from_stop_id == to_stop_id:
        return {"error": "起点和终点不能相同"}

    plans = []

    # frontier: { stop_id -> [(segments, total_sec, used_routes)] }
    frontier: Dict[str, List[Tuple]] = {from_stop_id: [([], 0, frozenset())]}
    visited_stops: Set[str] = {from_stop_id}

    for transfer_count in range(0, MAX_TRANSFERS + 1):
        if not frontier:
            break

        frontier_ids = list(frontier.keys())

        # SQL 1：查 frontier 各站经过的线路（每条线路1个代表trip）
        stop_routes = _get_routes_through_stops(frontier_ids, region)

        # 收集所有代表 trip_id
        trip_ids = list({
            r['trip_id']
            for routes in stop_routes.values()
            for r in routes
        })

        if not trip_ids:
            break

        # SQL 2：查这些 trip 的完整站点序列
        trip_stops = _get_stops_for_trips(trip_ids, region)

        found_this_layer = False
        new_frontier: Dict[str, List[Tuple]] = {}

        for board_stop_id, paths in frontier.items():
            route_list = stop_routes.get(board_stop_id, [])

            for route_info in route_list:
                trip_id = route_info['trip_id']
                route_id = route_info['route_id']
                board_seq = route_info['stop_sequence']
                depart_time_str = route_info['departure_time'] or '00:00:00'

                downstream = trip_stops.get(trip_id, [])

                for ds in downstream:
                    if ds['stop_sequence'] <= board_seq:
                        continue

                    alight_id = ds['stop_id']
                    arrive_time_str = ds['arrival_time'] or ds['departure_time'] or depart_time_str
                    seg_sec = max(0, _time_to_seconds(arrive_time_str) - _time_to_seconds(depart_time_str))

                    for prev_segs, prev_total, used_routes in paths:
                        if route_id in used_routes:
                            continue

                        board_name = _get_name_from_segs(prev_segs, board_stop_id) or (
                            from_stop['stop_name'] if board_stop_id == from_stop_id else board_stop_id
                        )

                        seg = {
                            'trip_id': trip_id,
                            'route_id': route_id,
                            'route_name': (route_info.get('route_short_name') or '') + (
                                (' - ' + route_info['route_long_name']) if route_info.get('route_long_name') else ''
                            ),
                            'route_short_name': route_info.get('route_short_name', ''),
                            'route_long_name': route_info.get('route_long_name', ''),
                            'route_color': route_info.get('route_color', ''),
                            'from_stop_id': board_stop_id,
                            'from_stop_name': board_name,
                            'to_stop_id': alight_id,
                            'to_stop_name': ds['stop_name'],
                            'depart_time': depart_time_str,
                            'arrive_time': arrive_time_str,
                            'stop_count': ds['stop_sequence'] - board_seq,
                            'minutes': _seconds_to_minutes(seg_sec)
                        }
                        new_segs = prev_segs + [seg]
                        new_total = prev_total + seg_sec
                        new_used = used_routes | {route_id}

                        if alight_id == to_stop_id:
                            plans.append({
                                'transfer_count': transfer_count,
                                'total_minutes': _seconds_to_minutes(new_total),
                                'segments': new_segs
                            })
                            found_this_layer = True
                            break  # 该 trip 找到终点，不再继续后续站

                        if alight_id not in visited_stops:
                            if alight_id not in new_frontier:
                                new_frontier[alight_id] = []
                            new_frontier[alight_id].append((new_segs, new_total, new_used))

        if found_this_layer:
            break

        # 每站只保留累计时间最短的1条路径，控制 frontier 规模
        trimmed: Dict[str, List[Tuple]] = {}
        for sid, paths in new_frontier.items():
            paths.sort(key=lambda x: x[1])
            trimmed[sid] = [paths[0]]
            visited_stops.add(sid)

        frontier = trimmed

    return _finish(plans, strategy, from_stop, to_stop)


def _get_name_from_segs(segments: List[Dict], stop_id: str) -> Optional[str]:
    for seg in segments:
        if seg['to_stop_id'] == stop_id:
            return seg['to_stop_name']
        if seg['from_stop_id'] == stop_id:
            return seg['from_stop_name']
    return None


def _deduplicate_plans(plans: List[Dict]) -> List[Dict]:
    seen: Dict[str, Dict] = {}
    for plan in plans:
        key = str(plan['transfer_count']) + '|' + '|'.join(
            s['route_id'] + ':' + s['from_stop_id'] + '->' + s['to_stop_id']
            for s in plan['segments']
        )
        if key not in seen or plan['total_minutes'] < seen[key]['total_minutes']:
            seen[key] = plan
    return list(seen.values())


def _finish(plans: List[Dict], strategy: str,
            from_stop: Dict, to_stop: Dict) -> Dict[str, Any]:
    plans = _deduplicate_plans(plans)
    if strategy == 'min_time':
        plans.sort(key=lambda p: (p['total_minutes'], p['transfer_count']))
    else:
        plans.sort(key=lambda p: (p['transfer_count'], p['total_minutes']))
    return {
        'from_stop': dict(from_stop),
        'to_stop': dict(to_stop),
        'plans': plans[:5],
        'strategy': strategy,
        'total_found': len(plans)
    }
