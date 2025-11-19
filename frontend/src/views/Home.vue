<template>
  <div class="home">
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="24" :sm="12" :md="6" v-for="(value, key) in stats" :key="key">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-content">
            <el-icon class="stat-icon" :size="40">
              <component :is="getIcon(key)" />
            </el-icon>
            <div class="stat-info">
              <div class="stat-value">{{ value }}</div>
              <div class="stat-label">{{ getLabel(key) }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="content-row">
      <el-col :xs="24" :md="12">
        <el-card class="section-card">
          <template #header>
            <div class="card-header">
              <span>快速访问</span>
            </div>
          </template>
          <div class="quick-links">
            <el-button type="primary" @click="$router.push('/routes')" size="large">
              <el-icon><Guide /></el-icon>
              浏览线路
            </el-button>
            <el-button type="success" @click="$router.push('/stops')" size="large">
              <el-icon><Location /></el-icon>
              查找站点
            </el-button>
            <el-button type="info" @click="$router.push('/map')" size="large">
              <el-icon><MapLocation /></el-icon>
              地图视图
            </el-button>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :md="12">
        <el-card class="section-card">
          <template #header>
            <div class="card-header">
              <span>系统信息</span>
            </div>
          </template>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="数据来源">511 SF Bay API</el-descriptions-item>
            <el-descriptions-item label="覆盖区域">旧金山湾区</el-descriptions-item>
            <el-descriptions-item label="数据类型">GTFS 静态数据</el-descriptions-item>
            <el-descriptions-item label="更新频率">每周更新</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores/appStore'
import {
  Guide,
  Location,
  MapLocation,
  TrendCharts,
  Position,
  Timer,
  DataLine
} from '@element-plus/icons-vue'

const router = useRouter()
const appStore = useAppStore()

const stats = ref({})

const iconMap = {
  agencies: TrendCharts,
  routes: Guide,
  stops: Location,
  trips: Timer,
  stop_times: DataLine,
  shapes: Position
}

const labelMap = {
  agencies: '运营机构',
  routes: '线路数量',
  stops: '站点数量',
  trips: '班次数量',
  stop_times: '时刻表记录',
  shapes: '轨迹数量'
}

const getIcon = (key) => {
  return iconMap[key] || TrendCharts
}

const getLabel = (key) => {
  return labelMap[key] || key
}

onMounted(async () => {
  try {
    stats.value = await appStore.fetchStats()
  } catch (error) {
    console.error('加载统计信息失败:', error)
  }
})
</script>

<style scoped>
.home {
  padding: 20px;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  height: 100%;
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  color: #409eff;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.content-row {
  margin-bottom: 20px;
}

.section-card {
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}

.quick-links {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.quick-links .el-button {
  width: 100%;
  justify-content: flex-start;
}
</style>
