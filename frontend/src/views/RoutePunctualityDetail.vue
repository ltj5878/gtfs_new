<template>
  <div class="route-punctuality-detail">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <el-button :icon="ArrowLeft" @click="goBack" style="margin-bottom:8px">返回列表</el-button>
        <h1>{{ routeInfo.route_short_name || routeInfo.route_id || '线路' }} 运行时刻表</h1>
        <p>{{ routeInfo.route_long_name || '查看该线路各班次的计划到站与实际到站时间对比' }}</p>
      </div>
    </div>

    <!-- 班次选择器 -->
    <el-card class="trip-selector-card" v-loading="loading">
      <el-row :gutter="16" align="middle">
        <el-col :span="8">
          <el-select
            v-model="selectedTripId"
            placeholder="选择班次"
            @change="handleTripChange"
            style="width: 100%"
            filterable
          >
            <el-option
              v-for="trip in trips"
              :key="trip.trip_id"
              :label="formatTripLabel(trip)"
              :value="trip.trip_id"
            />
          </el-select>
        </el-col>
        <el-col :span="16">
          <span class="trip-info" v-if="selectedTrip">
            共 {{ selectedTrip.stops.length }} 个站点
          </span>
        </el-col>
      </el-row>
    </el-card>

    <!-- 时刻表 -->
    <el-card class="timetable-card" v-if="selectedTrip">
      <template #header>
        <div class="table-header">
          <h3>站点时刻表</h3>
        </div>
      </template>

      <el-table :data="selectedTrip.stops" stripe>
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="stop_name" label="站点名称" min-width="200">
          <template #default="{ row }">
            <div class="stop-name-cell">
              <el-icon><Location /></el-icon>
              <span>{{ row.stop_name }}</span>
            </div>
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
    </el-card>

    <!-- 空状态 -->
    <el-card v-if="!loading && trips.length === 0" class="timetable-card">
      <el-empty description="暂无该线路的时刻表数据" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePunctualityStore } from '../stores/punctualityStore'
import { ArrowLeft, Location, Clock } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const punctualityStore = usePunctualityStore()

const loading = ref(false)
const routeInfo = ref({})
const trips = ref([])
const selectedTripId = ref('')

const selectedTrip = computed(() => {
  return trips.value.find(t => t.trip_id === selectedTripId.value) || null
})

const goBack = () => {
  router.push({ name: 'route-punctuality' })
}

const formatTripLabel = (trip) => {
  const headsign = trip.trip_headsign ? ` → ${trip.trip_headsign}` : ''
  const firstStop = trip.stops?.[0]?.scheduled_time || ''
  const time = firstStop ? ` (${formatTime(firstStop)})` : ''
  return `${trip.trip_id}${headsign}${time}`
}

const formatTime = (timeStr) => {
  if (!timeStr) return '-'
  // 去掉秒，只显示 HH:MM
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

const handleTripChange = () => {
  // 选择班次时自动滚动到顶部
}

const fetchData = async () => {
  const routeId = route.params.routeId
  if (!routeId) return

  loading.value = true
  try {
    const data = await punctualityStore.fetchRouteTimetable(routeId, { limit: 10 })
    routeInfo.value = data.route_info || {}
    trips.value = data.trips || []
    if (trips.value.length > 0) {
      selectedTripId.value = trips.value[0].trip_id
    }
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
.route-punctuality-detail {
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

.trip-selector-card {
  margin-bottom: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.trip-info {
  font-size: 14px;
  color: #6b7280;
}

.timetable-card {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.table-header h3 {
  margin: 0;
  color: #1f2937;
  font-size: 16px;
  font-weight: 600;
}

.stop-name-cell {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 500;
  color: #1f2937;
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
