<template>
  <div class="stop-punctuality">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <el-button :icon="ArrowLeft" @click="goHome" style="margin-bottom:8px">返回首页</el-button>
        <h1>站点准点率分析</h1>
        <p>分析各个公交站点的准点率情况和延误分布</p>
      </div>
      <div class="header-actions">
        <el-button
          type="primary"
          :loading="refreshing"
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
        <div class="stat-label">总访访问数</div>
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

        <el-table-column prop="total_visits" label="访问次数" width="120" sortable="custom">
          <template #default="{ row }">
            <span class="visits-count">{{ (row.total_visits || 0).toLocaleString() }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="avg_delay_minutes" label="平均延误" width="150" sortable="custom" align="center">
          <template #default="{ row }">
            <div class="delay-cell">
              <el-icon class="delay-icon" :class="getDelayClass(row.avg_delay_minutes || 0)">
                <Clock />
              </el-icon>
              <span style="white-space: nowrap;">{{ formatDelay(row.avg_delay_minutes || 0) }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="max_delay_minutes" label="最大延误" width="120" sortable="custom">
          <template #default="{ row }">
            <span class="max-delay">{{ formatDelay(row.max_delay_minutes || 0) }}</span>
          </template>
        </el-table-column>

        <el-table-column min-width="260">
          <template #header>
            <span style="padding-left: 48px;">准点分布</span>
          </template>
          <template #default="{ row }">
            <div class="punctuality-distribution">
              <div class="dist-item" :title="`准点: ${row.on_time_visits || 0}次`">
                <span class="dist-name on-time-text">准点</span>
                <div class="dist-bar on-time" :style="{ width: getDistribution(row).onTime + '%' }"></div>
                <span class="dist-label">{{ getDistribution(row).onTime }}%</span>
              </div>
              <div class="dist-item" :title="`延误: ${row.late_visits || 0}次`">
                <span class="dist-name late-text">延误</span>
                <div class="dist-bar late" :style="{ width: getDistribution(row).late + '%' }"></div>
                <span class="dist-label">{{ getDistribution(row).late }}%</span>
              </div>
              <div class="dist-item" :title="`严重延误: ${row.very_late_visits || 0}次`">
                <span class="dist-name very-late-text">严重延误</span>
                <div class="dist-bar very-late" :style="{ width: getDistribution(row).veryLate + '%' }"></div>
                <span class="dist-label">{{ getDistribution(row).veryLate }}%</span>
              </div>
              <div class="dist-item" :title="`提前: ${row.early_visits || 0}次`">
                <span class="dist-name early-text">提前</span>
                <div class="dist-bar early" :style="{ width: getDistribution(row).early + '%' }"></div>
                <span class="dist-label">{{ getDistribution(row).early }}%</span>
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
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { usePunctualityStore } from '../stores/punctualityStore'
import { useRegionStore } from '@/stores/regionStore'
import {
  Refresh, Download, Search, Clock, Location, MapLocation, ArrowLeft
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

// Store
const router = useRouter()
const punctualityStore = usePunctualityStore()
const regionStore = useRegionStore()

const goHome = () => { window.location.href = '/' }

// 响应式数据
const loading = computed(() => punctualityStore.loading)
const refreshing = ref(false)
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
      limit: 10000,
      days: parseInt(filters.value.timeRange)
    }

    await punctualityStore.fetchStopPunctuality(params)
  } catch (err) {
    ElMessage.error('获取站点准点率数据失败')
  }
}

const refreshData = async () => {
  try {
    refreshing.value = true
    await punctualityStore.refreshPunctualityData()
    await fetchData()
    ElMessage.success('数据刷新成功')
  } catch (err) {
    ElMessage.error('刷新数据失败')
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
  router.push({ name: 'stop-punctuality-detail', params: { stopId: stop.stop_id } })
}

const viewOnMap = (stop) => {
  router.push({ name: 'stop-detail', params: { id: stop.stop_id } })
}

const exportData = () => {
  const stops = filteredStops.value
  if (!stops.length) {
    ElMessage.warning('没有可导出的数据')
    return
  }

  const headers = ['站点ID', '站点名称', '纬度', '经度', '准点率(%)', '总访问次数', '准点次数', '提前次数', '延误次数', '严重延误次数', '平均延误(分钟)', '最大延误(分钟)', '最后统计日期']
  const rows = stops.map(s => [
    s.stop_id,
    s.stop_name || '',
    s.stop_lat || '',
    s.stop_lon || '',
    (s.avg_punctuality_rate || 0).toFixed(1),
    s.total_visits || 0,
    s.on_time_visits || 0,
    s.early_visits || 0,
    s.late_visits || 0,
    s.very_late_visits || 0,
    (s.avg_delay_minutes || 0).toFixed(2),
    (s.max_delay_minutes || 0).toFixed(2),
    s.last_stat_date || ''
  ])

  const csvContent = '\uFEFF' + [headers, ...rows].map(row =>
    row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(',')
  ).join('\n')

  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `站点准点率_${new Date().toISOString().slice(0, 10)}.csv`
  link.click()
  URL.revokeObjectURL(url)

  ElMessage.success(`已导出 ${stops.length} 个站点数据`)
}

// 工具方法
const formatPunctualityRate = (rate) => {
  return `${(rate || 0).toFixed(1)}%`
}

const formatDelay = (minutes) => {
  if (!minutes || minutes === 0) return '准点'
  if (minutes < 0) return `提前 ${Math.abs(minutes).toFixed(1)} 分钟`
  return `延误 ${minutes.toFixed(1)} 分钟`
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

// 计算四项分布，用最大余数法保证总和精确为 100%
const getDistribution = (stop) => {
  if (!stop) return { onTime: 0, late: 0, veryLate: 0, early: 0 }
  const onTime = stop.on_time_visits || 0
  const late = stop.late_visits || 0
  const veryLate = stop.very_late_visits || 0
  const early = stop.early_visits || 0
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
  if (delay < 0) return 'delay-good'
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