<template>
  <div class="stop-punctuality-detail">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <el-button :icon="ArrowLeft" @click="goBack" style="margin-bottom:8px">返回列表</el-button>
        <h1>{{ stopInfo.stop_name || '站点' }} 到站时刻表</h1>
        <p v-if="stopInfo.stop_id">站点ID: {{ stopInfo.stop_id }}</p>
      </div>
    </div>

    <!-- 时刻表 -->
    <el-card class="timetable-card" v-loading="loading">
      <template #header>
        <div class="table-header">
          <h3>经过该站点的线路到站记录</h3>
          <span class="record-count" v-if="records.length">共 {{ records.length }} 条记录</span>
        </div>
      </template>

      <el-table :data="records" stripe>
        <el-table-column prop="route_short_name" label="线路" width="120">
          <template #default="{ row }">
            <div class="route-cell">
              <span class="route-name">{{ row.route_short_name || row.route_id }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="route_long_name" label="线路名称" min-width="180">
          <template #default="{ row }">
            <span class="route-long">{{ truncateText(row.route_long_name, 30) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="trip_headsign" label="方向" width="150">
          <template #default="{ row }">
            <span>{{ row.trip_headsign || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="scheduled_time" label="计划到站" width="120" align="center">
          <template #default="{ row }">
            <span class="time-text">{{ formatTime(row.scheduled_time) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="actual_time" label="实际到站" width="120" align="center">
          <template #default="{ row }">
            <span class="time-text actual">{{ formatTime(row.actual_time) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="延误" width="150" align="center">
          <template #default="{ row }">
            <div class="delay-cell">
              <el-icon class="delay-icon" :class="getDelayClass(row.delay_seconds)">
                <Clock />
              </el-icon>
              <span :class="getDelayClass(row.delay_seconds)" style="white-space:nowrap">
                {{ formatDelay(row.delay_seconds) }}
              </span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.delay_seconds)" size="small">
              {{ getStatusLabel(row.delay_seconds) }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!loading && records.length === 0" description="暂无该站点的时刻表数据" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePunctualityStore } from '../stores/punctualityStore'
import { ArrowLeft, Clock } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const punctualityStore = usePunctualityStore()

const loading = ref(false)
const stopInfo = ref({})
const records = ref([])

const goBack = () => {
  router.push({ name: 'stop-punctuality' })
}

const truncateText = (text, maxLength) => {
  if (!text) return '-'
  return text.length > maxLength ? text.substring(0, maxLength) + '...' : text
}

const formatTime = (timeStr) => {
  if (!timeStr) return '-'
  const parts = timeStr.split(':')
  if (parts.length >= 2) {
    return `${parts[0]}:${parts[1]}`
  }
  return timeStr
}

const formatDelay = (seconds) => {
  if (seconds === 0 || seconds === undefined || seconds === null) return '准点'
  const minutes = Math.abs(seconds / 60)
  if (seconds < 0) return `提前 ${minutes.toFixed(1)} 分钟`
  return `延误 ${minutes.toFixed(1)} 分钟`
}

const getDelayClass = (seconds) => {
  if (!seconds || seconds === 0) return 'delay-good'
  if (seconds < 0) return 'delay-good'
  if (seconds <= 120) return 'delay-good'
  if (seconds <= 300) return 'delay-warning'
  return 'delay-bad'
}

const getStatusType = (seconds) => {
  if (!seconds || seconds === 0) return 'success'
  if (seconds < -60) return 'info'
  if (seconds <= 120) return 'success'
  if (seconds <= 300) return 'warning'
  return 'danger'
}

const getStatusLabel = (seconds) => {
  if (!seconds || seconds === 0) return '准点'
  if (seconds < -60) return '提前'
  if (seconds <= 120) return '准点'
  if (seconds <= 300) return '延误'
  return '严重延误'
}

const fetchData = async () => {
  const stopId = route.params.stopId
  if (!stopId) return

  loading.value = true
  try {
    const data = await punctualityStore.fetchStopTimetable(stopId, { limit: 50 })
    stopInfo.value = data.stop_info || {}
    records.value = data.records || []
  } catch (err) {
    ElMessage.error('获取时刻表数据失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.stop-punctuality-detail {
  padding: 20px;
  background: #f5f7fa;
  min-height: 100vh;
}

.page-header {
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

.timetable-card {
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

.record-count {
  font-size: 14px;
  color: #6b7280;
}

.route-cell {
  display: flex;
  align-items: center;
}

.route-name {
  font-weight: 600;
  color: #1f2937;
}

.route-long {
  font-size: 13px;
  color: #6b7280;
}

.time-text {
  font-family: monospace;
  font-size: 14px;
  color: #374151;
}

.time-text.actual {
  font-weight: 600;
}

.delay-cell {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.delay-icon {
  font-size: 16px;
}

.delay-good {
  color: #10b981;
}

.delay-warning {
  color: #f59e0b;
}

.delay-bad {
  color: #ef4444;
}

@media (max-width: 768px) {
  .page-header {
    padding: 16px;
  }

  .header-content h1 {
    font-size: 20px;
  }
}
</style>
