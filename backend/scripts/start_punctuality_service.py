#!/usr/bin/env python3
"""
准点率数据收集服务启动脚本
独立进程，定时从 GTFS Realtime API 收集数据并写入数据库

用法:
    python3 scripts/start_punctuality_service.py --region sf
    python3 scripts/start_punctuality_service.py --region sydney
    python3 scripts/start_punctuality_service.py --region nyc

支持从配置文件或环境变量读取 API Key：
    SF_511_API_KEY=xxx python3 scripts/start_punctuality_service.py --region sf
    或在 backend/config.json 中配置
"""

import argparse
import os
import sys

# 将 backend 目录加入 sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.db import Database
from core.config import get_config
from services.punctuality_service import PunctualityDataService


def main():
    parser = argparse.ArgumentParser(description='启动准点率数据收集服务')
    parser.add_argument('--region', default='sf', choices=['sf', 'nyc', 'sydney'],
                        help='地区代码 (默认: sf)')
    args = parser.parse_args()
    region = args.region

    # 加载配置
    config = get_config()

    # 从环境变量或配置文件读取 API Key
    api_key_env_map = {
        'sf':     'SF_511_API_KEY',
        'nyc':    'MTA_API_KEY',
        'sydney': 'TFNSW_API_KEY',
    }
    env_var = api_key_env_map[region]
    api_key = os.getenv(env_var) or config.get_api_key(region)

    if not api_key:
        print(f"警告：未设置 {region} 的 API Key")
        print(f"可以通过以下方式设置：")
        print(f"  1. 环境变量: {env_var}=your_key python3 scripts/start_punctuality_service.py --region {region}")
        print(f"  2. 配置文件: 在 backend/config.json 中配置 api_keys.{region}")
        print(f"\n将使用模拟数据模式运行...")

    print(f"初始化数据库连接...")
    Database.initialize()

    print(f"启动准点率数据收集服务 (region={region})，每2分钟收集一次...")
    if api_key:
        print(f"使用真实 API 数据（失败时自动降级到模拟数据）")
    else:
        print(f"使用模拟数据模式")

    service = PunctualityDataService(api_key=api_key, region=region)
    service.start_service()


if __name__ == '__main__':
    main()
