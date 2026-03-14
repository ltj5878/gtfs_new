"""
纽约 MTA GTFS 数据获取工具
支持纽约地铁和公交的静态数据下载及实时数据获取（预留）
"""

import requests
import zipfile
import io
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

# MTA 静态数据下载地址（免费，无需 API Key）
MTA_STATIC_URLS = {
    'subway': 'http://web.mta.info/developers/data/nyct/subway/google_transit.zip',
    'bus_manhattan': 'http://web.mta.info/developers/data/nyct/bus/google_transit_manhattan.zip',
    'bus_bronx': 'http://web.mta.info/developers/data/nyct/bus/google_transit_bronx.zip',
    'bus_brooklyn': 'http://web.mta.info/developers/data/nyct/bus/google_transit_brooklyn.zip',
    'bus_queens': 'http://web.mta.info/developers/data/nyct/bus/google_transit_queens.zip',
    'bus_staten_island': 'http://web.mta.info/developers/data/nyct/bus/google_transit_staten_island.zip',
}

# MTA GTFS-RT 端点（需要 API Key，从 https://api.mta.info 免费注册）
MTA_REALTIME_URLS = {
    'subway_feed': 'https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs',
    'service_alerts': 'https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/camsys%2Fall-alerts',
}


class MTADataFetcher:
    """纽约 MTA GTFS 数据获取器"""

    def __init__(self, api_key: Optional[str] = None):
        """
        初始化 MTA 数据获取器

        Args:
            api_key: MTA API Key（实时数据需要，静态数据不需要）
                     从 https://api.mta.info 免费注册获取
        """
        self.api_key = api_key

    def download_gtfs_static(self, feed_type: str = 'subway',
                             output_dir: str = './gtfs_data') -> Optional[Path]:
        """
        下载 MTA GTFS 静态数据（免费，无需 API Key）

        Args:
            feed_type: 数据类型，可选值见 MTA_STATIC_URLS
            output_dir: 输出目录

        Returns:
            下载的 ZIP 文件路径，失败返回 None
        """
        url = MTA_STATIC_URLS.get(feed_type)
        if not url:
            print(f"✗ 不支持的数据类型: {feed_type}")
            print(f"  可选类型: {', '.join(MTA_STATIC_URLS.keys())}")
            return None

        print(f"正在下载 MTA {feed_type} 的 GTFS 静态数据...")
        try:
            response = requests.get(url, timeout=120)

            if response.status_code == 200:
                output_path = Path(output_dir)
                output_path.mkdir(parents=True, exist_ok=True)

                date_str = datetime.now().strftime('%Y%m%d')
                zip_file = output_path / f"gtfs_nyc_{feed_type}_{date_str}.zip"

                with open(zip_file, 'wb') as f:
                    f.write(response.content)

                print(f"✓ MTA 静态数据已保存到: {zip_file}")
                return zip_file
            else:
                print(f"✗ 下载失败: {response.status_code} - {response.text[:200]}")
                return None

        except requests.RequestException as e:
            print(f"✗ 下载失败: {e}")
            return None

    def fetch_gtfs_realtime(self, feed_type: str = 'subway_feed') -> Optional[Any]:
        """
        获取 MTA GTFS Realtime 数据（需要 API Key）

        Args:
            feed_type: 实时数据类型

        Returns:
            GTFS Realtime FeedMessage，失败返回 None
        """
        if not self.api_key:
            print("✗ 需要 MTA API Key。请从 https://api.mta.info 免费注册获取")
            return None

        url = MTA_REALTIME_URLS.get(feed_type)
        if not url:
            print(f"✗ 不支持的实时数据类型: {feed_type}")
            return None

        headers = {'x-api-key': self.api_key}

        print(f"正在获取 MTA {feed_type} 实时数据...")
        try:
            response = requests.get(url, headers=headers, timeout=30)

            if response.status_code == 200:
                from google.transit import gtfs_realtime_pb2
                feed = gtfs_realtime_pb2.FeedMessage()
                feed.ParseFromString(response.content)
                print(f"✓ 成功获取 {len(feed.entity)} 条实时数据")
                return feed
            else:
                print(f"✗ 获取失败: {response.status_code} - {response.text[:200]}")
                return None

        except requests.RequestException as e:
            print(f"✗ 获取失败: {e}")
            return None

    def parse_vehicle_positions(self, feed) -> List[Dict[str, Any]]:
        """解析车辆位置数据"""
        vehicles = []
        for entity in feed.entity:
            if entity.HasField('vehicle'):
                vehicle = entity.vehicle
                vehicles.append({
                    'vehicle_id': vehicle.vehicle.id if vehicle.HasField('vehicle') else None,
                    'trip_id': vehicle.trip.trip_id if vehicle.HasField('trip') else None,
                    'route_id': vehicle.trip.route_id if vehicle.HasField('trip') else None,
                    'latitude': vehicle.position.latitude if vehicle.HasField('position') else None,
                    'longitude': vehicle.position.longitude if vehicle.HasField('position') else None,
                    'timestamp': vehicle.timestamp if vehicle.HasField('timestamp') else None,
                    'current_status': vehicle.current_status if vehicle.HasField('current_status') else None,
                    'stop_id': vehicle.stop_id if vehicle.HasField('stop_id') else None,
                })
        return vehicles

    def parse_trip_updates(self, feed) -> List[Dict[str, Any]]:
        """解析行程更新数据"""
        trips = []
        for entity in feed.entity:
            if entity.HasField('trip_update'):
                trip = entity.trip_update
                for stop_update in trip.stop_time_update:
                    trips.append({
                        'trip_id': trip.trip.trip_id if trip.HasField('trip') else None,
                        'route_id': trip.trip.route_id if trip.HasField('trip') else None,
                        'stop_id': stop_update.stop_id,
                        'stop_sequence': stop_update.stop_sequence,
                        'arrival_delay': stop_update.arrival.delay if stop_update.HasField('arrival') else None,
                        'departure_delay': stop_update.departure.delay if stop_update.HasField('departure') else None,
                    })
        return trips

    def list_available_feeds(self) -> Dict[str, str]:
        """列出所有可用的数据源"""
        return {
            'static': MTA_STATIC_URLS,
            'realtime': MTA_REALTIME_URLS
        }


if __name__ == '__main__':
    fetcher = MTADataFetcher()

    # 下载地铁静态数据（无需 API Key）
    print("\n=== 下载 MTA 地铁静态数据 ===")
    zip_path = fetcher.download_gtfs_static(feed_type='subway')
    if zip_path:
        print(f"下载完成: {zip_path}")
