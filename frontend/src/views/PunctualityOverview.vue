<template>
  <div class="punctuality-overview">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <h1>准点率分析系统</h1>
        <p>实时监控公交准点率，提供全面的数据分析和可视化</p>
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

    <!-- 错误提示 -->
    <el-alert
      v-if="error"
      :title="error"
      type="error"
      show-icon
      closable
      @close="clearError"
      class="error-alert"
    />

    <!-- 系统概览卡片 -->
    <div class="overview-cards" v-loading="loading">
      <!-- 总体统计卡片 -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-icon">
            <el-icon><TrendCharts /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ systemStats.totalRoutes }}</div>
            <div class="stat-label">运营线路</div>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon">
            <el-icon><Bus /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ systemStats.totalTrips.toLocaleString() }}</div>
            <div class="stat-label">总班次</div>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon success">
            <el-icon><CircleCheck /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ formatPunctualityRate(systemStats.systemPunctualityRate) }}</div>
            <div class="stat-label">系统准点率</div>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon warning">
            <el-icon><Timer /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ systemStats.systemAvgDelay.toFixed(1) }}分钟</div>
            <div class="stat-label">平均延误</div>
          </div>
        </div>
      </div>

      <!-- 实时状态卡片 -->
      <div class="realtime-cards">
        <div class="realtime-card">
          <h3>实时车辆</h3>
          <div class="realtime-value">{{ realtimeSummary.active_vehicles || 0 }}</div>
          <div class="realtime-label">辆</div>
        </div>

        <div class="realtime-card">
          <h3>最近延误</h3>
          <div class="realtime-value">{{ realtimeSummary.recent_delays || 0 }}</div>
          <div class="realtime-label">条记录</div>
        </div>

        <div class="realtime-card">
          <h3>平均延误</h3>
          <div class="realtime-value">{{ (realtimeSummary.avg_delay_minutes || 0).toFixed(1) }}</div>
          <div class="realtime-label">分钟</div>
        </div>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="main-content" v-loading="loading">
      <el-row :gutter="24">
        <!-- 左侧：线路排名 -->
        <el-col :span="12">
          <el-card class="ranking-card">
            <template #header>
              <div class="card-header">
                <h3>准点率排名</h3>
                <el-select v-model="rankingType" @change="fetchOverviewData">
                  <el-option label="最佳表现" value="best" />
                  <el-option label="最差表现" value="worst" />
                </el-select>
              </div>
            </template>

            <div class="ranking-list" v-if="hasPunctualityData">
              <div
                v-for="(route, index) in currentRanking"
                :key="route.route_id"
                class="ranking-item"
                :class="{ 'best': rankingType === 'best', 'worst': rankingType === 'worst' }"
              >
                <div class="rank-number">{{ index + 1 }}</div>
                <div class="route-info">
                  <div class="route-name">{{ route.route_short_name || route.route_id }}</div>
                  <div class="route-detail">{{ route.route_long_name }}</div>
                </div>
                <div class="punctuality-rate">
                  <div class="rate-value">{{ formatPunctualityRate(route.avg_punctuality_rate) }}</div>
                  <div class="trips-count">{{ route.total_trips }}班次</div>
                </div>
              </div>
            </div>

            <el-empty
              v-else
              description="暂无数据"
              :image-size="100"
            />
          </el-card>
        </el-col>

        <!-- 右侧：时段分析 -->
        <el-col :span="12">
          <el-card class="chart-card">
            <template #header>
              <div class="card-header">
                <h3>时段准点率分析</h3>
                <el-date-picker
                  v-model="selectedDate"
                  type="date"
                  placeholder="选择日期"
                  @change="fetchHourlyData"
                  :disabled-date="disableFutureDates"
                />
              </div>
            </template>

            <div class="chart-container">
              <!-- 时段准点率柱状图 -->
              <div class="hourly-chart">
                <div
                  v-for="hour in hourlyData"
                  :key="hour.hour"
                  class="hour-bar"
                >
                  <div class="hour-label">{{ hour.hour_label }}</div>
                  <div class="bar-container">
                    <div
                      class="bar-fill"
                      :style="{
                        width: `${Math.min(hour.punctuality_rate, 100)}%`,
                        backgroundColor: getBarColor(hour.punctuality_rate)
                      }"
                    />
                  </div>
                  <div class="hour-rate">{{ formatPunctualityRate(hour.punctuality_rate) }}</div>
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 数据状态提示 -->
      <el-card v-if="!hasPunctualityData" class="data-status-card">
        <el-empty description="暂无准点率数据">
          <template #description>
            <p>系统正在收集数据中...</p>
            <p class="status-hint">数据来源：GTFS Realtime API</p>
            <p class="status-hint">更新频率：每2分钟</p>
          </template>
          <el-button type="primary" @click="startDataCollection">
            开始数据收集
          </el-button>
        </el-empty>
      </el-card>
    </div>

    <!-- 底部数据信息 -->
    <div class="footer-info" v-if="hasPunctualityData">
      <div class="data-source">
        <el-icon><InfoFilled /></el-icon>
        <span>数据来源：511 SF Bay GTFS Realtime</span>
      </div>
      <div class="update-time">
        <el-icon><Clock /></el-icon>
        <span>最后更新：{{ lastUpdateTime }}</span>
      </div>
      <div class="analysis-period">
        <el-icon><Calendar /></el-icon>
        <span>分析周期：{{ punctualityOverview.analysis_period }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { usePunctualityStore } from '../stores/punctualityStore'
import {
  Refresh, Download, TrendCharts, Bus, CircleCheck,
  Timer, InfoFilled, Clock, Calendar
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'

// Store
const punctualityStore = usePunctualityStore()

// 响应式数据
const rankingType = ref('best')
const selectedDate = ref(new Date())
const refreshTimer = ref(null)

// 计算属性
const loading = computed(() => punctualityStore.loading)
const error = computed(() => punctualityStore.error)
const systemStats = computed(() => punctualityStore.systemStats)
const hasRealtimeData = computed(() => punctualityStore.hasRealtimeData)
const hasPunctualityData = computed(() => punctualityStore.hasPunctualityData)
const punctualityOverview = computed(() => punctualityStore.punctualityOverview)
const realtimeSummary = computed(() => punctualityStore.realtimeSummary)
const hourlyData = computed(() => punctualityStore.hourlyPunctuality)

const currentRanking = computed(() => {
  const overview = punctualityOverview.value
  return rankingType.value === 'best' ? overview.best_routes : overview.worst_routes
})

const lastUpdateTime = computed(() => {
  if (!punctualityOverview.value.latest_data_date) return '暂无数据'
  return new Date(punctualityOverview.value.latest_data_date).toLocaleString('zh-CN')
})

// 方法
const fetchOverviewData = async () => {
  try {
    await punctualityStore.fetchAllPunctualityData()
  } catch (err) {
    ElMessage.error('获取数据失败')
  }
}

const fetchHourlyData = async () => {
  try {
    const dateStr = selectedDate.value.toISOString().split('T')[0]
    await punctualityStore.fetchHourlyPunctuality({ date: dateStr })
  } catch (err) {
    ElMessage.error('获取时段数据失败')
  }
}

const refreshData = async () => {
  try {
    await Promise.all([
      fetchOverviewData(),
      fetchHourlyData()
    ])
    ElMessage.success('数据刷新成功')
  } catch (err) {
    ElMessage.error('数据刷新失败')
  }
}

const exportData = async () => {
  try {
    await ElMessageBox.confirm('确定要导出准点率报表吗？', '导出确认', {
      type: 'warning'
    })

    // 这里可以调用导出API
    ElMessage.success('导出功能开发中...')
  } catch {
    // 用户取消
  }
}

const startDataCollection = () => {
  ElMessage.info('请联系管理员启动数据收集服务')
}

const clearError = () => {
  punctualityStore.clearError()
}

const formatPunctualityRate = (rate) => {
  return `${(rate || 0).toFixed(1)}%`
}

const getBarColor = (rate) => {
  if (rate >= 90) return '#67C23A'  // 绿色 - 优秀
  if (rate >= 75) return '#409EFF'  // 蓝色 - 良好
  if (rate >= 60) return '#E6A23C'  // 黄色 - 一般
  return '#F56C6C'  // 红色 - 较差
}

const disableFutureDates = (time) => {
  return time.getTime() > Date.now()
}

// 定时刷新
const startAutoRefresh = () => {
  refreshTimer.value = setInterval(() => {
    refreshData()
  }, 5 * 60 * 1000) // 每5分钟刷新一次
}

const stopAutoRefresh = () => {
  if (refreshTimer.value) {
    clearInterval(refreshTimer.value)
    refreshTimer.value = null
  }
}

// 生命周期
onMounted(async () => {
  // 初始化数据
  await fetchOverviewData()
  await fetchHourlyData()

  // 启动自动刷新
  startAutoRefresh()
})

onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<style scoped>
.punctuality-overview {
  padding: 20px;
  background: #f5f7fa;
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
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

.error-alert {
  margin-bottom: 20px;
}

.overview-cards {
  display: flex;
  gap: 20px;
  margin-bottom: 24px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  flex: 1;
}

.stat-card {
  display: flex;
  align-items: center;
  padding: 20px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  transition: transform 0.2s, box-shadow 0.2s;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.12);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f0f9ff;
  color: #0284c7;
  margin-right: 16px;
  font-size: 24px;
}

.stat-icon.success {
  background: #f0f9ff;
  color: #10b981;
}

.stat-icon.warning {
  background: #fef3c7;
  color: #f59e0b;
}

.stat-content .stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #1f2937;
  line-height: 1;
  margin-bottom: 4px;
}

.stat-content .stat-label {
  font-size: 14px;
  color: #6b7280;
}

.realtime-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  min-width: 320px;
}

.realtime-card {
  background: white;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  text-align: center;
}

.realtime-card h3 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #6b7280;
  font-weight: 500;
}

.realtime-value {
  font-size: 32px;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 4px;
}

.realtime-label {
  font-size: 12px;
  color: #9ca3af;
}

.main-content {
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  margin: 0;
  color: #1f2937;
  font-size: 16px;
  font-weight: 600;
}

.ranking-card,
.chart-card {
  margin-bottom: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.ranking-list {
  max-height: 400px;
  overflow-y: auto;
}

.ranking-item {
  display: flex;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid #f3f4f6;
  transition: background-color 0.2s;
}

.ranking-item:hover {
  background-color: #f9fafb;
}

.ranking-item:last-child {
  border-bottom: none;
}

.rank-number {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 14px;
  margin-right: 16px;
  background: #f3f4f6;
  color: #6b7280;
}

.ranking-item.best .rank-number {
  background: #dcfce7;
  color: #166534;
}

.ranking-item.worst .rank-number {
  background: #fee2e2;
  color: #991b1b;
}

.route-info {
  flex: 1;
}

.route-name {
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 2px;
}

.route-detail {
  font-size: 12px;
  color: #6b7280;
}

.punctuality-rate {
  text-align: right;
}

.rate-value {
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 2px;
}

.trips-count {
  font-size: 12px;
  color: #6b7280;
}

.chart-container {
  height: 400px;
  overflow: hidden;
}

.hourly-chart {
  height: 100%;
  overflow-y: auto;
}

.hour-bar {
  display: flex;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #f3f4f6;
}

.hour-label {
  width: 60px;
  font-size: 12px;
  color: #6b7280;
  text-align: right;
  margin-right: 12px;
}

.bar-container {
  flex: 1;
  height: 24px;
  background: #f3f4f6;
  border-radius: 12px;
  overflow: hidden;
  margin-right: 12px;
}

.bar-fill {
  height: 100%;
  transition: width 0.3s ease;
  border-radius: 12px;
}

.hour-rate {
  width: 60px;
  text-align: right;
  font-weight: 600;
  color: #1f2937;
  font-size: 12px;
}

.data-status-card {
  text-align: center;
  margin-top: 24px;
}

.status-hint {
  color: #6b7280;
  font-size: 12px;
  margin: 4px 0;
}

.footer-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: white;
  border-radius: 8px;
  font-size: 12px;
  color: #6b7280;
}

.footer-info > div {
  display: flex;
  align-items: center;
  gap: 6px;
}

@media (max-width: 1200px) {
  .overview-cards {
    flex-direction: column;
  }

  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .realtime-cards {
    grid-template-columns: repeat(3, 1fr);
  }
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

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .realtime-cards {
    grid-template-columns: 1fr;
  }

  .footer-info {
    flex-direction: column;
    gap: 8px;
    text-align: center;
  }
}
</style>