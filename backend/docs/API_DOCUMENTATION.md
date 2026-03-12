# GTFS RESTful API 文档

## 概述

这是一个基于 Flask 的 RESTful API 服务，提供对 PostgreSQL 中 GTFS 数据的查询接口。

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动服务

```bash
python api.py
```

默认端口：5000
默认地址：http://localhost:5000

### 3. 环境变量配置

可选的环境变量：
- `PORT`: API 服务端口（默认：5000）
- `DEBUG`: 调试模式（默认：True）

## API 响应格式

### 成功响应

```json
{
  "code": 200,
  "message": "success",
  "data": { ... }
}
```

### 错误响应

```json
{
  "code": 400,
  "message": "错误信息",
  "data": null
}
```

## API 接口列表

### 1. 健康检查

**GET** `/api/health`

检查 API 服务和数据库连接状态。

**响应示例：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "status": "healthy",
    "database": "connected"
  }
}
```

---

### 2. 运营机构 (Agencies)

#### 2.1 获取所有运营机构

**GET** `/api/agencies`

**响应示例：**
```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "agency_id": "SFMTA",
      "agency_name": "San Francisco Municipal Transportation Agency",
      "agency_url": "http://www.sfmta.com",
      "agency_timezone": "America/Los_Angeles",
      "agency_lang": "en",
      "agency_phone": "311",
      "agency_fare_url": null,
      "agency_email": null
    }
  ]
}
```

#### 2.2 获取指定运营机构

**GET** `/api/agencies/{agency_id}`

**路径参数：**
- `agency_id`: 运营机构 ID

---

### 3. 线路 (Routes)

#### 3.1 获取所有线路

**GET** `/api/routes`

**查询参数：**
- `page`: 页码（默认：1）
- `page_size`: 每页数量（默认：20）
- `agency_id`: 运营机构 ID（可选）
- `route_type`: 线路类型（可选）
  - 0: 轻轨/地铁
  - 1: 地铁
  - 2: 铁路
  - 3: 公交
  - 4: 轮渡
  - 5: 有轨电车
  - 6: 缆车
  - 7: 索道
- `search`: 搜索关键词（匹配线路名称，可选）

**响应示例：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "routes": [
      {
        "route_id": "1",
        "agency_id": "SFMTA",
        "route_short_name": "1",
        "route_long_name": "CALIFORNIA",
        "route_desc": null,
        "route_type": 3,
        "route_url": null,
        "route_color": "005596",
        "route_text_color": "FFFFFF",
        "category": "Local",
        "subcategory": null,
        "running_way": "Street"
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total": 100,
      "total_pages": 5
    }
  }
}
```

#### 3.2 获取指定线路

**GET** `/api/routes/{route_id}`

**路径参数：**
- `route_id`: 线路 ID

#### 3.3 获取线路方向

**GET** `/api/routes/{route_id}/directions`

获取指定线路的所有方向信息。

**响应示例：**
```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "route_id": "1",
      "direction_id": 0,
      "direction": "Outbound"
    },
    {
      "route_id": "1",
      "direction_id": 1,
      "direction": "Inbound"
    }
  ]
}
```

#### 3.4 获取线路站点

**GET** `/api/routes/{route_id}/stops`

获取指定线路的所有站点。

**查询参数：**
- `direction_id`: 方向 ID（可选，0 或 1）

**响应示例：**
```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "stop_id": "3016",
      "stop_code": "13016",
      "stop_name": "Clay St & Drumm St",
      "stop_lat": 37.79539,
      "stop_lon": -122.39699,
      "stop_desc": null,
      "min_sequence": 1
    }
  ]
}
```

---

### 4. 站点 (Stops)

#### 4.1 获取所有站点

**GET** `/api/stops`

**查询参数：**
- `page`: 页码（默认：1）
- `page_size`: 每页数量（默认：20）
- `search`: 搜索关键词（匹配站点名称，可选）
- `lat`: 纬度（可选，用于地理位置筛选）
- `lon`: 经度（可选，用于地理位置筛选）
- `radius`: 半径（公里，默认：1.0，需要配合 lat/lon 使用）

**响应示例：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "stops": [
      {
        "stop_id": "3016",
        "stop_code": "13016",
        "stop_name": "Clay St & Drumm St",
        "stop_lat": 37.79539,
        "stop_lon": -122.39699,
        "zone_id": null,
        "stop_desc": null,
        "stop_url": null,
        "location_type": 0,
        "parent_station": null,
        "stop_timezone": null,
        "wheelchair_boarding": 0,
        "platform_code": null
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total": 5000,
      "total_pages": 250
    }
  }
}
```

#### 4.2 获取指定站点

**GET** `/api/stops/{stop_id}`

**路径参数：**
- `stop_id`: 站点 ID

#### 4.3 获取站点经过的线路

**GET** `/api/stops/{stop_id}/routes`

获取经过指定站点的所有线路。

**响应示例：**
```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "route_id": "1",
      "route_short_name": "1",
      "route_long_name": "CALIFORNIA",
      "route_type": 3,
      "route_color": "005596",
      "route_text_color": "FFFFFF"
    }
  ]
}
```

---

### 5. 班次 (Trips)

#### 5.1 获取班次列表

**GET** `/api/trips`

**查询参数：**
- `page`: 页码（默认：1）
- `page_size`: 每页数量（默认：20）
- `route_id`: 线路 ID（可选）
- `service_id`: 服务 ID（可选）
- `direction_id`: 方向 ID（可选）

**响应示例：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "trips": [
      {
        "trip_id": "10001",
        "route_id": "1",
        "service_id": "WKDY",
        "trip_headsign": "Downtown",
        "trip_short_name": null,
        "direction_id": 0,
        "block_id": "1001",
        "shape_id": "1_0_var1",
        "wheelchair_accessible": 1,
        "bikes_allowed": 1
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total": 10000,
      "total_pages": 500
    }
  }
}
```

#### 5.2 获取指定班次

**GET** `/api/trips/{trip_id}`

**路径参数：**
- `trip_id`: 班次 ID

#### 5.3 获取班次时刻表

**GET** `/api/trips/{trip_id}/stop_times`

获取指定班次的所有站点时刻表。

**响应示例：**
```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "trip_id": "10001",
      "arrival_time": "06:00:00",
      "departure_time": "06:00:00",
      "stop_id": "3016",
      "stop_sequence": 1,
      "stop_headsign": null,
      "pickup_type": 0,
      "drop_off_type": 0,
      "shape_dist_traveled": 0.0,
      "stop_name": "Clay St & Drumm St",
      "stop_lat": 37.79539,
      "stop_lon": -122.39699
    }
  ]
}
```

---

### 6. 线路轨迹 (Shapes)

#### 6.1 获取线路轨迹

**GET** `/api/shapes/{shape_id}`

获取指定线路的地理轨迹点。

**路径参数：**
- `shape_id`: 轨迹 ID

**响应示例：**
```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "shape_id": "1_0_var1",
      "shape_pt_lat": 37.79539,
      "shape_pt_lon": -122.39699,
      "shape_pt_sequence": 1,
      "shape_dist_traveled": 0.0
    },
    {
      "shape_id": "1_0_var1",
      "shape_pt_lat": 37.79545,
      "shape_pt_lon": -122.39705,
      "shape_pt_sequence": 2,
      "shape_dist_traveled": 10.5
    }
  ]
}
```

---

### 7. 服务日历 (Calendar)

#### 7.1 获取服务日历

**GET** `/api/calendar`

获取所有服务日历信息。

**响应示例：**
```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "service_id": "WKDY",
      "monday": 1,
      "tuesday": 1,
      "wednesday": 1,
      "thursday": 1,
      "friday": 1,
      "saturday": 0,
      "sunday": 0,
      "start_date": "2025-01-01",
      "end_date": "2025-12-31",
      "service_description": "Weekday"
    }
  ]
}
```

---

### 8. 统计信息 (Stats)

#### 8.1 获取数据统计

**GET** `/api/stats`

获取数据库中各类数据的统计信息。

**响应示例：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "agencies": 1,
    "routes": 100,
    "stops": 5000,
    "trips": 10000,
    "stop_times": 150000,
    "shapes": 200
  }
}
```

---

## 使用示例

### 使用 curl

```bash
# 健康检查
curl http://localhost:5000/api/health

# 获取所有线路
curl http://localhost:5000/api/routes

# 搜索线路
curl "http://localhost:5000/api/routes?search=Market"

# 获取线路站点
curl http://localhost:5000/api/routes/1/stops

# 按地理位置搜索站点（旧金山市中心附近 1 公里）
curl "http://localhost:5000/api/stops?lat=37.7749&lon=-122.4194&radius=1"

# 获取班次时刻表
curl http://localhost:5000/api/trips/10001/stop_times
```

### 使用 Python requests

```python
import requests

BASE_URL = "http://localhost:5000/api"

# 获取所有线路
response = requests.get(f"{BASE_URL}/routes")
data = response.json()
routes = data['data']['routes']

# 获取指定线路的站点
route_id = routes[0]['route_id']
response = requests.get(f"{BASE_URL}/routes/{route_id}/stops")
stops = response.json()['data']

# 搜索站点
response = requests.get(f"{BASE_URL}/stops", params={
    'search': 'Market',
    'page': 1,
    'page_size': 10
})
stops = response.json()['data']['stops']
```

### 使用 JavaScript fetch

```javascript
const BASE_URL = 'http://localhost:5000/api';

// 获取所有线路
fetch(`${BASE_URL}/routes`)
  .then(response => response.json())
  .then(data => {
    console.log(data.data.routes);
  });

// 获取站点附近的线路
const stopId = '3016';
fetch(`${BASE_URL}/stops/${stopId}/routes`)
  .then(response => response.json())
  .then(data => {
    console.log(data.data);
  });
```

---

## 错误码说明

- `200`: 成功
- `400`: 请求参数错误
- `404`: 资源不存在
- `500`: 服务器内部错误

---

## 性能优化建议

1. **使用分页**: 对于大量数据的查询，始终使用分页参数
2. **缓存结果**: 对于静态数据（如线路、站点），可以在前端缓存
3. **按需查询**: 只查询需要的字段和数据
4. **地理位置查询**: 使用 lat/lon/radius 参数限制查询范围

---

## 开发计划

未来可能添加的功能：
- [ ] 实时车辆位置查询
- [ ] 到站时间预测
- [ ] 线路延误统计
- [ ] 用户收藏功能
- [ ] WebSocket 实时推送
- [ ] GraphQL 支持
- [ ] API 认证和限流

---

## 技术栈

- **框架**: Flask 3.0+
- **数据库**: PostgreSQL 16
- **CORS**: Flask-CORS
- **连接池**: psycopg2 SimpleConnectionPool

---

## 许可证

本项目遵循项目主许可证。
