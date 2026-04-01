<template>
  <div class="reachability-page">
    <div class="page-header">
      <div>
        <p class="eyebrow">{{ $t('analysis.reachability.eyebrow') }}</p>
        <h1 class="page-title">{{ $t('analysis.reachability.title') }}</h1>
        <p class="page-subtitle">{{ $t('analysis.reachability.subtitle') }}</p>
      </div>

      <div class="summary-strip">
        <div class="summary-item">
          <span class="summary-label">{{ $t('analysis.reachability.reachableCount') }}</span>
          <strong class="summary-value">{{ reachableCount }}</strong>
        </div>
        <div class="summary-item">
          <span class="summary-label">{{ $t('analysis.reachability.maxMinutes') }}</span>
          <strong class="summary-value">{{ form.maxMinutes }}</strong>
        </div>
      </div>
    </div>

    <div class="page-workspace">
      <aside class="control-panel">
        <section class="panel-section">
          <div class="section-heading">{{ $t('analysis.reachability.controls') }}</div>

          <div class="field-block">
            <label class="field-label">{{ $t('analysis.reachability.selectAgency') }}</label>
            <el-select
              v-model="form.agencyId"
              clearable
              filterable
              :loading="loadingAgencies"
              :placeholder="$t('stopList.agencyPlaceholder')"
              style="width: 100%"
              @change="handleAgencyChange"
            >
              <el-option
                :label="$t('analysis.reachability.allAgencies')"
                value=""
              />
              <el-option
                v-for="agency in agencies"
                :key="agency.agency_id"
                :label="agency.agency_name"
                :value="agency.agency_id"
              />
            </el-select>
          </div>

          <div class="field-block">
            <label class="field-label">{{ $t('analysis.reachability.selectStop') }}</label>
            <el-select
              v-model="form.stopId"
              filterable
              remote
              clearable
              reserve-keyword
              :placeholder="$t('analysis.reachability.selectStopPlaceholder')"
              :remote-method="handleStopSearch"
              :loading="searchingStops"
              popper-class="reachability-stop-select-dropdown"
              style="width: 100%"
              @change="handleStopChange"
              @visible-change="handleStopDropdown"
              @clear="handleStopClear"
            >
              <el-option
                v-for="stop in stopOptions"
                :key="stop.stop_id"
                :label="stop.stop_name"
                :value="stop.stop_id"
              >
                <div class="stop-option">
                  <span>{{ stop.stop_name }}</span>
                  <span class="stop-option-id">{{ stop.stop_id }}</span>
                </div>
              </el-option>
            </el-select>
          </div>

          <div class="field-block">
            <label class="field-label">{{ $t('analysis.reachability.departTime') }}</label>
            <el-time-picker
              v-model="form.depart"
              style="width: 100%"
              format="HH:mm"
              value-format="HH:mm:ss"
              :clearable="false"
              :placeholder="$t('analysis.reachability.departTime')"
            />
          </div>

          <div class="field-block">
            <div class="field-label-row">
              <label class="field-label">{{ $t('analysis.reachability.maxMinutes') }}</label>
              <span class="field-value">{{ form.maxMinutes }} min</span>
            </div>
            <el-slider
              v-model="form.maxMinutes"
              :min="15"
              :max="60"
              :step="15"
              show-stops
              :marks="sliderMarks"
            />
          </div>

          <el-alert
            v-if="isDirty"
            type="warning"
            :closable="false"
            show-icon
            class="param-alert"
            :title="$t('analysis.reachability.paramsChanged')"
          />

          <el-button
            type="primary"
            size="large"
            class="analyze-btn"
            :loading="loading"
            @click="analyzeReachability"
          >
            <el-icon><Search /></el-icon>
            {{ $t('analysis.reachability.analyze') }}
          </el-button>
        </section>

        <section class="panel-section legend-section">
          <div class="section-heading">{{ $t('analysis.reachability.legend') }}</div>
          <div class="legend-list">
            <div
              v-for="item in visibleLegendItems"
              :key="item.limit"
              class="legend-item"
            >
              <span class="legend-swatch" :style="{ backgroundColor: item.color }"></span>
              <span>{{ $t(item.labelKey) }}</span>
            </div>
          </div>
        </section>

        <section class="panel-section">
          <div class="section-heading">{{ $t('analysis.reachability.results') }}</div>

          <div v-if="selectedStopName" class="origin-card">
            <div class="origin-card-label">{{ $t('analysis.reachability.originStop') }}</div>
            <div class="origin-card-name">{{ selectedStopName }}</div>
          </div>

          <div v-if="reachablePreview.length > 0" class="result-list">
            <div
              v-for="stop in reachablePreview"
              :key="stop.stop_id"
              class="result-item"
            >
              <div class="result-item-main">
                <span class="result-dot" :style="{ backgroundColor: getLayerStyle(stop.minutes).color }"></span>
                <div>
                  <div class="result-name">{{ stop.stop_name }}</div>
                  <div class="result-id">{{ stop.stop_id }}</div>
                </div>
              </div>
              <span class="result-minutes">{{ stop.minutes }} min</span>
            </div>
          </div>

          <el-empty
            v-else
            :description="hasSearched ? $t('analysis.reachability.noResult') : $t('analysis.reachability.awaitingAnalysis')"
          />
        </section>
      </aside>

      <section class="map-stage">
        <div class="map-toolbar">
          <div class="toolbar-pill">
            <el-icon><MapLocation /></el-icon>
            <span>{{ selectedStopName || $t('analysis.reachability.mapWaiting') }}</span>
          </div>
          <div class="toolbar-pill">
            <el-icon><Timer /></el-icon>
            <span>{{ form.depart.slice(0, 5) }}</span>
          </div>
          <div class="toolbar-pill">
            <el-icon><Location /></el-icon>
            <span>{{ reachableCount }} {{ $t('common.stops') }}</span>
          </div>
        </div>

        <div ref="mapElement" class="map-canvas"></div>

        <div v-if="loading" class="map-overlay">
          <el-icon class="is-loading" :size="28"><Loading /></el-icon>
          <span>{{ $t('analysis.reachability.loading') }}</span>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { Loading, Location, MapLocation, Search, Timer } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getReachability } from '@/api/analysis'
import { getStops } from '@/api/stops'
import { getAgencies } from '@/api/common'
import { useRegionStore } from '@/stores/regionStore'

const { t } = useI18n()
const regionStore = useRegionStore()

const DEFAULT_CENTER = [37.7749, -122.4194]
const DEFAULT_ZOOM = 12
const STOP_PAGE_SIZE = 100
const STOP_DROPDOWN_BOTTOM_GAP = 24
const LAYER_STYLES = [
  { limit: 15, color: '#4ade80', labelKey: 'analysis.reachability.min15' },
  { limit: 30, color: '#facc15', labelKey: 'analysis.reachability.min30' },
  { limit: 45, color: '#fb923c', labelKey: 'analysis.reachability.min45' },
  { limit: 60, color: '#f87171', labelKey: 'analysis.reachability.min60' }
]

const form = reactive({
  agencyId: '',
  stopId: '',
  depart: '08:00:00',
  maxMinutes: 60
})

const sliderMarks = {
  15: '15',
  30: '30',
  45: '45',
  60: '60'
}

const mapElement = ref(null)
const map = ref(null)
const markerLayer = ref(null)
const polygonLayer = ref(null)

const agencies = ref([])
const loadingAgencies = ref(false)
const stopOptions = ref([])
const selectedStop = ref(null)
const searchingStops = ref(false)
const stopKeyword = ref('')
const stopPage = ref(1)
const stopHasMore = ref(true)
const stopDropdownVisible = ref(false)
const stopDropdownScrollElement = ref(null)
const loading = ref(false)
const hasSearched = ref(false)
const result = ref(null)
const analyzedParams = ref(null)

const reachableCount = computed(() => result.value?.reachable?.length || 0)
const reachablePreview = computed(() => (result.value?.reachable || []).slice(0, 10))
const selectedStopName = computed(() => {
  return result.value?.origin?.stop_name || selectedStop.value?.stop_name || ''
})
const visibleLegendItems = computed(() => {
  return LAYER_STYLES.filter(item => item.limit <= form.maxMinutes)
})
const isDirty = computed(() => {
  if (!analyzedParams.value) {
    return false
  }
  return (
    analyzedParams.value.stopId !== form.stopId ||
    analyzedParams.value.depart !== form.depart ||
    analyzedParams.value.maxMinutes !== form.maxMinutes ||
    analyzedParams.value.region !== regionStore.selectedRegion
  )
})

const isValidCoordinate = (value) => {
  return value !== null && value !== undefined && value !== '' && !Number.isNaN(Number(value))
}

const mergeStopOptions = (stops = []) => {
  const merged = new Map()

  if (selectedStop.value?.stop_id) {
    merged.set(selectedStop.value.stop_id, selectedStop.value)
  }

  stops.forEach(stop => {
    if (stop?.stop_id) {
      merged.set(stop.stop_id, stop)
    }
  })

  stopOptions.value = Array.from(merged.values())
}

const fetchAgencies = async () => {
  loadingAgencies.value = true
  try {
    const data = await getAgencies()
    agencies.value = Array.isArray(data) ? data : []
  } catch (error) {
    console.error('加载运营机构失败:', error)
    agencies.value = []
  } finally {
    loadingAgencies.value = false
  }
}

const fetchStopOptions = async ({ keyword = stopKeyword.value, reset = false } = {}) => {
  if (searchingStops.value) {
    return
  }

  const normalizedKeyword = keyword.trim()
  const page = reset ? 1 : stopPage.value

  if (!reset && !stopHasMore.value) {
    return
  }

  searchingStops.value = true
  try {
    const data = await getStops({
      page,
      page_size: STOP_PAGE_SIZE,
      search: normalizedKeyword || undefined,
      agency_id: form.agencyId || undefined
    })
    const stops = data?.stops || []
    mergeStopOptions(reset ? stops : [...stopOptions.value, ...stops])

    const pagination = data?.pagination || {}
    const currentPage = Number(pagination.page || page)
    const totalPages = Number(pagination.total_pages || 0)
    stopPage.value = currentPage + 1
    stopHasMore.value = totalPages > 0 && currentPage < totalPages
  } catch (error) {
    console.error('加载站点选项失败:', error)
  } finally {
    searchingStops.value = false
  }
}

const handleStopSearch = (query) => {
  stopKeyword.value = query.trim()
  stopPage.value = 1
  stopHasMore.value = true
  fetchStopOptions({ keyword: stopKeyword.value, reset: true })
}

const detachStopDropdownScroll = () => {
  if (stopDropdownScrollElement.value) {
    stopDropdownScrollElement.value.removeEventListener('scroll', handleStopDropdownScroll)
    stopDropdownScrollElement.value = null
  }
}

const attachStopDropdownScroll = async () => {
  detachStopDropdownScroll()
  await nextTick()

  const dropdown = document.querySelector('.reachability-stop-select-dropdown')
  const scrollElement = dropdown?.querySelector('.el-select-dropdown__wrap')
    || dropdown?.querySelector('.el-scrollbar__wrap')

  if (scrollElement) {
    scrollElement.addEventListener('scroll', handleStopDropdownScroll, { passive: true })
    stopDropdownScrollElement.value = scrollElement
  }
}

const handleStopDropdownScroll = (event) => {
  const target = event.target
  if (!target || searchingStops.value || !stopHasMore.value) {
    return
  }

  const reachedBottom = target.scrollTop + target.clientHeight >= target.scrollHeight - STOP_DROPDOWN_BOTTOM_GAP
  if (reachedBottom) {
    fetchStopOptions({ keyword: stopKeyword.value, reset: false })
  }
}

const handleStopDropdown = async (visible) => {
  stopDropdownVisible.value = visible

  if (visible) {
    await attachStopDropdownScroll()
    if (stopOptions.value.length === 0) {
      stopKeyword.value = ''
      stopPage.value = 1
      stopHasMore.value = true
      fetchStopOptions({ keyword: '', reset: true })
    }
    return
  }

  detachStopDropdownScroll()
}

const handleStopChange = (stopId) => {
  selectedStop.value = stopOptions.value.find(stop => stop.stop_id === stopId) || null
}

const clearAnalysisState = async () => {
  result.value = null
  hasSearched.value = false
  analyzedParams.value = null
  clearMapLayers()
  await resetMapView()
}

const handleAgencyChange = async () => {
  form.stopId = ''
  selectedStop.value = null
  stopOptions.value = []
  stopKeyword.value = ''
  stopPage.value = 1
  stopHasMore.value = true
  await clearAnalysisState()

  if (stopDropdownVisible.value) {
    fetchStopOptions({ keyword: '', reset: true })
  }
}

const handleStopClear = () => {
  stopKeyword.value = ''
  stopPage.value = 1
  stopHasMore.value = true
  selectedStop.value = null
  fetchStopOptions({ keyword: '', reset: true })
}

const getLayerStyle = (minutes) => {
  return LAYER_STYLES.find(item => Number(minutes) <= item.limit) || LAYER_STYLES[LAYER_STYLES.length - 1]
}

const buildConvexHull = (points) => {
  const uniquePoints = Array.from(
    new Map(
      points
        .filter(point => isValidCoordinate(point.lat) && isValidCoordinate(point.lon))
        .map(point => {
          const x = Number(point.lon)
          const y = Number(point.lat)
          return [`${x.toFixed(6)},${y.toFixed(6)}`, { x, y }]
        })
    ).values()
  )

  if (uniquePoints.length <= 1) {
    return uniquePoints.map(point => [point.y, point.x])
  }

  uniquePoints.sort((a, b) => (a.x === b.x ? a.y - b.y : a.x - b.x))

  const cross = (origin, a, b) => {
    return ((a.x - origin.x) * (b.y - origin.y)) - ((a.y - origin.y) * (b.x - origin.x))
  }

  const lower = []
  uniquePoints.forEach(point => {
    while (lower.length >= 2 && cross(lower[lower.length - 2], lower[lower.length - 1], point) <= 0) {
      lower.pop()
    }
    lower.push(point)
  })

  const upper = []
  for (let index = uniquePoints.length - 1; index >= 0; index -= 1) {
    const point = uniquePoints[index]
    while (upper.length >= 2 && cross(upper[upper.length - 2], upper[upper.length - 1], point) <= 0) {
      upper.pop()
    }
    upper.push(point)
  }

  const hull = lower.slice(0, -1).concat(upper.slice(0, -1))
  return hull.map(point => [point.y, point.x])
}

const initMap = () => {
  if (map.value || !mapElement.value) {
    return
  }

  map.value = L.map(mapElement.value).setView(DEFAULT_CENTER, DEFAULT_ZOOM)

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors',
    maxZoom: 19
  }).addTo(map.value)

  polygonLayer.value = L.layerGroup().addTo(map.value)
  markerLayer.value = L.layerGroup().addTo(map.value)
}

const resetMapView = async () => {
  await nextTick()
  if (!map.value) {
    return
  }
  map.value.invalidateSize()
  map.value.setView(DEFAULT_CENTER, DEFAULT_ZOOM)
}

const clearMapLayers = () => {
  polygonLayer.value?.clearLayers()
  markerLayer.value?.clearLayers()
}

const renderMap = async () => {
  initMap()
  clearMapLayers()

  if (!map.value) {
    return
  }

  const visibleStops = (result.value?.reachable || []).filter(stop => Number(stop.minutes) <= form.maxMinutes)
  const bounds = []

  LAYER_STYLES
    .filter(item => item.limit <= form.maxMinutes)
    .slice()
    .reverse()
    .forEach(item => {
      const hullPoints = buildConvexHull(
        visibleStops
          .filter(stop => Number(stop.minutes) <= item.limit)
          .map(stop => ({
            lat: stop.stop_lat,
            lon: stop.stop_lon
          }))
      )

      if (hullPoints.length >= 3) {
        L.polygon(hullPoints, {
          color: item.color,
          fillColor: item.color,
          fillOpacity: 0.16,
          weight: 2,
          opacity: 0.8
        })
          .bindTooltip(t(item.labelKey))
          .addTo(polygonLayer.value)
      } else if (hullPoints.length === 2) {
        L.polyline(hullPoints, {
          color: item.color,
          weight: 4,
          opacity: 0.75
        })
          .bindTooltip(t(item.labelKey))
          .addTo(polygonLayer.value)
      } else if (hullPoints.length === 1) {
        L.circle(hullPoints[0], {
          radius: 180,
          color: item.color,
          fillColor: item.color,
          fillOpacity: 0.12,
          weight: 2
        })
          .bindTooltip(t(item.labelKey))
          .addTo(polygonLayer.value)
      }
    })

  visibleStops.forEach(stop => {
    if (!isValidCoordinate(stop.stop_lat) || !isValidCoordinate(stop.stop_lon)) {
      return
    }

    const layerStyle = getLayerStyle(stop.minutes)
    const latLng = [Number(stop.stop_lat), Number(stop.stop_lon)]
    bounds.push(latLng)

    L.circleMarker(latLng, {
      radius: 5,
      color: '#ffffff',
      weight: 1,
      fillColor: layerStyle.color,
      fillOpacity: 0.9,
      opacity: 1
    })
      .bindTooltip(`${stop.stop_name} · ${stop.minutes} min`)
      .addTo(markerLayer.value)
  })

  if (result.value?.origin && isValidCoordinate(result.value.origin.stop_lat) && isValidCoordinate(result.value.origin.stop_lon)) {
    const originLatLng = [Number(result.value.origin.stop_lat), Number(result.value.origin.stop_lon)]
    bounds.push(originLatLng)

    L.circleMarker(originLatLng, {
      radius: 9,
      color: '#1d4ed8',
      weight: 2,
      fillColor: '#60a5fa',
      fillOpacity: 0.95
    })
      .bindTooltip(result.value.origin.stop_name)
      .addTo(markerLayer.value)
  }

  await nextTick()
  map.value.invalidateSize()

  if (bounds.length > 1) {
    map.value.fitBounds(bounds, { padding: [32, 32] })
  } else if (bounds.length === 1) {
    map.value.setView(bounds[0], 14)
  } else {
    map.value.setView(DEFAULT_CENTER, DEFAULT_ZOOM)
  }
}

const analyzeReachability = async () => {
  if (!form.stopId) {
    ElMessage.warning(t('analysis.reachability.selectStopRequired'))
    return
  }

  loading.value = true

  try {
    const data = await getReachability({
      stop_id: form.stopId,
      max_min: form.maxMinutes,
      depart: form.depart
    })

    result.value = data
    hasSearched.value = true
    analyzedParams.value = {
      stopId: form.stopId,
      depart: form.depart,
      maxMinutes: form.maxMinutes,
      region: regionStore.selectedRegion
    }

    if (data?.origin?.stop_id) {
      selectedStop.value = data.origin
      form.stopId = data.origin.stop_id
      mergeStopOptions([data.origin])
    }

    await renderMap()

    if (!data?.reachable?.length) {
      ElMessage.info(t('analysis.reachability.noResult'))
    }
  } catch (error) {
    console.error('站点可达性分析失败:', error)
    result.value = null
    hasSearched.value = true
    clearMapLayers()
    await resetMapView()
    ElMessage.error(error.message || t('common.operationFailed'))
  } finally {
    loading.value = false
  }
}

watch(() => regionStore.selectedRegion, async () => {
  form.agencyId = ''
  form.stopId = ''
  selectedStop.value = null
  stopOptions.value = []
  stopKeyword.value = ''
  stopPage.value = 1
  stopHasMore.value = true
  await clearAnalysisState()
  await fetchAgencies()
  fetchStopOptions({ keyword: '', reset: true })
})

watch(() => form.stopId, (value) => {
  if (!value) {
    selectedStop.value = null
  }
})

onMounted(async () => {
  initMap()
  await resetMapView()
  await fetchAgencies()
  fetchStopOptions({ keyword: '', reset: true })
})

onBeforeUnmount(() => {
  detachStopDropdownScroll()
  if (map.value) {
    map.value.remove()
    map.value = null
  }
})
</script>

<style scoped>
.reachability-page {
  min-height: 100vh;
  padding: 32px 20px 40px;
  background:
    radial-gradient(circle at top left, rgba(96, 165, 250, 0.16), transparent 30%),
    radial-gradient(circle at top right, rgba(74, 222, 128, 0.12), transparent 28%),
    linear-gradient(180deg, rgba(248, 250, 252, 0.92), rgba(241, 245, 249, 0.96));
}

.page-header {
  display: flex;
  justify-content: space-between;
  gap: 24px;
  align-items: flex-end;
  margin-bottom: 24px;
}

.eyebrow {
  margin-bottom: 10px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #2563eb;
}

.page-title {
  font-size: 30px;
  line-height: 1.1;
  color: #0f172a;
}

.page-subtitle {
  max-width: 680px;
  margin-top: 10px;
  color: #475569;
  font-size: 15px;
  line-height: 1.7;
}

.summary-strip {
  display: grid;
  grid-template-columns: repeat(2, minmax(120px, 1fr));
  gap: 12px;
  min-width: 260px;
}

.summary-item {
  padding: 16px 18px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.78);
  backdrop-filter: blur(8px);
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.08);
}

.summary-label {
  display: block;
  font-size: 12px;
  color: #64748b;
  margin-bottom: 6px;
}

.summary-value {
  font-size: 24px;
  color: #0f172a;
}

.page-workspace {
  display: grid;
  grid-template-columns: 340px minmax(0, 1fr);
  gap: 18px;
  align-items: stretch;
}

.control-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.panel-section {
  padding: 20px;
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.86);
  border: 1px solid rgba(148, 163, 184, 0.18);
  box-shadow: 0 16px 40px rgba(15, 23, 42, 0.08);
}

.section-heading {
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #475569;
  margin-bottom: 16px;
}

.field-block + .field-block {
  margin-top: 16px;
}

.field-label-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.field-label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #0f172a;
}

.field-value {
  font-size: 13px;
  color: #2563eb;
}

.param-alert {
  margin-top: 16px;
}

.analyze-btn {
  width: 100%;
  margin-top: 18px;
  height: 44px;
  border-radius: 14px;
}

.legend-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #1e293b;
}

.legend-swatch {
  width: 14px;
  height: 14px;
  border-radius: 999px;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.6);
}

.origin-card {
  margin-bottom: 16px;
  padding: 14px 16px;
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.08), rgba(96, 165, 250, 0.18));
}

.origin-card-label {
  font-size: 12px;
  color: #1d4ed8;
  margin-bottom: 4px;
}

.origin-card-name {
  font-size: 17px;
  font-weight: 700;
  color: #0f172a;
}

.result-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.result-item {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
  padding: 12px 14px;
  border-radius: 14px;
  background: rgba(248, 250, 252, 0.94);
}

.result-item-main {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.result-dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  flex-shrink: 0;
}

.result-name {
  color: #0f172a;
  font-weight: 600;
}

.result-id {
  margin-top: 2px;
  font-size: 12px;
  color: #64748b;
}

.result-minutes {
  font-size: 13px;
  font-weight: 700;
  color: #334155;
  white-space: nowrap;
}

.map-stage {
  position: relative;
  min-height: 720px;
  padding: 18px;
  border-radius: 28px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.94), rgba(248, 250, 252, 0.98));
  border: 1px solid rgba(148, 163, 184, 0.22);
  box-shadow: 0 24px 50px rgba(15, 23, 42, 0.08);
  overflow: hidden;
}

.map-toolbar {
  position: absolute;
  top: 18px;
  left: 18px;
  right: 18px;
  z-index: 500;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.toolbar-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(148, 163, 184, 0.2);
  color: #334155;
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.08);
  backdrop-filter: blur(8px);
}

.map-canvas {
  width: 100%;
  height: 100%;
  min-height: 684px;
  border-radius: 20px;
  border: 1px solid rgba(226, 232, 240, 0.9);
}

.map-overlay {
  position: absolute;
  inset: 0;
  z-index: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  background: rgba(255, 255, 255, 0.58);
  color: #0f172a;
  backdrop-filter: blur(4px);
}

.stop-option {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.stop-option-id {
  font-size: 12px;
  color: #94a3b8;
}

@media (max-width: 1200px) {
  .page-workspace {
    grid-template-columns: 320px minmax(0, 1fr);
  }
}

@media (max-width: 960px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .summary-strip {
    width: 100%;
    min-width: 0;
  }

  .page-workspace {
    grid-template-columns: 1fr;
  }

  .map-stage {
    min-height: 560px;
  }

  .map-canvas {
    min-height: 520px;
  }
}

@media (max-width: 640px) {
  .reachability-page {
    padding: 20px 12px 28px;
  }

  .page-title {
    font-size: 24px;
  }

  .summary-strip {
    grid-template-columns: 1fr;
  }

  .panel-section,
  .map-stage {
    border-radius: 20px;
  }

  .map-stage {
    padding: 14px;
  }

  .map-toolbar {
    top: 14px;
    left: 14px;
    right: 14px;
  }

  .toolbar-pill {
    width: 100%;
    justify-content: center;
  }
}
</style>
