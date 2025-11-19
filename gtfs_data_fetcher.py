"""
GTFS和GTFS Realtime数据获取工具
支持旧金山湾区511 SF Bay API
"""

import requests
import zipfile
import io
from pathlib import Path
from google.transit import gtfs_realtime_pb2
from datetime import datetime


class GTFSDataFetcher:
    def __init__(self, api_key=None):
        """
        初始化数据获取器
        api_key: 511 SF Bay的API key，从 https://511.org/open-data/token 获取
        """
        self.api_key = api_key
        self.base_url = "https://api.511.org/transit"

    def download_gtfs_static(self, operator_id="SF", output_dir="./gtfs_data"):
        """
        下载GTFS静态数据
        operator_id: 运营商ID，默认SF(San Francisco Muni)
        其他选项: 'AC'(AC Transit), 'BA'(BART), 'CC'(County Connection)等
        """
        if not self.api_key:
            raise ValueError("需要API key。请从 https://511.org/open-data/token 获取")

        url = f"{self.base_url}/datafeeds"
        params = {
            "api_key": self.api_key,
            "operator_id": operator_id
        }

        print(f"正在下载 {operator_id} 的GTFS静态数据...")
        response = requests.get(url, params=params)

        if response.status_code == 200:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            zip_file = output_path / f"gtfs_{operator_id}_{datetime.now().strftime('%Y%m%d')}.zip"
            with open(zip_file, 'wb') as f:
                f.write(response.content)

            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                extract_dir = output_path / f"gtfs_{operator_id}"
                extract_dir.mkdir(exist_ok=True)
                zip_ref.extractall(extract_dir)

            print(f"✓ GTFS静态数据已保存到: {extract_dir}")
            return extract_dir
        else:
            print(f"✗ 下载失败: {response.status_code} - {response.text}")
            return None

    def fetch_gtfs_realtime(self, operator_id="SF", feed_type="vehiclepositions"):
        """
        获取GTFS Realtime数据
        operator_id: 运营商ID
        feed_type: 'vehiclepositions', 'tripupdates', 或 'servicealerts'
        """
        if not self.api_key:
            raise ValueError("需要API key。请从 https://511.org/open-data/token 获取")

        url = f"{self.base_url}/{feed_type}"
        params = {
            "api_key": self.api_key,
            "agency": operator_id
        }

        print(f"正在获取 {operator_id} 的 {feed_type} 实时数据...")
        response = requests.get(url, params=params)

        if response.status_code == 200:
            feed = gtfs_realtime_pb2.FeedMessage()
            feed.ParseFromString(response.content)

            print(f"✓ 成功获取 {len(feed.entity)} 条实时数据")
            return feed
        else:
            print(f"✗ 获取失败: {response.status_code} - {response.text}")
            return None

    def parse_vehicle_positions(self, feed):
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
                })
        return vehicles

    def parse_trip_updates(self, feed):
        """解析行程更新数据（包含延误信息）"""
        trips = []
        for entity in feed.entity:
            if entity.HasField('trip_update'):
                trip = entity.trip_update
                for stop_update in trip.stop_time_update:
                    trips.append({
                        'trip_id': trip.trip.trip_id if trip.HasField('trip') else None,
                        'route_id': trip.trip.route_id if trip.HasField('trip') else None,
                        'stop_id': stop_update.stop_id,
                        'arrival_delay': stop_update.arrival.delay if stop_update.HasField('arrival') else None,
                        'departure_delay': stop_update.departure.delay if stop_update.HasField('departure') else None,
                    })
        return trips


def example_usage():
    """使用示例"""

    # 步骤1: 设置你的API key（从 https://511.org/open-data/token 获取）
    API_KEY = "bee75731-9589-41c0-a9c0-435461d7c486"  # 替换为你的API key

    fetcher = GTFSDataFetcher(api_key=API_KEY)

    # 步骤2: 下载GTFS静态数据
    print("\n=== 下载GTFS静态数据 ===")
    gtfs_dir = fetcher.download_gtfs_static(operator_id="SF")

    # 步骤3: 获取实时车辆位置
    print("\n=== 获取实时车辆位置 ===")
    vehicle_feed = fetcher.fetch_gtfs_realtime(operator_id="SF", feed_type="vehiclepositions")
    if vehicle_feed:
        vehicles = fetcher.parse_vehicle_positions(vehicle_feed)
        print(f"当前在线车辆数: {len(vehicles)}")
        if vehicles:
            print("示例车辆数据:", vehicles[0])

    # 步骤4: 获取行程更新（延误信息）
    print("\n=== 获取行程更新数据 ===")
    trip_feed = fetcher.fetch_gtfs_realtime(operator_id="SF", feed_type="tripupdates")
    if trip_feed:
        trips = fetcher.parse_trip_updates(trip_feed)
        print(f"行程更新数量: {len(trips)}")
        if trips:
            print("示例延误数据:", trips[0])


if __name__ == "__main__":
    example_usage()
