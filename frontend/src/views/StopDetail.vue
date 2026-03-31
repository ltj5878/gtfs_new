<template>
  <div class="stop-detail-page">
    <div v-loading="stopStore.loading" class="detail-content">
      <div v-if="stopStore.currentStop" class="stop-detail">
        <el-page-header @back="$router.back()" :title="$t('common.back')">
          <template #content>
            <div class="stop-title">
              <el-icon :size="24"><Location /></el-icon>
              <span>{{ stopStore.currentStop.stop_name }}</span>
              <!-- 收藏按钮 -->
              <el-icon
                class="favorite-btn"
                :class="{ 'is-favorited': stopFavorited }"
                :size="22"
                @click.stop="handleFavorite"
                :title="stopFavorited ? $t('common.unfavorite') : $t('common.favoriteStop')"
              >
                <Star />
              </el-icon>
            </div>
          </template>
        </el-page-header>

        <el-divider />

        <el-row :gutter="20">
          <el-col :xs="24" :md="12">
            <el-card>
              <template #header>
                <span>{{ $t('stopDetail.stopInfo') }}</span>
              </template>
              <el-descriptions :column="1" border>
                <el-descriptions-item :label="$t('stopDetail.stopId')">{{ stopStore.currentStop.stop_id }}</el-descriptions-item>
                <el-descriptions-item :label="$t('stopDetail.stopName')">{{ stopStore.currentStop.stop_name }}</el-descriptions-item>
                <el-descriptions-item v-if="stopStore.currentStop.stop_code" :label="$t('stopDetail.stopCode')">{{ stopStore.currentStop.stop_code }}</el-descriptions-item>
                <el-descriptions-item :label="$t('stopDetail.latitude')">{{ stopStore.currentStop.stop_lat.toFixed(6) }}</el-descriptions-item>
                <el-descriptions-item :label="$t('stopDetail.longitude')">{{ stopStore.currentStop.stop_lon.toFixed(6) }}</el-descriptions-item>
                <el-descriptions-item v-if="stopStore.currentStop.stop_desc" :label="$t('stopDetail.description')">{{ stopStore.currentStop.stop_desc }}</el-descriptions-item>
                <el-descriptions-item v-if="stopStore.currentStop.wheelchair_boarding !== null" :label="$t('stopDetail.wheelchair')">
                  {{ getWheelchairText(stopStore.currentStop.wheelchair_boarding) }}
                </el-descriptions-item>
              </el-descriptions>
            </el-card>
          </el-col>

          <el-col :xs="24" :md="12">
            <el-card>
              <template #header>
                <div class="map-header">
                  <span>{{ $t('stopDetail.mapLocation') }}</span>
                  <el-button
                    v-if="stopStore.stopRoutes.length > 0"
                    type="primary"
                    size="small"
                    @click="viewRouteMap"
                  >
                    {{ $t('stopDetail.viewRouteMap') }}
                  </el-button>
                </div>
              </template>
              <div class="map-container">
                <div id="stop-map" class="map"></div>
              </div>
            </el-card>
          </el-col>
        </el-row>

        <el-card class="routes-card">
          <template #header>
            <span>{{ $t('stopDetail.passingRoutes') }}</span>
          </template>
          <div v-loading="loadingRoutes">
            <div v-if="stopStore.stopRoutes.length > 0" class="routes-list">
              <el-card
                v-for="route in stopStore.stopRoutes"
                :key="route.route_id"
                shadow="hover"
                class="route-item"
                @click="handleRouteClick(route)"
              >
                <div class="route-item-content">
                  <div class="route-badge" :style="{ backgroundColor: `#${route.route_color || '005596'}` }">
                    <span :style="{ color: `#${route.route_text_color || 'FFFFFF'}` }">
                      {{ route.route_short_name || 'N/A' }}
                    </span>
                  </div>
                  <div class="route-info">
                    <div class="route-name">{{ route.route_long_name }}</div>
                    <div class="route-type">{{ getRouteTypeName(route.route_type) }}</div>
                  </div>
                </div>
              </el-card>
            </div>
            <el-empty v-else :description="$t('stopDetail.noRouteInfo')" />
          </div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { useStopStore } from '@/stores/stopStore'
import { useRegionStore } from '@/stores/regionStore'
import { useFavoriteStore } from '@/stores/favoriteStore.js'
import { useAuthStore } from '@/stores/authStore.js'
import { Location, MapLocation, Star } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const stopStore = useStopStore()
const regionStore = useRegionStore()
const favoriteStore = useFavoriteStore()
const authStore = useAuthStore()

const loadingRoutes = ref(false)
const map = ref(null)

const stopFavorited = computed(() =>
  stopStore.currentStop
    ? favoriteStore.isFavorite(regionStore.selectedRegion, 'stop', stopStore.currentStop.stop_id)
    : false
)

const handleFavorite = async () => {
  if (!authStore.isLoggedIn) {
    ElMessage.warning(t('common.loginFirst'))
    return
  }
  if (!stopStore.currentStop) return
  try {
    await favoriteStore.toggleFavorite({
      region: regionStore.selectedRegion,
      item_type: 'stop',
      item_id: stopStore.currentStop.stop_id,
      item_name: stopStore.currentStop.stop_name || stopStore.currentStop.stop_id
    })
  } catch (e) {
    ElMessage.error(t('common.operationFailed'))
  }
}

// 修复Leaflet默认图标问题
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
})

// 初始化站点地图
const initStopMap = () => {
  if (!stopStore.currentStop) return

  // 使用 setTimeout 确保 DOM 完全渲染
  setTimeout(() => {
    try {
      const mapElement = document.getElementById('stop-map')
      if (!mapElement) {
        console.error('地图容器不存在')
        return
      }

      // 创建地图实例，以站点位置为中心
      map.value = L.map('stop-map', {
        center: [stopStore.currentStop.stop_lat, stopStore.currentStop.stop_lon],
        zoom: 16,
        scrollWheelZoom: true
      })

      // 添加地图图层
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19
      }).addTo(map.value)

      // 添加站点标记
      const stopMarker = L.marker([
        stopStore.currentStop.stop_lat,
        stopStore.currentStop.stop_lon
      ]).addTo(map.value)

      // 创建弹出窗口内容
      const popupContent = `
        <div>
          <strong>${stopStore.currentStop.stop_name}</strong><br>
          <small>ID: ${stopStore.currentStop.stop_id}</small><br>
          ${stopStore.currentStop.stop_code ? `<small>编号: ${stopStore.currentStop.stop_code}</small><br>` : ''}
          <small>纬度: ${stopStore.currentStop.stop_lat.toFixed(6)}</small><br>
          <small>经度: ${stopStore.currentStop.stop_lon.toFixed(6)}</small>
        </div>
      `

      stopMarker.bindPopup(popupContent).openPopup()

      // 强制刷新地图尺寸
      map.value.invalidateSize()

      console.log('站点地图初始化成功，站点:', stopStore.currentStop.stop_name)
    } catch (error) {
      console.error('站点地图初始化失败:', error)
    }
  }, 100)
}

const routeTypeNames = computed(() => ({
  0: t('routeType.0'),
  1: t('routeType.1'),
  2: t('routeType.2'),
  3: t('routeType.3'),
  4: t('routeType.4'),
  5: t('routeType.5'),
  6: t('routeType.6'),
  7: t('routeType.7')
}))

const getRouteTypeName = (type) => {
  return routeTypeNames.value[type] || t('common.unknown')
}

const getWheelchairText = (value) => {
  return t(`wheelchair.${value}`) || t('common.unknown')
}

const handleRouteClick = (route) => {
  router.push(`/routes/${route.route_id}`)
}

const viewRouteMap = () => {
  if (stopStore.stopRoutes.length > 0) {
    // 跳转到第一条线路的详情页，那里有完整的线路地图
    router.push(`/routes/${stopStore.stopRoutes[0].route_id}`)
  }
}

onMounted(async () => {
  try {
    await stopStore.fetchStopById(route.params.id)

    // 初始化地图
    initStopMap()

    loadingRoutes.value = true
    await stopStore.fetchStopRoutes(route.params.id)
  } catch (error) {
    console.error('加载站点详情失败:', error)
  } finally {
    loadingRoutes.value = false
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
.stop-detail-page {
  padding: 20px;
}

.stop-title {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 20px;
  font-weight: 600;
}

.favorite-btn {
  color: #c0c4cc;
  cursor: pointer;
  transition: color 0.2s, transform 0.2s;
  flex-shrink: 0;
}

.favorite-btn:hover {
  color: #f0a020;
  transform: scale(1.2);
}

.favorite-btn.is-favorited {
  color: #f0a020;
}

.map-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.map-container {
  height: 300px;
  position: relative;
}

.map {
  width: 100%;
  height: 100%;
  border-radius: 4px;
  min-height: 300px;
}

.routes-card {
  margin-top: 20px;
}

.routes-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
}

.route-item {
  cursor: pointer;
  transition: transform 0.2s;
}

.route-item:hover {
  transform: translateY(-2px);
}

.route-item-content {
  display: flex;
  align-items: center;
  gap: 12px;
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
  flex-shrink: 0;
}

.route-info {
  flex: 1;
  min-width: 0;
}

.route-name {
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.route-type {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

@media (max-width: 768px) {
  .routes-list {
    grid-template-columns: 1fr;
  }
}
</style>
