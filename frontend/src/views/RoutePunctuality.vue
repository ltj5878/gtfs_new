<template>
  <div class="route-punctuality">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <h1>线路准点率分析</h1>
        <p>详细分析每条公交线路的准点率和延误情况</p>
      </div>
      <div class="header-actions">
        <el-button
          type="primary"
          :loading="loading"
          @click="refreshData"
          :icon="Refresh"
        >
          刷新数据
        </el-button>
        <el-button
          @click="exportData"
          :icon="Download"
        >
          导出报表
        </el-button>
      </div>
    </div>

    <!-- 筛选器 -->
    <el-card class="filter-card">
      <el-row :gutter="16">
        <el-col :span="6">
          <el-input
            v-model="filters.routeName"
            placeholder="搜索线路名称"
            :prefix-icon="Search"
            clearable
            @input="handleSearch"
          />
        </el-col>
        <el-col :span="6">
          <el-select
            v-model="filters.timeRange"
            placeholder="时间范围"
            @change="handleTimeRangeChange"
            style="width: 100%"
          >
            <el-option label="最近7天" value="7" />
            <el-option label="最近30天" value="30" />
            <el-option label="最近90天" value="90" />
            <el-option label="自定义" value="custom" />
          </el-select>
        </el-col>
        <el-col :span="6" v-if="filters.timeRange === 'custom'">
          <el-date-picker
            v-model="filters.customDateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            @change="handleCustomDateChange"
            style="width: 100%"
          />
        </el-col>
        <el-col :span="6">
          <el-select
            v-model="filters.sortBy"
            placeholder="排序方式"
            @change="handleSortChange"
            style="width: 100%"
          >
            <el-option label="准点率从高到低" value="punctuality_desc" />
            <el-option label="准点率从低到高" value="punctuality_asc" />
            <el-option label="班次从多到少" value="trips_desc" />
            <el-option label="班次从少到多" value="trips_asc" />
            <el-option label="延误从少到多" value="delay_asc" />
            <el-option label="延误从多到少" value="delay_desc" />
          </el-select>
        </el-col>
      </el-row>
    </el-card>

    <!-- 统计概览 -->
    <div class="stats-overview" v-loading="loading">
      <div class="stat-item">
        <div class="stat-value">{{ filteredRoutes.length }}</div>
        <div class="stat-label">显示线路</div>
      </div>
      <div class="stat-item">
        <div class="stat-value">{{ formatPunctualityRate(averagePunctualityRate) }}</div>
        <div class="stat-label">平均准点率</div>
      </div>
      <div class="stat-item">
        <div class="stat-value">{{ totalTrips.toLocaleString() }}</div>
        <div class="stat-label">总班次</div>
      </div>
      <div class="stat-item">
        <div class="stat-value">{{ formatDelay(averageDelay) }}</div>
        <div class="stat-label">平均延误</div>
      </div>
    </div>

    <!-- 线路列表 -->
    <el-card class="routes-table-card">
      <template #header>
        <div class="table-header">
          <h3>线路列表</h3>
          <div class="table-actions">
            <el-input-number
              v-model="pagination.pageSize"
              :min="10"
              :max="100"
              :step="10"
              @change="handlePageSizeChange"
              style="width: 120px"
            />
            <span class="page-size-label">条/页</span>
          </div>
        </div>
      </template>

      <el-table
        :data="paginatedRoutes"
        v-loading="loading"
        stripe
        @sort-change="handleTableSort"
      >
        <el-table-column prop="route_short_name" label="线路" width="120" sortable>
          <template #default="{ row }">
            <div class="route-name">
              <div class="route-short">{{ row.route_short_name || row.route_id }}</div>
              <div class="route-long">{{ truncateText(row.route_long_name, 20) }}</div>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="avg_punctuality_rate" label="准点率" width="120" sortable="custom">
          <template #default="{ row }">
            <div class="punctuality-cell">
              <el-progress
                :percentage="row.avg_punctuality_rate || 0"
                :color="getProgressColor(row.avg_punctuality_rate || 0)"
                :stroke-width="8"
                :show-text="false"
              />
              <span class="rate-text">{{ formatPunctualityRate(row.avg_punctuality_rate) }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="total_trips" label="总班次" width="100" sortable="custom">
          <template #default="{ row }">
            <span class="trips-count">{{ (row.total_trips || 0).toLocaleString() }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="avg_delay_minutes" label="平均延误" width="120" sortable="custom">
          <template #default="{ row }">
            <div class="delay-cell">
              <el-icon class="delay-icon" :class="getDelayClass(row.avg_delay_minutes || 0)">
                <Clock />
              </el-icon>
              <span>{{ formatDelay(row.avg_delay_minutes || 0) }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="max_delay_minutes" label="最大延误" width="120" sortable="custom">
          <template #default="{ row }">
            <span class="max-delay">{{ formatDelay(row.max_delay_minutes || 0) }}</span>
          </template>
        </el-table-column>

        <el-table-column label="准点分布" width="200">
          <template #default="{ row }">
            <div class="punctuality-distribution">
              <div class="dist-item" :title="`准点: ${row.on_time_trips || 0}班`">
                <div class="dist-bar on-time" :style="{ width: getPercentage(row.on_time_trips, row.total_trips) + '%' }"></div>
                <span class="dist-label">{{ getPercentage(row.on_time_trips, row.total_trips) }}%</span>
              </div>
              <div class="dist-item" :title="`延误: ${row.late_trips || 0}班`">
                <div class="dist-bar late" :style="{ width: getPercentage(row.late_trips, row.total_trips) + '%' }"></div>
                <span class="dist-label">{{ getPercentage(row.late_trips, row.total_trips) }}%</span>
              </div>
              <div class="dist-item" :title="`严重延误: ${row.very_late_trips || 0}班`">
                <div class="dist-bar very-late" :style="{ width: getPercentage(row.very_late_trips, row.total_trips) + '%' }"></div>
                <span class="dist-label">{{ getPercentage(row.very_late_trips, row.total_trips) }}%</span>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="last_stat_date" label="最后统计" width="120">
          <template #default="{ row }">
            <span class="stat-date">{{ formatDate(row.last_stat_date) }}</span>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              link
              size="small"
              @click="viewRouteDetail(row)"
            >
              详情
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

    <!-- 线路详情弹窗 -->
    <el-dialog
      v-model="detailVisible"
      title="线路准点率详情"
      width="800px"
      destroy-on-close
    >
      <div v-if="selectedRoute" v-loading="detailLoading">
        <div class="route-detail-header">
          <h2>{{ selectedRoute.route_short_name || selectedRoute.route_id }}</h2>
          <p>{{ selectedRoute.route_long_name }}</p>
        </div>

        <el-row :gutter="24" class="detail-stats">
          <el-col :span="6">
            <div class="detail-stat-card">
              <div class="detail-stat-value">{{ formatPunctualityRate(selectedRoute.avg_punctuality_rate) }}</div>
              <div class="detail-stat-label">准点率</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="detail-stat-card">
              <div class="detail-stat-value">{{ (selectedRoute.total_trips || 0).toLocaleString() }}</div>
              <div class="detail-stat-label">总班次</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="detail-stat-card">
              <div class="detail-stat-value">{{ formatDelay(selectedRoute.avg_delay_minutes || 0) }}</div>
              <div class="detail-stat-label">平均延误</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="detail-stat-card">
              <div class="detail-stat-value">{{ formatDelay(selectedRoute.max_delay_minutes || 0) }}</div>
              <div class="detail-stat-label">最大延误</div>
            </div>
          </el-col>
        </el-row>

        <el-divider />

        <!-- 准点分布图表 -->
        <div class="punctuality-chart">
          <h4>准点率分布</h4>
          <div class="chart-bars">
            <div class="chart-bar">
              <div class="bar-label">准点</div>
              <div class="bar-container">
                <div class="bar-fill on-time" :style="{ width: getPercentage(selectedRoute.on_time_trips, selectedRoute.total_trips) + '%' }"></div>
              </div>
              <div class="bar-value">{{ getPercentage(selectedRoute.on_time_trips, selectedRoute.total_trips) }}%</div>
            </div>
            <div class="chart-bar">
              <div class="bar-label">延误</div>
              <div class="bar-container">
                <div class="bar-fill late" :style="{ width: getPercentage(selectedRoute.late_trips, selectedRoute.total_trips) + '%' }"></div>
              </div>
              <div class="bar-value">{{ getPercentage(selectedRoute.late_trips, selectedRoute.total_trips) }}%</div>
            </div>
            <div class="chart-bar">
              <div class="bar-label">严重延误</div>
              <div class="bar-container">
                <div class="bar-fill very-late" :style="{ width: getPercentage(selectedRoute.very_late_trips, selectedRoute.total_trips) + '%' }"></div>
              </div>
              <div class="bar-value">{{ getPercentage(selectedRoute.very_late_trips, selectedRoute.total_trips) }}%</div>
            </div>
            <div class="chart-bar">
              <div class="bar-label">提前</div>
              <div class="bar-container">
                <div class="bar-fill early" :style="{ width: getPercentage(selectedRoute.early_trips, selectedRoute.total_trips) + '%' }"></div>
              </div>
              <div class="bar-value">{{ getPercentage(selectedRoute.early_trips, selectedRoute.total_trips) }}%</div>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { usePunctualityStore } from '../stores/punctualityStore'
import {
  Refresh, Download, Search, Clock
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

// Store
const punctualityStore = usePunctualityStore()

// 响应式数据
const loading = computed(() => punctualityStore.loading)
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

const detailVisible = ref(false)
const selectedRoute = ref(null)
const detailLoading = ref(false)

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
        return (b.avg_punctuality_rate || 0) - (a.avg_punctuality_rate || 0)
      case 'punctuality_asc':
        return (a.avg_punctuality_rate || 0) - (b.avg_punctuality_rate || 0)
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
  const total = filteredRoutes.value.reduce((sum, route) => sum + (route.avg_punctuality_rate || 0), 0)
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
    ElMessage.error('获取线路准点率数据失败')
  }
}

const refreshData = async () => {
  await fetchData()
  ElMessage.success('数据刷新成功')
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
  selectedRoute.value = route
  detailVisible.value = true
}

const exportData = () => {
  ElMessage.info('导出功能开发中...')
}

// 工具方法
const formatPunctualityRate = (rate) => {
  return `${(rate || 0).toFixed(1)}%`
}

const formatDelay = (minutes) => {
  if (!minutes) return '0分钟'
  return `${minutes.toFixed(1)}分钟`
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

const getProgressColor = (rate) => {
  if (rate >= 90) return '#67C23A'  // 绿色
  if (rate >= 75) return '#409EFF'  // 蓝色
  if (rate >= 60) return '#E6A23C'  // 黄色
  return '#F56C6C'  // 红色
}

const getDelayClass = (delay) => {
  if (delay <= 2) return 'delay-good'
  if (delay <= 5) return 'delay-warning'
  return 'delay-bad'
}

// 生命周期
onMounted(() => {
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
  gap: 8px;
  height: 16px;
}

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

/* 详情弹窗样式 */
.route-detail-header {
  text-align: center;
  margin-bottom: 24px;
}

.route-detail-header h2 {
  margin: 0 0 8px 0;
  color: #1f2937;
  font-size: 24px;
  font-weight: 700;
}

.route-detail-header p {
  margin: 0;
  color: #6b7280;
  font-size: 16px;
}

.detail-stats {
  margin-bottom: 24px;
}

.detail-stat-card {
  text-align: center;
  padding: 16px;
  background: #f9fafb;
  border-radius: 8px;
}

.detail-stat-value {
  font-size: 20px;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 4px;
}

.detail-stat-label {
  font-size: 12px;
  color: #6b7280;
}

.punctuality-chart h4 {
  margin: 0 0 16px 0;
  color: #1f2937;
  font-size: 16px;
  font-weight: 600;
}

.chart-bars {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.chart-bar {
  display: flex;
  align-items: center;
  gap: 12px;
}

.bar-label {
  width: 80px;
  font-size: 14px;
  color: #374151;
  text-align: right;
}

.bar-container {
  flex: 1;
  height: 20px;
  background: #f3f4f6;
  border-radius: 10px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  transition: width 0.3s ease;
  border-radius: 10px;
}

.bar-fill.on-time {
  background-color: #10b981;
}

.bar-fill.late {
  background-color: #f59e0b;
}

.bar-fill.very-late {
  background-color: #ef4444;
}

.bar-fill.early {
  background-color: #3b82f6;
}

.bar-value {
  width: 50px;
  font-weight: 600;
  color: #1f2937;
  text-align: right;
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