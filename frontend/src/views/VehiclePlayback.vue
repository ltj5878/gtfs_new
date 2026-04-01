<template>
  <div class="vehicle-playback-page">
    <!-- 控制栏 -->
    <div class="playback-controls">
      <div class="control-section">
        <el-date-picker
          v-model="selectedDate"
          type="date"
          :placeholder="$t('playback.selectDate')"
          value-format="YYYY-MM-DD"
          :disabled-date="disabledDate"
          size="small"
          style="width: 160px"
          @change="handleDateChange"
        />
        <el-button
          :icon="playing ? VideoPause : VideoPlay"
          :type="playing ? 'danger' : 'primary'"
          size="small"
          :disabled="!dataLoaded"
          @click="togglePlay"
        >
          {{ playing ? $t('playback.pause') : $t('playback.play') }}
        </el-button>
        <el-select v-model="speed" size="small" style="width: 80px">
          <el-option label="1x" :value="1" />
          <el-option label="2x" :value="2" />
          <el-option label="4x" :value="4" />
          <el-option label="8x" :value="8" />
        </el-select>
        <el-button
          :icon="Refresh"
          size="small"
          :loading="syncing"
          @click="syncData"
        >
          {{ $t('playback.syncData') }}
        </el-button>
      </div>
      <div class="control-info">
        <span class="time-display" v-if="dataLoaded">{{ currentTimeStr }}</span>
        <el-tag v-if="visibleCount > 0" type="success" size="small">
          {{ $t('playback.vehicleCount', { n: visibleCount }) }}
        </el-tag>
        <el-tag v-if="totalPoints > 0" type="info" size="small">
          {{ $t('playback.totalPoints', { n: totalPoints }) }}
        </el-tag>
      </div>
    </div>

    <!-- 地图 -->
    <div class="map-container">
      <div id="playback-map" class="map-element"></div>
      <div v-if="loading" class="loading-overlay">
        <el-icon class="spinning" :size="32"><Loading /></el-icon>
        <p>{{ $t('playback.loading') }}</p>
      </div>
    </div>

    <!-- 时间轴 -->
    <div class="timeline-bar" v-if="dataLoaded">
      <span class="timeline-label">{{ minTimeStr }}</span>
      <el-slider
        v-model="currentMinute"
        :min="minMinute"
        :max="maxMinute"
        :step="1"
        :show-tooltip="false"
        style="flex: 1; margin: 0 12px"
        @input="handleSliderInput"
      />
      <span class="timeline-label">{{ maxTimeStr }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { useRegionStore } from '@/stores/regionStore.js'
import { VideoPlay, VideoPause, Loading, Refresh } from '@element-plus/icons-vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import apiClient from '@/api/index.js'

const { t } = useI18n()
const regionStore = useRegionStore()

const REGION_CENTERS = {
  sf: [37.7749, -122.4194],
  nyc: [40.7128, -74.0060],
  sydney: [-33.8688, 151.2093],
}

// 线路颜色池
const COLORS = ['#409eff', '#67c23a', '#e6a23c', '#f56c6c', '#9c27b0', '#00bcd4', '#ff5722', '#795548', '#607d8b', '#3f51b5']

const selectedDate = ref('')
const availableDates = ref([])
const loading = ref(false)
const syncing = ref(false)
const playing = ref(false)
const speed = ref(1)
const currentMinute = ref(0)
const visibleCount = ref(0)

// 所有位置数据
const allPoints = ref([])
const totalPoints = computed(() => allPoints.value.length)
const dataLoaded = computed(() => allPoints.value.length > 0)

// 时间范围（分钟）
const minMinute = ref(0)
const maxMinute = ref(1440)

const minuteToStr = (m) => {
  const h = Math.floor(m / 60)
  const min = m % 60
  return `${String(h).padStart(2, '0')}:${String(min).padStart(2, '0')}`
}

const currentTimeStr = computed(() => minuteToStr(currentMinute.value))
const minTimeStr = computed(() => minuteToStr(minMinute.value))
const maxTimeStr = computed(() => minuteToStr(maxMinute.value))

let map = null
let markersLayer = null
let playTimer = null
let routeColorMap = {}

const disabledDate = (date) => {
  const ds = date.toISOString().slice(0, 10)
  return !availableDates.value.includes(ds)
}

const initMap = () => {
  const center = REGION_CENTERS[regionStore.selectedRegion] || REGION_CENTERS.sf
  map = L.map('playback-map').setView(center, 12)
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors',
    maxZoom: 18,
  }).addTo(map)
  markersLayer = L.layerGroup().addTo(map)
}

const loadDates = async () => {
  try {
    availableDates.value = await apiClient.get('/realtime/vehicles/dates') || []
    if (availableDates.value.length > 0 && !selectedDate.value) {
      selectedDate.value = availableDates.value[0]
      await loadData()
    }
  } catch { /* 静默 */ }
}

const loadData = async () => {
  if (!selectedDate.value) return
  loading.value = true
  stopPlay()
  try {
    const data = await apiClient.get('/realtime/vehicles/history', {
      params: { date: selectedDate.value }
    })
    allPoints.value = (data || []).map(p => ({
      ...p,
      minute: tsToMinute(p.position_timestamp),
    }))

    // 计算时间范围
    if (allPoints.value.length > 0) {
      const minutes = allPoints.value.map(p => p.minute)
      minMinute.value = Math.min(...minutes)
      maxMinute.value = Math.max(...minutes)
      currentMinute.value = minMinute.value
    }

    // 构建线路颜色映射
    routeColorMap = {}
    const routeIds = [...new Set(allPoints.value.map(p => p.route_id).filter(Boolean))]
    routeIds.forEach((id, i) => { routeColorMap[id] = COLORS[i % COLORS.length] })

    renderFrame()
  } catch {
    allPoints.value = []
  } finally {
    loading.value = false
  }
}

const tsToMinute = (ts) => {
  if (!ts) return 0
  const d = new Date(ts)
  return d.getHours() * 60 + d.getMinutes()
}

const renderFrame = () => {
  if (!markersLayer) return
  markersLayer.clearLayers()

  const cur = currentMinute.value
  // 显示当前时间 ±2 分钟内的车辆（取每辆车最新位置）
  const vehicleLatest = {}
  for (const p of allPoints.value) {
    if (p.minute >= cur - 2 && p.minute <= cur + 2) {
      if (!vehicleLatest[p.vehicle_id] || p.minute > vehicleLatest[p.vehicle_id].minute) {
        vehicleLatest[p.vehicle_id] = p
      }
    }
  }

  const vehicles = Object.values(vehicleLatest)
  visibleCount.value = vehicles.length

  for (const v of vehicles) {
    const color = routeColorMap[v.route_id] || '#409eff'
    const icon = L.divIcon({
      className: 'vehicle-marker',
      html: `<div class="vehicle-dot" style="background:${color};transform:rotate(${v.bearing || 0}deg)"></div>`,
      iconSize: [14, 14],
      iconAnchor: [7, 7],
    })
    const marker = L.marker([v.latitude, v.longitude], { icon })
      .bindPopup(`<b>${v.vehicle_id}</b><br/>Route: ${v.route_id || '—'}<br/>Speed: ${(v.speed || 0).toFixed(1)} km/h`)
    markersLayer.addLayer(marker)
  }
}

const togglePlay = () => {
  if (playing.value) {
    stopPlay()
  } else {
    startPlay()
  }
}

const startPlay = () => {
  if (currentMinute.value >= maxMinute.value) {
    currentMinute.value = minMinute.value
  }
  playing.value = true
  playTimer = setInterval(() => {
    currentMinute.value += 1
    renderFrame()
    if (currentMinute.value >= maxMinute.value) {
      stopPlay()
    }
  }, 1000 / speed.value)
}

const stopPlay = () => {
  playing.value = false
  if (playTimer) {
    clearInterval(playTimer)
    playTimer = null
  }
}

const handleSliderInput = () => {
  renderFrame()
}

const handleDateChange = () => {
  loadData()
}

const syncData = async () => {
  syncing.value = true
  try {
    const res = await apiClient.post('/realtime/vehicles/sync')
    ElMessage.success(t('playback.syncSuccess', { n: res.total_points || 0 }))
    // 重新加载日期列表和数据
    await loadDates()
  } catch (e) {
    ElMessage.error(t('playback.syncFailed'))
  } finally {
    syncing.value = false
  }
}

// 倍速变化时重启播放
watch(speed, () => {
  if (playing.value) {
    stopPlay()
    startPlay()
  }
})

watch(() => regionStore.selectedRegion, () => {
  const center = REGION_CENTERS[regionStore.selectedRegion] || REGION_CENTERS.sf
  if (map) map.setView(center, 12)
  selectedDate.value = ''
  allPoints.value = []
  loadDates()
})

onMounted(() => {
  initMap()
  loadDates()
})

onUnmounted(() => {
  stopPlay()
  if (map) { map.remove(); map = null }
})
</script>

<style scoped>
.vehicle-playback-page {
  height: calc(100vh - 120px);
  display: flex;
  flex-direction: column;
  background: var(--el-bg-color-page);
}

.playback-controls {
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
  gap: 10px;
  align-items: center;
}

.control-info {
  display: flex;
  gap: 10px;
  align-items: center;
}

.time-display {
  font-size: 20px;
  font-weight: 700;
  font-family: monospace;
  color: var(--el-text-color-primary);
  min-width: 60px;
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
}

.spinning {
  animation: spin 1s linear infinite;
  color: #409eff;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.timeline-bar {
  background: var(--el-bg-color);
  padding: 10px 20px;
  display: flex;
  align-items: center;
  gap: 8px;
  border-top: 1px solid var(--el-border-color-lighter);
  z-index: 1000;
}

.timeline-label {
  font-size: 12px;
  font-family: monospace;
  color: var(--el-text-color-secondary);
  min-width: 40px;
}
</style>

<style>
/* 车辆标记样式（非 scoped，因为 Leaflet 动态创建 DOM） */
.vehicle-dot {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 2px solid #fff;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.3);
}
</style>
