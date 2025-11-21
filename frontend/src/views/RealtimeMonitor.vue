<template>
  <div class="realtime-monitor">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <h1>实时监控</h1>
        <p>实时监控公交车辆位置和准点情况</p>
      </div>
      <div class="header-actions">
        <div class="auto-refresh-control">
          <el-switch
            v-model="autoRefresh"
            active-text="自动刷新"
            inactive-text="手动刷新"
            @change="toggleAutoRefresh"
          />
          <el-select
            v-model="refreshInterval"
            :disabled="!autoRefresh"
            @change="handleIntervalChange"
            style="width: 120px; margin-left: 12px;"
          >
            <el-option label="10秒" :value="10" />
            <el-option label="30秒" :value="30" />
            <el-option label="1分钟" :value="60" />
            <el-option label="5分钟" :value="300" />
          </el-select>
        </div>
        <el-button
          type="primary"
          :loading="loading"
          @click="refreshData"
          :icon="Refresh"
        >
          立即刷新
        </el-button>
      </div>
    </div>

    <!-- 实时统计卡片 -->
    <div class="realtime-stats" v-loading="loading">
      <div class="stat-card">
        <div class="stat-icon">
          <el-icon><Location /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ realtimeSummary.active_vehicles || 0 }}</div>
          <div class="stat-label">活跃车辆</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon">
          <el-icon><Clock /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ realtimeSummary.recent_delays || 0 }}</div>
          <div class="stat-label">延误记录</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon warning">
          <el-icon><Warning /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ realtimeSummary.routes_with_delays || 0 }}</div>
          <div class="stat-label">延误线路</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon info">
          <el-icon><Timer /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ (realtimeSummary.avg_delay_minutes || 0).toFixed(1) }}</div>
          <div class="stat-label">平均延误(分钟)</div>
        </div>
      </div>

      <div class="last-update">
        <el-icon><RefreshRight /></el-icon>
        <span>最后更新: {{ lastUpdateTime }}</span>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <el-row :gutter="20">
      <!-- 左侧：实时延误记录 -->
      <el-col :span="14">
        <el-card class="delays-card">
          <template #header>
            <div class="card-header">
              <h3>实时延误记录</h3>
              <div class="card-actions">
                <el-select v-model="delaysFilter.route" placeholder="筛选线路" clearable @change="filterDelays">
                  <el-option
                    v-for="route in routeOptions"
                    :key="route.value"
                    :label="route.label"
                    :value="route.value"
                  />
                </el-select>
                <el-select v-model="delaysFilter.timeRange" @change="filterDelays" style="width: 120px;">
                  <el-option label="最近1小时" value="1" />
                  <el-option label="最近3小时" value="3" />
                  <el-option label="最近6小时" value="6" />
                  <el-option label="最近24小时" value="24" />
                </el-select>
              </div>
            </div>
          </template>

          <div class="delays-list" v-loading="delaysLoading">
            <div
              v-for="delay in filteredDelays"
              :key="`${delay.trip_id}-${delay.stop_id}`"
              class="delay-item"
              :class="getDelaySeverityClass(delay.arrival_delay)"
            >
              <div class="delay-header">
                <div class="delay-route">
                  <span class="route-name">{{ delay.route_short_name || delay.route_id }}</span>
                  <span class="route-desc">{{ truncateText(delay.route_long_name, 20) }}</span>
                </div>
                <div class="delay-time">
                  {{ formatTime(delay.record_timestamp) }}
                </div>
              </div>

              <div class="delay-content">
                <div class="delay-info">
                  <div class="delay-stop">
                    <el-icon><MapLocation /></el-icon>
                    {{ delay.stop_name }}
                  </div>
                  <div class="delay-vehicle">
                    <el-icon><Van /></el-icon>
                    车辆: {{ delay.vehicle_id || '未知' }}
                  </div>
                </div>

                <div class="delay-status">
                  <div class="delay-value" :class="getDelayValueClass(delay.arrival_delay)">
                    {{ formatDelayTime(delay.arrival_delay) }}
                  </div>
                  <div class="delay-status-badge" :class="getDelaySeverityClass(delay.arrival_delay)">
                    {{ getDelayStatus(delay.arrival_delay).label }}
                  </div>
                </div>
              </div>
            </div>

            <el-empty
              v-if="filteredDelays.length === 0 && !delaysLoading"
              description="暂无延误记录"
              :image-size="100"
            />
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：车辆位置和地图 -->
      <el-col :span="10">
        <el-card class="vehicles-card">
          <template #header>
            <div class="card-header">
              <h3>实时车辆位置</h3>
              <div class="card-actions">
                <el-select v-model="vehiclesFilter.route" placeholder="筛选线路" clearable @change="filterVehicles">
                  <el-option
                    v-for="route in routeOptions"
                    :key="route.value"
                    :label="route.label"
                    :value="route.value"
                  />
                </el-select>
              </div>
            </div>
          </template>

          <div class="vehicles-list" v-loading="vehiclesLoading">
            <div
              v-for="vehicle in filteredVehicles"
              :key="vehicle.vehicle_id"
              class="vehicle-item"
            >
              <div class="vehicle-header">
                <div class="vehicle-info">
                  <span class="vehicle-route">{{ vehicle.route_id }}</span>
                  <span class="vehicle-id">{{ vehicle.vehicle_id }}</span>
                </div>
                <div class="vehicle-speed" v-if="vehicle.speed">
                  {{ vehicle.speed.toFixed(1) }} km/h
                </div>
              </div>

              <div class="vehicle-location">
                <el-icon><Location /></el-icon>
                <span>{{ formatCoordinates(vehicle.latitude, vehicle.longitude) }}</span>
              </div>

              <div class="vehicle-time">
                <el-icon><Clock /></el-icon>
                <span>{{ formatTime(vehicle.position_timestamp) }}</span>
              </div>

              <div class="vehicle-status" v-if="vehicle.stop_id">
                当前站点: {{ vehicle.stop_id }}
              </div>
            </div>

            <el-empty
              v-if="filteredVehicles.length === 0 && !vehiclesLoading"
              description="暂无车辆位置数据"
              :image-size="100"
            />
          </div>
        </el-card>

        <!-- 延误统计图表 -->
        <el-card class="delay-chart-card" style="margin-top: 20px;">
          <template #header>
            <h3>延误分布统计</h3>
          </template>

          <div class="delay-distribution">
            <div class="dist-item">
              <div class="dist-header">
                <div class="dist-label">准点</div>
                <div class="dist-count">{{ delayStats.onTime }}条</div>
              </div>
              <div class="dist-bar-container">
                <div class="dist-bar on-time" :style="{ width: delayStats.onTimePercent + '%' }"></div>
              </div>
              <div class="dist-percent">{{ delayStats.onTimePercent }}%</div>
            </div>

            <div class="dist-item">
              <div class="dist-header">
                <div class="dist-label">延误</div>
                <div class="dist-count">{{ delayStats.late }}条</div>
              </div>
              <div class="dist-bar-container">
                <div class="dist-bar late" :style="{ width: delayStats.latePercent + '%' }"></div>
              </div>
              <div class="dist-percent">{{ delayStats.latePercent }}%</div>
            </div>

            <div class="dist-item">
              <div class="dist-header">
                <div class="dist-label">严重延误</div>
                <div class="dist-count">{{ delayStats.veryLate }}条</div>
              </div>
              <div class="dist-bar-container">
                <div class="dist-bar very-late" :style="{ width: delayStats.veryLatePercent + '%' }"></div>
              </div>
              <div class="dist-percent">{{ delayStats.veryLatePercent }}%</div>
            </div>

            <div class="dist-item">
              <div class="dist-header">
                <div class="dist-label">提前</div>
                <div class="dist-count">{{ delayStats.early }}条</div>
              </div>
              <div class="dist-bar-container">
                <div class="dist-bar early" :style="{ width: delayStats.earlyPercent + '%' }"></div>
              </div>
              <div class="dist-percent">{{ delayStats.earlyPercent }}%</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { usePunctualityStore } from '../stores/punctualityStore'
import {
  Refresh, Location, Clock, Warning, Timer, RefreshRight,
  MapLocation, Van
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

// Store
const punctualityStore = usePunctualityStore()

// 响应式数据
const loading = computed(() => punctualityStore.loading)
const realtimeDelays = computed(() => punctualityStore.realtimeDelays)
const realtimeVehicles = computed(() => punctualityStore.realtimeVehicles)
const realtimeSummary = computed(() => punctualityStore.realtimeSummary)

const autoRefresh = ref(true)
const refreshInterval = ref(30) // 秒
const refreshTimer = ref(null)
const lastUpdateTime = ref('')

const delaysFilter = ref({
  route: '',
  timeRange: '3'
})

const vehiclesFilter = ref({
  route: ''
})

const delaysLoading = ref(false)
const vehiclesLoading = ref(false)

// 计算属性
const routeOptions = computed(() => {
  const routes = new Set()

  // 从延误记录中提取线路
  realtimeDelays.value.forEach(delay => {
    if (delay.route_id) {
      routes.add(delay.route_id)
    }
  })

  // 从车辆位置中提取线路
  realtimeVehicles.value.forEach(vehicle => {
    if (vehicle.route_id) {
      routes.add(vehicle.route_id)
    }
  })

  return Array.from(routes).map(route => ({
    label: route,
    value: route
  })).sort((a, b) => a.label.localeCompare(b.label))
})

const filteredDelays = computed(() => {
  let delays = [...realtimeDelays.value]

  // 按线路筛选
  if (delaysFilter.value.route) {
    delays = delays.filter(delay => delay.route_id === delaysFilter.value.route)
  }

  // 按时间筛选（这里简化处理，实际应该根据时间戳筛选）
  // 实现中可以添加更复杂的时间筛选逻辑

  // 按时间倒序排列
  delays.sort((a, b) => new Date(b.record_timestamp) - new Date(a.record_timestamp))

  return delays.slice(0, 50) // 限制显示数量
})

const filteredVehicles = computed(() => {
  let vehicles = [...realtimeVehicles.value]

  // 按线路筛选
  if (vehiclesFilter.value.route) {
    vehicles = vehicles.filter(vehicle => vehicle.route_id === vehiclesFilter.value.route)
  }

  // 按时间倒序排列
  vehicles.sort((a, b) => new Date(b.position_timestamp) - new Date(a.position_timestamp))

  return vehicles.slice(0, 20) // 限制显示数量
})

const delayStats = computed(() => {
  const delays = filteredDelays.value
  const total = delays.length

  if (total === 0) {
    return {
      onTime: 0,
      late: 0,
      veryLate: 0,
      early: 0,
      onTimePercent: 0,
      latePercent: 0,
      veryLatePercent: 0,
      earlyPercent: 0
    }
  }

  const stats = delays.reduce((acc, delay) => {
    const status = getDelayStatus(delay.arrival_delay)

    if (status.status === 'onTime') {
      acc.onTime++
    } else if (status.status === 'late') {
      acc.late++
    } else if (status.status === 'veryLate') {
      acc.veryLate++
    } else if (status.status === 'early') {
      acc.early++
    }

    return acc
  }, { onTime: 0, late: 0, veryLate: 0, early: 0 })

  return {
    ...stats,
    onTimePercent: Math.round(stats.onTime / total * 100),
    latePercent: Math.round(stats.late / total * 100),
    veryLatePercent: Math.round(stats.veryLate / total * 100),
    earlyPercent: Math.round(stats.early / total * 100)
  }
})

// 方法
const fetchData = async () => {
  try {
    await Promise.all([
      punctualityStore.fetchRealtimeDelays({ hours: parseInt(delaysFilter.value.timeRange) }),
      punctualityStore.fetchRealtimeVehicles({ limit: 100 }),
      punctualityStore.fetchRealtimeSummary()
    ])

    lastUpdateTime.value = new Date().toLocaleTimeString('zh-CN')
  } catch (err) {
    ElMessage.error('获取实时数据失败')
  }
}

const refreshData = async () => {
  delaysLoading.value = true
  vehiclesLoading.value = true

  try {
    await fetchData()
    ElMessage.success('数据刷新成功')
  } catch (err) {
    ElMessage.error('数据刷新失败')
  } finally {
    delaysLoading.value = false
    vehiclesLoading.value = false
  }
}

const filterDelays = async () => {
  delaysLoading.value = true
  try {
    await punctualityStore.fetchRealtimeDelays({
      hours: parseInt(delaysFilter.value.timeRange),
      route_id: delaysFilter.value.route || undefined
    })
  } finally {
    delaysLoading.value = false
  }
}

const filterVehicles = async () => {
  vehiclesLoading.value = true
  try {
    await punctualityStore.fetchRealtimeVehicles({
      route_id: vehiclesFilter.value.route || undefined
    })
  } finally {
    vehiclesLoading.value = false
  }
}

const toggleAutoRefresh = (enabled) => {
  if (enabled) {
    startAutoRefresh()
  } else {
    stopAutoRefresh()
  }
}

const handleIntervalChange = () => {
  if (autoRefresh.value) {
    stopAutoRefresh()
    startAutoRefresh()
  }
}

const startAutoRefresh = () => {
  stopAutoRefresh()
  refreshTimer.value = setInterval(() => {
    fetchData()
  }, refreshInterval.value * 1000)
}

const stopAutoRefresh = () => {
  if (refreshTimer.value) {
    clearInterval(refreshTimer.value)
    refreshTimer.value = null
  }
}

// 工具方法
const formatTime = (timeStr) => {
  if (!timeStr) return '-'
  return new Date(timeStr).toLocaleString('zh-CN')
}

const formatDelayTime = (seconds) => {
  if (!seconds) return '准点'
  const minutes = Math.abs(seconds / 60)
  if (seconds < 0) {
    return `提前${minutes.toFixed(1)}分钟`
  } else {
    return `延误${minutes.toFixed(1)}分钟`
  }
}

const formatCoordinates = (lat, lng) => {
  if (!lat || !lng) return '未知位置'
  return `${lat.toFixed(4)}, ${lng.toFixed(4)}`
}

const truncateText = (text, maxLength) => {
  if (!text) return ''
  return text.length > maxLength ? text.substring(0, maxLength) + '...' : text
}

const getDelayStatus = (delaySeconds) => {
  if (delaySeconds < -60) {
    return { status: 'early', label: '提前', color: 'success' }
  } else if (Math.abs(delaySeconds) <= 120) {
    return { status: 'onTime', label: '准点', color: 'success' }
  } else if (delaySeconds <= 300) {
    return { status: 'late', label: '延误', color: 'warning' }
  } else {
    return { status: 'veryLate', label: '严重延误', color: 'danger' }
  }
}

const getDelaySeverityClass = (delaySeconds) => {
  const status = getDelayStatus(delaySeconds)
  return `delay-${status.status}`
}

const getDelayValueClass = (delaySeconds) => {
  if (delaySeconds < -60) return 'delay-early'
  if (Math.abs(delaySeconds) <= 120) return 'delay-on-time'
  if (delaySeconds <= 300) return 'delay-late'
  return 'delay-very-late'
}

// 生命周期
onMounted(async () => {
  await fetchData()
  if (autoRefresh.value) {
    startAutoRefresh()
  }
})

onUnmounted(() => {
  stopAutoRefresh()
})

// 监听筛选条件变化
watch(() => delaysFilter.value.timeRange, () => {
  filterDelays()
})
</script>

<style scoped>
.realtime-monitor {
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
  align-items: center;
  gap: 16px;
}

.auto-refresh-control {
  display: flex;
  align-items: center;
}

.realtime-stats {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 20px;
  padding: 20px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  position: relative;
}

.stat-card {
  display: flex;
  align-items: center;
  flex: 1;
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
  margin-right: 12px;
  font-size: 24px;
}

.stat-icon.warning {
  background: #fef3c7;
  color: #f59e0b;
}

.stat-icon.info {
  background: #ede9fe;
  color: #8b5cf6;
}

.stat-content .stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #1f2937;
  line-height: 1;
  margin-bottom: 4px;
}

.stat-content .stat-label {
  font-size: 14px;
  color: #6b7280;
}

.last-update {
  position: absolute;
  right: 20px;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #6b7280;
}

.delays-card,
.vehicles-card,
.delay-chart-card {
  margin-bottom: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
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

.card-actions {
  display: flex;
  gap: 12px;
}

.delays-list,
.vehicles-list {
  max-height: 600px;
  overflow-y: auto;
}

.delay-item {
  padding: 16px;
  border-bottom: 1px solid #f3f4f6;
  transition: background-color 0.2s;
}

.delay-item:hover {
  background-color: #f9fafb;
}

.delay-item:last-child {
  border-bottom: none;
}

.delay-item.delay-on-time {
  border-left: 4px solid #10b981;
}

.delay-item.delay-early {
  border-left: 4px solid #3b82f6;
}

.delay-item.delay-late {
  border-left: 4px solid #f59e0b;
}

.delay-item.delay-very-late {
  border-left: 4px solid #ef4444;
}

.delay-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.delay-route .route-name {
  font-weight: 600;
  color: #1f2937;
  margin-right: 8px;
}

.delay-route .route-desc {
  font-size: 12px;
  color: #6b7280;
}

.delay-time {
  font-size: 12px;
  color: #6b7280;
}

.delay-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.delay-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.delay-stop,
.delay-vehicle {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: #374151;
}

.delay-status {
  text-align: right;
}

.delay-value {
  font-weight: 600;
  margin-bottom: 4px;
}

.delay-value.delay-on-time {
  color: #10b981;
}

.delay-value.delay-early {
  color: #3b82f6;
}

.delay-value.delay-late {
  color: #f59e0b;
}

.delay-value.delay-very-late {
  color: #ef4444;
}

.delay-status-badge {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 12px;
  background: #f3f4f6;
  color: #374151;
}

.delay-status-badge.delay-on-time,
.delay-status-badge.delay-early {
  background: #dcfce7;
  color: #166534;
}

.delay-status-badge.delay-late {
  background: #fef3c7;
  color: #92400e;
}

.delay-status-badge.delay-very-late {
  background: #fee2e2;
  color: #991b1b;
}

.vehicle-item {
  padding: 12px;
  border-bottom: 1px solid #f3f4f6;
  transition: background-color 0.2s;
}

.vehicle-item:hover {
  background-color: #f9fafb;
}

.vehicle-item:last-child {
  border-bottom: none;
}

.vehicle-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.vehicle-info .vehicle-route {
  font-weight: 600;
  color: #1f2937;
  margin-right: 8px;
}

.vehicle-info .vehicle-id {
  font-size: 12px;
  color: #6b7280;
}

.vehicle-speed {
  font-size: 12px;
  color: #059669;
  font-weight: 500;
}

.vehicle-location,
.vehicle-time,
.vehicle-status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 4px;
}

.delay-distribution {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.dist-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.dist-header {
  display: flex;
  flex-direction: column;
  min-width: 60px;
}

.dist-label {
  font-size: 14px;
  color: #374151;
  font-weight: 500;
}

.dist-count {
  font-size: 12px;
  color: #6b7280;
}

.dist-bar-container {
  flex: 1;
  height: 16px;
  background: #f3f4f6;
  border-radius: 8px;
  overflow: hidden;
}

.dist-bar {
  height: 100%;
  transition: width 0.3s ease;
  border-radius: 8px;
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

.dist-percent {
  min-width: 40px;
  text-align: right;
  font-weight: 600;
  color: #1f2937;
  font-size: 12px;
}

@media (max-width: 1200px) {
  .realtime-stats {
    flex-wrap: wrap;
  }

  .stat-card {
    flex: 1 1 20%;
    min-width: 150px;
  }

  .last-update {
    position: static;
    transform: none;
    margin-top: 12px;
    justify-content: center;
  }
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    gap: 16px;
  }

  .header-actions {
    width: 100%;
    flex-direction: column;
    gap: 12px;
  }

  .auto-refresh-control {
    width: 100%;
    justify-content: center;
  }

  .card-header {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }

  .card-actions {
    justify-content: stretch;
  }

  .card-actions .el-select {
    width: 100%;
  }
}
</style>