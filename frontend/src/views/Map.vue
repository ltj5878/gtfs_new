<template>
  <div class="map-page">
    <el-card class="map-card">
      <template #header>
        <div class="map-header">
          <span>公交地图</span>
          <div class="map-controls">
            <el-select
              v-model="selectedRoute"
              placeholder="选择线路"
              clearable
              @change="onRouteChange"
              style="width: 200px; margin-right: 10px"
            >
              <el-option
                v-for="route in routes"
                :key="route.route_id"
                :label="`${route.route_short_name} ${route.route_long_name}`"
                :value="route.route_id"
              />
            </el-select>
            <el-button-group>
              <el-button
                :type="showStops ? 'primary' : 'default'"
                @click="toggleStops"
                size="small"
              >
                <el-icon><MapPin /></el-icon>
                站点
              </el-button>
              <el-button
                :type="showShapes ? 'primary' : 'default'"
                @click="toggleShapes"
                size="small"
              >
                <el-icon><Location /></el-icon>
                轨迹
              </el-button>
            </el-button-group>
          </div>
        </div>
      </template>
      <div class="map-container">
        <div id="map" class="map"></div>
        <div v-if="loading" class="map-loading">
          <el-icon class="is-loading"><Loading /></el-icon>
          <p>加载中...</p>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { MapPin, Location, Loading } from '@element-plus/icons-vue'
import L from 'leaflet'
import { getRoutes } from '@/api/routes'
import { getStops } from '@/api/stops'
import { getRouteShapes } from '@/api/shapes'

// 响应式数据
const map = ref(null)
const loading = ref(true)
const routes = ref([])
const selectedRoute = ref('')
const showStops = ref(true)
const showShapes = ref(true)

// 图层管理
const stopsLayer = ref(null)
const shapesLayer = ref(null)

// 修复Leaflet默认图标问题
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
})

// 初始化地图
const initMap = () => {
  nextTick(() => {
    try {
      map.value = L.map('map').setView([37.7749, -122.4194], 12)

      // 添加地图图层
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
      }).addTo(map.value)

      // 创建图层组
      stopsLayer.value = L.layerGroup().addTo(map.value)
      shapesLayer.value = L.layerGroup()

      console.log('地图初始化成功')
    } catch (error) {
      console.error('地图初始化失败:', error)
      ElMessage.error('地图初始化失败')
    }
  })
}

// 加载线路数据
const loadRoutes = async () => {
  try {
    console.log('开始加载线路数据')
    const response = await getRoutes({ page_size: 100 })
    console.log('线路数据响应:', response)
    routes.value = response.routes
    console.log('线路数据加载成功:', routes.value.length, '条线路')
  } catch (error) {
    console.error('加载线路失败:', error)
    ElMessage.error('加载线路数据失败')
  }
}

// 加载站点数据
const loadStops = async () => {
  try {
    console.log('开始加载站点数据')
    const response = await getStops({ page_size: 1000 })
    const stops = response.stops
    console.log('站点数据加载成功:', stops.length, '个站点')

    // 清除现有站点标记
    stopsLayer.value.clearLayers()

    // 添加站点标记（限制数量避免性能问题）
    stops.slice(0, 500).forEach(stop => {
      const marker = L.marker([stop.stop_lat, stop.stop_lon])
        .bindPopup(`
          <div>
            <strong>${stop.stop_name}</strong><br>
            <small>ID: ${stop.stop_id}</small>
          </div>
        `)
        .addTo(stopsLayer.value)
    })

    // 自动调整地图视图到所有站点
    if (stops.length > 0) {
      const bounds = L.latLngBounds(stops.slice(0, 100).map(stop => [stop.stop_lat, stop.stop_lon]))
      map.value.fitBounds(bounds, { padding: [50, 50] })
    }
  } catch (error) {
    console.error('加载站点失败:', error)
    ElMessage.error('加载站点数据失败')
  }
}

// 加载线路轨迹
const loadRouteShapes = async (routeId) => {
  try {
    console.log('开始加载线路轨迹:', routeId)
    const response = await getRouteShapes(routeId)
    const shapes = response
    console.log('轨迹数据加载成功:', shapes.length, '个轨迹')

    // 清除现有轨迹
    shapesLayer.value.clearLayers()

    // 绘制每个方向的轨迹
    shapes.forEach((shapeData, index) => {
      const points = shapeData.points.map(point => [point.shape_pt_lat, point.shape_pt_lon])

      // 不同方向使用不同颜色
      const colors = ['#005B95', '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
      const color = colors[index % colors.length]

      const polyline = L.polyline(points, {
        color: color,
        weight: 4,
        opacity: 0.8
      }).addTo(shapesLayer.value)

      // 添加轨迹信息
      polyline.bindPopup(`
        <div>
          <strong>线路轨迹</strong><br>
          <small>Shape ID: ${shapeData.shape_id}</small><br>
          <small>方向: ${shapeData.direction_id || '未知'}</small>
        </div>
      `)
    })

    ElMessage.success(`已加载线路轨迹`)
  } catch (error) {
    console.error('加载轨迹失败:', error)
    ElMessage.error('加载线路轨迹失败')
  }
}

// 线路选择变化
const onRouteChange = (routeId) => {
  console.log('线路选择变化:', routeId)
  if (routeId && showShapes.value) {
    loadRouteShapes(routeId)
  } else if (!routeId) {
    shapesLayer.value.clearLayers()
  }
}

// 切换站点显示
const toggleStops = () => {
  showStops.value = !showStops.value
  if (showStops.value) {
    map.value.addLayer(stopsLayer.value)
    if (stopsLayer.value.getLayers().length === 0) {
      loadStops()
    }
  } else {
    map.value.removeLayer(stopsLayer.value)
  }
  console.log('站点显示切换:', showStops.value)
}

// 切换轨迹显示
const toggleShapes = () => {
  showShapes.value = !showShapes.value
  if (showShapes.value) {
    map.value.addLayer(shapesLayer.value)
    if (selectedRoute.value) {
      loadRouteShapes(selectedRoute.value)
    }
  } else {
    map.value.removeLayer(shapesLayer.value)
  }
  console.log('轨迹显示切换:', showShapes.value)
}

// 组件挂载
onMounted(async () => {
  console.log('Map组件挂载')
  try {
    await Promise.all([
      loadRoutes(),
      loadStops()
    ])
    initMap()
    loading.value = false
    console.log('Map组件初始化完成')
  } catch (error) {
    console.error('Map组件初始化失败:', error)
    ElMessage.error('地图初始化失败')
    loading.value = false
  }
})

// 组件卸载
onUnmounted(() => {
  if (map.value) {
    map.value.remove()
  }
})
</script>

<style scoped>
.map-page {
  padding: 20px;
  height: calc(100vh - 120px);
}

.map-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.map-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.map-controls {
  display: flex;
  align-items: center;
}

.map-container {
  flex: 1;
  position: relative;
}

.map {
  width: 100%;
  height: 100%;
  border-radius: 4px;
}

.map-loading {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  color: #909399;
}

.map-loading p {
  margin-top: 10px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .map-page {
    padding: 10px;
  }

  .map-header {
    flex-direction: column;
    gap: 10px;
    align-items: flex-start;
  }

  .map-controls {
    width: 100%;
    justify-content: space-between;
  }
}
</style>