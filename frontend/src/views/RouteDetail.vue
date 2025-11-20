<template>
  <div class="route-detail-page">
    <div v-loading="routeStore.loading" class="detail-content">
      <div v-if="routeStore.currentRoute" class="route-detail">
        <el-page-header @back="$router.back()" title="返回">
          <template #content>
            <div class="route-title">
              <div class="route-badge" :style="{ backgroundColor: `#${routeStore.currentRoute.route_color || '005596'}` }">
                <span :style="{ color: `#${routeStore.currentRoute.route_text_color || 'FFFFFF'}` }">
                  {{ routeStore.currentRoute.route_short_name || 'N/A' }}
                </span>
              </div>
              <span>{{ routeStore.currentRoute.route_long_name }}</span>
            </div>
          </template>
        </el-page-header>

        <el-divider />

        <el-row :gutter="20">
          <el-col :xs="24" :md="12">
            <el-card>
              <template #header>
                <span>线路信息</span>
              </template>
              <el-descriptions :column="1" border>
                <el-descriptions-item label="线路ID">{{ routeStore.currentRoute.route_id }}</el-descriptions-item>
                <el-descriptions-item label="线路名称">{{ routeStore.currentRoute.route_long_name }}</el-descriptions-item>
                <el-descriptions-item label="线路编号">{{ routeStore.currentRoute.route_short_name }}</el-descriptions-item>
                <el-descriptions-item label="线路类型">{{ getRouteTypeName(routeStore.currentRoute.route_type) }}</el-descriptions-item>
                <el-descriptions-item v-if="routeStore.currentRoute.category" label="类别">{{ routeStore.currentRoute.category }}</el-descriptions-item>
                <el-descriptions-item v-if="routeStore.currentRoute.subcategory" label="子类别">{{ routeStore.currentRoute.subcategory }}</el-descriptions-item>
                <el-descriptions-item v-if="routeStore.currentRoute.running_way" label="运行方式">{{ routeStore.currentRoute.running_way }}</el-descriptions-item>
              </el-descriptions>
            </el-card>
          </el-col>

          <el-col :xs="24" :md="12">
            <el-card>
              <template #header>
                <span>方向信息</span>
              </template>
              <div v-if="routeStore.directions.length > 0">
                <el-radio-group v-model="selectedDirection" @change="handleDirectionChange">
                  <el-radio-button
                    v-for="dir in routeStore.directions"
                    :key="dir.direction_id"
                    :label="dir.direction_id"
                  >
                    {{ dir.direction }}
                  </el-radio-button>
                </el-radio-group>
              </div>
              <el-empty v-else description="暂无方向信息" :image-size="80" />
            </el-card>
          </el-col>
        </el-row>

        <el-row :gutter="20" class="content-row">
          <el-col :xs="24" :lg="12">
            <el-card class="stops-card">
              <template #header>
                <span>站点列表</span>
              </template>
              <div v-loading="loadingStops">
                <el-timeline v-if="routeStore.stops.length > 0">
                  <el-timeline-item
                    v-for="(stop, index) in routeStore.stops"
                    :key="stop.stop_id"
                    :timestamp="`站点 ${index + 1}`"
                  >
                    <el-card shadow="hover" class="stop-item" @click="handleStopClick(stop)">
                      <div class="stop-item-content">
                        <div class="stop-name">{{ stop.stop_name }}</div>
                        <div class="stop-code">{{ stop.stop_code }}</div>
                      </div>
                    </el-card>
                  </el-timeline-item>
                </el-timeline>
                <el-empty v-else description="暂无站点信息" />
              </div>
            </el-card>
          </el-col>

          <el-col :xs="24" :lg="12">
            <el-card class="map-card">
              <template #header>
                <span>线路地图</span>
              </template>
              <div class="map-container">
                <div id="route-map" class="route-map"></div>
                <div v-if="loadingMap" class="map-loading">
                  <el-icon class="is-loading"><Loading /></el-icon>
                  <p>加载地图中...</p>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useRouteStore } from '@/stores/routeStore'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { Loading } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const routeStore = useRouteStore()

const selectedDirection = ref(null)
const loadingStops = ref(false)
const loadingMap = ref(false)
const map = ref(null)
const markersLayer = ref(null)
const routeLineLayer = ref(null)

const routeTypeNames = {
  0: '轻轨/地铁',
  1: '地铁',
  2: '铁路',
  3: '公交',
  4: '轮渡',
  5: '有轨电车',
  6: '缆车',
  7: '索道'
}

const getRouteTypeName = (type) => {
  return routeTypeNames[type] || '未知'
}

const loadRouteStops = async (directionId = null) => {
  loadingStops.value = true
  try {
    await routeStore.fetchRouteStops(route.params.id, directionId)
  } catch (error) {
    console.error('加载站点失败:', error)
  } finally {
    loadingStops.value = false
  }
}

const handleDirectionChange = (directionId) => {
  loadRouteStops(directionId)
}

const handleStopClick = (stop) => {
  router.push(`/stops/${stop.stop_id}`)
}

// 修复Leaflet默认图标问题
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
})

// 初始化地图
const initMap = () => {
  // 使用 setTimeout 确保 DOM 完全渲染
  setTimeout(() => {
    if (!map.value) {
      try {
        const mapElement = document.getElementById('route-map')
        if (!mapElement) {
          console.error('地图容器不存在')
          return
        }

        map.value = L.map('route-map', {
          center: [37.7749, -122.4194],
          zoom: 13,
          scrollWheelZoom: true
        })

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
          attribution: '© OpenStreetMap contributors',
          maxZoom: 19
        }).addTo(map.value)

        markersLayer.value = L.layerGroup().addTo(map.value)
        routeLineLayer.value = L.layerGroup().addTo(map.value)

        // 强制刷新地图尺寸
        map.value.invalidateSize()

        console.log('地图初始化成功')
      } catch (error) {
        console.error('地图初始化失败:', error)
      }
    }
  }, 100)
}

// 绘制线路和站点
const drawRouteOnMap = () => {
  if (!map.value || !routeStore.stops || routeStore.stops.length === 0) {
    return
  }

  loadingMap.value = true

  try {
    // 清除现有标记和线路
    if (markersLayer.value) {
      markersLayer.value.clearLayers()
    }
    if (routeLineLayer.value) {
      routeLineLayer.value.clearLayers()
    }

    const stops = routeStore.stops
    const routeColor = `#${routeStore.currentRoute?.route_color || '005B95'}`

    // 创建站点坐标数组
    const coordinates = []

    // 添加站点标记
    stops.forEach((stop, index) => {
      if (stop.stop_lat && stop.stop_lon) {
        coordinates.push([stop.stop_lat, stop.stop_lon])

        // 创建自定义图标
        const customIcon = L.divIcon({
          className: 'custom-stop-marker',
          html: `<div style="background-color: ${routeColor}; color: white; width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: bold; border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.3);">${index + 1}</div>`,
          iconSize: [28, 28],
          iconAnchor: [14, 14]
        })

        const marker = L.marker([stop.stop_lat, stop.stop_lon], { icon: customIcon })
          .bindPopup(`
            <div style="min-width: 150px;">
              <strong>${stop.stop_name}</strong><br>
              <small>站点 ${index + 1}</small><br>
              <small>编号: ${stop.stop_code || 'N/A'}</small>
            </div>
          `)
          .addTo(markersLayer.value)

        // 点击标记跳转到站点详情
        marker.on('click', () => {
          router.push(`/stops/${stop.stop_id}`)
        })
      }
    })

    // 调整地图视图以显示所有站点
    if (coordinates.length > 1) {
      const bounds = L.latLngBounds(coordinates)
      map.value.fitBounds(bounds, { padding: [50, 50] })
    } else if (coordinates.length === 1) {
      // 如果只有一个站点，居中显示
      map.value.setView(coordinates[0], 15)
    }

    console.log('站点绘制成功，共', stops.length, '个站点')
  } catch (error) {
    console.error('绘制线路失败:', error)
  } finally {
    loadingMap.value = false
  }
}

// 监听站点数据变化
watch(() => routeStore.stops, () => {
  if (map.value && routeStore.stops.length > 0) {
    drawRouteOnMap()
  }
}, { deep: true })

onMounted(async () => {
  try {
    await routeStore.fetchRouteById(route.params.id)
    await routeStore.fetchRouteDirections(route.params.id)

    // 初始化地图
    initMap()

    if (routeStore.directions.length > 0) {
      selectedDirection.value = routeStore.directions[0].direction_id
      await loadRouteStops(selectedDirection.value)
    } else {
      await loadRouteStops()
    }

    // 等待地图初始化完成后绘制线路
    await nextTick()
    if (routeStore.stops.length > 0) {
      drawRouteOnMap()
    }
  } catch (error) {
    console.error('加载线路详情失败:', error)
  }
})

onUnmounted(() => {
  if (map.value) {
    map.value.remove()
    map.value = null
  }
})
</script>

<style scoped>
.route-detail-page {
  padding: 20px;
}

.route-title {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 20px;
  font-weight: 600;
}

.route-badge {
  width: 40px;
  height: 40px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 14px;
}

.content-row {
  margin-top: 20px;
}

.stops-card {
  height: 600px;
  overflow-y: auto;
}

.map-card {
  height: 600px;
}

.map-container {
  height: 520px;
  position: relative;
}

.route-map {
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
  background-color: rgba(255, 255, 255, 0.9);
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.map-loading p {
  margin-top: 10px;
}

.stop-item {
  cursor: pointer;
  transition: transform 0.2s;
}

.stop-item:hover {
  transform: translateX(4px);
}

.stop-item-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stop-name {
  font-weight: 500;
}

.stop-code {
  font-size: 12px;
  color: #909399;
}

/* 响应式设计 */
@media (max-width: 992px) {
  .map-card {
    margin-top: 20px;
  }
}
</style>
