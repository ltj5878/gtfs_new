#!/usr/bin/env python3
"""
公交准点率分析模块
计算和分析公交车辆的准点率、延误等关键指标
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
import statistics
from enum import Enum
import json


class PunctualityStatus(Enum):
    """准点状态枚举"""
    EARLY = "early"          # 提前
    ON_TIME = "on_time"      # 准点
    LATE = "late"           # 延误
    VERY_LATE = "very_late" # 严重延误


@dataclass
class PunctualityThresholds:
    """准点判断阈值配置（单位：秒）"""
    early_threshold: int = 60      # 提早60秒以上算提前
    on_time_threshold: int = 120   # 延误120秒内算准点
    very_late_threshold: int = 300 # 延误300秒以上算严重延误


@dataclass
class DelayRecord:
    """延误记录"""
    trip_id: str
    route_id: str
    stop_id: str
    stop_sequence: int
    scheduled_time: datetime
    actual_time: datetime
    arrival_delay: int      # 到达延误（秒，正数为延误，负数为提前）
    departure_delay: int    # 出发延误（秒）
    vehicle_id: Optional[str] = None
    timestamp: Optional[datetime] = None


@dataclass
class PunctualityRecord:
    """准点率记录"""
    route_id: str
    stop_id: str
    trip_count: int = 0
    on_time_count: int = 0
    early_count: int = 0
    late_count: int = 0
    very_late_count: int = 0

    # 延误统计
    avg_arrival_delay: float = 0.0    # 平均到达延误（秒）
    avg_departure_delay: float = 0.0  # 平均出发延误（秒）
    max_delay: int = 0                # 最大延误时间
    min_delay: int = 0                # 最小延误时间（负值表示提前）

    # 时间范围
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


@dataclass
class RoutePunctualityStats:
    """线路准点率统计"""
    route_id: str
    route_name: str
    total_trips: int
    punctuality_rate: float      # 准点率（百分比）
    on_time_rate: float          # 准点到达率
    early_rate: float            # 提前到达率
    late_rate: float             # 延误率
    very_late_rate: float        # 严重延误率

    # 延误统计
    avg_delay_minutes: float     # 平均延误（分钟）
    max_delay_minutes: int       # 最大延误（分钟）

    # 时间范围
    analysis_period: str
    data_collection_time: datetime

    # 按站点统计
    stop_stats: List[Dict[str, Any]] = field(default_factory=list)

    # 按时间段统计
    hourly_stats: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class SystemPunctualityOverview:
    """系统准点率概览"""
    total_routes: int
    total_trips: int
    system_punctuality_rate: float    # 系统整体准点率
    system_avg_delay: float           # 系统平均延误（分钟）

    # 路线排名
    best_routes: List[Dict[str, Any]]  # 准点率最高的线路
    worst_routes: List[Dict[str, Any]] # 准点率最低的线路

    # 时间分布
    peak_hours_punctuality: Dict[str, float]  # 高峰时段准点率
    off_peak_punctuality: float                # 非高峰时段准点率

    # 其他统计
    analysis_period: str
    last_updated: datetime


class PunctualityCalculator:
    """准点率计算器"""

    def __init__(self, thresholds: Optional[PunctualityThresholds] = None):
        """
        初始化准点率计算器

        Args:
            thresholds: 准点判断阈值，如未提供则使用默认值
        """
        self.thresholds = thresholds or PunctualityThresholds()
        self.delay_records: List[DelayRecord] = []
        self.punctuality_cache: Dict[str, PunctualityRecord] = {}

    def add_delay_record(self, record: DelayRecord) -> None:
        """
        添加延误记录

        Args:
            record: 延误记录对象
        """
        if record.timestamp is None:
            record.timestamp = datetime.now()

        self.delay_records.append(record)

        # 更新缓存统计
        cache_key = f"{record.route_id}_{record.stop_id}"
        if cache_key not in self.punctuality_cache:
            self.punctuality_cache[cache_key] = PunctualityRecord(
                route_id=record.route_id,
                stop_id=record.stop_id,
                start_time=record.scheduled_time,
                end_time=record.scheduled_time
            )

        self._update_punctuality_cache(cache_key, record)

    def _update_punctuality_cache(self, cache_key: str, record: DelayRecord) -> None:
        """更新准点率缓存"""
        punctuality_rec = self.punctuality_cache[cache_key]

        # 更新统计计数
        punctuality_rec.trip_count += 1

        # 判断准点状态
        status = self._get_punctuality_status(record.arrival_delay)

        if status == PunctualityStatus.ON_TIME:
            punctuality_rec.on_time_count += 1
        elif status == PunctualityStatus.EARLY:
            punctuality_rec.early_count += 1
        elif status == PunctualityStatus.LATE:
            punctuality_rec.late_count += 1
        elif status == PunctualityStatus.VERY_LATE:
            punctuality_rec.very_late_count += 1

        # 更新延误统计
        punctuality_rec.avg_arrival_delay = (
            (punctuality_rec.avg_arrival_delay * (punctuality_rec.trip_count - 1) + record.arrival_delay)
            / punctuality_rec.trip_count
        )

        if record.departure_delay != 0:  # 有些记录可能没有出发延误
            punctuality_rec.avg_departure_delay = (
                (punctuality_rec.avg_departure_delay * (punctuality_rec.trip_count - 1) + record.departure_delay)
                / punctuality_rec.trip_count
            )

        # 更新最大最小延误
        punctuality_rec.max_delay = max(punctuality_rec.max_delay, record.arrival_delay)
        punctuality_rec.min_delay = min(punctuality_rec.min_delay, record.arrival_delay)

        # 更新时间范围
        if punctuality_rec.start_time > record.scheduled_time:
            punctuality_rec.start_time = record.scheduled_time
        if punctuality_rec.end_time < record.scheduled_time:
            punctuality_rec.end_time = record.scheduled_time

    def _get_punctuality_status(self, delay_seconds: int) -> PunctualityStatus:
        """根据延误时间判断准点状态"""
        if delay_seconds < -self.thresholds.early_threshold:
            return PunctualityStatus.EARLY
        elif abs(delay_seconds) <= self.thresholds.on_time_threshold:
            return PunctualityStatus.ON_TIME
        elif delay_seconds <= self.thresholds.very_late_threshold:
            return PunctualityStatus.LATE
        else:
            return PunctualityStatus.VERY_LATE

    def calculate_route_punctuality(self, route_id: str,
                                  start_time: Optional[datetime] = None,
                                  end_time: Optional[datetime] = None) -> Optional[RoutePunctualityStats]:
        """
        计算指定线路的准点率统计

        Args:
            route_id: 线路ID
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            线路准点率统计对象，如果没有数据则返回None
        """
        # 筛选指定线路和时间范围的延误记录
        route_records = [
            record for record in self.delay_records
            if record.route_id == route_id and
               (start_time is None or record.scheduled_time >= start_time) and
               (end_time is None or record.scheduled_time <= end_time)
        ]

        if not route_records:
            return None

        # 计算基本统计
        total_trips = len(route_records)
        delays = [record.arrival_delay for record in route_records]

        on_time_count = sum(1 for delay in delays
                          if abs(delay) <= self.thresholds.on_time_threshold)
        early_count = sum(1 for delay in delays
                         if delay < -self.thresholds.early_threshold)
        late_count = sum(1 for delay in delays
                        if self.thresholds.on_time_threshold < delay <= self.thresholds.very_late_threshold)
        very_late_count = sum(1 for delay in delays
                            if delay > self.thresholds.very_late_threshold)

        # 构建统计结果
        return RoutePunctualityStats(
            route_id=route_id,
            route_name=self._get_route_name(route_id),
            total_trips=total_trips,
            punctuality_rate=(on_time_count / total_trips) * 100 if total_trips > 0 else 0,
            on_time_rate=(on_time_count / total_trips) * 100 if total_trips > 0 else 0,
            early_rate=(early_count / total_trips) * 100 if total_trips > 0 else 0,
            late_rate=(late_count / total_trips) * 100 if total_trips > 0 else 0,
            very_late_rate=(very_late_count / total_trips) * 100 if total_trips > 0 else 0,
            avg_delay_minutes=statistics.mean(delays) / 60 if delays else 0,
            max_delay_minutes=max(delays) / 60 if delays else 0,
            stop_stats=self._calculate_stop_stats(route_records),
            hourly_stats=self._calculate_hourly_stats(route_records),
            analysis_period=self._format_time_period(start_time, end_time),
            data_collection_time=datetime.now()
        )

    def calculate_system_overview(self,
                                start_time: Optional[datetime] = None,
                                end_time: Optional[datetime] = None) -> SystemPunctualityOverview:
        """
        计算系统准点率概览

        Args:
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            系统准点率概览对象
        """
        # 筛选时间范围内的记录
        if start_time or end_time:
            filtered_records = [
                record for record in self.delay_records
                if (start_time is None or record.scheduled_time >= start_time) and
                     (end_time is None or record.scheduled_time <= end_time)
            ]
        else:
            filtered_records = self.delay_records

        if not filtered_records:
            return SystemPunctualityOverview(
                total_routes=0,
                total_trips=0,
                system_punctuality_rate=0,
                system_avg_delay=0,
                best_routes=[],
                worst_routes=[],
                peak_hours_punctuality={},
                off_peak_punctuality=0,
                analysis_period="",
                last_updated=datetime.now()
            )

        # 获取所有线路
        route_ids = set(record.route_id for record in filtered_records)
        route_stats = []

        for route_id in route_ids:
            stats = self.calculate_route_punctuality(route_id, start_time, end_time)
            if stats:
                route_stats.append(stats)

        # 排序获取最佳和最差线路
        sorted_routes = sorted(route_stats, key=lambda x: x.punctuality_rate, reverse=True)
        best_routes = [
            {
                'route_id': r.route_id,
                'route_name': r.route_name,
                'punctuality_rate': r.punctuality_rate,
                'total_trips': r.total_trips
            }
            for r in sorted_routes[:5]  # 前5名
        ]

        worst_routes = [
            {
                'route_id': r.route_id,
                'route_name': r.route_name,
                'punctuality_rate': r.punctuality_rate,
                'total_trips': r.total_trips
            }
            for r in sorted_routes[-5:]  # 后5名
        ]

        # 计算系统整体统计
        total_trips = sum(r.total_trips for r in route_stats)
        total_on_time = sum(r.on_time_count * r.total_trips / 100 for r in route_stats)
        system_punctuality_rate = (total_on_time / total_trips * 100) if total_trips > 0 else 0

        all_delays = [record.arrival_delay for record in filtered_records]
        system_avg_delay = statistics.mean(all_delays) / 60 if all_delays else 0

        # 计算时段统计
        peak_hours_stats = self._calculate_peak_hours_stats(filtered_records)
        off_peak_rate = self._calculate_off_peak_rate(filtered_records)

        return SystemPunctualityOverview(
            total_routes=len(route_stats),
            total_trips=total_trips,
            system_punctuality_rate=system_punctuality_rate,
            system_avg_delay=system_avg_delay,
            best_routes=best_routes,
            worst_routes=worst_routes,
            peak_hours_punctuality=peak_hours_stats,
            off_peak_punctuality=off_peak_rate,
            analysis_period=self._format_time_period(start_time, end_time),
            last_updated=datetime.now()
        )

    def _calculate_stop_stats(self, route_records: List[DelayRecord]) -> List[Dict[str, Any]]:
        """计算站点级别统计"""
        stop_stats = {}

        for record in route_records:
            stop_id = record.stop_id
            if stop_id not in stop_stats:
                stop_stats[stop_id] = {
                    'stop_id': stop_id,
                    'stop_name': self._get_stop_name(stop_id),
                    'total_trips': 0,
                    'delays': []
                }

            stop_stats[stop_id]['total_trips'] += 1
            stop_stats[stop_id]['delays'].append(record.arrival_delay)

        # 计算每个站点的统计
        for stop_id, stats in stop_stats.items():
            delays = stats['delays']
            if delays:
                on_time_count = sum(1 for delay in delays
                                  if abs(delay) <= self.thresholds.on_time_threshold)
                stats['punctuality_rate'] = (on_time_count / len(delays)) * 100
                stats['avg_delay_minutes'] = statistics.mean(delays) / 60
                stats['max_delay_minutes'] = max(delays) / 60

        return list(stop_stats.values())

    def _calculate_hourly_stats(self, route_records: List[DelayRecord]) -> List[Dict[str, Any]]:
        """计算小时级别统计"""
        hourly_stats = {}

        for record in route_records:
            hour = record.scheduled_time.hour
            if hour not in hourly_stats:
                hourly_stats[hour] = {
                    'hour': hour,
                    'total_trips': 0,
                    'delays': []
                }

            hourly_stats[hour]['total_trips'] += 1
            hourly_stats[hour]['delays'].append(record.arrival_delay)

        # 计算每小时的统计
        for hour, stats in hourly_stats.items():
            delays = stats['delays']
            if delays:
                on_time_count = sum(1 for delay in delays
                                  if abs(delay) <= self.thresholds.on_time_threshold)
                stats['punctuality_rate'] = (on_time_count / len(delays)) * 100
                stats['avg_delay_minutes'] = statistics.mean(delays) / 60
                stats['trip_count'] = len(delays)

        return [hourly_stats[hour] for hour in sorted(hourly_stats.keys())]

    def _calculate_peak_hours_stats(self, records: List[DelayRecord]) -> Dict[str, float]:
        """计算高峰时段统计"""
        morning_peak = []  # 7:00-9:00
        evening_peak = []  # 17:00-19:00

        for record in records:
            hour = record.scheduled_time.hour
            if 7 <= hour <= 9:
                morning_peak.append(record.arrival_delay)
            elif 17 <= hour <= 19:
                evening_peak.append(record.arrival_delay)

        result = {}
        if morning_peak:
            on_time_morning = sum(1 for delay in morning_peak
                                if abs(delay) <= self.thresholds.on_time_threshold)
            result['morning_peak'] = (on_time_morning / len(morning_peak)) * 100

        if evening_peak:
            on_time_evening = sum(1 for delay in evening_peak
                                if abs(delay) <= self.thresholds.on_time_threshold)
            result['evening_peak'] = (on_time_evening / len(evening_peak)) * 100

        return result

    def _calculate_off_peak_rate(self, records: List[DelayRecord]) -> float:
        """计算非高峰时段准点率"""
        off_peak_delays = []

        for record in records:
            hour = record.scheduled_time.hour
            if not (7 <= hour <= 9 or 17 <= hour <= 19):  # 非高峰时段
                off_peak_delays.append(record.arrival_delay)

        if off_peak_delays:
            on_time_count = sum(1 for delay in off_peak_delays
                              if abs(delay) <= self.thresholds.on_time_threshold)
            return (on_time_count / len(off_peak_delays)) * 100

        return 0.0

    def _get_route_name(self, route_id: str) -> str:
        """获取线路名称（从数据库查询）"""
        try:
            from db import execute_query_one
            result = execute_query_one(
                "SELECT route_long_name FROM routes WHERE route_id = %s",
                (route_id,)
            )
            return result['route_long_name'] if result else route_id
        except Exception:
            return route_id

    def _get_stop_name(self, stop_id: str) -> str:
        """获取站点名称（从数据库查询）"""
        try:
            from db import execute_query_one
            result = execute_query_one(
                "SELECT stop_name FROM stops WHERE stop_id = %s",
                (stop_id,)
            )
            return result['stop_name'] if result else stop_id
        except Exception:
            return stop_id

    def _format_time_period(self, start_time: Optional[datetime],
                           end_time: Optional[datetime]) -> str:
        """格式化时间范围"""
        if not start_time and not end_time:
            return "全部时间"
        elif not start_time:
            return f"截至 {end_time.strftime('%Y-%m-%d %H:%M')}"
        elif not end_time:
            return f"从 {start_time.strftime('%Y-%m-%d %H:%M')} 开始"
        else:
            return f"{start_time.strftime('%Y-%m-%d %H:%M')} - {end_time.strftime('%Y-%m-%d %H:%M')}"

    def get_delay_summary_by_route(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取按线路分组的延误汇总

        Args:
            limit: 返回的线路数量限制

        Returns:
            延误汇总列表
        """
        route_summary = {}

        for record in self.delay_records:
            route_id = record.route_id
            if route_id not in route_summary:
                route_summary[route_id] = {
                    'route_id': route_id,
                    'route_name': self._get_route_name(route_id),
                    'total_trips': 0,
                    'delays': [],
                    'on_time_count': 0,
                    'late_count': 0,
                    'very_late_count': 0
                }

            summary = route_summary[route_id]
            summary['total_trips'] += 1
            summary['delays'].append(record.arrival_delay)

            status = self._get_punctuality_status(record.arrival_delay)
            if status == PunctualityStatus.ON_TIME:
                summary['on_time_count'] += 1
            elif status == PunctualityStatus.LATE:
                summary['late_count'] += 1
            elif status == PunctualityStatus.VERY_LATE:
                summary['very_late_count'] += 1

        # 计算统计数据并排序
        results = []
        for route_id, summary in route_summary.items():
            delays = summary['delays']
            if delays:
                results.append({
                    'route_id': route_id,
                    'route_name': summary['route_name'],
                    'total_trips': summary['total_trips'],
                    'punctuality_rate': (summary['on_time_count'] / len(delays)) * 100,
                    'avg_delay_minutes': statistics.mean(delays) / 60,
                    'max_delay_minutes': max(delays) / 60,
                    'on_time_count': summary['on_time_count'],
                    'late_count': summary['late_count'],
                    'very_late_count': summary['very_late_count']
                })

        # 按准点率降序排序
        results.sort(key=lambda x: x['punctuality_rate'], reverse=True)
        return results[:limit]

    def clear_records(self) -> None:
        """清空所有记录"""
        self.delay_records.clear()
        self.punctuality_cache.clear()

    def export_to_json(self, filepath: str) -> None:
        """导出数据到JSON文件"""
        export_data = {
            'thresholds': {
                'early_threshold': self.thresholds.early_threshold,
                'on_time_threshold': self.thresholds.on_time_threshold,
                'very_late_threshold': self.thresholds.very_late_threshold
            },
            'total_records': len(self.delay_records),
            'records': [
                {
                    'trip_id': record.trip_id,
                    'route_id': record.route_id,
                    'stop_id': record.stop_id,
                    'stop_sequence': record.stop_sequence,
                    'scheduled_time': record.scheduled_time.isoformat(),
                    'actual_time': record.actual_time.isoformat(),
                    'arrival_delay': record.arrival_delay,
                    'departure_delay': record.departure_delay,
                    'vehicle_id': record.vehicle_id,
                    'timestamp': record.timestamp.isoformat() if record.timestamp else None
                }
                for record in self.delay_records
            ]
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)

    def get_record_count(self) -> int:
        """获取记录总数"""
        return len(self.delay_records)