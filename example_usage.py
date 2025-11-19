"""
Example usage of SpeedCalculator with GTFSDataFetcher

This script demonstrates how to integrate the SpeedCalculator module
with the existing GTFS data fetcher without modifying the original code.
"""

from gtfs_data_fetcher import GTFSDataFetcher
from speed_calculator import SpeedCalculator
import time


def main():
    api_key = "YOUR_API_KEY_HERE"

    fetcher = GTFSDataFetcher(api_key)
    calculator = SpeedCalculator(
        min_time_delta=5,
        min_distance_threshold=5,
        max_speed_kmh=120
    )

    print("Starting real-time vehicle speed monitoring...")
    print("Press Ctrl+C to stop\n")

    try:
        while True:
            vehicle_positions = fetcher.fetch_gtfs_realtime('vehiclepositions')

            if vehicle_positions:
                parsed_positions = fetcher.parse_vehicle_positions(vehicle_positions)

                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Processing {len(parsed_positions)} vehicles")

                speed_count = 0
                for position in parsed_positions:
                    result = calculator.calculate_speed(
                        vehicle_id=position['vehicle_id'],
                        latitude=position['latitude'],
                        longitude=position['longitude'],
                        timestamp=position['timestamp']
                    )

                    if result:
                        speed_count += 1
                        print(f"  Vehicle {result.vehicle_id[:8]}... | "
                              f"Route: {position.get('route_id', 'N/A')} | "
                              f"Speed: {result.speed_kmh:6.2f} km/h | "
                              f"Distance: {result.distance_meters:7.2f}m | "
                              f"Time: {result.time_delta_seconds}s")

                print(f"  Calculated speed for {speed_count} vehicles")
                print(f"  Total tracked vehicles: {calculator.get_vehicle_count()}\n")

            time.sleep(30)

    except KeyboardInterrupt:
        print("\nStopping monitoring...")
        print(f"Final tracked vehicles: {calculator.get_vehicle_count()}")


if __name__ == "__main__":
    main()
