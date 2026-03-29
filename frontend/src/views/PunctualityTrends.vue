<template>
  <div class="punctuality-trends">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <el-button :icon="ArrowLeft" @click="$router.push('/')" style="margin-bottom:8px">返回首页</el-button>
        <h1>准点率趋势总览</h1>
        <p>多维度准点率趋势分析与可视化</p>
      </div>
      <div class="header-actions">
        <el-radio-group v-model="days" @change="fetchData">
          <el-radio-button :value="7">近7天</el-radio-button>
          <el-radio-button :value="30">近30天</el-radio-button>
          <el-radio-button :value="90">近90天</el-radio-button>
        </el-radio-group>
      </div>
    </div>

    <!-- 系统每日准点率折线图 -->
    <el-card class="chart-card" v-loading="loading">
      <template #header>
        <span class="card-title">系统每日准点率趋势</span>
      </template>
      <div ref="dailyTrendChart" class="chart-container"></div>
    </el-card>

    <!-- 准点率分布饼图 + 高峰/非高峰对比 -->
    <el-row :gutter="20">
      <el-col :xs="24" :md="12">
        <el-card class="chart-card" v-loading="loading">
          <template #header>
            <span class="card-title">准点率分布</span>
          </template>
          <div ref="distributionChart" class="chart-container"></div>
        </el-card>
      </el-col>
      <el-col :xs="24" :md="12">
        <el-card class="chart-card" v-loading="loading">
          <template #header>
            <span class="card-title">高峰 / 非高峰时段对比</span>
          </template>
          <div ref="peakChart" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 线路排名 TOP5 / BOTTOM5 -->
    <el-card class="chart-card" v-loading="loading">
      <template #header>
        <div class="card-header-row">
          <span class="card-title">线路准点率排名</span>
          <el-radio-group v-model="routeRankType" size="small">
            <el-radio-button value="top">最佳 TOP5</el-radio-button>
            <el-radio-button value="bottom">最差 TOP5</el-radio-button>
          </el-radio-group>
        </div>
      </template>
      <div ref="routeRankChart" class="chart-container"></div>
    </el-card>

    <!-- 站点排名 TOP5 / BOTTOM5 -->
    <el-card class="chart-card" v-loading="loading">
      <template #header>
        <div class="card-header-row">
          <span class="card-title">站点准点率排名</span>
          <el-radio-group v-model="stopRankType" size="small">
            <el-radio-button value="top">最佳 TOP5</el-radio-button>
            <el-radio-button value="bottom">最差 TOP5</el-radio-button>
          </el-radio-group>
        </div>
      </template>
      <div ref="stopRankChart" class="chart-container"></div>
    </el-card>

    <!-- 单条线路/站点趋势查询 -->
    <el-card class="chart-card">
      <template #header>
        <div class="card-header-row">
          <span class="card-title">单线路 / 站点准点率趋势查询</span>
          <div class="query-controls">
            <el-select
              v-model="queryType"
              style="width: 120px; margin-right: 12px"
              @change="clearQuery"
            >
              <el-option label="按线路" value="route" />
              <el-option label="按站点" value="stop" />
            </el-select>
            <el-select
              v-if="queryType === 'route'"
              v-model="selectedRouteId"
              filterable
              clearable
              placeholder="搜索线路"
              style="width: 260px; margin-right: 12px"
              @change="fetchSingleTrend"
            >
              <el-option
                v-for="r in routeOptions"
                :key="r.route_id"
                :label="`${r.route_short_name || ''} ${r.route_long_name || ''}`"
                :value="r.route_id"
              />
            </el-select>
            <el-select
              v-else
              v-model="selectedStopId"
              filterable
              clearable
              placeholder="搜索站点"
              style="width: 260px; margin-right: 12px"
              @change="fetchSingleTrend"
            >
              <el-option
                v-for="s in stopOptions"
                :key="s.stop_id"
                :label="s.stop_name"
                :value="s.stop_id"
              />
            </el-select>
          </div>
        </div>
      </template>
      <div v-loading="singleTrendLoading" class="chart-container">
        <div v-show="singleTrendData.length" ref="singleTrendChart" style="width:100%;height:100%"></div>
        <el-empty v-if="!singleTrendLoading && !singleTrendData.length" description="请选择一条线路或一个站点查看趋势" style="padding-top:60px" />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { ArrowLeft } from '@element-plus/icons-vue'
import { useRegionStore } from '@/stores/regionStore'
import { getPunctualityTrends, getRoutePunctuality, getStopPunctuality } from '@/api/punctuality'
import * as echarts from 'echarts'

const regionStore = useRegionStore()

// 状态
const days = ref(30)
const loading = ref(false)
const routeRankType = ref('top')
const stopRankType = ref('bottom')
const queryType = ref('route')
const selectedRouteId = ref('')
const selectedStopId = ref('')
const singleTrendLoading = ref(false)
const singleTrendData = ref([])

// 数据
const trendsData = ref({})
const routeOptions = ref([])
const stopOptions = ref([])

// 图表 DOM 引用
const dailyTrendChart = ref(null)
const distributionChart = ref(null)
const peakChart = ref(null)
const routeRankChart = ref(null)
const stopRankChart = ref(null)
const singleTrendChart = ref(null)

// ECharts 实例
let charts = {}

// 初始化图表实例
const initChart = (domRef, key) => {
  if (!domRef) return null
  if (charts[key]) {
    charts[key].dispose()
  }
  charts[key] = echarts.init(domRef)
  return charts[key]
}

// 格式化日期：将 "Thu, 26 Feb 2026 00:00:00 GMT" 转为 "02-26"
const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return dateStr
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${m}-${day}`
}

// 获取主数据
const fetchData = async () => {
  loading.value = true
  try {
    const res = await getPunctualityTrends({
      days: days.value,
      region: regionStore.selectedRegion
    })
    trendsData.value = res || {}
    await nextTick()
    renderDailyTrend()
    renderDistribution()
    renderPeakComparison()
    renderRouteRank()
    renderStopRank()
  } catch (e) {
    console.error('获取趋势数据失败:', e)
  } finally {
    loading.value = false
  }
}

// 获取线路/站点选项列表
const fetchOptions = async () => {
  try {
    const [routeRes, stopRes] = await Promise.all([
      getRoutePunctuality({ days: days.value, region: regionStore.selectedRegion, limit: 500 }),
      getStopPunctuality({ days: days.value, region: regionStore.selectedRegion, limit: 500 })
    ])
    routeOptions.value = routeRes || []
    stopOptions.value = stopRes || []
  } catch (e) {
    console.error('获取选项列表失败:', e)
  }
}

// 清空查询
const clearQuery = () => {
  selectedRouteId.value = ''
  selectedStopId.value = ''
  singleTrendData.value = []
}

// 查询单条线路/站点趋势
const fetchSingleTrend = async () => {
  const routeId = queryType.value === 'route' ? selectedRouteId.value : ''
  const stopId = queryType.value === 'stop' ? selectedStopId.value : ''
  if (!routeId && !stopId) {
    singleTrendData.value = []
    return
  }
  singleTrendLoading.value = true
  try {
    const params = { days: days.value, region: regionStore.selectedRegion }
    if (routeId) params.route_id = routeId
    if (stopId) params.stop_id = stopId
    const res = await getPunctualityTrends(params)
    const data = res || {}
    singleTrendData.value = data.route_trend || data.stop_trend || []
    await nextTick()
    renderSingleTrend()
  } catch (e) {
    console.error('获取单项趋势失败:', e)
  } finally {
    singleTrendLoading.value = false
  }
}

// ==================== 图表渲染 ====================

// 高峰时段颜色映射（按名称而非索引）
const peakColorMap = {
  '早高峰': '#e6a23c',
  '晚高峰': '#f56c6c',
  '非高峰': '#67c23a'
}
const getPeakColor = (period) => {
  for (const [key, color] of Object.entries(peakColorMap)) {
    if (period.includes(key)) return color
  }
  return '#409eff'
}

// 1. 系统每日准点率折线图
const renderDailyTrend = () => {
  const chart = initChart(dailyTrendChart.value, 'daily')
  if (!chart) return
  const data = trendsData.value.daily_trends || []
  const rates = data.map(d => parseFloat(d.avg_punctuality_rate || 0))
  const delays = data.map(d => parseFloat(d.avg_delay_minutes || 0))
  const trips = data.map(d => parseInt(d.total_trips || 0))
  // 准点率Y轴自适应范围，留出上下余量
  const rateMin = Math.max(0, Math.floor(Math.min(...rates) - 3))
  const rateMax = Math.min(100, Math.ceil(Math.max(...rates) + 3))
  chart.setOption({
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        let tip = params[0]?.axisValue || ''
        params.forEach(p => {
          tip += `<br/>${p.marker}${p.seriesName}: ${p.value}${p.seriesName.includes('班次') ? '' : ''}`
        })
        return tip
      }
    },
    legend: { data: ['准点率(%)', '平均延误(分钟)', '班次数'], top: 0 },
    grid: { left: 60, right: 60, bottom: 60, top: 50 },
    xAxis: {
      type: 'category',
      data: data.map(d => formatDate(d.stat_date)),
      axisLabel: { rotate: 45, fontSize: 11 }
    },
    yAxis: [
      { type: 'value', name: '准点率(%)', min: rateMin, max: rateMax },
      { type: 'value', name: '延误(分钟)', position: 'right' },
      { type: 'value', show: false }
    ],
    series: [
      {
        name: '班次数',
        type: 'bar',
        yAxisIndex: 2,
        data: trips,
        itemStyle: { color: 'rgba(64,158,255,0.15)' },
        barMaxWidth: 24,
        silent: true,
        z: 0
      },
      {
        name: '准点率(%)',
        type: 'line',
        smooth: true,
        data: rates.map(v => v.toFixed(1)),
        itemStyle: { color: '#67c23a' },
        lineStyle: { width: 2.5 },
        areaStyle: { color: 'rgba(103,194,58,0.1)' },
        z: 2
      },
      {
        name: '平均延误(分钟)',
        type: 'line',
        smooth: true,
        yAxisIndex: 1,
        data: delays.map(v => v.toFixed(2)),
        itemStyle: { color: '#e6a23c' },
        lineStyle: { width: 2.5 },
        z: 2
      }
    ]
  })
}

// 2. 准点率分布饼图
const renderDistribution = () => {
  const chart = initChart(distributionChart.value, 'dist')
  if (!chart) return
  const data = trendsData.value.daily_trends || []
  // 汇总所有天的分布，过滤负值
  let onTime = 0, early = 0, late = 0, veryLate = 0
  data.forEach(d => {
    onTime += Math.max(0, parseInt(d.on_time_trips || 0))
    early += Math.max(0, parseInt(d.early_trips || 0))
    late += Math.max(0, parseInt(d.late_trips || 0))
    veryLate += Math.max(0, parseInt(d.very_late_trips || 0))
  })
  const total = onTime + early + late + veryLate
  chart.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { bottom: 0 },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      avoidLabelOverlap: true,
      itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
      label: { show: total > 0, formatter: '{b}\n{d}%' },
      data: total > 0 ? [
        { value: onTime, name: '准点', itemStyle: { color: '#67c23a' } },
        { value: early, name: '早到', itemStyle: { color: '#409eff' } },
        { value: late, name: '晚到', itemStyle: { color: '#e6a23c' } },
        { value: veryLate, name: '严重晚到', itemStyle: { color: '#f56c6c' } }
      ] : [{ value: 1, name: '暂无数据', itemStyle: { color: '#dcdfe6' } }]
    }]
  })
}

// 3. 高峰/非高峰对比
const renderPeakComparison = () => {
  const chart = initChart(peakChart.value, 'peak')
  if (!chart) return
  const data = trendsData.value.peak_comparison || []
  const periods = data.map(d => d.period)
  chart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['准点率(%)', '平均延误(分钟)'], top: 0 },
    grid: { left: 60, right: 70, bottom: 60, top: 40 },
    xAxis: { type: 'category', data: periods, axisLabel: { rotate: 15, fontSize: 12 } },
    yAxis: [
      { type: 'value', name: '准点率(%)', min: 0, max: 100 },
      { type: 'value', name: '延误(分钟)', position: 'right' }
    ],
    series: [
      {
        name: '准点率(%)',
        type: 'bar',
        data: data.map(d => ({
          value: parseFloat(d.avg_punctuality_rate || 0).toFixed(1),
          itemStyle: { color: getPeakColor(d.period) }
        })),
        barMaxWidth: 50
      },
      {
        name: '平均延误(分钟)',
        type: 'bar',
        yAxisIndex: 1,
        data: data.map(d => parseFloat(d.avg_delay_minutes || 0).toFixed(2)),
        itemStyle: { color: 'rgba(64,158,255,0.5)' },
        barMaxWidth: 50
      }
    ]
  })
}

// 4. 线路排名柱状图
const renderRouteRank = () => {
  const chart = initChart(routeRankChart.value, 'routeRank')
  if (!chart) return
  const isTop = routeRankType.value === 'top'
  const list = isTop
    ? (trendsData.value.top_routes || [])
    : (trendsData.value.bottom_routes || [])
  // top_routes: 后端按准点率DESC排序，index0最高 → reverse让最高在Y轴顶部
  // bottom_routes: 后端返回最差在前(index0最低) → 直接用，最差在Y轴底部
  const display = isTop ? list.slice().reverse() : list.slice()
  const names = display.map(r => r.route_short_name || r.route_id)
  const rates = display.map(r => parseFloat(r.avg_punctuality_rate || 0).toFixed(1))
  const color = isTop ? '#67c23a' : '#f56c6c'
  chart.setOption({
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        const item = params[0]
        const orig = display[item.dataIndex]
        return `${orig?.route_short_name || ''} ${orig?.route_long_name || ''}<br/>准点率: ${item.value}%`
      }
    },
    grid: { left: 120, right: 80, bottom: 30, top: 20 },
    xAxis: { type: 'value', name: '准点率(%)', min: 0, max: 100, nameGap: 5 },
    yAxis: { type: 'category', data: names, axisLabel: { fontSize: 12, width: 100, overflow: 'truncate' } },
    series: [{
      type: 'bar',
      data: rates.map(v => ({ value: v, itemStyle: { color } })),
      barMaxWidth: 36,
      label: { show: true, position: 'right', formatter: '{c}%' }
    }]
  })
}

// 5. 站点排名柱状图
const renderStopRank = () => {
  const chart = initChart(stopRankChart.value, 'stopRank')
  if (!chart) return
  const isTop = stopRankType.value === 'top'
  const list = isTop
    ? (trendsData.value.top_stops || [])
    : (trendsData.value.bottom_stops || [])
  const display = isTop ? list.slice().reverse() : list.slice()
  const names = display.map(s => {
    const name = s.stop_name || s.stop_id
    return name.length > 14 ? name.substring(0, 14) + '…' : name
  })
  const rates = display.map(s => parseFloat(s.avg_punctuality_rate || 0).toFixed(1))
  const color = isTop ? '#67c23a' : '#f56c6c'
  chart.setOption({
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        const item = params[0]
        const orig = display[item.dataIndex]
        return `${orig?.stop_name || orig?.stop_id || ''}<br/>准点率: ${item.value}%`
      }
    },
    grid: { left: 120, right: 80, bottom: 30, top: 20 },
    xAxis: { type: 'value', name: '准点率(%)', min: 0, max: 100, nameGap: 5 },
    yAxis: { type: 'category', data: names, axisLabel: { fontSize: 11, width: 100, overflow: 'truncate' } },
    series: [{
      type: 'bar',
      data: rates.map(v => ({ value: v, itemStyle: { color } })),
      barMaxWidth: 36,
      label: { show: true, position: 'right', formatter: '{c}%' }
    }]
  })
}

// 6. 单线路/站点趋势折线图
const renderSingleTrend = () => {
  const chart = initChart(singleTrendChart.value, 'single')
  if (!chart) return
  const data = singleTrendData.value
  const isRoute = queryType.value === 'route'
  const label = isRoute
    ? (data[0]?.route_short_name || selectedRouteId.value)
    : (data[0]?.stop_name || selectedStopId.value)
  chart.setOption({
    title: { text: `${label} 准点率趋势`, left: 'center', textStyle: { fontSize: 14 } },
    tooltip: { trigger: 'axis' },
    legend: { data: ['准点率(%)', '平均延误(分钟)'], top: 30 },
    grid: { left: 60, right: 70, top: 70, bottom: 60 },
    xAxis: {
      type: 'category',
      data: data.map(d => formatDate(d.stat_date)),
      axisLabel: { rotate: 45, fontSize: 11 }
    },
    yAxis: [
      { type: 'value', name: '准点率(%)', min: 0, max: 100 },
      { type: 'value', name: '延误(分钟)', position: 'right' }
    ],
    series: [
      {
        name: '准点率(%)',
        type: 'line',
        smooth: true,
        data: data.map(d => parseFloat(d.punctuality_rate || 0).toFixed(1)),
        itemStyle: { color: '#409eff' },
        areaStyle: { color: 'rgba(64,158,255,0.15)' }
      },
      {
        name: '平均延误(分钟)',
        type: 'line',
        smooth: true,
        yAxisIndex: 1,
        data: data.map(d => parseFloat(d.avg_delay_minutes || 0).toFixed(2)),
        itemStyle: { color: '#e6a23c' }
      }
    ]
  })
}

// 窗口 resize 处理
const handleResize = () => {
  Object.values(charts).forEach(c => c?.resize())
}

// 监听排名切换
watch(routeRankType, () => renderRouteRank())
watch(stopRankType, () => renderStopRank())
watch(() => regionStore.selectedRegion, () => {
  fetchData()
  fetchOptions()
})

onMounted(() => {
  fetchData()
  fetchOptions()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  Object.values(charts).forEach(c => c?.dispose())
  charts = {}
})
</script>

<style scoped>
.punctuality-trends {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 16px;
}

.header-content h1 {
  font-size: 24px;
  font-weight: 600;
  color: #2c3e50;
  margin: 0 0 4px;
}

.header-content p {
  font-size: 14px;
  color: #6c757d;
  margin: 0;
}

.chart-card {
  margin-bottom: 20px;
}

.chart-container {
  height: 360px;
  width: 100%;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
}

.card-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

.query-controls {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

@media (max-width: 768px) {
  .punctuality-trends {
    padding: 16px;
  }

  .page-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .chart-container {
    height: 280px;
  }

  .card-header-row {
    flex-direction: column;
    align-items: flex-start;
  }

  .query-controls {
    width: 100%;
  }

  .query-controls .el-select {
    width: 100% !important;
    margin-right: 0 !important;
  }
}
</style>
