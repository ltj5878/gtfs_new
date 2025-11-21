<template>
  <div class="stop-punctuality">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <h1>站点准点率分析</h1>
        <p>分析各个公交站点的准点率情况和延误分布</p>
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
            v-model="filters.stopName"
            placeholder="搜索站点名称"
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
          </el-select>
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
            <el-option label="访问次数从多到少" value="visits_desc" />
            <el-option label="访问次数从少到多" value="visits_asc" />
            <el-option label="延误从少到多" value="delay_asc" />
            <el-option label="延误从多到少" value="delay_desc" />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-select
            v-model="filters.areaFilter"
            placeholder="区域筛选"
            @change="handleAreaFilter"
            clearable
            style="width: 100%"
          >
            <el-option label="市中心" value="downtown" />
            <el-option label="商业区" value="commercial" />
            <el-option label="住宅区" value="residential" />
            <el-option label="郊区" value="suburban" />
          </el-select>
        </el-col>
      </el-row>
    </el-card>

    <!-- 统计概览 -->
    <div class="stats-overview" v-loading="loading">
      <div class="stat-item">
        <div class="stat-value">{{ filteredStops.length }}</div>
        <div class="stat-label">显示站点</div>
      </div>
      <div class="stat-item">
        <div class="stat-value">{{ formatPunctualityRate(averagePunctualityRate) }}</div>
        <div class="stat-label">平均准点率</div>
      </div>
      <div class="stat-item">
        <div class="stat-value">{{ totalVisits.toLocaleString() }}</div>
        <div class="stat-label">总访问次数</div>
      </div>
      <div class="stat-item">
        <div class="stat-value">{{ formatDelay(averageDelay) }}</div>
        <div class="stat-label">平均延误</div>
      </div>
    </div>

    <!-- 站点列表 -->
    <el-card class="stops-table-card">
      <template #header>
        <div class="table-header">
          <h3>站点列表</h3>
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
        :data="paginatedStops"
        v-loading="loading"
        stripe
        @sort-change="handleTableSort"
      >
        <el-table-column prop="stop_name" label="站点名称" min-width="200" sortable>
          <template #default="{ row }">
            <div class="stop-info">
              <div class="stop-name">
                <el-icon><Location /></el-icon>
                {{ row.stop_name }}
              </div>
              <div class="stop-id">ID: {{ row.stop_id }}</div>
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

        <el-table-column prop="total_visits" label="访问次数" width="100" sortable="custom">
          <template #default="{ row }">
            <span class="visits-count">{{ (row.total_visits || 0).toLocaleString() }}</span>
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
              <div class="dist-item" :title="`准点: ${row.on_time_visits || 0}次`">
                <div class="dist-bar on-time" :style="{ width: getPercentage(row.on_time_visits, row.total_visits) + '%' }"></div>
                <span class="dist-label">{{ getPercentage(row.on_time_visits, row.total_visits) }}%</span>
              </div>
              <div class="dist-item" :title="`延误: ${row.late_visits || 0}次`">
                <div class="dist-bar late" :style="{ width: getPercentage(row.late_visits, row.total_visits) + '%' }"></div>
                <span class="dist-label">{{ getPercentage(row.late_visits, row.total_visits) }}%</span>
              </div>
              <div class="dist-item" :title="`严重延误: ${row.very_late_visits || 0}次`">
                <div class="dist-bar very-late" :style="{ width: getPercentage(row.very_late_visits, row.total_visits) + '%' }"></div>
                <span class="dist-label">{{ getPercentage(row.very_late_visits, row.total_visits) }}%</span>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="last_stat_date" label="最后统计" width="120">
          <template #default="{ row }">
            <span class="stat-date">{{ formatDate(row.last_stat_date) }}</span>
          </template>
        </el-table-column>

        <el-table-column label="位置信息" width="150">
          <template #default="{ row }">
            <div class="location-info" v-if="row.stop_lat && row.stop_lon">
              <div class="coords">{{ formatCoordinates(row.stop_lat, row.stop_lon) }}</div>
              <div class="location-actions">
                <el-button type="text" size="small" @click="viewOnMap(row)">
                  <el-icon><MapLocation /></el-icon>
                  地图
                </el-button>
              </div>
            </div>
            <span v-else class="no-location">位置未知</span>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              link
              size="small"
              @click="viewStopDetail(row)"
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
          :total="filteredStops.length"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handlePageSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 站点详情弹窗 -->
    <el-dialog
      v-model="detailVisible"
      title="站点准点率详情"
      width="800px"
      destroy-on-close
    >
      <div v-if="selectedStop" v-loading="detailLoading">
        <div class="stop-detail-header">
          <h2>{{ selectedStop.stop_name }}</h2>
          <p>站点ID: {{ selectedStop.stop_id }}</p>
          <div class="stop-location" v-if="selectedStop.stop_lat && selectedStop.stop_lon">
            <el-icon><Location /></el-icon>
            {{ formatCoordinates(selectedStop.stop_lat, selectedStop.stop_lon) }}
          </div>
        </div>

        <el-row :gutter="24" class="detail-stats">
          <el-col :span="6">
            <div class="detail-stat-card">
              <div class="detail-stat-value">{{ formatPunctualityRate(selectedStop.avg_punctuality_rate) }}</div>
              <div class="detail-stat-label">准点率</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="detail-stat-card">
              <div class="detail-stat-value">{{ (selectedStop.total_visits || 0).toLocaleString() }}</div>
              <div class="detail-stat-label">总访问次数</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="detail-stat-card">
              <div class="detail-stat-value">{{ formatDelay(selectedStop.avg_delay_minutes || 0) }}</div>
              <div class="detail-stat-label">平均延误</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="detail-stat-card">
              <div class="detail-stat-value">{{ formatDelay(selectedStop.max_delay_minutes || 0) }}</div>
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
                <div class="bar-fill on-time" :style="{ width: getPercentage(selectedStop.on_time_visits, selectedStop.total_visits) + '%' }"></div>
              </div>
              <div class="bar-value">{{ getPercentage(selectedStop.on_time_visits, selectedStop.total_visits) }}%</div>
            </div>
            <div class="chart-bar">
              <div class="bar-label">延误</div>
              <div class="bar-container">
                <div class="bar-fill late" :style="{ width: getPercentage(selectedStop.late_visits, selectedStop.total_visits) + '%' }"></div>
              </div>
              <div class="bar-value">{{ getPercentage(selectedStop.late_visits, selectedStop.total_visits) }}%</div>
            </div>
            <div class="chart-bar">
              <div class="bar-label">严重延误</div>
              <div class="bar-container">
                <div class="bar-fill very-late" :style="{ width: getPercentage(selectedStop.very_late_visits, selectedStop.total_visits) + '%' }"></div>
              </div>
              <div class="bar-value">{{ getPercentage(selectedStop.very_late_visits, selectedStop.total_visits) }}%</div>
            </div>
            <div class="chart-bar">
              <div class="bar-label">提前</div>
              <div class="bar-container">
                <div class="bar-fill early" :style="{ width: getPercentage(selectedStop.early_visits, selectedStop.total_visits) + '%' }"></div>
              </div>
              <div class="bar-value">{{ getPercentage(selectedStop.early_visits, selectedStop.total_visits) }}%</div>
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
  Refresh, Download, Search, Clock, Location, MapLocation
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

// Store
const punctualityStore = usePunctualityStore()

// 响应式数据
const loading = computed(() => punctualityStore.loading)
const stopPunctuality = computed(() => punctualityStore.stopPunctuality)

const filters = ref({
  stopName: '',
  timeRange: '7',
  sortBy: 'punctuality_desc',
  areaFilter: ''
})

const pagination = ref({
  currentPage: 1,
  pageSize: 20
})

const detailVisible = ref(false)
const selectedStop = ref(null)
const detailLoading = ref(false)

// 计算属性
const filteredStops = computed(() => {
  let stops = [...(stopPunctuality.value || [])]

  // 按站点名称筛选
  if (filters.value.stopName) {
    const searchTerm = filters.value.stopName.toLowerCase()
    stops = stops.filter(stop =>
      (stop.stop_name?.toLowerCase().includes(searchTerm) ||
       stop.stop_id?.toLowerCase().includes(searchTerm))
    )
  }

  // 排序
  stops.sort((a, b) => {
    switch (filters.value.sortBy) {
      case 'punctuality_desc':
        return (b.avg_punctuality_rate || 0) - (a.avg_punctuality_rate || 0)
      case 'punctuality_asc':
        return (a.avg_punctuality_rate || 0) - (b.avg_punctuality_rate || 0)
      case 'visits_desc':
        return (b.total_visits || 0) - (a.total_visits || 0)
      case 'visits_asc':
        return (a.total_visits || 0) - (b.total_visits || 0)
      case 'delay_desc':
        return (b.avg_delay_minutes || 0) - (a.avg_delay_minutes || 0)
      case 'delay_asc':
        return (a.avg_delay_minutes || 0) - (b.avg_delay_minutes || 0)
      default:
        return 0
    }
  })

  return stops
})

const paginatedStops = computed(() => {
  const start = (pagination.value.currentPage - 1) * pagination.value.pageSize
  const end = start + pagination.value.pageSize
  return filteredStops.value.slice(start, end)
})

const averagePunctualityRate = computed(() => {
  if (filteredStops.value.length === 0) return 0
  const total = filteredStops.value.reduce((sum, stop) => sum + (stop.avg_punctuality_rate || 0), 0)
  return total / filteredStops.value.length
})

const totalVisits = computed(() => {
  return filteredStops.value.reduce((sum, stop) => sum + (stop.total_visits || 0), 0)
})

const averageDelay = computed(() => {
  if (filteredStops.value.length === 0) return 0
  const total = filteredStops.value.reduce((sum, stop) => sum + (stop.avg_delay_minutes || 0), 0)
  return total / filteredStops.value.length
})

// 方法
const fetchData = async () => {
  try {
    const params = {
      limit: 1000,
      days: parseInt(filters.value.timeRange)
    }

    await punctualityStore.fetchStopPunctuality(params)
  } catch (err) {
    ElMessage.error('获取站点准点率数据失败')
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

const handleSortChange = () => {
  pagination.value.currentPage = 1
}

const handleTableSort = ({ prop, order }) => {
  let sortBy = 'punctuality_desc'

  if (prop === 'avg_punctuality_rate') {
    sortBy = order === 'ascending' ? 'punctuality_asc' : 'punctuality_desc'
  } else if (prop === 'total_visits') {
    sortBy = order === 'ascending' ? 'visits_asc' : 'visits_desc'
  } else if (prop === 'avg_delay_minutes') {
    sortBy = order === 'ascending' ? 'delay_asc' : 'delay_desc'
  }

  filters.value.sortBy = sortBy
}

const handleAreaFilter = () => {
  // 区域筛选逻辑
  pagination.value.currentPage = 1
}

const handlePageSizeChange = (size) => {
  pagination.value.pageSize = size
  pagination.value.currentPage = 1
}

const handleCurrentChange = (page) => {
  pagination.value.currentPage = page
}

const viewStopDetail = (stop) => {
  selectedStop.value = stop
  detailVisible.value = true
}

const viewOnMap = (stop) => {
  ElMessage.info('地图功能开发中...')
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

const formatCoordinates = (lat, lng) => {
  if (!lat || !lng) return '未知位置'
  return `${lat.toFixed(4)}, ${lng.toFixed(4)}`
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
.stop-punctuality {
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

.stops-table-card {
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

.stop-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stop-name {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  color: #1f2937;
}

.stop-id {
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

.visits-count {
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

.location-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.coords {
  font-size: 12px;
  color: #6b7280;
}

.location-actions {
  display: flex;
  gap: 4px;
}

.no-location {
  color: #9ca3af;
  font-size: 12px;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

/* 详情弹窗样式 */
.stop-detail-header {
  text-align: center;
  margin-bottom: 24px;
}

.stop-detail-header h2 {
  margin: 0 0 8px 0;
  color: #1f2937;
  font-size: 24px;
  font-weight: 700;
}

.stop-detail-header p {
  margin: 0 0 8px 0;
  color: #6b7280;
  font-size: 16px;
}

.stop-location {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  color: #6b7280;
  font-size: 14px;
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