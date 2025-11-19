"""
GTFS Realtime Speed Calculator Module

This module provides speed calculation functionality for vehicles based on
consecutive GPS position updates from GTFS Realtime data.

Usage:
    calculator = SpeedCalculator()

    # Process vehicle positions from GTFS Realtime
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
    """Store vehicle position data"""
    latitude: float
    longitude: float
    timestamp: int


@dataclass
class SpeedResult:
    """Speed calculation result"""
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
    Calculate vehicle speed from consecutive GPS positions.

    This class maintains a history of vehicle positions and calculates
    speed based on distance traveled and time elapsed between updates.
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
        Initialize the speed calculator.

        Args:
            min_time_delta: Minimum seconds between updates to calculate speed (default: 5)
            min_distance_threshold: Distance in meters below which vehicle is considered stopped (default: 5)
            max_speed_kmh: Maximum realistic speed in km/h for filtering GPS errors (default: 120)
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
        Calculate vehicle speed based on current and previous position.

        Args:
            vehicle_id: Unique vehicle identifier
            latitude: Current latitude in degrees
            longitude: Current longitude in degrees
            timestamp: Unix timestamp of current position

        Returns:
            SpeedResult object if speed can be calculated, None otherwise
            (None is returned for first position or if time delta is too small)
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
        Calculate great-circle distance between two GPS coordinates using Haversine formula.

        Args:
            lat1: Latitude of first point in degrees
            lon1: Longitude of first point in degrees
            lat2: Latitude of second point in degrees
            lon2: Longitude of second point in degrees

        Returns:
            Distance in meters
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
        """Get number of vehicles being tracked."""
        return len(self._vehicle_history)

    def get_tracked_vehicles(self) -> list:
        """Get list of vehicle IDs currently being tracked."""
        return list(self._vehicle_history.keys())

    def clear_vehicle(self, vehicle_id: str) -> bool:
        """
        Clear history for a specific vehicle.

        Args:
            vehicle_id: Vehicle ID to clear

        Returns:
            True if vehicle was found and cleared, False otherwise
        """
        if vehicle_id in self._vehicle_history:
            del self._vehicle_history[vehicle_id]
            return True
        return False

    def clear_all(self):
        """Clear all vehicle history."""
        self._vehicle_history.clear()

    def get_last_position(self, vehicle_id: str) -> Optional[Tuple[float, float, int]]:
        """
        Get last known position for a vehicle.

        Args:
            vehicle_id: Vehicle ID to query

        Returns:
            Tuple of (latitude, longitude, timestamp) or None if not found
        """
        if vehicle_id in self._vehicle_history:
            pos = self._vehicle_history[vehicle_id]
            return (pos.latitude, pos.longitude, pos.timestamp)
        return None
