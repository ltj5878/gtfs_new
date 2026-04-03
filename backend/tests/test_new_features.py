#!/usr/bin/env python3
"""
六个新增功能的脚本式冒烟测试
"""

from __future__ import annotations

from datetime import date
import os
import sys

import requests


API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:5001/api')


def api_request(session, method, path, *, token=None, params=None, json_data=None):
    headers = {}
    if token:
        headers['Authorization'] = f'Bearer {token}'

    response = session.request(
        method,
        f'{API_BASE_URL}{path}',
        headers=headers,
        params=params,
        json=json_data,
        timeout=120,
    )
    response.raise_for_status()
    payload = response.json()
    if payload.get('code') != 200:
        raise RuntimeError(f'{path} 返回错误: {payload.get("message")}')
    return payload.get('data')


def expect(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    session = requests.Session()
    session.trust_env = False

    login_data = api_request(
        session,
        'POST',
        '/auth/login',
        json_data={'username': 'admin', 'password': 'admin'},
    )
    token = login_data['token']
    print('✅ 登录成功')

    routes_data = api_request(
        session,
        'GET',
        '/routes',
        params={'region': 'sf', 'page_size': 3},
    )
    stops_data = api_request(
        session,
        'GET',
        '/stops',
        params={'region': 'sf', 'page_size': 3},
    )
    route_id = routes_data['routes'][0]['route_id']
    stop_id = stops_data['stops'][0]['stop_id']

    data_quality = api_request(
        session,
        'GET',
        '/admin/data-quality/latest',
        token=token,
        params={'region': 'sf'},
    )
    expect(data_quality is None or 'quality_score' in data_quality, '数据质量接口返回异常')
    print('✅ 数据质量接口正常')

    health_scores = api_request(
        session,
        'GET',
        '/routes/health-scores',
        params={'region': 'sf', 'limit': 5},
    )
    expect(len(health_scores) > 0, '健康度排行榜为空')
    health_detail = api_request(
        session,
        'GET',
        f'/routes/{route_id}/health-score',
        params={'region': 'sf'},
    )
    expect(health_detail['latest'] is not None, '健康度详情缺少 latest')
    expect(len(health_detail['history']) >= 1, '健康度详情缺少 history')
    print('✅ 健康度功能正常')

    active_alerts = api_request(
        session,
        'GET',
        '/alerts/active',
        params={'region': 'sf', 'refresh': 1},
    )
    alert_stats = api_request(
        session,
        'GET',
        '/alerts/stats',
        params={'region': 'sf'},
    )
    alert_history = api_request(
        session,
        'GET',
        '/alerts/history',
        params={'region': 'sf', 'days': 7, 'page_size': 10},
    )
    expect(len(active_alerts) > 0, '活跃告警为空')
    expect(alert_stats['active_count'] >= 0, '告警统计异常')
    expect(alert_history['total'] > 0, '告警历史为空')
    print('✅ 告警功能正常')

    carbon_route = api_request(
        session,
        'GET',
        f'/carbon/route/{route_id}',
        params={'region': 'sf'},
    )
    carbon_record = api_request(
        session,
        'POST',
        '/carbon/record',
        token=token,
        json_data={
            'route_id': route_id,
            'region': 'sf',
            'trip_date': date.today().isoformat(),
            'ride_count': 2,
        },
    )
    carbon_stats = api_request(
        session,
        'GET',
        '/carbon/my-stats',
        token=token,
        params={'region': 'sf'},
    )
    carbon_records = api_request(
        session,
        'GET',
        '/carbon/my-records',
        token=token,
        params={'region': 'sf', 'limit': 5},
    )
    carbon_board = api_request(
        session,
        'GET',
        '/carbon/leaderboard',
        params={'region': 'sf', 'limit': 5},
    )
    expect(carbon_stats['total_trips'] > 0, '碳排放个人统计为空')
    expect(carbon_route['distance_km'] > 0, '线路碳排放距离异常')
    expect(carbon_record['ride_count'] == 2, '碳排放录入次数异常')
    expect(len(carbon_records) > 0, '碳排放个人记录为空')
    expect(len(carbon_board) > 0, '碳排放排行榜为空')
    print('✅ 碳排放功能正常')

    flow_prediction = api_request(
        session,
        'GET',
        f'/stops/{stop_id}/flow-prediction',
        params={'region': 'sf'},
    )
    best_time = api_request(
        session,
        'GET',
        f'/stops/{stop_id}/best-time',
        params={'region': 'sf'},
    )
    flow_heatmap = api_request(
        session,
        'GET',
        '/stops/flow-heatmap',
        params={'region': 'sf'},
    )
    expect(len(flow_prediction) == 24, '客流预测未返回 24 小时数据')
    expect(len(best_time) > 0, '最佳时段推荐为空')
    expect(len(flow_heatmap) > 0, '客流热力图为空')
    print('✅ 客流预测功能正常')

    recommendations = api_request(
        session,
        'GET',
        '/recommendations',
        token=token,
        params={'region': 'sf', 'limit': 5},
    )
    expect(len(recommendations) > 0, '推荐列表为空')
    print('✅ 推荐功能正常')

    print('🎉 六个新增功能冒烟测试通过')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(f'❌ 测试失败: {exc}')
        sys.exit(1)
