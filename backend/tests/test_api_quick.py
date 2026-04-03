#!/usr/bin/env python3
"""
快速API接口测试脚本
"""

import requests
import json

API_BASE_URL = "http://localhost:5001/api"
SESSION = requests.Session()
SESSION.trust_env = False

def test_endpoint(endpoint, description, params=None):
    """测试单个API端点"""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        response = SESSION.get(url, params=params, timeout=20)

        if response.status_code == 200:
            data = response.json()
            if data.get("code") == 200:
                result_data = data.get("data", [])
                print(f"✅ {description}: 返回 {len(result_data)} 条记录")
                return True
            else:
                print(f"❌ {description}: {data.get('message', '未知错误')}")
                return False
        else:
            print(f"❌ {description}: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ {description}: 请求失败 - {e}")
        return False

def main():
    print("快速API接口测试")
    print("=" * 40)

    # 测试列表
    tests = [
        ("/health", "健康检查"),
        ("/stats", "数据统计"),
        ("/realtime/summary", "实时数据汇总"),
        ("/punctuality/overview", "准点率概览"),
        ("/punctuality/routes", "线路准点率", {"limit": 5}),
        ("/punctuality/stops", "站点准点率", {"limit": 5}),
        ("/punctuality/hourly", "时段准点率"),
        ("/punctuality/config", "配置查询"),
        ("/routes", "线路查询", {"limit": 5}),
        ("/stops", "站点查询", {"limit": 5})
    ]

    success_count = 0
    total_count = len(tests)

    for test in tests:
        if len(test) == 2:
            endpoint, desc = test
            params = None
        else:
            endpoint, desc, params = test

        if test_endpoint(endpoint, desc, params):
            success_count += 1

    print("=" * 40)
    print(f"测试完成: {success_count}/{total_count} 个接口正常")

    if success_count == total_count:
        print("🎉 所有API接口测试通过!")
    else:
        print("⚠️  部分接口存在问题，请检查服务状态")

if __name__ == "__main__":
    main()
