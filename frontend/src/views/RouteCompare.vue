<template>
  <div class="route-compare">
    <!-- 标题 -->
    <div class="search-section">
      <div class="section-title">{{ $t('compare.title') }}</div>
      <div class="search-card">
        <div class="slots-row">
          <div v-for="(slot, idx) in slots" :key="idx" class="search-slot">
            <div class="slot-label">
              {{ $t('compare.routeN', { n: idx + 1 }) }}
              <el-button
                v-if="slots.length > 2"
                link type="danger" :icon="Close" size="small"
                style="margin-left:4px"
                @click="removeSlot(idx)"
              />
            </div>
            <!-- 运营机构筛选 -->
            <el-select
              v-model="slot.agencyId"
              clearable
              :placeholder="$t('compare.filterByAgency')"
              :loading="agenciesLoading"
              style="width:100%;margin-bottom:8px"
              @change="() => { slot.routeId = ''; clearSlotData(idx) }"
            >
              <el-option
                v-for="a in agencies"
                :key="a.agency_id"
                :label="a.agency_name"
                :value="a.agency_id"
              />
            </el-select>
            <!-- 线路选择 -->
            <el-select
              v-model="slot.routeId"
              filterable
              clearable
              :placeholder="$t('compare.selectRoute')"
              :loading="routesLoading"
              style="width:100%"
              @change="(val) => onRouteChange(val, idx)"
            >
              <el-option
                v-for="r in filteredRoutes(slot.agencyId)"
                :key="r.route_id"
                :label="(r.route_short_name || r.route_id) + (r.route_long_name ? ' - ' + r.route_long_name : '')"
                :value="r.route_id"
              >
                <span v-if="r.route_color" class="route-dot" :style="{ background: '#' + r.route_color }"></span>
                <span style="font-weight:600">{{ r.route_short_name || r.route_id }}</span>
                <span style="color:#999;font-size:12px;margin-left:6px">{{ r.route_long_name }}</span>
              </el-option>
            </el-select>
          </div>

          <div v-if="slots.length < 3" class="add-slot">
            <el-button :icon="Plus" @click="addSlot">{{ $t('compare.addRoute') }}</el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 对比结果 -->
    <div v-if="hasAnyData" class="compare-section">

      <!-- 基本信息 -->
      <div class="compare-block">
        <div class="compare-block-title">{{ $t('compare.basicInfo') }}</div>
        <div class="compare-grid" :style="gridStyle">
          <div v-for="(slot, idx) in slots" :key="idx" class="compare-col">
            <div v-if="slot.loading" class="col-loading">
              <el-icon class="spinning"><Loading /></el-icon>
            </div>
            <template v-else-if="slot.data">
              <div class="route-name-row">
                <span
                  class="route-badge"
                  :style="slot.data.route_color
                    ? { background: '#' + slot.data.route_color, color: '#fff' }
                    : { background: '#409eff', color: '#fff' }"
                >{{ slot.data.route_short_name || slot.data.route_id }}</span>
                <span class="route-long-name">{{ slot.data.route_long_name }}</span>
              </div>
              <div class="info-rows">
                <div class="info-row">
                  <span class="info-key">{{ $t('compare.agency') }}</span>
                  <span class="info-val">{{ slot.data.agency_id || '—' }}</span>
                </div>
                <div class="info-row">
                  <span class="info-key">{{ $t('compare.routeType') }}</span>
                  <span class="info-val">{{ routeTypeLabel(slot.data.route_type) }}</span>
                </div>
                <div class="info-row">
                  <span class="info-key">{{ $t('compare.directionCount') }}</span>
                  <span class="info-val">{{ slot.directions.length }}</span>
                </div>
                <div class="info-row">
                  <span class="info-key">{{ $t('compare.stopCount') }}</span>
                  <span class="info-val">
                    <el-tag type="primary" size="small">{{ slot.stops.length }} {{ $t('compare.stopsUnit') }}</el-tag>
                  </span>
                </div>
                <div v-if="commonStopIds.size > 0" class="info-row">
                  <span class="info-key">{{ $t('compare.commonStops') }}</span>
                  <span class="info-val">
                    <el-tag type="success" size="small">{{ commonStopIds.size }} {{ $t('compare.stopsUnit') }}</el-tag>
                  </span>
                </div>
              </div>
            </template>
            <div v-else class="col-empty">
              <el-icon :size="32" color="#dcdfe6"><Guide /></el-icon>
              <p>{{ $t('compare.selectRoute') }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- 准点率对比 -->
      <div class="compare-block">
        <div class="compare-block-title">
          {{ $t('compare.punctualityCompare') }}
          <span style="font-size:12px;color:#909399;font-weight:400;margin-left:8px">{{ $t('compare.last30Days') }}</span>
        </div>
        <div class="compare-grid" :style="gridStyle">
          <div v-for="(slot, idx) in slots" :key="idx" class="compare-col">
            <div v-if="slot.loading" class="col-loading">
              <el-icon class="spinning"><Loading /></el-icon>
            </div>
            <template v-else-if="slot.data">
              <template v-if="slot.punctuality">
                <div class="punctuality-rate">
                  <el-progress
                    type="circle"
                    :percentage="Math.min(100, Math.max(0, Math.round(Number(slot.punctuality.avg_punctuality_rate) || 0)))"
                    :color="rateColor(slot.punctuality.avg_punctuality_rate)"
                    :width="100"
                    :stroke-width="8"
                  />
                  <span class="rate-label">{{ $t('compare.punctualityRate') }}</span>
                </div>
                <div class="info-rows" style="margin-top:12px">
                  <div class="info-row">
                    <span class="info-key">{{ $t('compare.totalTrips') }}</span>
                    <span class="info-val">{{ slot.punctuality.total_trips?.toLocaleString() || '—' }}</span>
                  </div>
                  <div class="info-row">
                    <span class="info-key">{{ $t('compare.onTimeTrips') }}</span>
                    <span class="info-val" style="color:#67c23a">{{ slot.punctuality.on_time_trips?.toLocaleString() || '—' }}</span>
                  </div>
                  <div class="info-row">
                    <span class="info-key">{{ $t('compare.lateTrips') }}</span>
                    <span class="info-val" style="color:#e6a23c">{{ slot.punctuality.late_trips?.toLocaleString() || '—' }}</span>
                  </div>
                  <div class="info-row">
                    <span class="info-key">{{ $t('compare.veryLateTrips') }}</span>
                    <span class="info-val" style="color:#f56c6c">{{ slot.punctuality.very_late_trips?.toLocaleString() || '—' }}</span>
                  </div>
                  <div class="info-row">
                    <span class="info-key">{{ $t('compare.avgDelay') }}</span>
                    <span class="info-val">
                      <el-tag
                        :type="slot.punctuality.avg_delay_minutes > 5 ? 'danger' : slot.punctuality.avg_delay_minutes > 2 ? 'warning' : 'success'"
                        size="small"
                      >{{ (slot.punctuality.avg_delay_minutes || 0).toFixed(1) }} {{ $t('common.minutes') }}</el-tag>
                    </span>
                  </div>
                  <div class="info-row">
                    <span class="info-key">{{ $t('compare.maxDelay') }}</span>
                    <span class="info-val">{{ (slot.punctuality.max_delay_minutes || 0).toFixed(1) }} {{ $t('common.minutes') }}</span>
                  </div>
                </div>
              </template>
              <div v-else class="col-empty" style="height:120px">
                <el-icon :size="24" color="#dcdfe6"><Warning /></el-icon>
                <p>{{ $t('compare.noPunctualityData') }}</p>
              </div>
            </template>
            <div v-else class="col-empty" style="height:120px">
              <p>—</p>
            </div>
          </div>
        </div>
      </div>

      <!-- 站点列表对比 -->
      <div v-if="hasStopsData" class="compare-block">
        <div class="compare-block-title">
          {{ $t('compare.stopList') }}
          <span v-if="commonStopIds.size > 0" class="common-hint">
            <el-icon color="#67c23a"><CircleCheck /></el-icon>
            {{ $t('compare.commonStopHint') }}
          </span>
        </div>
        <div class="compare-grid" :style="gridStyle">
          <div v-for="(slot, idx) in slots" :key="idx" class="compare-col stops-col">
            <template v-if="slot.stops.length > 0">
              <div
                v-for="stop in slot.stops"
                :key="stop.stop_id"
                class="stop-item"
                :class="{ 'stop-common': commonStopIds.has(stop.stop_id) }"
              >
                <span class="stop-seq">{{ stop.min_sequence }}</span>
                <span class="stop-name">{{ stop.stop_name }}</span>
              </div>
            </template>
            <div v-else-if="!slot.data" class="col-empty"><p>—</p></div>
          </div>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else class="empty-state">
      <el-icon :size="64" color="#dcdfe6"><DataAnalysis /></el-icon>
      <p>{{ $t('compare.selectAtLeastOne') }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRegionStore } from '@/stores/regionStore'
import { getRoutes, getRouteById, getRouteStops, getRouteDirections } from '@/api/routes'
import { getAgencies } from '@/api/common'
import { getRoutePunctuality } from '@/api/punctuality'
import { Guide, Plus, Close, Loading, CircleCheck, DataAnalysis, Warning } from '@element-plus/icons-vue'

const regionStore = useRegionStore()
const { t } = useI18n()

// 运营机构
const agencies = ref([])
const agenciesLoading = ref(false)

// 全部线路
const allRoutes = ref([])
const routesLoading = ref(false)

// 按机构过滤线路
const filteredRoutes = (agencyId) => {
  if (!agencyId) return allRoutes.value
  return allRoutes.value.filter(r => r.agency_id === agencyId)
}

// 每个对比槽
const makeSlot = () => ({
  agencyId: '',
  routeId: '',
  loading: false,
  data: null,
  stops: [],
  directions: [],
  punctuality: null,
})
const slots = ref([makeSlot(), makeSlot()])

const addSlot = () => { if (slots.value.length < 3) slots.value.push(makeSlot()) }
const removeSlot = (idx) => { slots.value.splice(idx, 1) }

const clearSlotData = (idx) => {
  const s = slots.value[idx]
  s.data = null; s.stops = []; s.directions = []; s.punctuality = null
}

// 加载运营机构
const loadAgencies = async () => {
  agenciesLoading.value = true
  try {
    const data = await getAgencies()
    agencies.value = Array.isArray(data) ? data : []
  } catch { /* ignore */ } finally {
    agenciesLoading.value = false
  }
}

// 加载全量线路
const loadRoutes = async () => {
  routesLoading.value = true
  allRoutes.value = []
  try {
    const data = await getRoutes({ page_size: 500 })
    allRoutes.value = data?.routes || []
  } catch { /* ignore */ } finally {
    routesLoading.value = false
  }
}

// 选择线路后加载详情 + 准点率
const onRouteChange = async (routeId, idx) => {
  clearSlotData(idx)
  if (!routeId) return

  slots.value[idx].loading = true
  try {
    const [detail, stops, directions, punctData] = await Promise.all([
      getRouteById(routeId).catch(() => null),
      getRouteStops(routeId).catch(() => []),
      getRouteDirections(routeId).catch(() => []),
      // 不传 route_id，拿全量聚合数据（传 route_id 时后端返回按日期分组的明细行）
      getRoutePunctuality({ days: 30, limit: 1000 }).catch(() => null),
    ])
    const slot = slots.value[idx]
    slot.data = detail
    slot.stops = stops || []
    slot.directions = directions || []
    // 在聚合列表中找到当前线路
    const pList = Array.isArray(punctData) ? punctData : []
    const pRow = pList.find(r => r.route_id === routeId)
    slot.punctuality = pRow ? {
      avg_punctuality_rate: Math.min(100, Math.max(0, parseFloat(pRow.avg_punctuality_rate) || 0)),
      total_trips: parseInt(pRow.total_trips) || 0,
      on_time_trips: parseInt(pRow.on_time_trips) || 0,
      late_trips: parseInt(pRow.late_trips) || 0,
      very_late_trips: parseInt(pRow.very_late_trips) || 0,
      avg_delay_minutes: parseFloat(pRow.avg_delay_minutes) || 0,
      max_delay_minutes: parseFloat(pRow.max_delay_minutes) || 0,
    } : null
  } finally {
    slots.value[idx].loading = false
  }
}

// 地区切换时重置
watch(() => regionStore.selectedRegion, () => {
  slots.value.forEach((s, i) => { s.agencyId = ''; s.routeId = ''; clearSlotData(i) })
  loadAgencies()
  loadRoutes()
})

onMounted(() => {
  loadAgencies()
  loadRoutes()
})

// 共同站点
const commonStopIds = computed(() => {
  const loaded = slots.value.filter(s => s.stops.length > 0)
  if (loaded.length < 2) return new Set()
  const sets = loaded.map(s => new Set(s.stops.map(st => st.stop_id)))
  let inter = sets[0]
  for (let i = 1; i < sets.length; i++) inter = new Set([...inter].filter(id => sets[i].has(id)))
  return inter
})

const hasAnyData = computed(() => slots.value.some(s => s.data || s.loading))
const hasStopsData = computed(() => slots.value.some(s => s.stops.length > 0))
const gridStyle = computed(() => ({ gridTemplateColumns: `repeat(${slots.value.length}, 1fr)` }))

const rateColor = (rate) => {
  if (rate >= 90) return '#67c23a'
  if (rate >= 75) return '#e6a23c'
  return '#f56c6c'
}

const routeTypeNames = computed(() => ({
  0: t('compareRouteType.0'),
  1: t('compareRouteType.1'),
  2: t('compareRouteType.2'),
  3: t('compareRouteType.3'),
  4: t('compareRouteType.4'),
  5: t('compareRouteType.5'),
  6: t('compareRouteType.6'),
  7: t('compareRouteType.7'),
}))
const routeTypeLabel = (type) => routeTypeNames.value[type] || `${type}`
</script>

<style scoped>
.route-compare {
  min-height: 100vh;
  background: #f5f7fa;
  padding: 32px 20px;
}

.section-title {
  font-size: 20px;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 20px;
  padding-left: 12px;
  border-left: 4px solid #409eff;
}

.search-section {
  max-width: 1200px;
  margin: 0 auto 32px;
}

.search-card {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.slots-row {
  display: flex;
  gap: 16px;
  align-items: flex-end;
  flex-wrap: wrap;
}

.search-slot {
  flex: 1;
  min-width: 200px;
}

.slot-label {
  font-size: 13px;
  color: #606266;
  font-weight: 600;
  margin-bottom: 6px;
  display: flex;
  align-items: center;
}

.add-slot {
  display: flex;
  align-items: flex-end;
  padding-bottom: 0;
}

.route-dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin-right: 6px;
  vertical-align: middle;
  flex-shrink: 0;
}

.compare-section {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.compare-block {
  background: #fff;
  border-radius: 12px;
  padding: 20px 24px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.compare-block-title {
  font-size: 15px;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.common-hint {
  font-size: 13px;
  font-weight: 400;
  color: #67c23a;
  display: flex;
  align-items: center;
  gap: 4px;
}

.compare-grid {
  display: grid;
  gap: 16px;
}

.compare-col {
  border: 1px solid #f0f2f5;
  border-radius: 8px;
  padding: 16px;
  min-height: 80px;
}

.col-loading {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 80px;
}

.col-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 60px;
  color: #c0c4cc;
  font-size: 13px;
  gap: 6px;
}

.route-name-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.route-badge {
  padding: 2px 10px;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 600;
  white-space: nowrap;
}

.route-long-name {
  font-size: 13px;
  color: #606266;
}

.info-rows {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
}

.info-key { color: #909399; }
.info-val { color: #2c3e50; font-weight: 500; }

.punctuality-rate {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
}

.rate-label {
  font-size: 12px;
  color: #909399;
}

.stops-col {
  max-height: 400px;
  overflow-y: auto;
  padding: 8px;
}

.stop-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 5px 8px;
  border-radius: 4px;
  font-size: 13px;
  color: #606266;
}

.stop-item.stop-common {
  background: #f0faf0;
  color: #2c3e50;
  font-weight: 500;
}

.stop-seq {
  font-size: 11px;
  color: #c0c4cc;
  min-width: 24px;
  text-align: right;
}

.stop-name { flex: 1; }

.stop-item.stop-common .stop-name::before {
  content: '● ';
  color: #67c23a;
  font-size: 10px;
}

.empty-state {
  max-width: 1200px;
  margin: 60px auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  color: #c0c4cc;
  font-size: 15px;
}

.spinning {
  animation: spin 1s linear infinite;
  font-size: 28px;
  color: #409eff;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@media (max-width: 768px) {
  .route-compare { padding: 20px 12px; }
  .slots-row { flex-direction: column; }
  .search-slot { min-width: unset; width: 100%; }
}
</style>
