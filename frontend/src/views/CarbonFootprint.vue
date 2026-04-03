<template>
  <div class="carbon-page">
    <div class="page-header">
      <h1>{{ $t('carbon.title') }}</h1>
      <div class="header-actions">
        <el-button :icon="Refresh" @click="loadData" :loading="loading" size="small">{{ $t('common.refresh') }}</el-button>
      </div>
    </div>
    <p class="page-subtitle">{{ $t('carbon.subtitle') }}</p>

    <!-- 统计摘要 -->
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

    <!-- 本周/本月 -->
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

    <!-- 每日趋势 -->
    <el-card class="chart-card" v-if="myStats.daily_trend?.length">
      <template #header><span>{{ $t('carbon.dailyTrend') }}</span></template>
      <div ref="trendRef" class="chart-area"></div>
    </el-card>

    <!-- 线路碳排放查询 -->
    <el-card class="query-card">
      <template #header><span>{{ $t('carbon.routeQuery') }}</span></template>
      <div class="query-form">
        <el-select v-model="selectedRoute" filterable :placeholder="$t('carbon.selectRoute')" size="small"
          style="width:300px" @change="queryRouteCabon">
          <el-option v-for="r in routeList" :key="r.route_id" :label="`${r.route_short_name} - ${r.route_long_name || ''}`" :value="r.route_id" />
        </el-select>
      </div>
      <div v-if="routeCarbon" class="carbon-compare">
        <div class="compare-row">
          <div class="compare-item transit">
            <div class="compare-label">🚌 {{ $t('carbon.transit') }}</div>
            <div class="compare-value">{{ routeCarbon.transit_emission_kg }} kg CO₂</div>
          </div>
          <div class="compare-vs">VS</div>
          <div class="compare-item car">
            <div class="compare-label">🚗 {{ $t('carbon.car') }}</div>
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
        <el-button type="success" @click="handleRecord" :loading="recording" size="small" style="margin-top:12px">
          {{ $t('carbon.recordTrip') }}
        </el-button>
      </div>
    </el-card>

    <!-- 排行榜 -->
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
import { ref, onMounted, nextTick, watch } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import * as echarts from 'echarts'
import { getRouteCarbonData, recordCarbonTrip, getMyCarbonStats, getCarbonLeaderboard } from '@/api/carbon.js'
import { useRegionStore } from '@/stores/regionStore'
import apiClient from '@/api/index.js'

const { t } = useI18n()
const regionStore = useRegionStore()

const loading = ref(false)
const recording = ref(false)
const myStats = ref({})
const leaderboard = ref([])
const routeList = ref([])
const selectedRoute = ref('')
const routeCarbon = ref(null)
const trendRef = ref(null)
let trendChart = null

async function loadData() {
  loading.value = true
  try {
    const [stats, lb, routes] = await Promise.all([
      getMyCarbonStats().catch(() => ({})),
      getCarbonLeaderboard({ limit: 10 }).catch(() => []),
      apiClient.get('/routes', { params: { region: regionStore.selectedRegion, limit: 500 } }).catch(() => [])
    ])
    myStats.value = stats || {}
    leaderboard.value = lb || []
    routeList.value = Array.isArray(routes) ? routes : (routes?.items || routes?.data || [])
    renderTrend()
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function queryRouteCabon() {
  if (!selectedRoute.value) return
  try {
    routeCarbon.value = await getRouteCarbonData(selectedRoute.value, {
      region: regionStore.selectedRegion
    })
  } catch (e) {
    console.error(e)
  }
}

async function handleRecord() {
  if (!routeCarbon.value) return
  recording.value = true
  try {
    await recordCarbonTrip({
      route_id: selectedRoute.value,
      region: regionStore.selectedRegion,
      distance_km: routeCarbon.value.distance_km,
      transit_emission: routeCarbon.value.transit_emission_kg,
      car_emission: routeCarbon.value.car_emission_kg,
      carbon_saved: routeCarbon.value.carbon_saved_kg
    })
    ElMessage.success(t('carbon.recordSuccess'))
    loadData()
  } catch (e) {
    ElMessage.error(t('common.operationFailed'))
  } finally {
    recording.value = false
  }
}

function renderTrend() {
  nextTick(() => {
    if (!trendRef.value) return
    const daily = myStats.value.daily_trend || []
    if (!daily.length) return
    if (!trendChart) trendChart = echarts.init(trendRef.value)
    trendChart.setOption({
      tooltip: { trigger: 'axis' },
      grid: { left: 50, right: 20, top: 10, bottom: 30 },
      xAxis: { type: 'category', data: daily.map(d => d.trip_date) },
      yAxis: { type: 'value', name: 'kg CO₂' },
      series: [{
        type: 'bar',
        data: daily.map(d => d.saved),
        itemStyle: { color: '#67c23a', borderRadius: [4, 4, 0, 0] }
      }]
    })
  })
}

watch(() => regionStore.selectedRegion, () => loadData())
onMounted(() => loadData())
</script>

<style scoped>
.carbon-page { padding: 20px; max-width: 1200px; margin: 0 auto; }
.page-header { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; }
.page-header h1 { margin: 0; font-size: 22px; }
.header-actions { display: flex; gap: 8px; }
.page-subtitle { color: #909399; font-size: 14px; margin: 4px 0 16px; }
.stat-row { margin-bottom: 16px; }
.stat-card {
  text-align: center; padding: 16px; border-radius: 10px;
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
.query-card { margin-bottom: 16px; }
.query-form { margin-bottom: 16px; }
.carbon-compare { padding: 12px; }
.compare-row { display: flex; align-items: center; justify-content: center; gap: 24px; margin-bottom: 16px; }
.compare-item { text-align: center; padding: 16px 24px; border-radius: 8px; min-width: 150px; }
.compare-item.transit { background: #f0f9eb; }
.compare-item.car { background: #fef0f0; }
.compare-label { font-size: 14px; color: #606266; margin-bottom: 4px; }
.compare-value { font-size: 20px; font-weight: bold; }
.compare-item.transit .compare-value { color: #67c23a; }
.compare-item.car .compare-value { color: #f56c6c; }
.compare-vs { font-size: 18px; font-weight: bold; color: #909399; }
.saving-bar { margin-top: 8px; }
.saving-text { font-size: 14px; color: #606266; margin-bottom: 8px; }

html.dark .stat-card { background: linear-gradient(135deg, #1a2e1a 0%, #1a3a1a 100%); }
html.dark .stat-blue { background: linear-gradient(135deg, #1a1a2e 0%, #1a2a3a 100%); }
html.dark .stat-teal { background: linear-gradient(135deg, #1a2e2e 0%, #1a3a3a 100%); }
html.dark .stat-orange { background: linear-gradient(135deg, #2e2a1a 0%, #3a2a1a 100%); }
html.dark .compare-item.transit { background: #1a2e1a; }
html.dark .compare-item.car { background: #2e1a1a; }
</style>
