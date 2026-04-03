<template>
  <div class="flow-page">
    <div class="page-header">
      <h1>{{ $t('flowPrediction.title') }}</h1>
      <div class="header-actions">
        <el-button :icon="Refresh" @click="handleRefresh" :loading="loading || loadingPrediction" size="small">{{ $t('common.refresh') }}</el-button>
      </div>
    </div>
    <p class="page-subtitle">{{ $t('flowPrediction.subtitle') }}</p>

    <!-- 查询条件 -->
    <el-card class="query-card">
      <div class="query-form">
        <el-select v-model="selectedStop" filterable :placeholder="$t('flowPrediction.selectStop')"
          size="small" style="width:300px" @change="loadPrediction">
          <el-option v-for="s in stopList" :key="s.stop_id" :label="`${s.stop_name} (${s.stop_id})`" :value="s.stop_id" />
        </el-select>
        <el-radio-group v-model="dayType" size="small" @change="loadPrediction" style="margin-left:12px">
          <el-radio-button value="weekday">{{ $t('flowPrediction.weekday') }}</el-radio-button>
          <el-radio-button value="weekend">{{ $t('flowPrediction.weekend') }}</el-radio-button>
        </el-radio-group>
      </div>
    </el-card>

    <!-- 预测图表 -->
    <el-row :gutter="16" v-if="prediction.length">
      <el-col :xs="24" :md="16">
        <el-card>
          <template #header><span>{{ $t('flowPrediction.hourlyChart') }}</span></template>
          <div ref="chartRef" class="prediction-chart"></div>
        </el-card>
      </el-col>
      <el-col :xs="24" :md="8">
        <el-card>
          <template #header><span>{{ $t('flowPrediction.bestTime') }}</span></template>
          <div v-if="bestTimes.length" class="best-time-list">
            <div v-for="bt in bestTimes" :key="bt.hour_of_day" class="best-time-item">
              <div class="best-time-hour">{{ bt.hour_of_day }}:00</div>
              <div class="best-time-info">
                <span class="best-time-trips">{{ bt.scheduled_trips }} {{ $t('flowPrediction.tripsUnit') }}</span>
                <el-tag type="success" size="small">{{ $t('flowPrediction.lowCrowd') }}</el-tag>
              </div>
            </div>
          </div>
          <el-empty v-else :description="$t('common.noData')" />
        </el-card>

        <!-- 当前时刻指标 -->
        <el-card style="margin-top:16px" v-if="currentHourData">
          <template #header><span>{{ $t('flowPrediction.currentStatus') }}</span></template>
          <div class="current-indicator">
            <div class="current-hour">{{ currentHour }}:00</div>
            <div class="current-index" :class="crowdClass">
              {{ $t('flowPrediction.flowIndex') }}: {{ currentHourData.predicted_flow_index?.toFixed(0) }}
            </div>
            <div class="current-trips">
              {{ currentHourData.scheduled_trips }} {{ $t('flowPrediction.scheduledTrips') }}
            </div>
            <el-tag :type="crowdTagType" size="default" style="margin-top:8px">
              {{ crowdLabel }}
            </el-tag>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 无数据提示 -->
    <el-card v-if="selectedStop && !prediction.length && !loadingPrediction">
      <el-empty :description="$t('flowPrediction.noData')" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import { useI18n } from 'vue-i18n'
import * as echarts from 'echarts'
import { getStopFlowPrediction, getStopBestTime } from '@/api/flowPrediction.js'
import { useRegionStore } from '@/stores/regionStore'
import { getStops } from '@/api/stops.js'

const { t } = useI18n()
const regionStore = useRegionStore()

const loading = ref(false)
const loadingPrediction = ref(false)
const stopList = ref([])
const selectedStop = ref('')
const dayType = ref('weekday')
const prediction = ref([])
const bestTimes = ref([])
const chartRef = ref(null)
let chart = null

function normalizePredictionRows(list = []) {
  return list.map(item => ({
    ...item,
    hour_of_day: Number(item.hour_of_day ?? 0),
    scheduled_trips: Number(item.scheduled_trips ?? 0),
    predicted_flow_index: Number(item.predicted_flow_index ?? 0)
  }))
}

const currentHour = new Date().getHours()
const currentHourData = computed(() =>
  prediction.value.find(p => p.hour_of_day === currentHour)
)
const crowdClass = computed(() => {
  const idx = currentHourData.value?.predicted_flow_index ?? 0
  if (idx > 150) return 'crowd-high'
  if (idx > 80) return 'crowd-medium'
  return 'crowd-low'
})
const crowdTagType = computed(() => {
  const idx = currentHourData.value?.predicted_flow_index ?? 0
  if (idx > 150) return 'danger'
  if (idx > 80) return 'warning'
  return 'success'
})
const crowdLabel = computed(() => {
  const idx = currentHourData.value?.predicted_flow_index ?? 0
  if (idx > 150) return t('flowPrediction.crowdHigh')
  if (idx > 80) return t('flowPrediction.crowdMedium')
  return t('flowPrediction.crowdLow')
})

async function loadStops() {
  loading.value = true
  try {
    const data = await getStops({ page_size: 500 })
    stopList.value = Array.isArray(data?.stops) ? data.stops : []
    const exists = stopList.value.some(item => item.stop_id === selectedStop.value)
    if (!selectedStop.value || !exists) {
      selectedStop.value = stopList.value[0]?.stop_id || ''
    }
    if (selectedStop.value) {
      await loadPrediction()
    }
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function loadPrediction(forceRefresh = false) {
  if (!selectedStop.value) return
  loadingPrediction.value = true
  try {
    const [predData, btData] = await Promise.all([
      getStopFlowPrediction(selectedStop.value, {
        region: regionStore.selectedRegion,
        day_type: dayType.value,
        ...(forceRefresh ? { refresh: 1 } : {})
      }),
      getStopBestTime(selectedStop.value, {
        region: regionStore.selectedRegion,
        day_type: dayType.value,
        ...(forceRefresh ? { refresh: 1 } : {})
      })
    ])
    prediction.value = normalizePredictionRows(predData || [])
    bestTimes.value = normalizePredictionRows(btData || [])
    renderChart()
  } catch (e) {
    console.error(e)
  } finally {
    loadingPrediction.value = false
  }
}

async function handleRefresh() {
  await loadStops()
  if (selectedStop.value) {
    await loadPrediction(true)
  }
}

function renderChart() {
  nextTick(() => {
    if (!chartRef.value || !prediction.value.length) return
    if (!chart) chart = echarts.init(chartRef.value)

    const hours = prediction.value.map(p => `${p.hour_of_day}:00`)
    const trips = prediction.value.map(p => p.scheduled_trips)
    const flowIndex = prediction.value.map(p => p.predicted_flow_index)

    chart.setOption({
      tooltip: { trigger: 'axis' },
      legend: { data: [t('flowPrediction.trips'), t('flowPrediction.flowIndex')] },
      grid: { left: 50, right: 50, top: 40, bottom: 30 },
      xAxis: { type: 'category', data: hours },
      yAxis: [
        { type: 'value', name: t('flowPrediction.trips'), position: 'left' },
        { type: 'value', name: t('flowPrediction.flowIndex'), position: 'right' }
      ],
      series: [
        {
          name: t('flowPrediction.trips'),
          type: 'bar',
          data: trips,
          itemStyle: {
            color: (params) => {
              const idx = flowIndex[params.dataIndex]
              if (idx > 150) return '#f56c6c'
              if (idx > 80) return '#e6a23c'
              return '#67c23a'
            },
            borderRadius: [4, 4, 0, 0]
          }
        },
        {
          name: t('flowPrediction.flowIndex'),
          type: 'line',
          yAxisIndex: 1,
          data: flowIndex,
          smooth: true,
          lineStyle: { color: '#409eff', width: 2 },
          itemStyle: { color: '#409eff' }
        }
      ],
      // 标记当前时刻
      ...(prediction.value.length ? {
        markLine: undefined
      } : {})
    })
  })
}

watch(() => regionStore.selectedRegion, () => { loadStops(); prediction.value = [] })
onMounted(() => {
  loadStops()
  window.addEventListener('resize', () => chart?.resize())
})
</script>

<style scoped>
.flow-page { padding: 20px; max-width: 1200px; margin: 0 auto; }
.page-header { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; }
.page-header h1 { margin: 0; font-size: 22px; }
.header-actions { display: flex; gap: 8px; }
.page-subtitle { color: #909399; font-size: 14px; margin: 4px 0 16px; }
.query-card { margin-bottom: 16px; }
.query-form { display: flex; align-items: center; flex-wrap: wrap; }
.prediction-chart { width: 100%; height: 350px; }
.best-time-list { padding: 4px 0; }
.best-time-item {
  display: flex; justify-content: space-between; align-items: center;
  padding: 10px 12px; border-bottom: 1px solid #f0f0f0;
}
.best-time-item:last-child { border-bottom: none; }
.best-time-hour { font-size: 18px; font-weight: bold; color: #67c23a; }
.best-time-info { display: flex; align-items: center; gap: 8px; }
.best-time-trips { font-size: 13px; color: #909399; }
.current-indicator { text-align: center; padding: 12px 0; }
.current-hour { font-size: 24px; font-weight: bold; color: #303133; }
.current-index { font-size: 16px; margin: 8px 0; }
.crowd-high { color: #f56c6c; }
.crowd-medium { color: #e6a23c; }
.crowd-low { color: #67c23a; }
.current-trips { font-size: 13px; color: #909399; }
</style>
