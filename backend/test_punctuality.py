#!/usr/bin/env python3
"""
准点率分析功能测试脚本
用于验证准点率计算、API接口和数据库存储功能
"""

import json
import time
import requests
from datetime import datetime, timedelta, timezone
from punctuality_calculator import PunctualityCalculator, DelayRecord, PunctualityThresholds
from db import execute_query, execute_query_one, execute_count

# API 基础 URL
API_BASE_URL = "http://localhost:5001/api"

def test_punctuality_calculator():
    """测试准点率计算器"""
    print("=" * 50)
    print("测试准点率计算器")
    print("=" * 50)

    # 创建计算器实例
    calculator = PunctualityCalculator()

    # 创建测试延误记录
    test_records = [
        # 线路 1 的测试数据
        DelayRecord(
            trip_id="trip_1_1",
            route_id="route_1",
            stop_id="stop_1",
            stop_sequence=1,
            scheduled_time=datetime(2024, 1, 1, 8, 0, 0, tzinfo=timezone.utc),
            actual_time=datetime(2024, 1, 1, 8, 1, 30, tzinfo=timezone.utc),  # 延误90秒
            arrival_delay=90,
            departure_delay=0
        ),
        DelayRecord(
            trip_id="trip_1_2",
            route_id="route_1",
            stop_id="stop_1",
            stop_sequence=1,
            scheduled_time=datetime(2024, 1, 1, 8, 30, 0, tzinfo=timezone.utc),
            actual_time=datetime(2024, 1, 1, 8, 28, 0, tzinfo=timezone.utc),  # 提前120秒
            arrival_delay=-120,
            departure_delay=0
        ),
        DelayRecord(
            trip_id="trip_1_3",
            route_id="route_1",
            stop_id="stop_1",
            stop_sequence=1,
            scheduled_time=datetime(2024, 1, 1, 9, 0, 0, tzinfo=timezone.utc),
            actual_time=datetime(2024, 1, 1, 9, 5, 0, tzinfo=timezone.utc),  # 延误300秒（严重延误）
            arrival_delay=300,
            departure_delay=0
        ),
        # 线路 2 的测试数据（准点率更高）
        DelayRecord(
            trip_id="trip_2_1",
            route_id="route_2",
            stop_id="stop_2",
            stop_sequence=1,
            scheduled_time=datetime(2024, 1, 1, 8, 15, 0, tzinfo=timezone.utc),
            actual_time=datetime(2024, 1, 1, 8, 16, 0, tzinfo=timezone.utc),  # 延误60秒（准点）
            arrival_delay=60,
            departure_delay=0
        ),
        DelayRecord(
            trip_id="trip_2_2",
            route_id="route_2",
            stop_id="stop_2",
            stop_sequence=1,
            scheduled_time=datetime(2024, 1, 1, 8, 45, 0, tzinfo=timezone.utc),
            actual_time=datetime(2024, 1, 1, 8, 44, 30, tzinfo=timezone.utc),  # 延误30秒（准点）
            arrival_delay=30,
            departure_delay=0
        ),
    ]

    # 添加测试记录
    for record in test_records:
        calculator.add_delay_record(record)

    print(f"添加了 {len(test_records)} 条测试延误记录")

    # 测试线路准点率计算
    route_1_stats = calculator.calculate_route_punctuality("route_1")
    if route_1_stats:
        print(f"\n线路 1 准点率统计:")
        print(f"  总班次: {route_1_stats.total_trips}")
        print(f"  准点率: {route_1_stats.punctuality_rate:.2f}%")
        print(f"  平均延误: {route_1_stats.avg_delay_minutes:.2f}分钟")
        print(f"  最大延误: {route_1_stats.max_delay_minutes}分钟")

    route_2_stats = calculator.calculate_route_punctuality("route_2")
    if route_2_stats:
        print(f"\n线路 2 准点率统计:")
        print(f"  总班次: {route_2_stats.total_trips}")
        print(f"  准点率: {route_2_stats.punctuality_rate:.2f}%")
        print(f"  平均延误: {route_2_stats.avg_delay_minutes:.2f}分钟")

    # 测试系统概览
    system_overview = calculator.calculate_system_overview()
    print(f"\n系统准点率概览:")
    print(f"  总线路数: {system_overview.total_routes}")
    print(f"  总班次: {system_overview.total_trips}")
    print(f"  系统准点率: {system_overview.system_punctuality_rate:.2f}%")
    print(f"  系统平均延误: {system_overview.system_avg_delay:.2f}分钟")

    # 测试延误汇总
    delay_summary = calculator.get_delay_summary_by_route()
    print(f"\n线路延误汇总 (共 {len(delay_summary)} 条线路):")
    for summary in delay_summary:
        print(f"  {summary['route_id']}: 准点率 {summary['punctuality_rate']:.2f}%, "
              f"平均延误 {summary.get('avg_delay_minutes', 0):.2f}分钟")

    print("准点率计算器测试完成!\n")

def test_api_endpoints():
    """测试API接口"""
    print("=" * 50)
    print("测试API接口")
    print("=" * 50)

    # 测试健康检查
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            print("✅ 健康检查接口正常")
        else:
            print(f"❌ 健康检查接口异常: {response.status_code}")
    except Exception as e:
        print(f"❌ 无法连接到API服务: {e}")
        return

    # 测试实时车辆位置接口
    try:
        response = requests.get(f"{API_BASE_URL}/realtime/vehicles", params={"limit": 5})
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == 200:
                vehicles = data.get("data", [])
                print(f"✅ 实时车辆接口正常，返回 {len(vehicles)} 条记录")
            else:
                print(f"❌ 实时车辆接口返回错误: {data.get('message')}")
        else:
            print(f"❌ 实时车辆接口异常: {response.status_code}")
    except Exception as e:
        print(f"❌ 实时车辆接口请求失败: {e}")

    # 测试实时延误接口
    try:
        response = requests.get(f"{API_BASE_URL}/realtime/delays", params={"limit": 5})
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == 200:
                delays = data.get("data", [])
                print(f"✅ 实时延误接口正常，返回 {len(delays)} 条记录")
            else:
                print(f"❌ 实时延误接口返回错误: {data.get('message')}")
        else:
            print(f"❌ 实时延误接口异常: {response.status_code}")
    except Exception as e:
        print(f"❌ 实时延误接口请求失败: {e}")

    # 测试实时汇总接口
    try:
        response = requests.get(f"{API_BASE_URL}/realtime/summary")
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == 200:
                summary = data.get("data", {})
                print(f"✅ 实时汇总接口正常:")
                print(f"  活跃车辆: {summary.get('active_vehicles', 0)}")
                print(f"  最近延误记录: {summary.get('recent_delays', 0)}")
                print(f"  有延误的线路: {summary.get('routes_with_delays', 0)}")
            else:
                print(f"❌ 实时汇总接口返回错误: {data.get('message')}")
        else:
            print(f"❌ 实时汇总接口异常: {response.status_code}")
    except Exception as e:
        print(f"❌ 实时汇总接口请求失败: {e}")

    # 测试准点率概览接口
    try:
        response = requests.get(f"{API_BASE_URL}/punctuality/overview", params={"days": 7})
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == 200:
                overview = data.get("data", {})
                print(f"✅ 准点率概览接口正常:")
                print(f"  总线路数: {overview.get('total_routes', 0)}")
                print(f"  总班次: {overview.get('total_trips', 0)}")
                print(f"  系统准点率: {overview.get('system_punctuality_rate', 0):.2f}%")
                print(f"  数据可用: {overview.get('data_available', False)}")
            else:
                print(f"❌ 准点率概览接口返回错误: {data.get('message')}")
        else:
            print(f"❌ 准点率概览接口异常: {response.status_code}")
    except Exception as e:
        print(f"❌ 准点率概览接口请求失败: {e}")

    # 测试线路准点率接口
    try:
        response = requests.get(f"{API_BASE_URL}/punctuality/routes", params={"limit": 5})
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == 200:
                routes = data.get("data", [])
                print(f"✅ 线路准点率接口正常，返回 {len(routes)} 条记录")
                if routes:
                    # 显示前3条记录
                    for route in routes[:3]:
                        print(f"  {route.get('route_short_name', route.get('route_id'))}: "
                              f"准点率 {route.get('avg_punctuality_rate', 0):.2f}%")
            else:
                print(f"❌ 线路准点率接口返回错误: {data.get('message')}")
        else:
            print(f"❌ 线路准点率接口异常: {response.status_code}")
    except Exception as e:
        print(f"❌ 线路准点率接口请求失败: {e}")

    # 测试站点准点率接口
    try:
        response = requests.get(f"{API_BASE_URL}/punctuality/stops", params={"limit": 5})
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == 200:
                stops = data.get("data", [])
                print(f"✅ 站点准点率接口正常，返回 {len(stops)} 条记录")
            else:
                print(f"❌ 站点准点率接口返回错误: {data.get('message')}")
        else:
            print(f"❌ 站点准点率接口异常: {response.status_code}")
    except Exception as e:
        print(f"❌ 站点准点率接口请求失败: {e}")

    # 测试时段准点率接口
    try:
        response = requests.get(f"{API_BASE_URL}/punctuality/hourly")
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == 200:
                hourly_stats = data.get("data", [])
                print(f"✅ 时段准点率接口正常，返回 {len(hourly_stats)} 小时数据")
            else:
                print(f"❌ 时段准点率接口返回错误: {data.get('message')}")
        else:
            print(f"❌ 时段准点率接口异常: {response.status_code}")
    except Exception as e:
        print(f"❌ 时段准点率接口请求失败: {e}")

    # 测试配置接口
    try:
        response = requests.get(f"{API_BASE_URL}/punctuality/config")
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == 200:
                config = data.get("data", {})
                print(f"✅ 配置接口正常，返回 {len(config)} 个配置项:")
                for key, value in config.items():
                    print(f"  {key}: {value}")
            else:
                print(f"❌ 配置接口返回错误: {data.get('message')}")
        else:
            print(f"❌ 配置接口异常: {response.status_code}")
    except Exception as e:
        print(f"❌ 配置接口请求失败: {e}")

    print("API接口测试完成!\n")

def test_database_tables():
    """测试数据库表"""
    print("=" * 50)
    print("测试数据库表")
    print("=" * 50)

    tables_to_check = [
        'realtime_delay_records',
        'route_daily_punctuality',
        'stop_daily_punctuality',
        'hourly_punctuality_stats',
        'realtime_vehicle_positions',
        'system_punctuality_overview',
        'punctuality_config'
    ]

    for table in tables_to_check:
        try:
            count = execute_count(f"SELECT COUNT(*) FROM {table}")
            print(f"✅ 表 {table}: {count} 条记录")
        except Exception as e:
            print(f"❌ 表 {table} 检查失败: {e}")

    # 测试视图
    views_to_check = [
        'route_punctuality_detail',
        'stop_punctuality_detail',
        'realtime_delay_summary'
    ]

    for view in views_to_check:
        try:
            count = execute_count(f"SELECT COUNT(*) FROM {view}")
            print(f"✅ 视图 {view}: {count} 条记录")
        except Exception as e:
            print(f"❌ 视图 {view} 检查失败: {e}")

    print("数据库表测试完成!\n")

def generate_sample_data():
    """生成示例数据（用于测试）"""
    print("=" * 50)
    print("生成示例数据")
    print("=" * 50)

    try:
        # 模拟插入一些延误记录
        conn = None
        cursor = None

        # 这里只是示例，实际应该从 GTFS Realtime 获取数据
        sample_data = [
            ("test_trip_1", "test_route_1", "test_stop_1", 1, "test_vehicle_1",
             datetime.now(timezone.utc) - timedelta(minutes=5),  # 实际时间
             datetime.now(timezone.utc),                         # 记录时间
             120,  # 延误2分钟
             0,    # 出发延误
             "test_data"),
            ("test_trip_2", "test_route_1", "test_stop_1", 1, "test_vehicle_2",
             datetime.now(timezone.utc) - timedelta(minutes=3),
             datetime.now(timezone.utc),
             -60,  # 提前1分钟
             0,
             "test_data"),
            ("test_trip_3", "test_route_2", "test_stop_2", 1, "test_vehicle_3",
             datetime.now(timezone.utc) - timedelta(minutes=10),
             datetime.now(timezone.utc),
             300,  # 延误5分钟
             0,
             "test_data")
        ]

        print("注意: 此功能需要真实的数据库连接，当前为演示模式")
        print(f"准备插入 {len(sample_data)} 条示例延误记录")

        # 实际插入数据的代码需要数据库连接
        # 这里只是演示流程

        print("示例数据生成完成!\n")

    except Exception as e:
        print(f"生成示例数据时发生错误: {e}")

def main():
    """主函数"""
    print("开始准点率分析功能测试")
    print(f"测试时间: {datetime.now()}")
    print(f"API 服务地址: {API_BASE_URL}")

    try:
        # 测试准点率计算器
        test_punctuality_calculator()

        # 测试API接口
        test_api_endpoints()

        # 测试数据库表
        test_database_tables()

        # 生成示例数据
        generate_sample_data()

        print("=" * 50)
        print("所有测试完成!")
        print("=" * 50)

    except Exception as e:
        print(f"测试过程中发生错误: {e}")

if __name__ == "__main__":
    main()