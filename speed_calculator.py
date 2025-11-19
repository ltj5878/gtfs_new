"""
GTFS Realtime 速度计算模块

此模块基于 GTFS Realtime 数据中连续的 GPS 位置更新，
为车辆提供速度计算功能。

使用方法:
    calculator = SpeedCalculator()

    # 处理来自 GTFS Realtime 的车辆位置
    for position in vehicle_positions:
        result = calculator.calculate_speed(
            vehicle_id=position['vehicle_id'],
            latitude=position['latitude'],
            longitude=position['longitude'],
            timestamp=position['timestamp']
        )

        if result:
            print(f"Vehicle {result['vehicle_id']} speed: {result['speed_kmh']:.2f} km/h")
"""

import math
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class VehiclePosition:
    """存储车辆位置数据"""
    latitude: float
    longitude: float
    timestamp: int


@dataclass
class SpeedResult:
    """速度计算结果"""
    vehicle_id: str
    speed_mps: float
    speed_kmh: float
    distance_meters: float
    time_delta_seconds: float
    current_position: Tuple[float, float]
    previous_position: Tuple[float, float]
    timestamp: int


class SpeedCalculator:
    """
    根据连续的 GPS 位置计算车辆速度。

    此类维护车辆位置历史记录，并根据行驶距离和
    更新之间的时间间隔计算速度。
    """

    EARTH_RADIUS_METERS = 6371000
    MIN_TIME_DELTA = 5
    MIN_DISTANCE_THRESHOLD = 5
    MAX_REALISTIC_SPEED_KMH = 120

    def __init__(
        self,
        min_time_delta: int = MIN_TIME_DELTA,
        min_distance_threshold: float = MIN_DISTANCE_THRESHOLD,
        max_speed_kmh: float = MAX_REALISTIC_SPEED_KMH
    ):
        """
        初始化速度计算器。

        Args:
            min_time_delta: 计算速度所需的最小更新间隔秒数（默认: 5）
            min_distance_threshold: 低于此距离（米）时车辆被视为停止（默认: 5）
            max_speed_kmh: 用于过滤 GPS 错误的最大合理速度 km/h（默认: 120）
        """
        self._vehicle_history: Dict[str, VehiclePosition] = {}
        self.min_time_delta = min_time_delta
        self.min_distance_threshold = min_distance_threshold
        self.max_speed_kmh = max_speed_kmh

    def calculate_speed(
        self,
        vehicle_id: str,
        latitude: float,
        longitude: float,
        timestamp: int
    ) -> Optional[SpeedResult]:
        """
        根据当前和之前的位置计算车辆速度。

        Args:
            vehicle_id: 唯一车辆标识符
            latitude: 当前纬度（度）
            longitude: 当前经度（度）
            timestamp: 当前位置的 Unix 时间戳

        Returns:
            如果可以计算速度则返回 SpeedResult 对象，否则返回 None
            （首次位置或时间间隔太小时返回 None）
        """
        current_position = VehiclePosition(latitude, longitude, timestamp)

        if vehicle_id not in self._vehicle_history:
            self._vehicle_history[vehicle_id] = current_position
            return None

        previous_position = self._vehicle_history[vehicle_id]

        time_delta = timestamp - previous_position.timestamp

        if time_delta < self.min_time_delta:
            return None

        distance = self._haversine_distance(
            previous_position.latitude,
            previous_position.longitude,
            latitude,
            longitude
        )

        if distance < self.min_distance_threshold:
            speed_mps = 0.0
            speed_kmh = 0.0
        else:
            speed_mps = distance / time_delta
            speed_kmh = speed_mps * 3.6

        if speed_kmh > self.max_speed_kmh:
            speed_mps = 0.0
            speed_kmh = 0.0

        self._vehicle_history[vehicle_id] = current_position

        return SpeedResult(
            vehicle_id=vehicle_id,
            speed_mps=speed_mps,
            speed_kmh=speed_kmh,
            distance_meters=distance,
            time_delta_seconds=time_delta,
            current_position=(latitude, longitude),
            previous_position=(previous_position.latitude, previous_position.longitude),
            timestamp=timestamp
        )

    def _haversine_distance(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        """
        使用 Haversine 公式计算两个 GPS 坐标之间的大圆距离。

        Args:
            lat1: 第一个点的纬度（度）
            lon1: 第一个点的经度（度）
            lat2: 第二个点的纬度（度）
            lon2: 第二个点的经度（度）

        Returns:
            距离（米）
        """
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)

        a = (
            math.sin(delta_lat / 2) ** 2 +
            math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
        )
        c = 2 * math.asin(math.sqrt(a))

        return self.EARTH_RADIUS_METERS * c

    def get_vehicle_count(self) -> int:
        """获取正在跟踪的车辆数量"""
        return len(self._vehicle_history)

    def get_tracked_vehicles(self) -> list:
        """获取当前正在跟踪的车辆 ID 列表"""
        return list(self._vehicle_history.keys())

    def clear_vehicle(self, vehicle_id: str) -> bool:
        """
        清除特定车辆的历史记录。

        Args:
            vehicle_id: 要清除的车辆 ID

        Returns:
            如果找到并清除了车辆则返回 True，否则返回 False
        """
        if vehicle_id in self._vehicle_history:
            del self._vehicle_history[vehicle_id]
            return True
        return False

    def clear_all(self):
        """清除所有车辆历史记录"""
        self._vehicle_history.clear()

    def get_last_position(self, vehicle_id: str) -> Optional[Tuple[float, float, int]]:
        """
        获取车辆的最后已知位置。

        Args:
            vehicle_id: 要查询的车辆 ID

        Returns:
            (纬度, 经度, 时间戳) 的元组，如果未找到则返回 None
        """
        if vehicle_id in self._vehicle_history:
            pos = self._vehicle_history[vehicle_id]
            return (pos.latitude, pos.longitude, pos.timestamp)
        return None
