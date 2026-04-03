<template>
  <div class="carbon-page">
    <div class="page-header">
      <h1>{{ $t('carbon.title') }}</h1>
      <div class="header-actions">
        <el-button :icon="Refresh" @click="handleRefresh" :loading="loading" size="small">{{ $t('common.refresh') }}</el-button>
      </div>
    </div>
    <p class="page-subtitle">{{ $t('carbon.subtitle') }}</p>

    <el-row :gutter="16" class="stat-row">
      <el-col :xs="12" :sm="6">
        <div class="stat-card stat-green">
          <div class="stat-icon">🌱</div>
          <div class="stat-value">{{ myStats.total_saved_kg ?? 0 }} kg</div>
          <div class="stat-label">{{ $t('carbon.totalSaved') }}</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card stat-blue">
          <div class="stat-icon">🚌</div>
          <div class="stat-value">{{ myStats.total_trips ?? 0 }}</div>
          <div class="stat-label">{{ $t('carbon.totalTrips') }}</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card stat-teal">
          <div class="stat-icon">🌳</div>
          <div class="stat-value">{{ myStats.trees_equivalent ?? 0 }}</div>
          <div class="stat-label">{{ $t('carbon.treesEquivalent') }}</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card stat-orange">
          <div class="stat-icon">⛽</div>
          <div class="stat-value">{{ myStats.fuel_saved_liters ?? 0 }} L</div>
          <div class="stat-label">{{ $t('carbon.fuelSaved') }}</div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="period-row">
      <el-col :xs="12" :sm="12">
        <el-card>
          <div class="period-stat">
            <span class="period-label">{{ $t('carbon.weekSaved') }}</span>
            <span class="period-value">{{ myStats.week_saved_kg ?? 0 }} kg CO₂</span>
            <span class="period-trips">{{ myStats.week_trips ?? 0 }} {{ $t('carbon.tripsUnit') }}</span>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="12">
        <el-card>
          <div class="period-stat">
            <span class="period-label">{{ $t('carbon.monthSaved') }}</span>
            <span class="period-value">{{ myStats.month_saved_kg ?? 0 }} kg CO₂</span>
            <span class="period-trips">{{ myStats.month_trips ?? 0 }} {{ $t('carbon.tripsUnit') }}</span>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="chart-card" v-if="myStats.daily_trend?.length">
      <template #header><span>{{ $t('carbon.dailyTrend') }}</span></template>
      <div ref="trendRef" class="chart-area"></div>
    </el-card>

    <el-row :gutter="16" class="entry-row">
      <el-col :xs="24" :lg="14">
        <el-card class="query-card">
          <template #header><span>{{ $t('carbon.manualEntry') }}</span></template>
          <el-form label-position="top" class="entry-form">
            <el-form-item :label="$t('carbon.route')">
              <el-select
                v-model="selectedRoute"
                filterable
                :placeholder="$t('carbon.selectRoute')"
                size="small"
                style="width: 100%"
                @change="handleRouteChange"
              >
                <el-option
                  v-for="r in routeList"
                  :key="r.route_id"
                  :label="routeLabel(r)"
                  :value="r.route_id"
                />
              </el-select>
            </el-form-item>

            <div class="entry-grid">
              <el-form-item :label="$t('carbon.tripDate')">
                <el-date-picker
                  v-model="entryForm.trip_date"
                  type="date"
                  value-format="YYYY-MM-DD"
                  format="YYYY-MM-DD"
                  size="small"
                  style="width: 100%"
                />
              </el-form-item>

              <el-form-item :label="$t('carbon.rideCount')">
                <el-input-number
                  v-model="entryForm.ride_count"
                  :min="1"
                  :max="50"
                  :step="1"
                  size="small"
                  style="width: 100%"
                />
              </el-form-item>
            </div>

            <el-form-item :label="$t('carbon.manualDistance')">
              <el-input-number
                v-model="entryForm.distance_km"
                :min="0.5"
                :max="200"
                :step="0.5"
                :precision="1"
                size="small"
                style="width: 100%"
              />
              <div class="form-hint" v-if="routeCarbon">
                {{ $t('carbon.autoDistanceHint') }} {{ routeCarbon.distance_km }} km
              </div>
              <div class="form-hint" v-else>
                {{ $t('carbon.manualDistanceHint') }}
              </div>
            </el-form-item>
          </el-form>

          <div v-if="routeCarbon" class="carbon-compare">
            <div class="compare-row">
              <div class="compare-item transit">
                <div class="compare-label">{{ $t('carbon.transit') }}</div>
                <div class="compare-value">{{ routeCarbon.transit_emission_kg }} kg CO₂</div>
              </div>
              <div class="compare-vs">VS</div>
              <div class="compare-item car">
                <div class="compare-label">{{ $t('carbon.car') }}</div>
                <div class="compare-value">{{ routeCarbon.car_emission_kg }} kg CO₂</div>
              </div>
            </div>
            <div class="saving-bar">
              <div class="saving-text">
                {{ $t('carbon.savingPercent') }}: <b>{{ routeCarbon.saving_percent }}%</b>
                &nbsp;·&nbsp;{{ $t('carbon.distance') }}: {{ routeCarbon.distance_km }} km
              </div>
              <el-progress :percentage="routeCarbon.saving_percent" :color="'#67c23a'" :stroke-width="12" />
            </div>
          </div>

          <div v-if="previewMetrics" class="preview-panel">
            <div class="preview-title">{{ $t('carbon.totalPreview') }}</div>
            <div class="preview-grid">
              <div class="preview-card">
                <div class="preview-label">{{ $t('carbon.singleRide') }}</div>
                <div class="preview-value">{{ previewMetrics.single_distance_km }} km</div>
                <div class="preview-sub">{{ previewMetrics.single_carbon_saved }} kg CO₂</div>
              </div>
              <div class="preview-card highlight">
                <div class="preview-label">{{ $t('carbon.totalEstimate') }}</div>
                <div class="preview-value">{{ previewMetrics.total_distance_km }} km</div>
                <div class="preview-sub">{{ previewMetrics.total_carbon_saved }} kg CO₂</div>
              </div>
            </div>
            <el-button
              type="success"
              @click="handleRecord"
              :loading="recording"
              size="small"
            >
              {{ $t('carbon.recordTrip') }}
            </el-button>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="10">
        <el-card class="records-card">
          <template #header><span>{{ $t('carbon.recentRecords') }}</span></template>
          <el-table :data="recentRecords" stripe size="small" v-loading="recordsLoading" empty-text=" ">
            <el-table-column prop="trip_date" :label="$t('carbon.tripDate')" width="110" />
            <el-table-column :label="$t('carbon.route')" min-width="180">
              <template #default="{ row }">{{ routeLabel(row) }}</template>
            </el-table-column>
            <el-table-column prop="ride_count" :label="$t('carbon.tripCount')" width="80" align="center" />
            <el-table-column :label="$t('carbon.savedKg')" width="110" align="right">
              <template #default="{ row }">{{ Number(row.carbon_saved || 0).toFixed(2) }}</template>
            </el-table-column>
            <el-table-column :label="$t('carbon.actions')" width="90" align="center">
              <template #default="{ row }">
                <el-button
                  link
                  type="danger"
                  size="small"
                  :loading="deletingRecordId === row.id"
                  @click="handleDelete(row)"
                >
                  {{ $t('common.delete') }}
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-if="!recordsLoading && !recentRecords.length" :description="$t('carbon.noRecords')" />
        </el-card>
      </el-col>
    </el-row>

    <el-card>
      <template #header><span>{{ $t('carbon.leaderboard') }}</span></template>
      <el-table :data="leaderboard" stripe size="small">
        <el-table-column type="index" label="#" width="50" />
        <el-table-column prop="username" :label="$t('carbon.user')" />
        <el-table-column prop="trip_count" :label="$t('carbon.tripCount')" width="100" align="center" />
        <el-table-column :label="$t('carbon.savedKg')" width="140" align="right">
          <template #default="{ row }">{{ row.total_saved }} kg</template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useI18n } from 'vue-i18n'
import * as echarts from 'echarts'
import {
  deleteCarbonRecord,
  getCarbonLeaderboard,
  getMyCarbonRecords,
  getMyCarbonStats,
  getRouteCarbonData,
  recordCarbonTrip
} from '@/api/carbon.js'
import { useRegionStore } from '@/stores/regionStore'
import { getRoutes } from '@/api/routes.js'

const { t } = useI18n()
const regionStore = useRegionStore()

const loading = ref(false)
const recordsLoading = ref(false)
const recording = ref(false)
const deletingRecordId = ref(null)
const myStats = ref({})
const leaderboard = ref([])
const routeList = ref([])
const recentRecords = ref([])
const selectedRoute = ref('')
const routeCarbon = ref(null)
const trendRef = ref(null)
const entryForm = reactive({
  trip_date: todayString(),
  ride_count: 1,
  distance_km: null
})
let trendChart = null

const previewMetrics = computed(() => {
  if (!routeCarbon.value) return null

  const baseDistance = Number(routeCarbon.value.distance_km || 0)
  const singleDistance = entryForm.distance_km && entryForm.distance_km > 0
    ? Number(entryForm.distance_km)
    : baseDistance
  const rideCount = Number(entryForm.ride_count || 1)
  const transitFactor = Number(routeCarbon.value.transit_emission_kg || 0) / Math.max(baseDistance, 0.01)
  const carFactor = Number(routeCarbon.value.car_emission_kg || 0) / Math.max(baseDistance, 0.01)
  const singleTransit = Number((singleDistance * transitFactor).toFixed(4))
  const singleCar = Number((singleDistance * carFactor).toFixed(4))
  const singleSaved = Number((singleCar - singleTransit).toFixed(4))

  return {
    single_distance_km: Number(singleDistance.toFixed(1)),
    total_distance_km: Number((singleDistance * rideCount).toFixed(1)),
    single_carbon_saved: Number(singleSaved.toFixed(2)),
    total_carbon_saved: Number((singleSaved * rideCount).toFixed(2))
  }
})

async function loadData(forceRefresh = false) {
  loading.value = true
  recordsLoading.value = true
  try {
    const [stats, lb, routes, records] = await Promise.all([
      getMyCarbonStats().catch(() => ({})),
      getCarbonLeaderboard(forceRefresh ? { limit: 10, refresh: 1 } : { limit: 10 }).catch(() => []),
      getRoutes({ page_size: 500 }).catch(() => ({ routes: [] })),
      getMyCarbonRecords({ limit: 10 }).catch(() => [])
    ])
    myStats.value = stats || {}
    leaderboard.value = lb || []
    routeList.value = Array.isArray(routes?.routes) ? routes.routes : []
    recentRecords.value = Array.isArray(records) ? records : []

    if (routeList.value.length > 0) {
      const exists = routeList.value.some(item => item.route_id === selectedRoute.value)
      if (!selectedRoute.value || !exists) {
        selectedRoute.value = routeList.value[0].route_id
        entryForm.distance_km = null
      }
      await queryRouteCarbon()
    } else {
      routeCarbon.value = null
    }

    renderTrend()
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
    recordsLoading.value = false
  }
}

async function queryRouteCarbon() {
  if (!selectedRoute.value) return
  try {
    routeCarbon.value = await getRouteCarbonData(selectedRoute.value, {
      region: regionStore.selectedRegion
    })
  } catch (e) {
    routeCarbon.value = null
    console.error(e)
  }
}

function handleRouteChange() {
  entryForm.distance_km = null
  queryRouteCarbon()
}

async function handleRecord() {
  if (!selectedRoute.value) {
    ElMessage.warning(t('carbon.selectRoute'))
    return
  }
  recording.value = true
  try {
    await recordCarbonTrip({
      route_id: selectedRoute.value,
      region: regionStore.selectedRegion,
      trip_date: entryForm.trip_date,
      ride_count: entryForm.ride_count,
      distance_km: entryForm.distance_km
    })
    ElMessage.success(t('carbon.recordSuccess'))
    entryForm.ride_count = 1
    entryForm.distance_km = null
    await loadData()
  } catch (e) {
    ElMessage.error(e.message || t('common.operationFailed'))
  } finally {
    recording.value = false
  }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(t('carbon.deleteConfirm'), t('common.confirm'), {
      type: 'warning'
    })
    deletingRecordId.value = row.id
    await deleteCarbonRecord(row.id)
    ElMessage.success(t('carbon.deleteSuccess'))
    await loadData()
  } catch (e) {
    if (e !== 'cancel' && e !== 'close') {
      ElMessage.error(e.message || t('common.operationFailed'))
    }
  } finally {
    deletingRecordId.value = null
  }
}

function handleRefresh() {
  loadData(true)
}

function routeLabel(route) {
  const shortName = route?.route_short_name || route?.route_id || ''
  const longName = route?.route_long_name || ''
  return longName ? `${shortName} - ${longName}` : shortName
}

function renderTrend() {
  nextTick(() => {
    if (!trendRef.value) return
    const daily = myStats.value.daily_trend || []
    if (!daily.length) {
      trendChart?.clear()
      return
    }
    if (!trendChart) trendChart = echarts.init(trendRef.value)
    trendChart.setOption({
      tooltip: { trigger: 'axis' },
      grid: { left: 50, right: 20, top: 10, bottom: 30 },
      xAxis: { type: 'category', data: daily.map(d => d.trip_date) },
      yAxis: { type: 'value', name: 'kg CO₂' },
      series: [{
        type: 'bar',
        data: daily.map(d => Number(d.saved || 0)),
        itemStyle: { color: '#67c23a', borderRadius: [4, 4, 0, 0] }
      }]
    })
    trendChart.resize()
  })
}

function todayString() {
  return new Date().toISOString().slice(0, 10)
}

watch(() => regionStore.selectedRegion, () => {
  selectedRoute.value = ''
  entryForm.distance_km = null
  loadData()
})

onMounted(() => loadData())

onBeforeUnmount(() => {
  if (trendChart) {
    trendChart.dispose()
    trendChart = null
  }
})
</script>

<style scoped>
.carbon-page { padding: 20px; max-width: 1200px; margin: 0 auto; }
.page-header { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; }
.page-header h1 { margin: 0; font-size: 22px; }
.header-actions { display: flex; gap: 8px; }
.page-subtitle { color: #909399; font-size: 14px; margin: 4px 0 16px; }
.stat-row { margin-bottom: 16px; }
.stat-card {
  text-align: center;
  padding: 16px;
  border-radius: 10px;
  background: linear-gradient(135deg, #f0f9eb 0%, #e8f5e9 100%);
}
.stat-blue { background: linear-gradient(135deg, #ecf5ff 0%, #e3f2fd 100%); }
.stat-teal { background: linear-gradient(135deg, #e0f2f1 0%, #b2dfdb 100%); }
.stat-orange { background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%); }
.stat-icon { font-size: 24px; }
.stat-value { font-size: 24px; font-weight: bold; color: #303133; margin: 4px 0; }
.stat-label { font-size: 13px; color: #606266; }
.period-row { margin-bottom: 16px; }
.period-stat { display: flex; align-items: center; gap: 12px; padding: 8px 0; }
.period-label { font-size: 14px; color: #909399; }
.period-value { font-size: 18px; font-weight: bold; color: #67c23a; }
.period-trips { font-size: 13px; color: #909399; }
.chart-card { margin-bottom: 16px; }
.chart-area { width: 100%; height: 250px; }
.entry-row { margin-bottom: 16px; }
.query-card, .records-card { height: 100%; }
.entry-form { margin-bottom: 12px; }
.entry-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}
.form-hint {
  margin-top: 6px;
  color: #909399;
  font-size: 12px;
  line-height: 1.4;
}
.carbon-compare {
  padding: 12px;
  background: #f8faf7;
  border-radius: 12px;
  margin-bottom: 12px;
}
.compare-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 24px;
  margin-bottom: 16px;
}
.compare-item {
  flex: 1;
  min-width: 0;
  text-align: center;
  padding: 16px 12px;
  border-radius: 12px;
  background: #fff;
}
.compare-label { color: #606266; margin-bottom: 6px; }
.compare-value { font-size: 22px; font-weight: 700; color: #303133; }
.compare-vs { font-weight: 700; color: #909399; }
.saving-bar { margin-top: 6px; }
.saving-text { margin-bottom: 8px; color: #606266; }
.preview-panel {
  padding: 14px;
  border-radius: 12px;
  background: linear-gradient(135deg, #f6ffed 0%, #eefaf2 100%);
}
.preview-title {
  font-size: 14px;
  font-weight: 700;
  color: #303133;
  margin-bottom: 12px;
}
.preview-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 12px;
}
.preview-card {
  padding: 14px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.9);
}
.preview-card.highlight {
  background: #1f8f4e;
  color: #fff;
}
.preview-label { font-size: 12px; opacity: 0.78; }
.preview-value { font-size: 22px; font-weight: 700; margin: 6px 0 2px; }
.preview-sub { font-size: 13px; }

@media (max-width: 768px) {
  .entry-grid,
  .preview-grid {
    grid-template-columns: 1fr;
  }

  .compare-row {
    flex-direction: column;
    gap: 12px;
  }

  .period-stat {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
}
</style>
