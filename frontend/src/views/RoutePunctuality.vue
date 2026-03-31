<template>
  <div class="route-punctuality">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <el-button :icon="ArrowLeft" @click="goHome" style="margin-bottom:8px">{{ $t('common.backHome') }}</el-button>
        <h1>{{ $t('routePunctuality.title') }}</h1>
        <p>{{ $t('routePunctuality.subtitle') }}</p>
      </div>
      <div class="header-actions">
        <el-button
          type="primary"
          :loading="refreshing"
          @click="refreshData"
          :icon="Refresh"
        >
          {{ $t('common.refresh') }}
        </el-button>
        <el-button
          @click="exportData"
          :icon="Download"
        >
          {{ $t('common.export') }}
        </el-button>
      </div>
    </div>

    <!-- 筛选器 -->
    <el-card class="filter-card">
      <el-row :gutter="16">
        <el-col :span="6">
          <el-input
            v-model="filters.routeName"
            :placeholder="$t('routePunctuality.searchPlaceholder')"
            :prefix-icon="Search"
            clearable
            @input="handleSearch"
          />
        </el-col>
        <el-col :span="6">
          <el-select
            v-model="filters.timeRange"
            :placeholder="$t('routePunctuality.timeRange')"
            @change="handleTimeRangeChange"
            style="width: 100%"
          >
            <el-option :label="$t('routePunctuality.last7Days')" value="7" />
            <el-option :label="$t('routePunctuality.last30Days')" value="30" />
            <el-option :label="$t('routePunctuality.last90Days')" value="90" />
          </el-select>
        </el-col>
        <el-col :span="6" v-if="filters.timeRange === 'custom'">
          <el-date-picker
            v-model="filters.customDateRange"
            type="daterange"
            range-separator="-"
            start-placeholder=""
            end-placeholder=""
            @change="handleCustomDateChange"
            style="width: 100%"
          />
        </el-col>
        <el-col :span="6">
          <el-select
            v-model="filters.sortBy"
            :placeholder="$t('routePunctuality.sortBy')"
            @change="handleSortChange"
            style="width: 100%"
          >
            <el-option :label="$t('routePunctuality.rateHighToLow')" value="punctuality_desc" />
            <el-option :label="$t('routePunctuality.rateLowToHigh')" value="punctuality_asc" />
            <el-option :label="$t('routePunctuality.tripsHighToLow')" value="trips_desc" />
            <el-option :label="$t('routePunctuality.tripsLowToHigh')" value="trips_asc" />
            <el-option :label="$t('routePunctuality.delayLowToHigh')" value="delay_asc" />
            <el-option :label="$t('routePunctuality.delayHighToLow')" value="delay_desc" />
          </el-select>
        </el-col>
      </el-row>
    </el-card>

    <!-- 统计概览 -->
    <div class="stats-overview" v-loading="loading">
      <div class="stat-item">
        <div class="stat-value">{{ filteredRoutes.length }}</div>
        <div class="stat-label">{{ $t('routePunctuality.showingRoutes') }}</div>
      </div>
      <div class="stat-item">
        <div class="stat-value">{{ formatPunctualityRate(averagePunctualityRate) }}</div>
        <div class="stat-label">{{ $t('routePunctuality.avgRate') }}</div>
      </div>
      <div class="stat-item">
        <div class="stat-value">{{ totalTrips.toLocaleString() }}</div>
        <div class="stat-label">{{ $t('routePunctuality.totalTrips') }}</div>
      </div>
      <div class="stat-item">
        <div class="stat-value">{{ formatDelay(averageDelay) }}</div>
        <div class="stat-label">{{ $t('routePunctuality.avgDelay') }}</div>
      </div>
    </div>

    <!-- 线路列表 -->
    <el-card class="routes-table-card">
      <template #header>
        <div class="table-header">
          <h3>{{ $t('routePunctuality.routeList') }}</h3>
          <div class="table-actions">
            <el-input-number
              v-model="pagination.pageSize"
              :min="10"
              :max="100"
              :step="10"
              @change="handlePageSizeChange"
              style="width: 120px"
            />
            <span class="page-size-label">{{ $t('routePunctuality.perPage') }}</span>
          </div>
        </div>
      </template>

      <el-table
        :data="paginatedRoutes"
        v-loading="loading"
        stripe
        @sort-change="handleTableSort"
      >
        <template #empty>
          <el-empty :description="$t('routePunctuality.noData')" />
        </template>
        <el-table-column prop="route_short_name" :label="$t('routePunctuality.route')" min-width="200" sortable>
          <template #default="{ row }">
            <div class="route-name">
              <div class="route-short">{{ row.route_short_name || row.route_id }}</div>
              <div class="route-long">{{ truncateText(row.route_long_name, 40) }}</div>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="avg_punctuality_rate" :label="$t('routePunctuality.rate')" width="120" sortable="custom">
          <template #default="{ row }">
            <div class="punctuality-cell">
              <el-progress
                :percentage="getDistribution(row).onTime"
                :color="getProgressColor(getDistribution(row).onTime)"
                :stroke-width="8"
                :show-text="false"
              />
              <span class="rate-text">{{ getDistribution(row).onTime }}%</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="total_trips" :label="$t('routePunctuality.totalTrips')" width="100" sortable="custom">
          <template #default="{ row }">
            <span class="trips-count">{{ (row.total_trips || 0).toLocaleString() }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="avg_delay_minutes" :label="$t('routePunctuality.avgDelay')" width="150" sortable="custom" align="center">
          <template #default="{ row }">
            <div class="delay-cell">
              <el-icon class="delay-icon" :class="getDelayClass(row.avg_delay_minutes || 0)">
                <Clock />
              </el-icon>
              <span style="white-space: nowrap;">{{ formatDelay(row.avg_delay_minutes || 0) }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="max_delay_minutes" :label="$t('routePunctuality.maxDelay')" width="150" sortable="custom">
          <template #default="{ row }">
            <span class="max-delay" style="white-space: nowrap;">{{ formatDelay(row.max_delay_minutes || 0) }}</span>
          </template>
        </el-table-column>

        <el-table-column min-width="260">
          <template #header>
            <span style="padding-left: 48px;">{{ $t('routePunctuality.distribution') }}</span>
          </template>
          <template #default="{ row }">
            <div class="punctuality-distribution">
              <div class="dist-item" :title="`${$t('common.onTime')}: ${row.on_time_trips || 0}`">
                <span class="dist-name on-time-text">{{ $t('common.onTime') }}</span>
                <div class="dist-bar on-time" :style="{ width: getDistribution(row).onTime + '%' }"></div>
                <span class="dist-label">{{ getDistribution(row).onTime }}%</span>
              </div>
              <div class="dist-item" :title="`${$t('common.late')}: ${row.late_trips || 0}`">
                <span class="dist-name late-text">{{ $t('common.late') }}</span>
                <div class="dist-bar late" :style="{ width: getDistribution(row).late + '%' }"></div>
                <span class="dist-label">{{ getDistribution(row).late }}%</span>
              </div>
              <div class="dist-item" :title="`${$t('common.veryLate')}: ${row.very_late_trips || 0}`">
                <span class="dist-name very-late-text">{{ $t('common.veryLate') }}</span>
                <div class="dist-bar very-late" :style="{ width: getDistribution(row).veryLate + '%' }"></div>
                <span class="dist-label">{{ getDistribution(row).veryLate }}%</span>
              </div>
              <div class="dist-item" :title="`${$t('common.early')}: ${row.early_trips || 0}`">
                <span class="dist-name early-text">{{ $t('common.early') }}</span>
                <div class="dist-bar early" :style="{ width: getDistribution(row).early + '%' }"></div>
                <span class="dist-label">{{ getDistribution(row).early }}%</span>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="last_stat_date" :label="$t('routePunctuality.statTime')" width="120">
          <template #default="{ row }">
            <span class="stat-date">{{ formatDate(row.last_stat_date) }}</span>
          </template>
        </el-table-column>

        <el-table-column :label="$t('routePunctuality.operation')" width="100" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              link
              size="small"
              @click="viewRouteDetail(row)"
            >
              {{ $t('common.detail') }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.currentPage"
          v-model:page-size="pagination.pageSize"
          :total="filteredRoutes.length"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handlePageSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { usePunctualityStore } from '../stores/punctualityStore'
import { useRegionStore } from '@/stores/regionStore'
import {
  Refresh, Download, Search, Clock, ArrowLeft
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

// Store
const router = useRouter()
const { t } = useI18n()
const punctualityStore = usePunctualityStore()
const regionStore = useRegionStore()

const goHome = () => { window.location.href = '/' }

// 响应式数据
const loading = computed(() => punctualityStore.loading)
const refreshing = ref(false)
const routePunctuality = computed(() => punctualityStore.routePunctuality)

const filters = ref({
  routeName: '',
  timeRange: '7',
  customDateRange: null,
  sortBy: 'punctuality_desc'
})

const pagination = ref({
  currentPage: 1,
  pageSize: 20
})

// 计算属性
const filteredRoutes = computed(() => {
  let routes = [...(routePunctuality.value || [])]

  // 按线路名称筛选
  if (filters.value.routeName) {
    const searchTerm = filters.value.routeName.toLowerCase()
    routes = routes.filter(route =>
      (route.route_short_name?.toLowerCase().includes(searchTerm) ||
       route.route_long_name?.toLowerCase().includes(searchTerm) ||
       route.route_id?.toLowerCase().includes(searchTerm))
    )
  }

  // 排序
  routes.sort((a, b) => {
    switch (filters.value.sortBy) {
      case 'punctuality_desc':
        return getDistribution(b).onTime - getDistribution(a).onTime
      case 'punctuality_asc':
        return getDistribution(a).onTime - getDistribution(b).onTime
      case 'trips_desc':
        return (b.total_trips || 0) - (a.total_trips || 0)
      case 'trips_asc':
        return (a.total_trips || 0) - (b.total_trips || 0)
      case 'delay_desc':
        return (b.avg_delay_minutes || 0) - (a.avg_delay_minutes || 0)
      case 'delay_asc':
        return (a.avg_delay_minutes || 0) - (b.avg_delay_minutes || 0)
      default:
        return 0
    }
  })

  return routes
})

const paginatedRoutes = computed(() => {
  const start = (pagination.value.currentPage - 1) * pagination.value.pageSize
  const end = start + pagination.value.pageSize
  return filteredRoutes.value.slice(start, end)
})

const averagePunctualityRate = computed(() => {
  if (filteredRoutes.value.length === 0) return 0
  const total = filteredRoutes.value.reduce((sum, route) => sum + getDistribution(route).onTime, 0)
  return total / filteredRoutes.value.length
})

const totalTrips = computed(() => {
  return filteredRoutes.value.reduce((sum, route) => sum + (route.total_trips || 0), 0)
})

const averageDelay = computed(() => {
  if (filteredRoutes.value.length === 0) return 0
  const total = filteredRoutes.value.reduce((sum, route) => sum + (route.avg_delay_minutes || 0), 0)
  return total / filteredRoutes.value.length
})

// 方法
const fetchData = async () => {
  try {
    const params = {
      limit: 1000,
      days: filters.value.timeRange !== 'custom' ? parseInt(filters.value.timeRange) : undefined
    }

    if (filters.value.timeRange === 'custom' && filters.value.customDateRange) {
      const [start, end] = filters.value.customDateRange
      params.startDate = start.toISOString().split('T')[0]
      params.endDate = end.toISOString().split('T')[0]
    }

    await punctualityStore.fetchRoutePunctuality(params)
  } catch (err) {
    ElMessage.error(t('routePunctuality.fetchFailed'))
  }
}

const refreshData = async () => {
  try {
    refreshing.value = true
    await punctualityStore.refreshPunctualityData()
    await fetchData()
    ElMessage.success(t('common.refreshSuccess'))
  } catch (err) {
    ElMessage.error(t('common.refreshFailed'))
  } finally {
    refreshing.value = false
  }
}

const handleSearch = () => {
  pagination.value.currentPage = 1
}

const handleTimeRangeChange = () => {
  fetchData()
}

const handleCustomDateChange = () => {
  if (filters.value.customDateRange) {
    fetchData()
  }
}

const handleSortChange = () => {
  pagination.value.currentPage = 1
}

const handleTableSort = ({ prop, order }) => {
  // 处理表格排序
  let sortBy = 'punctuality_desc'

  if (prop === 'avg_punctuality_rate') {
    sortBy = order === 'ascending' ? 'punctuality_asc' : 'punctuality_desc'
  } else if (prop === 'total_trips') {
    sortBy = order === 'ascending' ? 'trips_asc' : 'trips_desc'
  } else if (prop === 'avg_delay_minutes') {
    sortBy = order === 'ascending' ? 'delay_asc' : 'delay_desc'
  }

  filters.value.sortBy = sortBy
}

const handlePageSizeChange = (size) => {
  pagination.value.pageSize = size
  pagination.value.currentPage = 1
}

const handleCurrentChange = (page) => {
  pagination.value.currentPage = page
}

const viewRouteDetail = (route) => {
  router.push({ name: 'route-punctuality-detail', params: { routeId: route.route_id } })
}

const exportData = () => {
  const routes = filteredRoutes.value
  if (!routes.length) {
    ElMessage.warning(t('routePunctuality.noExportData'))
    return
  }

  // CSV 表头
  const headers = [
    t('routePunctuality.csvRouteId'), t('routePunctuality.csvShortName'), t('routePunctuality.csvLongName'),
    t('routePunctuality.csvRate'), t('routePunctuality.csvTrips'), t('routePunctuality.csvOnTime'),
    t('routePunctuality.csvEarly'), t('routePunctuality.csvLate'), t('routePunctuality.csvVeryLate'),
    t('routePunctuality.csvAvgDelay'), t('routePunctuality.csvMaxDelay'), t('routePunctuality.csvLastStat')
  ]
  const rows = routes.map(r => [
    r.route_id,
    r.route_short_name || '',
    r.route_long_name || '',
    (r.avg_punctuality_rate || 0).toFixed(1),
    r.total_trips || 0,
    r.on_time_trips || 0,
    r.early_trips || 0,
    r.late_trips || 0,
    r.very_late_trips || 0,
    (r.avg_delay_minutes || 0).toFixed(2),
    (r.max_delay_minutes || 0).toFixed(2),
    r.last_stat_date || ''
  ])

  // 生成 CSV 内容（带 BOM 以支持中文 Excel 打开）
  const csvContent = '\uFEFF' + [headers, ...rows].map(row =>
    row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(',')
  ).join('\n')

  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `route-punctuality_${new Date().toISOString().slice(0, 10)}.csv`
  link.click()
  URL.revokeObjectURL(url)

  ElMessage.success(t('routePunctuality.exported', { count: routes.length }))
}

// 工具方法
const formatPunctualityRate = (rate) => {
  return `${(rate || 0).toFixed(1)}%`
}

const formatDelay = (minutes) => {
  if (!minutes || minutes === 0) return t('format.onTimeLabel')
  if (minutes < 0) return t('format.earlyLabel', { n: Math.abs(minutes).toFixed(1) })
  return t('format.delayLabel', { n: minutes.toFixed(1) })
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

const truncateText = (text, maxLength) => {
  if (!text) return '-'
  return text.length > maxLength ? text.substring(0, maxLength) + '...' : text
}

const getPercentage = (value, total) => {
  if (!total || total === 0) return 0
  return Math.round((value || 0) / total * 100)
}

// 计算四项分布，用最大余数法保证总和精确为 100%
const getDistribution = (route) => {
  if (!route) return { onTime: 0, late: 0, veryLate: 0, early: 0 }
  const onTime = route.on_time_trips || 0
  const late = route.late_trips || 0
  const veryLate = route.very_late_trips || 0
  const early = route.early_trips || 0
  const actualTotal = onTime + late + veryLate + early
  if (actualTotal === 0) return { onTime: 0, late: 0, veryLate: 0, early: 0 }
  const values = [
    { key: 'onTime', raw: onTime / actualTotal * 100 },
    { key: 'late', raw: late / actualTotal * 100 },
    { key: 'veryLate', raw: veryLate / actualTotal * 100 },
    { key: 'early', raw: early / actualTotal * 100 },
  ]
  values.forEach(v => { v.floor = Math.floor(v.raw); v.remainder = v.raw - v.floor })
  let sum = values.reduce((s, v) => s + v.floor, 0)
  const remaining = 100 - sum
  values.sort((a, b) => b.remainder - a.remainder)
  for (let i = 0; i < remaining; i++) values[i].floor += 1
  const result = {}
  values.forEach(v => { result[v.key] = v.floor })
  return result
}

const getProgressColor = (rate) => {
  if (rate >= 90) return '#67C23A'  // 绿色
  if (rate >= 75) return '#409EFF'  // 蓝色
  if (rate >= 60) return '#E6A23C'  // 黄色
  return '#F56C6C'  // 红色
}

const getDelayClass = (delay) => {
  if (delay < 0) return 'delay-good'   // 早到，绿色
  if (delay <= 2) return 'delay-good'
  if (delay <= 5) return 'delay-warning'
  return 'delay-bad'
}

// 生命周期
onMounted(() => {
  fetchData()
})

// 切换地区时重新加载
watch(() => regionStore.selectedRegion, () => {
  fetchData()
})

// 监听筛选条件变化
watch(() => filters.value.sortBy, () => {
  pagination.value.currentPage = 1
})
</script>

<style scoped>
.route-punctuality {
  padding: 20px;
  background: #f5f7fa;
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
  padding: 24px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.header-content h1 {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 28px;
  font-weight: 600;
}

.header-content p {
  margin: 0;
  color: #606266;
  font-size: 14px;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.filter-card {
  margin-bottom: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.stats-overview {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
  padding: 20px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.stat-item {
  flex: 1;
  text-align: center;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: #6b7280;
}

.routes-table-card {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.table-header h3 {
  margin: 0;
  color: #1f2937;
  font-size: 16px;
  font-weight: 600;
}

.table-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.page-size-label {
  font-size: 12px;
  color: #6b7280;
}

.route-name .route-short {
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 2px;
}

.route-name .route-long {
  font-size: 12px;
  color: #6b7280;
}

.punctuality-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.rate-text {
  font-weight: 600;
  color: #1f2937;
  min-width: 45px;
}

.trips-count {
  font-weight: 500;
  color: #374151;
}

.delay-cell {
  display: flex;
  align-items: center;
  gap: 6px;
}

.delay-icon {
  font-size: 16px;
}

.delay-icon.delay-good {
  color: #10b981;
}

.delay-icon.delay-warning {
  color: #f59e0b;
}

.delay-icon.delay-bad {
  color: #ef4444;
}

.max-delay {
  color: #ef4444;
  font-weight: 500;
}

.punctuality-distribution {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.dist-item {
  display: flex;
  align-items: center;
  gap: 6px;
  height: 16px;
}

.dist-name {
  font-size: 11px;
  font-weight: 500;
  min-width: 48px;
  flex-shrink: 0;
  text-align: right;
}

.dist-name.on-time-text { color: #10b981; }
.dist-name.late-text { color: #f59e0b; }
.dist-name.very-late-text { color: #ef4444; }
.dist-name.early-text { color: #3b82f6; }

.dist-bar {
  height: 100%;
  border-radius: 2px;
  min-width: 2px;
}

.dist-bar.on-time {
  background-color: #10b981;
}

.dist-bar.late {
  background-color: #f59e0b;
}

.dist-bar.very-late {
  background-color: #ef4444;
}

.dist-bar.early {
  background-color: #3b82f6;
}

.dist-label {
  font-size: 10px;
  color: #6b7280;
  min-width: 25px;
  text-align: right;
}

.stat-date {
  font-size: 12px;
  color: #6b7280;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    gap: 16px;
  }

  .header-actions {
    width: 100%;
    justify-content: flex-end;
  }

  .stats-overview {
    flex-wrap: wrap;
  }

  .stat-item {
    flex: 1 1 50%;
    margin-bottom: 16px;
  }

  .table-header {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }

  .table-actions {
    justify-content: center;
  }
}
</style>