<template>
  <div class="route-schedule-page">
    <div class="page-header">
      <div class="header-content">
        <h1>{{ $t('schedule.title') }}</h1>
        <p>{{ $t('schedule.subtitle') }}</p>
      </div>
    </div>

    <!-- 线路列表 -->
    <el-card class="table-card" v-loading="loading">
      <el-table :data="routes" stripe @row-click="handleRowClick" style="cursor: pointer" :cell-style="{ padding: '12px 8px' }">
        <template #empty>
          <el-empty :description="$t('schedule.noData')" />
        </template>
        <el-table-column prop="route_short_name" :label="$t('schedule.route')" width="140">
          <template #default="{ row }">
            <span style="font-weight: 600">{{ row.route_short_name || row.route_id }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="route_long_name" :label="$t('schedule.routeName')" min-width="180" show-overflow-tooltip />
        <el-table-column prop="first_departure" :label="$t('schedule.firstDeparture')" width="120" align="center" />
        <el-table-column prop="last_departure" :label="$t('schedule.lastDeparture')" width="120" align="center" />
        <el-table-column prop="total_trips" :label="$t('schedule.totalTrips')" width="100" sortable align="center" />
        <el-table-column :label="$t('schedule.morningPeak')" width="120" align="center">
          <template #default="{ row }">
            <el-tag type="danger" size="small">{{ row.morning_peak_trips }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="$t('schedule.eveningPeak')" width="120" align="center">
          <template #default="{ row }">
            <el-tag type="warning" size="small">{{ row.evening_peak_trips }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="$t('schedule.peakRatio')" width="100" align="center">
          <template #default="{ row }">
            <span>{{ peakRatio(row) }}</span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 单线路详情弹窗 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="800px" destroy-on-close>
      <div v-loading="detailLoading" class="detail-content">
        <div class="detail-stats" v-if="detail">
          <div class="stat-item">
            <div class="stat-label">{{ $t('schedule.firstDeparture') }}</div>
            <div class="stat-value">{{ detail.first_departure || '--' }}</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">{{ $t('schedule.lastDeparture') }}</div>
            <div class="stat-value">{{ detail.last_departure || '--' }}</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">{{ $t('schedule.totalTrips') }}</div>
            <div class="stat-value">{{ detail.total_trips }}</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">{{ $t('schedule.morningPeak') }}</div>
            <div class="stat-value" style="color: #f56c6c">{{ detail.morning_peak }}</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">{{ $t('schedule.eveningPeak') }}</div>
            <div class="stat-value" style="color: #e6a23c">{{ detail.evening_peak }}</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">{{ $t('schedule.offPeak') }}</div>
            <div class="stat-value" style="color: #67c23a">{{ detail.off_peak }}</div>
          </div>
        </div>
        <!-- 24小时柱状图 -->
        <div ref="chartRef" style="width: 100%; height: 320px; margin-top: 16px"></div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRegionStore } from '@/stores/regionStore.js'
import * as echarts from 'echarts'
import apiClient from '@/api/index.js'

const { t } = useI18n()
const regionStore = useRegionStore()

const loading = ref(false)
const routes = ref([])
const dialogVisible = ref(false)
const dialogTitle = ref('')
const detailLoading = ref(false)
const detail = ref(null)
const chartRef = ref(null)
let chartInstance = null

const peakRatio = (row) => {
  const peak = (row.morning_peak_trips || 0) + (row.evening_peak_trips || 0)
  const total = row.total_trips || 0
  if (total === 0) return '--'
  return (peak / total * 100).toFixed(0) + '%'
}

const loadRoutes = async () => {
  loading.value = true
  try {
    routes.value = await apiClient.get('/routes/schedule-summary') || []
  } catch {
    routes.value = []
  } finally {
    loading.value = false
  }
}

const handleRowClick = async (row) => {
  dialogTitle.value = `${row.route_short_name || row.route_id} — ${row.route_long_name || ''}`
  dialogVisible.value = true
  detailLoading.value = true
  detail.value = null

  try {
    detail.value = await apiClient.get(`/routes/${row.route_id}/schedule-analysis`)
    await nextTick()
    renderChart()
  } catch {
    detail.value = null
  } finally {
    detailLoading.value = false
  }
}

const renderChart = () => {
  if (!chartRef.value || !detail.value) return
  if (chartInstance) chartInstance.dispose()
  chartInstance = echarts.init(chartRef.value)

  const dist = detail.value.hourly_distribution || []
  const hours = dist.map(d => `${d.hour}:00`)
  const counts = dist.map(d => d.trip_count)

  // 高峰时段着色
  const colors = dist.map(d => {
    if (d.hour >= 7 && d.hour <= 9) return '#f56c6c'
    if (d.hour >= 17 && d.hour <= 19) return '#e6a23c'
    return '#409eff'
  })

  chartInstance.setOption({
    tooltip: { trigger: 'axis', formatter: '{b}<br/>' + t('schedule.trips') + ': {c}' },
    xAxis: { type: 'category', data: hours, axisLabel: { interval: 1, fontSize: 11 } },
    yAxis: { type: 'value', name: t('schedule.trips') },
    series: [{
      type: 'bar',
      data: counts.map((v, i) => ({ value: v, itemStyle: { color: colors[i] } })),
      barWidth: '60%',
    }],
    grid: { left: 50, right: 20, top: 30, bottom: 30 },
  })
}

watch(() => regionStore.selectedRegion, loadRoutes)
onMounted(loadRoutes)
</script>

<style scoped>
.route-schedule-page {
  padding: 20px;
  background: var(--el-bg-color-page);
  min-height: 100vh;
}

.page-header {
  margin-bottom: 20px;
  padding: 24px;
  background: var(--el-bg-color);
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.header-content h1 {
  margin: 0 0 8px 0;
  color: var(--el-text-color-primary);
  font-size: 28px;
  font-weight: 600;
}

.header-content p {
  margin: 0;
  color: var(--el-text-color-secondary);
  font-size: 14px;
}

.table-card {
  margin-bottom: 20px;
}

.detail-stats {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.stat-item {
  flex: 1;
  min-width: 100px;
  text-align: center;
  padding: 12px;
  background: var(--el-fill-color-light);
  border-radius: 8px;
}

.stat-label {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-bottom: 4px;
}

.stat-value {
  font-size: 20px;
  font-weight: 700;
  color: var(--el-text-color-primary);
}

@media (max-width: 768px) {
  .detail-stats {
    flex-direction: column;
  }
}
</style>
