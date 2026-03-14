<template>
  <div class="map-view">
    <!-- 顶部控制栏 -->
    <div class="map-controls">
      <div class="control-section">
        <el-select
          v-model="selectedAgency"
          placeholder="选择运营机构"
          clearable
          @change="handleAgencyChange"
          style="width: 200px"
        >
          <el-option
            v-for="agency in agencies"
            :key="agency.agency_id"
            :label="agency.agency_name"
            :value="agency.agency_id"
          />
        </el-select>

        <el-select
          v-model="selectedRoute"
          placeholder="选择线路"
          clearable
          filterable
          @change="handleRouteChange"
          style="width: 200px"
        >
          <el-option
            v-for="route in routes"
            :key="route.route_id"
            :label="`${route.route_short_name} - ${route.route_long_name}`"
            :value="route.route_id"
          />
        </el-select>

        <el-button type="primary" @click="showAllStops">
          <el-icon><Location /></el-icon>
          显示所有站点
        </el-button>

        <el-button @click="resetMap">
          <el-icon><RefreshRight /></el-icon>
          重置地图
        </el-button>
      </div>

      <div class="map-info">
        <el-tag v-if="selectedRoute" type="primary">
          已选线路: {{ getRouteLabel(selectedRoute) }}
        </el-tag>
        <el-tag type="info">
          站点数量: {{ visibleStops.length || 0 }}
        </el-tag>
        <el-tag v-if="!selectedRoute && Object.keys(routeStopsMap).length > 0" type="success">
          显示线路: {{ Object.keys(routeStopsMap).length }} 条
        </el-tag>
      </div>
    </div>

    <!-- 地图容器 -->
    <div id="map" class="map-container"></div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-overlay">
      <el-icon class="is-loading" :size="40"><Loading /></el-icon>
      <p>加载地图数据中...</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRouter } from 'vue-router'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { Location, RefreshRight, Loading } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import apiClient from '@/api/index'
import { useRegionStore } from '@/stores/regionStore'

const router = useRouter()
const regionStore = useRegionStore()
const loading = ref(false)
const map = ref(null)
const markersLayer = ref(null)
const routeLayer = ref(null)

const agencies = ref([])
const routes = ref([])
const stops = ref([])
const visibleStops = ref([])
const routeStopsMap = ref({}) // 存储每条线路的站点信息

const selectedAgency = ref(null)
const selectedRoute = ref(null)

// 旧金山湾区中心坐标
const DEFAULT_CENTER = [37.7749, -122.4194]
const DEFAULT_ZOOM = 12

// 预定义的线路颜色
const ROUTE_COLORS = [
  '#409eff', '#67c23a', '#e6a23c', '#f56c6c', '#909399',
  '#00d4aa', '#ff6b9d', '#c990ff', '#ffa940', '#36cfc9',
  '#5b8ff9', '#61ddaa', '#f6bd16', '#7262fd', '#78d3f8'
]

// 根据线路ID生成颜色
const getRouteColor = (routeId) => {
  // 如果线路有自定义颜色，使用自定义颜色
  const route = routes.value.find(r => r.route_id === routeId)
  if (route && route.route_color) {
    return '#' + route.route_color
  }
  // 否则根据ID生成颜色
  const index = parseInt(routeId) % ROUTE_COLORS.length
  return ROUTE_COLORS[index]
}

// 初始化地图
const initMap = () => {
  // 创建地图实例
  map.value = L.map('map').setView(DEFAULT_CENTER, DEFAULT_ZOOM)

  // 添加 OpenStreetMap 图层
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 19
  }).addTo(map.value)

  // 创建标记图层组
  markersLayer.value = L.layerGroup().addTo(map.value)
  routeLayer.value = L.layerGroup().addTo(map.value)
}

// 加载运营机构
const loadAgencies = async () => {
  try {
    const data = await apiClient.get('/agencies')
    agencies.value = Array.isArray(data) ? data : (data?.agencies || [])
  } catch (error) {
    console.error('加载运营机构失败:', error)
    ElMessage.error('加载运营机构失败')
  }
}

// 加载线路
const loadRoutes = async (agencyId = null) => {
  try {
    loading.value = true
    const params = { page_size: 1000 }
    if (agencyId) {
      params.agency_id = agencyId
    }
    const data = await apiClient.get('/routes', { params })
    routes.value = data?.routes || []
  } catch (error) {
    console.error('加载线路失败:', error)
    ElMessage.error('加载线路失败')
  } finally {
    loading.value = false
  }
}

// 加载站点
const loadStops = async (routeId = null) => {
  try {
    loading.value = true

    if (routeId) {
      // 加载特定线路的站点
      const data = await apiClient.get(`/routes/${routeId}/stops`)
      stops.value = Array.isArray(data) ? data : (data?.stops || [])
      visibleStops.value = stops.value

      // 存储该线路的站点信息
      routeStopsMap.value = {
        [routeId]: stops.value
      }

      displayStopsWithRoute(routeId)
    } else {
      // 加载所有线路及其站点
      await loadAllRoutesWithStops()
    }
  } catch (error) {
    console.error('加载站点失败:', error)
    ElMessage.error('加载站点失败')
  } finally {
    loading.value = false
  }
}

// 加载所有线路及其站点
const loadAllRoutesWithStops = async () => {
  try {
    // 获取所有线路
    const data = await apiClient.get('/routes', {
      params: { page_size: 100 } // 限制显示前100条线路，避免数据过多
    })
    const allRoutes = data?.routes || []

    // 为每条线路加载站点
    routeStopsMap.value = {}
    const promises = allRoutes.slice(0, 20).map(async (route) => { // 只显示前20条线路
      try {
        const routeData = await apiClient.get(`/routes/${route.route_id}/stops`)
        const routeStops = Array.isArray(routeData) ? routeData : (routeData?.stops || [])
        if (routeStops.length > 0) {
          routeStopsMap.value[route.route_id] = routeStops
        }
      } catch (error) {
        console.error(`加载线路 ${route.route_id} 的站点失败:`, error)
      }
    })

    await Promise.all(promises)
    displayAllRoutesWithStops()
  } catch (error) {
    console.error('加载线路站点失败:', error)
    ElMessage.error('加载线路站点失败')
  }
}

// 显示单条线路的站点（带轨迹线）
const displayStopsWithRoute = async (routeId) => {
  markersLayer.value.clearLayers()
  routeLayer.value.clearLayers()

  const routeStops = routeStopsMap.value[routeId]
  if (!routeStops || routeStops.length === 0) {
    return
  }

  const color = getRouteColor(routeId)
  const bounds = []

  // 先加载并显示线路轨迹
  await loadAndDisplayRouteShape(routeId, color)

  // 去重站点（同一个站点可能在多个 trip 中）
  const uniqueStops = {}
  routeStops.forEach(stop => {
    if (!uniqueStops[stop.stop_id]) {
      uniqueStops[stop.stop_id] = stop
    }
  })

  // 添加站点标记
  Object.values(uniqueStops).forEach((stop) => {
    if (stop.stop_lat && stop.stop_lon) {
      const latLng = [stop.stop_lat, stop.stop_lon]
      bounds.push(latLng)

      // 创建带颜色的站点标记
      const stopIcon = L.divIcon({
        className: 'custom-stop-marker',
        html: `<div class="marker-pin" style="background-color: ${color}; border-color: white;"></div>`,
        iconSize: [20, 20],
        iconAnchor: [10, 20]
      })

      const marker = L.marker(latLng, { icon: stopIcon })
        .bindPopup(`
          <div class="stop-popup">
            <h3>${stop.stop_name}</h3>
            <p><strong>站点ID:</strong> ${stop.stop_id}</p>
            ${stop.stop_code ? `<p><strong>站点代码:</strong> ${stop.stop_code}</p>` : ''}
            <button onclick="window.location.href='#/stops/${stop.stop_id}'">查看详情</button>
          </div>
        `)

      markersLayer.value.addLayer(marker)
    }
  })

  // 自动调整地图视野
  if (bounds.length > 0) {
    map.value.fitBounds(bounds, { padding: [50, 50] })
  }
}

// 加载并显示线路轨迹
const loadAndDisplayRouteShape = async (routeId, color) => {
  try {
    const shapes = await apiClient.get(`/routes/${routeId}/shapes`)
    const shapeList = Array.isArray(shapes) ? shapes : (shapes?.shapes || [])

    if (shapeList.length === 0) return

    // 按 shape_id 分组
    const shapeGroups = {}
    shapeList.forEach(point => {
      if (!shapeGroups[point.shape_id]) {
        shapeGroups[point.shape_id] = []
      }
      shapeGroups[point.shape_id].push(point)
    })

    // 绘制每条轨迹
    Object.values(shapeGroups).forEach(points => {
      const sortedPoints = points.sort((a, b) => a.shape_pt_sequence - b.shape_pt_sequence)
      const latLngs = sortedPoints.map(p => [p.shape_pt_lat, p.shape_pt_lon])

      const polyline = L.polyline(latLngs, {
        color: color,
        weight: 4,
        opacity: 0.7,
        smoothFactor: 1
      })

      routeLayer.value.addLayer(polyline)
    })
  } catch (error) {
    console.error('加载线路轨迹失败:', error)
  }
}

// 显示所有线路的站点（带轨迹线）
const displayAllRoutesWithStops = async () => {
  markersLayer.value.clearLayers()
  routeLayer.value.clearLayers()

  const bounds = []
  let totalStops = 0

  // 遍历每条线路
  for (const [routeId, routeStops] of Object.entries(routeStopsMap.value)) {
    if (!routeStops || routeStops.length === 0) continue

    const color = getRouteColor(routeId)

    // 加载并显示线路轨迹
    await loadAndDisplayRouteShape(routeId, color)

    // 去重站点
    const uniqueStops = {}
    routeStops.forEach(stop => {
      if (!uniqueStops[stop.stop_id]) {
        uniqueStops[stop.stop_id] = stop
      }
    })

    // 添加站点标记
    Object.values(uniqueStops).forEach((stop) => {
      if (stop.stop_lat && stop.stop_lon) {
        const latLng = [stop.stop_lat, stop.stop_lon]
        bounds.push(latLng)
        totalStops++

        // 创建带颜色的站点标记
        const stopIcon = L.divIcon({
          className: 'custom-stop-marker',
          html: `<div class="marker-pin" style="background-color: ${color}; border-color: white;"></div>`,
          iconSize: [14, 14],
          iconAnchor: [7, 14]
        })

        const route = routes.value.find(r => r.route_id === routeId)
        const routeName = route ? `${route.route_short_name} - ${route.route_long_name}` : routeId

        const marker = L.marker(latLng, { icon: stopIcon })
          .bindPopup(`
            <div class="stop-popup">
              <h3>${stop.stop_name}</h3>
              <p><strong>所属线路:</strong> ${routeName}</p>
              <p><strong>站点ID:</strong> ${stop.stop_id}</p>
              <button onclick="window.location.href='#/stops/${stop.stop_id}'">查看详情</button>
            </div>
          `)

        markersLayer.value.addLayer(marker)
      }
    })
  }

  // 更新可见站点数量
  visibleStops.value = { length: totalStops }

  // 自动调整地图视野
  if (bounds.length > 0) {
    map.value.fitBounds(bounds, { padding: [50, 50] })
  }
}


// 处理运营机构变化
const handleAgencyChange = (agencyId) => {
  selectedRoute.value = null
  if (agencyId) {
    loadRoutes(agencyId)
  } else {
    loadRoutes()
  }
  resetMap()
}

// 处理线路变化
const handleRouteChange = (routeId) => {
  if (routeId) {
    loadStops(routeId)
  } else {
    resetMap()
  }
}

// 显示所有站点
const showAllStops = () => {
  selectedAgency.value = null
  selectedRoute.value = null
  loadStops()
}

// 重置地图
const resetMap = () => {
  markersLayer.value.clearLayers()
  routeLayer.value.clearLayers()
  visibleStops.value = []
  routeStopsMap.value = {}
  map.value.setView(DEFAULT_CENTER, DEFAULT_ZOOM)
}

// 获取线路标签
const getRouteLabel = (routeId) => {
  const route = routes.value.find(r => r.route_id === routeId)
  return route ? `${route.route_short_name} - ${route.route_long_name}` : ''
}

onMounted(async () => {
  initMap()
  await loadAgencies()
  await loadRoutes()
})

watch(() => regionStore.selectedRegion, async () => {
  selectedAgency.value = null
  selectedRoute.value = null
  markersLayer.value.clearLayers()
  routeLayer.value.clearLayers()
  visibleStops.value = []
  routeStopsMap.value = {}
  await loadAgencies()
  await loadRoutes()
})

onBeforeUnmount(() => {
  if (map.value) {
    map.value.remove()
  }
})
</script>

<style scoped>
.map-view {
  height: calc(100vh - 120px);
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
}

.map-controls {
  background: white;
  padding: 16px 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  z-index: 1000;
}

.control-section {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  align-items: center;
}

.map-info {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.map-container {
  flex: 1;
  position: relative;
  z-index: 1;
}

.loading-overlay {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: rgba(255, 255, 255, 0.95);
  padding: 40px 60px;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  text-align: center;
  z-index: 2000;
}

.loading-overlay p {
  margin-top: 16px;
  color: #606266;
  font-size: 14px;
}

/* 自定义站点标记样式 */
:deep(.custom-stop-marker) {
  background: transparent;
  border: none;
}

:deep(.marker-pin) {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #409eff;
  border: 3px solid white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  cursor: pointer;
  transition: all 0.3s ease;
}

:deep(.marker-pin:hover) {
  transform: scale(1.2);
  background: #66b1ff;
}

/* 弹出窗口样式 */
:deep(.leaflet-popup-content) {
  margin: 0;
  padding: 0;
}

:deep(.stop-popup) {
  padding: 16px;
  min-width: 200px;
}

:deep(.stop-popup h3) {
  margin: 0 0 12px 0;
  font-size: 16px;
  color: #303133;
  font-weight: 600;
}

:deep(.stop-popup p) {
  margin: 6px 0;
  font-size: 13px;
  color: #606266;
}

:deep(.stop-popup button) {
  margin-top: 12px;
  width: 100%;
  padding: 8px 16px;
  background: #409eff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  transition: background 0.3s ease;
}

:deep(.stop-popup button:hover) {
  background: #66b1ff;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .map-view {
    height: calc(100vh - 100px);
  }

  .map-controls {
    padding: 12px;
  }

  .control-section {
    width: 100%;
  }

  .control-section .el-select,
  .control-section .el-button {
    flex: 1;
    min-width: 120px;
  }
}
</style>
