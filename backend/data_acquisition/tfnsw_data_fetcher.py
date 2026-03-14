"""
悉尼 TfNSW (Transport for NSW) GTFS 数据获取工具
支持悉尼公交的静态数据下载和实时数据获取
"""

import requests
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

# TfNSW GTFS 端点
TFNSW_BASE_URL = 'https://api.transport.nsw.gov.au/v1/gtfs'

TFNSW_STATIC_URLS = {
    'buses': f'{TFNSW_BASE_URL}/schedule/buses',
    'ferries': f'{TFNSW_BASE_URL}/schedule/ferries',
    'lightrail': f'{TFNSW_BASE_URL}/schedule/lightrail',
    'trains': f'{TFNSW_BASE_URL}/schedule/nswtrains',
    'metro': f'{TFNSW_BASE_URL}/schedule/metro',
}

TFNSW_REALTIME_URLS = {
    'vehicles_buses': f'{TFNSW_BASE_URL}/vehiclepos/buses',
    'vehicles_ferries': f'{TFNSW_BASE_URL}/vehiclepos/ferries',
    'vehicles_lightrail': f'{TFNSW_BASE_URL}/vehiclepos/lightrail',
    'vehicles_trains': f'{TFNSW_BASE_URL}/vehiclepos/nswtrains',
    'tripupdates_buses': f'{TFNSW_BASE_URL}/realtime/buses',
    'tripupdates_ferries': f'{TFNSW_BASE_URL}/realtime/ferries',
    'tripupdates_lightrail': f'{TFNSW_BASE_URL}/realtime/lightrail',
    'tripupdates_trains': f'{TFNSW_BASE_URL}/realtime/nswtrains',
    'alerts_buses': f'{TFNSW_BASE_URL}/alerts/buses',
    'alerts_ferries': f'{TFNSW_BASE_URL}/alerts/ferries',
    'alerts_lightrail': f'{TFNSW_BASE_URL}/alerts/lightrail',
    'alerts_trains': f'{TFNSW_BASE_URL}/alerts/nswtrains',
}


class TfNSWDataFetcher:
    """悉尼 TfNSW GTFS 数据获取器"""

    def __init__(self, api_key: str):
        """
        初始化 TfNSW 数据获取器

        Args:
            api_key: TfNSW API Key
                     从 https://opendata.transport.nsw.gov.au 注册获取
        """
        self.api_key = api_key
        self.headers = {
            'Authorization': f'apikey {api_key}',
            'Accept': 'application/x-google-protobuf'
        }

    def download_gtfs_static(self, feed_type: str = 'buses',
                             output_dir: str = './gtfs_data') -> Optional[Path]:
        """
        下载 TfNSW GTFS 静态数据

        Args:
            feed_type: 数据类型，可选值见 TFNSW_STATIC_URLS
            output_dir: 输出目录

        Returns:
            下载的 ZIP 文件路径，失败返回 None
        """
        url = TFNSW_STATIC_URLS.get(feed_type)
        if not url:
            print(f"✗ 不支持的数据类型: {feed_type}")
            print(f"  可选类型: {', '.join(TFNSW_STATIC_URLS.keys())}")
            return None

        # 静态数据下载使用不同的 Accept header
        headers = {
            'Authorization': f'apikey {self.api_key}',
            'Accept': 'application/octet-stream'
        }

        print(f"正在下载 TfNSW {feed_type} 的 GTFS 静态数据...")
        try:
            response = requests.get(url, headers=headers, timeout=180)

            if response.status_code == 200:
                output_path = Path(output_dir)
                output_path.mkdir(parents=True, exist_ok=True)

                date_str = datetime.now().strftime('%Y%m%d')
                zip_file = output_path / f"gtfs_sydney_{feed_type}_{date_str}.zip"

                with open(zip_file, 'wb') as f:
                    f.write(response.content)

                print(f"✓ TfNSW 静态数据已保存到: {zip_file}")
                return zip_file
            else:
                print(f"✗ 下载失败: {response.status_code} - {response.text[:200]}")
                return None

        except requests.RequestException as e:
            print(f"✗ 下载失败: {e}")
            return None

    def fetch_gtfs_realtime(self, feed_type: str = 'vehicles_buses') -> Optional[Any]:
        """
        获取 TfNSW GTFS Realtime 数据

        Args:
            feed_type: 实时数据类型

        Returns:
            GTFS Realtime FeedMessage，失败返回 None
        """
        url = TFNSW_REALTIME_URLS.get(feed_type)
        if not url:
            print(f"✗ 不支持的实时数据类型: {feed_type}")
            return None

        print(f"正在获取 TfNSW {feed_type} 实时数据...")
        try:
            response = requests.get(url, headers=self.headers, timeout=30)

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
                    'bearing': vehicle.position.bearing if vehicle.HasField('position') else None,
                    'speed': vehicle.position.speed if vehicle.HasField('position') else None,
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
                        'scheduled_time': stop_update.arrival.time if stop_update.HasField('arrival') else None,
                        'actual_time': (stop_update.arrival.time + stop_update.arrival.delay)
                                       if stop_update.HasField('arrival') and stop_update.arrival.delay else None,
                    })
        return trips

    def list_available_feeds(self) -> Dict[str, Dict[str, str]]:
        """列出所有可用的数据源"""
        return {
            'static': TFNSW_STATIC_URLS,
            'realtime': TFNSW_REALTIME_URLS
        }


if __name__ == '__main__':
    import sys

    api_key = sys.argv[1] if len(sys.argv) > 1 else None
    if not api_key:
        print("用法: python tfnsw_data_fetcher.py <API_KEY>")
        print("从 https://opendata.transport.nsw.gov.au 注册获取 API Key")
        sys.exit(1)

    fetcher = TfNSWDataFetcher(api_key=api_key)

    # 下载公交静态数据
    print("\n=== 下载 TfNSW 公交静态数据 ===")
    zip_path = fetcher.download_gtfs_static(feed_type='buses')
    if zip_path:
        print(f"下载完成: {zip_path}")
