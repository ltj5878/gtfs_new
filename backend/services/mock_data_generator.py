#!/usr/bin/env python3
"""
模拟数据生成器
用于在真实 API 调用失败时生成模拟的准点率数据
"""

import random
import logging
from datetime import datetime, timedelta
from typing import List, Tuple, Optional
from core.db import Database

logger = logging.getLogger(__name__)


class MockDataGenerator:
    """模拟数据生成器"""

    # 地区坐标范围
    COORD_RANGES = {
        'sf':     (37.70, 37.80, -122.50, -122.35),
        'nyc':    (40.60, 40.80, -74.05, -73.85),
        'sydney': (-33.95, -33.75, 151.00, 151.25),
    }

    def __init__(self, region: str = 'sf'):
        """
        初始化模拟数据生成器

        Args:
            region: 地区代码（sf, nyc, sydney）
        """
        self.region = region

    def generate_delay_records(self, count: int = 5) -> List[Tuple]:
        """
        生成模拟的延误记录

        Args:
            count: 生成记录数量

        Returns:
            延误记录列表
        """
        try:
            conn = Database.get_connection()
            cursor = conn.cursor()

            # 获取现有的行程站点数据
            cursor.execute("""
                SELECT DISTINCT r.route_id, t.trip_id, st.stop_id, s.stop_name, st.stop_sequence
                FROM routes r
                JOIN trips t ON r.route_id = t.route_id AND r.region = t.region
                JOIN stop_times st ON t.trip_id = st.trip_id AND t.region = st.region
                JOIN stops s ON st.stop_id = s.stop_id AND st.region = s.region
                WHERE r.region = %s AND st.stop_sequence <= 5
                LIMIT %s
            """, (self.region, count))

            trip_stops = cursor.fetchall()

            if not trip_stops:
                logger.warning(f"没有找到 {self.region} 的行程站点数据，无法生成模拟延误记录")
                return []

            current_time = datetime.now()
            delay_records = []

            for record in trip_stops:
                minutes_ago = random.randint(1, 30)
                record_timestamp = current_time - timedelta(minutes=minutes_ago)
                scheduled_time = record_timestamp - timedelta(minutes=random.randint(-2, 15))
                delay_seconds = random.randint(-180, 600)  # -3分钟到10分钟

                delay_records.append((
                    self.region,
                    record[1],  # trip_id
                    record[0],  # route_id
                    record[2],  # stop_id
                    record[4],  # stop_sequence
                    f"VEH_{record[0]}_{random.randint(100, 999)}",  # vehicle_id
                    scheduled_time,
                    record_timestamp,  # actual_time
                    record_timestamp,  # record_timestamp
                    delay_seconds,  # arrival_delay
                    0,  # departure_delay
                    'mock',  # data_source
                    False  # processed
                ))

            logger.info(f"生成了 {len(delay_records)} 条模拟延误记录")
            return delay_records

        except Exception as e:
            logger.error(f"生成模拟延误记录失败: {e}")
            return []

    def generate_vehicle_positions(self, count: int = 3) -> List[Tuple]:
        """
        生成模拟的车辆位置

        Args:
            count: 生成记录数量

        Returns:
            车辆位置记录列表
        """
        try:
            conn = Database.get_connection()
            cursor = conn.cursor()

            # 获取现有的行程数据
            cursor.execute("""
                SELECT DISTINCT r.route_id, t.trip_id, st.stop_id
                FROM routes r
                JOIN trips t ON r.route_id = t.route_id AND r.region = t.region
                JOIN stop_times st ON t.trip_id = st.trip_id AND t.region = st.region
                WHERE r.region = %s
                LIMIT %s
            """, (self.region, count))

            trips = cursor.fetchall()

            if not trips:
                logger.warning(f"没有找到 {self.region} 的行程数据，无法生成模拟车辆位置")
                return []

            # 获取地区坐标范围
            lat_min, lat_max, lng_min, lng_max = self.COORD_RANGES.get(
                self.region,
                (37.70, 37.80, -122.50, -122.35)
            )

            current_time = datetime.now()
            vehicle_positions = []

            for trip in trips:
                lat = random.uniform(lat_min, lat_max)
                lng = random.uniform(lng_min, lng_max)
                minutes_ago = random.randint(1, 10)
                position_timestamp = current_time - timedelta(minutes=minutes_ago)

                vehicle_positions.append((
                    self.region,
                    f"VEH_{trip[0]}_{random.randint(100, 999)}",  # vehicle_id
                    trip[1],  # trip_id
                    trip[0],  # route_id
                    lat,
                    lng,
                    position_timestamp,
                    current_time,  # record_timestamp
                    random.choice([0, 1, 2]),  # current_status (INCOMING_AT, STOPPED_AT, IN_TRANSIT_TO)
                    trip[2]  # stop_id
                ))

            logger.info(f"生成了 {len(vehicle_positions)} 条模拟车辆位置")
            return vehicle_positions

        except Exception as e:
            logger.error(f"生成模拟车辆位置失败: {e}")
            return []

    def insert_delay_records(self, records: List[Tuple]) -> int:
        """
        插入延误记录到数据库

        Args:
            records: 延误记录列表

        Returns:
            插入的记录数
        """
        if not records:
            return 0

        try:
            conn = Database.get_connection()
            cursor = conn.cursor()

            insert_query = """
                INSERT INTO realtime_delay_records
                (region, trip_id, route_id, stop_id, stop_sequence, vehicle_id,
                 scheduled_time, actual_time, record_timestamp,
                 arrival_delay, departure_delay, data_source, processed)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            cursor.executemany(insert_query, records)
            conn.commit()

            logger.info(f"成功插入 {len(records)} 条延误记录")
            return len(records)

        except Exception as e:
            logger.error(f"插入延误记录失败: {e}")
            conn.rollback()
            return 0

    def insert_vehicle_positions(self, positions: List[Tuple]) -> int:
        """
        插入车辆位置到数据库

        Args:
            positions: 车辆位置列表

        Returns:
            插入的记录数
        """
        if not positions:
            return 0

        try:
            conn = Database.get_connection()
            cursor = conn.cursor()

            insert_query = """
                INSERT INTO realtime_vehicle_positions
                (region, vehicle_id, trip_id, route_id, latitude, longitude,
                 position_timestamp, record_timestamp, current_status, stop_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            cursor.executemany(insert_query, positions)
            conn.commit()

            logger.info(f"成功插入 {len(positions)} 条车辆位置")
            return len(positions)

        except Exception as e:
            logger.error(f"插入车辆位置失败: {e}")
            conn.rollback()
            return 0

    def generate_and_insert(self, delay_count: int = 5, vehicle_count: int = 3) -> Tuple[int, int]:
        """
        生成并插入模拟数据

        Args:
            delay_count: 延误记录数量
            vehicle_count: 车辆位置数量

        Returns:
            (插入的延误记录数, 插入的车辆位置数)
        """
        logger.info(f"开始生成模拟数据 (region={self.region})")

        delay_records = self.generate_delay_records(delay_count)
        vehicle_positions = self.generate_vehicle_positions(vehicle_count)

        delay_inserted = self.insert_delay_records(delay_records)
        vehicle_inserted = self.insert_vehicle_positions(vehicle_positions)

        logger.info(f"模拟数据生成完成: {delay_inserted} 条延误记录, {vehicle_inserted} 条车辆位置")

        return delay_inserted, vehicle_inserted
