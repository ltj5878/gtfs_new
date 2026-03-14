#!/usr/bin/env python3
"""
准点率数据收集服务启动脚本
独立进程，定时从 GTFS Realtime API 收集数据并写入数据库

用法:
    SF_511_API_KEY=xxx python3 scripts/start_punctuality_service.py --region sf
    TFNSW_API_KEY=xxx python3 scripts/start_punctuality_service.py --region sydney
    MTA_API_KEY=xxx python3 scripts/start_punctuality_service.py --region nyc
"""

import argparse
import os
import sys

# 将 backend 目录加入 sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.db import Database
from services.punctuality_service import PunctualityDataService


def main():
    parser = argparse.ArgumentParser(description='启动准点率数据收集服务')
    parser.add_argument('--region', default='sf', choices=['sf', 'nyc', 'sydney'],
                        help='地区代码 (默认: sf)')
    args = parser.parse_args()
    region = args.region

    # 从环境变量读取 API Key
    api_key_env = {
        'sf':     'SF_511_API_KEY',
        'nyc':    'MTA_API_KEY',
        'sydney': 'TFNSW_API_KEY',
    }
    env_var = api_key_env[region]
    api_key = os.getenv(env_var, '')

    if not api_key:
        print(f"错误：请设置环境变量 {env_var}")
        print(f"示例: {env_var}=your_key python3 scripts/start_punctuality_service.py --region {region}")
        sys.exit(1)

    print(f"初始化数据库连接...")
    Database.initialize()

    print(f"启动准点率数据收集服务 (region={region})，每2分钟收集一次...")
    service = PunctualityDataService(api_key=api_key, region=region)
    service.start_service()


if __name__ == '__main__':
    main()
