#!/usr/bin/env python3
"""
SF Muni GTFS Route Attributes 映射
提供 category、subcategory 和 running_way 的中英文映射
"""

# Category 映射（类别）
CATEGORY_MAPPING = {
    '2': {
        'en': 'Core Routes',
        'zh': '核心线路',
        'description': '主要的轨道交通和高频公交线路'
    },
    '3': {
        'en': 'Secondary Routes',
        'zh': '辅助线路',
        'description': '普通公交、缆车和快线服务'
    },
    '4': {
        'en': 'Neighborhood Routes',
        'zh': '社区线路',
        'description': '服务于特定社区的线路'
    },
    '5': {
        'en': 'Special Service',
        'zh': '特殊服务',
        'description': '特殊服务线路'
    }
}

# Subcategory 映射（子类别）
SUBCATEGORY_MAPPING = {
    '201': {
        'en': 'Rapid Transit',
        'zh': '快速交通',
        'description': '轨道交通和高频公交'
    },
    '203': {
        'en': 'Rapid Transit Substitute',
        'zh': '快速交通替代',
        'description': '快速交通的临时替代服务'
    },
    '301': {
        'en': 'Local Service',
        'zh': '本地服务',
        'description': '普通公交和缆车服务'
    },
    '302': {
        'en': 'Express Service',
        'zh': '快线服务',
        'description': '快速直达服务，减少停靠站点'
    },
    '303': {
        'en': 'Owl Service',
        'zh': '夜间服务',
        'description': '深夜运营的线路'
    },
    '401': {
        'en': 'Community Service',
        'zh': '社区服务',
        'description': '服务于特定社区的线路'
    },
    '501': {
        'en': 'Special Service',
        'zh': '特殊服务',
        'description': '特殊服务线路（如 BART 早班车）'
    }
}

# Running Way 映射（运行方式）
RUNNING_WAY_MAPPING = {
    '2': {
        'en': 'Mixed Traffic with Partial Dedicated Lanes',
        'zh': '混合路权（部分专用道）',
        'description': '与其他车辆共享道路，但有部分专用车道'
    },
    '3': {
        'en': 'Mixed Traffic',
        'zh': '混合路权',
        'description': '与其他车辆共享道路'
    },
    '4': {
        'en': 'Mixed Traffic with Dedicated Lanes',
        'zh': '混合路权（含专用道）',
        'description': '主要与其他车辆共享道路，但有专用车道'
    },
    '5': {
        'en': 'Street Running',
        'zh': '街道运行',
        'description': '完全在街道上运行'
    }
}


def get_category_text(category: str, lang: str = 'zh') -> str:
    """
    获取类别的文本描述

    Args:
        category: 类别代码
        lang: 语言 ('zh' 或 'en')

    Returns:
        类别文本描述
    """
    if not category:
        return ''

    mapping = CATEGORY_MAPPING.get(str(category))
    if not mapping:
        return str(category)

    return mapping.get(lang, str(category))


def get_subcategory_text(subcategory: str, lang: str = 'zh') -> str:
    """
    获取子类别的文本描述

    Args:
        subcategory: 子类别代码
        lang: 语言 ('zh' 或 'en')

    Returns:
        子类别文本描述
    """
    if not subcategory:
        return ''

    mapping = SUBCATEGORY_MAPPING.get(str(subcategory))
    if not mapping:
        return str(subcategory)

    return mapping.get(lang, str(subcategory))


def get_running_way_text(running_way: str, lang: str = 'zh') -> str:
    """
    获取运行方式的文本描述

    Args:
        running_way: 运行方式代码
        lang: 语言 ('zh' 或 'en')

    Returns:
        运行方式文本描述
    """
    if not running_way:
        return ''

    mapping = RUNNING_WAY_MAPPING.get(str(running_way))
    if not mapping:
        return str(running_way)

    return mapping.get(lang, str(running_way))


def enrich_route_attributes(route_data: dict, lang: str = 'zh') -> dict:
    """
    为路线数据添加映射后的文本字段

    Args:
        route_data: 路线数据字典
        lang: 语言 ('zh' 或 'en')

    Returns:
        添加了文本字段的路线数据
    """
    if 'category' in route_data and route_data['category']:
        route_data['category_text'] = get_category_text(route_data['category'], lang)
        category_mapping = CATEGORY_MAPPING.get(str(route_data['category']))
        if category_mapping:
            route_data['category_description'] = category_mapping.get('description', '')

    if 'subcategory' in route_data and route_data['subcategory']:
        route_data['subcategory_text'] = get_subcategory_text(route_data['subcategory'], lang)
        subcategory_mapping = SUBCATEGORY_MAPPING.get(str(route_data['subcategory']))
        if subcategory_mapping:
            route_data['subcategory_description'] = subcategory_mapping.get('description', '')

    if 'running_way' in route_data and route_data['running_way']:
        route_data['running_way_text'] = get_running_way_text(route_data['running_way'], lang)
        running_way_mapping = RUNNING_WAY_MAPPING.get(str(route_data['running_way']))
        if running_way_mapping:
            route_data['running_way_description'] = running_way_mapping.get('description', '')

    return route_data


if __name__ == '__main__':
    # 测试映射
    print("Category 映射测试:")
    for code in ['2', '3', '4', '5']:
        print(f"  {code}: {get_category_text(code, 'zh')} / {get_category_text(code, 'en')}")

    print("\nSubcategory 映射测试:")
    for code in ['201', '203', '301', '302', '303', '401', '501']:
        print(f"  {code}: {get_subcategory_text(code, 'zh')} / {get_subcategory_text(code, 'en')}")

    print("\nRunning Way 映射测试:")
    for code in ['2', '3', '4', '5']:
        print(f"  {code}: {get_running_way_text(code, 'zh')} / {get_running_way_text(code, 'en')}")

    print("\n完整路线数据映射测试:")
    test_route = {
        'route_id': '14',
        'route_short_name': '14',
        'route_long_name': 'MISSION',
        'category': '2',
        'subcategory': '201',
        'running_way': '3'
    }
    enriched = enrich_route_attributes(test_route.copy())
    print(f"  原始数据: {test_route}")
    print(f"  映射后: {enriched}")
