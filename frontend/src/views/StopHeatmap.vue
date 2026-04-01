<template>
  <div class="stop-heatmap-page">
    <!-- 筛选栏 -->
    <div class="heatmap-controls">
      <div class="control-section">
        <el-select v-model="period" :placeholder="$t('heatmap.period')" style="width: 140px" @change="loadData">
          <el-option :label="$t('heatmap.allDay')" value="all" />
          <el-option :label="$t('heatmap.morning')" value="morning" />
          <el-option :label="$t('heatmap.evening')" value="evening" />
        </el-select>
        <el-select v-model="routeType" :placeholder="$t('heatmap.allTypes')" clearable style="width: 140px" @change="loadData">
          <el-option :label="$t('heatmap.tram')" :value="0" />
          <el-option :label="$t('heatmap.subway')" :value="1" />
          <el-option :label="$t('heatmap.rail')" :value="2" />
          <el-option :label="$t('heatmap.bus')" :value="3" />
          <el-option :label="$t('heatmap.ferry')" :value="4" />
          <el-option :label="$t('heatmap.cableCar')" :value="5" />
        </el-select>
        <el-button :icon="Refresh" :loading="loading" @click="loadData" size="small">
          {{ $t('heatmap.refresh') }}
        </el-button>
      </div>
      <div class="control-info">
        <el-tag v-if="stopCount > 0" type="info" size="small">
          {{ $t('heatmap.stopCount', { n: stopCount }) }}
        </el-tag>
        <el-tag v-if="maxFreq > 0" type="success" size="small">
          {{ $t('heatmap.maxFreq', { n: maxFreq }) }}
        </el-tag>
      </div>
    </div>

    <!-- 地图容器 -->
    <div class="map-container">
      <div id="heatmap" class="map-element"></div>
      <div v-if="loading" class="loading-overlay">
        <el-icon class="spinning" :size="32"><Loading /></el-icon>
        <p>{{ $t('heatmap.loading') }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRegionStore } from '@/stores/regionStore.js'
import { Refresh, Loading } from '@element-plus/icons-vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import 'leaflet.heat'
import apiClient from '@/api/index.js'

const { t } = useI18n()
const regionStore = useRegionStore()

const period = ref('all')
const routeType = ref('')
const loading = ref(false)
const stopCount = ref(0)
const maxFreq = ref(0)

let map = null
let heatLayer = null

// 各地区默认中心点
const REGION_CENTERS = {
  sf: [37.7749, -122.4194],
  nyc: [40.7128, -74.0060],
  sydney: [-33.8688, 151.2093],
}

const initMap = () => {
  const center = REGION_CENTERS[regionStore.selectedRegion] || REGION_CENTERS.sf
  map = L.map('heatmap').setView(center, 12)
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors',
    maxZoom: 18,
  }).addTo(map)
}

const loadData = async () => {
  if (!map) return
  loading.value = true
  try {
    const params = { period: period.value }
    if (routeType.value !== '') params.route_type = routeType.value
    const data = await apiClient.get('/stops/frequency', { params })
    const list = data || []

    stopCount.value = list.length
    maxFreq.value = list.length > 0 ? Math.max(...list.map(s => s.frequency)) : 0

    // 移除旧热力图层
    if (heatLayer) {
      map.removeLayer(heatLayer)
      heatLayer = null
    }

    if (list.length === 0) return

    // 构建热力图数据点 [lat, lon, intensity]
    const points = list
      .filter(s => s.stop_lat && s.stop_lon)
      .map(s => [s.stop_lat, s.stop_lon, s.frequency])

    heatLayer = L.heatLayer(points, {
      radius: 20,
      blur: 15,
      maxZoom: 16,
      max: maxFreq.value,
      gradient: { 0.2: '#2196f3', 0.4: '#4caf50', 0.6: '#ffeb3b', 0.8: '#ff9800', 1.0: '#f44336' },
    }).addTo(map)

    // 自动调整视野到数据范围
    if (points.length > 0) {
      const bounds = L.latLngBounds(points.map(p => [p[0], p[1]]))
      map.fitBounds(bounds, { padding: [30, 30] })
    }
  } catch (e) {
    console.error('加载站点频率数据失败:', e)
  } finally {
    loading.value = false
  }
}

// 切换地区时重新加载
watch(() => regionStore.selectedRegion, () => {
  const center = REGION_CENTERS[regionStore.selectedRegion] || REGION_CENTERS.sf
  if (map) map.setView(center, 12)
  loadData()
})

onMounted(() => {
  initMap()
  loadData()
})

onUnmounted(() => {
  if (map) {
    map.remove()
    map = null
  }
})
</script>

<style scoped>
.stop-heatmap-page {
  height: calc(100vh - 120px);
  display: flex;
  flex-direction: column;
  background: var(--el-bg-color-page);
}

.heatmap-controls {
  background: var(--el-bg-color);
  padding: 12px 20px;
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
  align-items: center;
  flex-wrap: wrap;
}

.control-info {
  display: flex;
  gap: 8px;
}

.map-container {
  flex: 1;
  position: relative;
  z-index: 1;
}

.map-element {
  width: 100%;
  height: 100%;
}

.loading-overlay {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: rgba(255, 255, 255, 0.9);
  padding: 30px 50px;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  text-align: center;
  z-index: 2000;
}

.loading-overlay p {
  margin-top: 12px;
  color: var(--el-text-color-secondary);
  font-size: 14px;
}

.spinning {
  animation: spin 1s linear infinite;
  color: #409eff;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
