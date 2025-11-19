# GTFS数据获取设置指南

## 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 获取API Key
访问：https://511.org/open-data/token

填写邮箱后立即收到API key（无需等待审核）

### 3. 配置API Key
打开 `gtfs_data_fetcher.py`，找到第103行：
```python
API_KEY = "YOUR_API_KEY_HERE"
```
替换为你获取的API key

### 4. 运行
```bash
python gtfs_data_fetcher.py
```

## 支持的运营商

旧金山湾区主要运营商ID：
- `SF` - San Francisco Muni（旧金山公交）
- `AC` - AC Transit（东湾公交）
- `BA` - BART（湾区捷运）
- `CC` - County Connection
- `CT` - Caltrain（加州火车）

## 数据说明

### GTFS静态数据
包含：routes.txt, stops.txt, trips.txt, stop_times.txt等
用途：线路、站点、时刻表等基础信息

### GTFS Realtime数据
- **vehiclepositions**: 车辆实时位置
- **tripupdates**: 行程更新（延误信息）
- **servicealerts**: 服务警报

## 准点率分析建议

使用 `tripupdates` 中的 `arrival_delay` 和 `departure_delay` 字段：
- 正值表示延误（秒）
- 负值表示提前
- 0表示准点
