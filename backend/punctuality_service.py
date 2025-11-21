#!/usr/bin/env python3
"""
准点率数据收集和存储服务
负责从 GTFS Realtime 数据源收集延误信息，计算准点率并存储到数据库
"""

import time
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple, Any
import psycopg2
from psycopg2.extras import execute_batch, execute_values
import schedule

from gtfs_data_fetcher import GTFSDataFetcher
from punctuality_calculator import PunctualityCalculator, DelayRecord, PunctualityThresholds
from db import Database, execute_query, execute_query_one, execute_count, get_connection

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('punctuality_service.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class PunctualityDataService:
    """准点率数据收集和存储服务"""

    def __init__(self, api_key: str):
        """
        初始化服务

        Args:
            api_key: 511 SF Bay API Key
        """
        self.api_key = api_key
        self.data_fetcher = GTFSDataFetcher(api_key)
        self.punctuality_calculator = PunctualityCalculator()
        self.is_running = False
        self.last_collection_time = None

        # 从数据库加载配置
        self.config = self._load_config()
        logger.info(f"初始化完成，配置: {self.config}")

    def _load_config(self) -> Dict[str, Any]:
        """从数据库加载配置"""
        try:
            query = "SELECT config_key, config_value FROM punctuality_config"
            results = execute_query(query)
            config = {}

            for result in results:
                key = result['config_key']
                value = result['config_value']
                # 尝试转换为数值类型
                try:
                    if '.' in value:
                        config[key] = float(value)
                    else:
                        config[key] = int(value)
                except ValueError:
                    config[key] = value

            return config
        except Exception as e:
            logger.warning(f"加载配置失败，使用默认配置: {e}")
            # 返回默认配置
            return {
                'early_threshold_seconds': 60,
                'on_time_threshold_seconds': 120,
                'very_late_threshold_seconds': 300,
                'collection_interval_minutes': 2,
                'data_retention_days': 90
            }

    def collect_realtime_data(self) -> bool:
        """
        收集实时数据并计算准点率

        Returns:
            bool: 收集是否成功
        """
        try:
            logger.info("开始收集实时数据...")
            start_time = datetime.now()

            # 获取车辆位置数据
            vehicle_positions_feed = self.data_fetcher.fetch_gtfs_realtime(
                operator_id="SF",
                feed_type="vehiclepositions"
            )

            if not vehicle_positions_feed:
                logger.warning("无法获取车辆位置数据")
                return False

            # 获取行程更新数据（包含延误信息）
            trip_updates_feed = self.data_fetcher.fetch_gtfs_realtime(
                operator_id="SF",
                feed_type="tripupdates"
            )

            if not trip_updates_feed:
                logger.warning("无法获取行程更新数据")
                return False

            # 解析数据
            vehicle_positions = self.data_fetcher.parse_vehicle_positions(vehicle_positions_feed)
            trip_updates = self.data_fetcher.parse_trip_updates(trip_updates_feed)

            logger.info(f"获取到 {len(vehicle_positions)} 个车辆位置，{len(trip_updates)} 个行程更新")

            # 存储车辆位置数据
            self._store_vehicle_positions(vehicle_positions)

            # 处理延误数据并计算准点率
            delay_records = self._process_trip_updates(trip_updates)
            logger.info(f"处理了 {len(delay_records)} 个延误记录")

            # 存储延误记录到数据库
            self._store_delay_records(delay_records)

            # 更新准点率统计
            self._update_punctuality_statistics()

            self.last_collection_time = datetime.now()
            duration = (self.last_collection_time - start_time).total_seconds()
            logger.info(f"数据收集完成，耗时: {duration:.2f}秒")

            return True

        except Exception as e:
            logger.error(f"收集实时数据时发生错误: {e}")
            return False

    def _store_vehicle_positions(self, vehicle_positions: List[Dict[str, Any]]) -> None:
        """存储车辆位置数据到数据库"""
        if not vehicle_positions:
            return

        try:
            conn = get_connection()
            cursor = conn.cursor()

            # 准备插入数据
            insert_data = []
            current_time = datetime.now(timezone.utc)

            for position in vehicle_positions:
                insert_data.append((
                    position.get('vehicle_id'),
                    position.get('trip_id'),
                    position.get('route_id'),
                    position.get('latitude'),
                    position.get('longitude'),
                    position.get('bearing'),
                    position.get('speed'),
                    datetime.fromtimestamp(position.get('timestamp', current_time.timestamp()), timezone.utc),
                    current_time,
                    position.get('current_status'),
                    position.get('stop_id')
                ))

            # 使用批量插入提高性能
            query = """
                INSERT INTO realtime_vehicle_positions
                (vehicle_id, trip_id, route_id, latitude, longitude,
                 bearing, speed, position_timestamp, record_timestamp,
                 current_status, stop_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            execute_batch(cursor, query, insert_data)
            conn.commit()

            logger.info(f"成功存储 {len(insert_data)} 条车辆位置记录")

        except Exception as e:
            logger.error(f"存储车辆位置数据时发生错误: {e}")
            if 'conn' in locals():
                conn.rollback()
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    def _process_trip_updates(self, trip_updates: List[Dict[str, Any]]) -> List[DelayRecord]:
        """处理行程更新数据，生成延误记录"""
        delay_records = []

        for update in trip_updates:
            try:
                # 创建延误记录
                delay_record = DelayRecord(
                    trip_id=update.get('trip_id', ''),
                    route_id=update.get('route_id', ''),
                    stop_id=update.get('stop_id', ''),
                    stop_sequence=update.get('stop_sequence', 0),
                    scheduled_time=datetime.fromtimestamp(
                        update.get('scheduled_time', 0), timezone.utc
                    ),
                    actual_time=datetime.fromtimestamp(
                        update.get('actual_time', 0), timezone.utc
                    ),
                    arrival_delay=update.get('arrival_delay', 0),
                    departure_delay=update.get('departure_delay', 0),
                    vehicle_id=update.get('vehicle_id'),
                    timestamp=datetime.now(timezone.utc)
                )

                delay_records.append(delay_record)

                # 添加到准点率计算器
                self.punctuality_calculator.add_delay_record(delay_record)

            except Exception as e:
                logger.warning(f"处理行程更新记录时发生错误: {e}")
                continue

        return delay_records

    def _store_delay_records(self, delay_records: List[DelayRecord]) -> None:
        """存储延误记录到数据库"""
        if not delay_records:
            return

        try:
            conn = get_connection()
            cursor = conn.cursor()

            # 准备插入数据
            insert_data = []
            for record in delay_records:
                insert_data.append((
                    record.trip_id,
                    record.route_id,
                    record.stop_id,
                    record.stop_sequence,
                    record.vehicle_id,
                    record.scheduled_time,
                    record.actual_time,
                    record.timestamp,
                    record.arrival_delay,
                    record.departure_delay,
                    'GTFS_Realtime',
                    False  # processed
                ))

            # 使用批量插入
            query = """
                INSERT INTO realtime_delay_records
                (trip_id, route_id, stop_id, stop_sequence, vehicle_id,
                 scheduled_time, actual_time, record_timestamp,
                 arrival_delay, departure_delay, data_source, processed)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            execute_batch(cursor, query, insert_data)
            conn.commit()

            logger.info(f"成功存储 {len(insert_data)} 条延误记录")

        except Exception as e:
            logger.error(f"存储延误记录时发生错误: {e}")
            if 'conn' in locals():
                conn.rollback()
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    def _update_punctuality_statistics(self) -> None:
        """更新准点率统计表"""
        try:
            logger.info("开始更新准点率统计...")

            # 更新线路日统计
            self._update_route_daily_stats()

            # 更新站点日统计
            self._update_stop_daily_stats()

            # 更新时段统计
            self._update_hourly_stats()

            # 更新系统概览
            self._update_system_overview()

            logger.info("准点率统计更新完成")

        except Exception as e:
            logger.error(f"更新准点率统计时发生错误: {e}")

    def _update_route_daily_stats(self) -> None:
        """更新线路日统计"""
        try:
            conn = get_connection()
            cursor = conn.cursor()

            # 获取阈值配置
            on_time_threshold = self.config.get('on_time_threshold_seconds', 120)
            very_late_threshold = self.config.get('very_late_threshold_seconds', 300)

            # 更新或插入线路日统计
            query = """
                INSERT INTO route_daily_punctuality
                (route_id, stat_date, total_trips, on_time_trips, early_trips,
                 late_trips, very_late_trips, avg_arrival_delay, max_arrival_delay,
                 min_arrival_delay, punctuality_rate, early_rate, late_rate, very_late_rate)
                SELECT
                    route_id,
                    DATE(record_timestamp) as stat_date,
                    COUNT(*) as total_trips,
                    COUNT(CASE WHEN ABS(arrival_delay) <= %s THEN 1 END) as on_time_trips,
                    COUNT(CASE WHEN arrival_delay < -60 THEN 1 END) as early_trips,
                    COUNT(CASE WHEN arrival_delay > %s AND arrival_delay <= %s THEN 1 END) as late_trips,
                    COUNT(CASE WHEN arrival_delay > %s THEN 1 END) as very_late_trips,
                    AVG(arrival_delay) as avg_arrival_delay,
                    MAX(arrival_delay) as max_arrival_delay,
                    MIN(arrival_delay) as min_arrival_delay,
                    (COUNT(CASE WHEN ABS(arrival_delay) <= %s THEN 1 END) * 100.0 / COUNT(*)) as punctuality_rate,
                    (COUNT(CASE WHEN arrival_delay < -60 THEN 1 END) * 100.0 / COUNT(*)) as early_rate,
                    (COUNT(CASE WHEN arrival_delay > %s AND arrival_delay <= %s THEN 1 END) * 100.0 / COUNT(*)) as late_rate,
                    (COUNT(CASE WHEN arrival_delay > %s THEN 1 END) * 100.0 / COUNT(*)) as very_late_rate
                FROM realtime_delay_records
                WHERE DATE(record_timestamp) = CURRENT_DATE
                  AND processed = false
                GROUP BY route_id, DATE(record_timestamp)
                ON CONFLICT (route_id, stat_date) DO UPDATE SET
                    total_trips = EXCLUDED.total_trips,
                    on_time_trips = EXCLUDED.on_time_trips,
                    early_trips = EXCLUDED.early_trips,
                    late_trips = EXCLUDED.late_trips,
                    very_late_trips = EXCLUDED.very_late_trips,
                    avg_arrival_delay = EXCLUDED.avg_arrival_delay,
                    max_arrival_delay = EXCLUDED.max_arrival_delay,
                    min_arrival_delay = EXCLUDED.min_arrival_delay,
                    punctuality_rate = EXCLUDED.punctuality_rate,
                    early_rate = EXCLUDED.early_rate,
                    late_rate = EXCLUDED.late_rate,
                    very_late_rate = EXCLUDED.very_late_rate,
                    updated_at = CURRENT_TIMESTAMP
            """

            params = [on_time_threshold, on_time_threshold, very_late_threshold,
                     very_late_threshold, on_time_threshold, on_time_threshold,
                     very_late_threshold, very_late_threshold]

            cursor.execute(query, params)

            # 标记记录为已处理
            cursor.execute("""
                UPDATE realtime_delay_records
                SET processed = true
                WHERE DATE(record_timestamp) = CURRENT_DATE
                  AND processed = false
            """)

            conn.commit()
            logger.info("线路日统计更新完成")

        except Exception as e:
            logger.error(f"更新线路日统计时发生错误: {e}")
            if 'conn' in locals():
                conn.rollback()
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    def _update_stop_daily_stats(self) -> None:
        """更新站点日统计"""
        try:
            conn = get_connection()
            cursor = conn.cursor()

            on_time_threshold = self.config.get('on_time_threshold_seconds', 120)

            query = """
                INSERT INTO stop_daily_punctuality
                (stop_id, stat_date, total_visits, on_time_visits, early_visits,
                 late_visits, very_late_visits, avg_arrival_delay, max_arrival_delay,
                 min_arrival_delay, punctuality_rate)
                SELECT
                    stop_id,
                    DATE(record_timestamp) as stat_date,
                    COUNT(*) as total_visits,
                    COUNT(CASE WHEN ABS(arrival_delay) <= %s THEN 1 END) as on_time_visits,
                    COUNT(CASE WHEN arrival_delay < -60 THEN 1 END) as early_visits,
                    COUNT(CASE WHEN arrival_delay > %s AND arrival_delay <= 300 THEN 1 END) as late_visits,
                    COUNT(CASE WHEN arrival_delay > 300 THEN 1 END) as very_late_visits,
                    AVG(arrival_delay) as avg_arrival_delay,
                    MAX(arrival_delay) as max_arrival_delay,
                    MIN(arrival_delay) as min_arrival_delay,
                    (COUNT(CASE WHEN ABS(arrival_delay) <= %s THEN 1 END) * 100.0 / COUNT(*)) as punctuality_rate
                FROM realtime_delay_records
                WHERE DATE(record_timestamp) = CURRENT_DATE
                  AND processed = true
                GROUP BY stop_id, DATE(record_timestamp)
                ON CONFLICT (stop_id, stat_date) DO UPDATE SET
                    total_visits = EXCLUDED.total_visits,
                    on_time_visits = EXCLUDED.on_time_visits,
                    early_visits = EXCLUDED.early_visits,
                    late_visits = EXCLUDED.late_visits,
                    very_late_visits = EXCLUDED.very_late_visits,
                    avg_arrival_delay = EXCLUDED.avg_arrival_delay,
                    max_arrival_delay = EXCLUDED.max_arrival_delay,
                    min_arrival_delay = EXCLUDED.min_arrival_delay,
                    punctuality_rate = EXCLUDED.punctuality_rate,
                    updated_at = CURRENT_TIMESTAMP
            """

            cursor.execute(query, [on_time_threshold, on_time_threshold, on_time_threshold])
            conn.commit()

            logger.info("站点日统计更新完成")

        except Exception as e:
            logger.error(f"更新站点日统计时发生错误: {e}")
            if 'conn' in locals():
                conn.rollback()
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    def _update_hourly_stats(self) -> None:
        """更新时段统计"""
        try:
            conn = get_connection()
            cursor = conn.cursor()

            on_time_threshold = self.config.get('on_time_threshold_seconds', 120)

            query = """
                INSERT INTO hourly_punctuality_stats
                (route_id, stop_id, hour_of_day, stat_date, total_trips,
                 on_time_trips, avg_arrival_delay, max_arrival_delay, punctuality_rate)
                SELECT
                    route_id,
                    stop_id,
                    EXTRACT(HOUR FROM scheduled_time) as hour_of_day,
                    DATE(scheduled_time) as stat_date,
                    COUNT(*) as total_trips,
                    COUNT(CASE WHEN ABS(arrival_delay) <= %s THEN 1 END) as on_time_trips,
                    AVG(arrival_delay) as avg_arrival_delay,
                    MAX(arrival_delay) as max_arrival_delay,
                    (COUNT(CASE WHEN ABS(arrival_delay) <= %s THEN 1 END) * 100.0 / COUNT(*)) as punctuality_rate
                FROM realtime_delay_records
                WHERE DATE(scheduled_time) = CURRENT_DATE
                  AND processed = true
                GROUP BY route_id, stop_id, EXTRACT(HOUR FROM scheduled_time), DATE(scheduled_time)
                ON CONFLICT (route_id, stop_id, hour_of_day, stat_date) DO UPDATE SET
                    total_trips = EXCLUDED.total_trips,
                    on_time_trips = EXCLUDED.on_time_trips,
                    avg_arrival_delay = EXCLUDED.avg_arrival_delay,
                    max_arrival_delay = EXCLUDED.max_arrival_delay,
                    punctuality_rate = EXCLUDED.punctuality_rate,
                    updated_at = CURRENT_TIMESTAMP
            """

            cursor.execute(query, [on_time_threshold, on_time_threshold])
            conn.commit()

            logger.info("时段统计更新完成")

        except Exception as e:
            logger.error(f"更新时段统计时发生错误: {e}")
            if 'conn' in locals():
                conn.rollback()
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    def _update_system_overview(self) -> None:
        """更新系统概览"""
        try:
            conn = get_connection()
            cursor = conn.cursor()

            # 计算早高峰和晚高峰准点率
            morning_peak_query = """
                SELECT AVG(punctuality_rate) as morning_peak_rate
                FROM hourly_punctuality_stats
                WHERE stat_date = CURRENT_DATE
                  AND hour_of_day BETWEEN 7 AND 9
            """

            evening_peak_query = """
                SELECT AVG(punctuality_rate) as evening_peak_rate
                FROM hourly_punctuality_stats
                WHERE stat_date = CURRENT_DATE
                  AND hour_of_day BETWEEN 17 AND 19
            """

            off_peak_query = """
                SELECT AVG(punctuality_rate) as off_peak_rate
                FROM hourly_punctuality_stats
                WHERE stat_date = CURRENT_DATE
                  AND NOT (hour_of_day BETWEEN 7 AND 9 OR hour_of_day BETWEEN 17 AND 19)
            """

            morning_result = execute_query_one(morning_peak_query)
            evening_result = execute_query_one(evening_peak_query)
            off_peak_result = execute_query_one(off_peak_query)

            # 更新系统概览
            query = """
                INSERT INTO system_punctuality_overview
                (stat_date, total_routes, total_trips, system_punctuality_rate,
                 system_avg_delay_minutes, morning_peak_rate, evening_peak_rate, off_peak_rate)
                SELECT
                    CURRENT_DATE as stat_date,
                    COUNT(DISTINCT route_id) as total_routes,
                    SUM(total_trips) as total_trips,
                    AVG(punctuality_rate) as system_punctuality_rate,
                    AVG(avg_arrival_delay) / 60 as system_avg_delay_minutes,
                    %s as morning_peak_rate,
                    %s as evening_peak_rate,
                    %s as off_peak_rate
                FROM route_daily_punctuality
                WHERE stat_date = CURRENT_DATE
                ON CONFLICT (stat_date) DO UPDATE SET
                    total_routes = EXCLUDED.total_routes,
                    total_trips = EXCLUDED.total_trips,
                    system_punctuality_rate = EXCLUDED.system_punctuality_rate,
                    system_avg_delay_minutes = EXCLUDED.system_avg_delay_minutes,
                    morning_peak_rate = EXCLUDED.morning_peak_rate,
                    evening_peak_rate = EXCLUDED.evening_peak_rate,
                    off_peak_rate = EXCLUDED.off_peak_rate,
                    updated_at = CURRENT_TIMESTAMP
            """

            params = [
                morning_result['morning_peak_rate'] or 0,
                evening_result['evening_peak_rate'] or 0,
                off_peak_result['off_peak_rate'] or 0
            ]

            cursor.execute(query, params)
            conn.commit()

            logger.info("系统概览更新完成")

        except Exception as e:
            logger.error(f"更新系统概览时发生错误: {e}")
            if 'conn' in locals():
                conn.rollback()
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    def cleanup_old_data(self) -> None:
        """清理过期数据"""
        try:
            retention_days = self.config.get('data_retention_days', 90)
            cutoff_date = datetime.now() - timedelta(days=retention_days)

            conn = get_connection()
            cursor = conn.cursor()

            # 清理实时车辆位置数据
            cursor.execute("""
                DELETE FROM realtime_vehicle_positions
                WHERE record_timestamp < %s
            """, (cutoff_date,))

            vehicle_deleted = cursor.rowcount

            # 清理实时延误记录数据
            cursor.execute("""
                DELETE FROM realtime_delay_records
                WHERE record_timestamp < %s
            """, (cutoff_date,))

            delays_deleted = cursor.rowcount

            conn.commit()

            logger.info(f"清理过期数据完成: 删除了 {vehicle_deleted} 条车辆位置记录，{delays_deleted} 条延误记录")

        except Exception as e:
            logger.error(f"清理过期数据时发生错误: {e}")
            if 'conn' in locals():
                conn.rollback()
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    def start_service(self) -> None:
        """启动数据收集服务"""
        logger.info("启动准点率数据收集服务...")
        self.is_running = True

        # 立即执行一次数据收集
        self.collect_realtime_data()

        # 设置定时任务
        collection_interval = self.config.get('collection_interval_minutes', 2)
        schedule.every(collection_interval).minutes.do(self.collect_realtime_data)

        # 每天凌晨清理过期数据
        schedule.every().day.at("02:00").do(self.cleanup_old_data)

        # 每小时重新加载配置
        schedule.every().hour.do(self._reload_config)

        logger.info(f"服务已启动，数据收集间隔: {collection_interval}分钟")

        try:
            while self.is_running:
                schedule.run_pending()
                time.sleep(30)  # 每30秒检查一次

        except KeyboardInterrupt:
            logger.info("收到停止信号，正在关闭服务...")
        finally:
            self.stop_service()

    def stop_service(self) -> None:
        """停止数据收集服务"""
        logger.info("停止准点率数据收集服务...")
        self.is_running = False
        schedule.clear()

    def _reload_config(self) -> None:
        """重新加载配置"""
        try:
            self.config = self._load_config()
            logger.info("配置重新加载完成")
        except Exception as e:
            logger.warning(f"重新加载配置失败: {e}")

    def get_service_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        return {
            'is_running': self.is_running,
            'last_collection_time': self.last_collection_time.isoformat() if self.last_collection_time else None,
            'config': self.config,
            'total_records_collected': self.punctuality_calculator.get_record_count()
        }


def main():
    """主函数"""
    # API Key - 在实际部署中应该从环境变量或配置文件中读取
    API_KEY = "your_511_api_key_here"  # 请替换为实际的 API Key

    if API_KEY == "your_511_api_key_here":
        logger.error("请设置有效的 511 API Key")
        return

    # 创建并启动服务
    service = PunctualityDataService(API_KEY)

    try:
        service.start_service()
    except Exception as e:
        logger.error(f"服务运行时发生错误: {e}")
    finally:
        service.stop_service()


if __name__ == "__main__":
    main()