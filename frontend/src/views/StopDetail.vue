<template>
  <div class="stop-detail-page">
    <div v-loading="stopStore.loading" class="detail-content">
      <div v-if="stopStore.currentStop" class="stop-detail">
        <el-page-header @back="$router.back()" title="返回">
          <template #content>
            <div class="stop-title">
              <el-icon :size="24"><Location /></el-icon>
              <span>{{ stopStore.currentStop.stop_name }}</span>
            </div>
          </template>
        </el-page-header>

        <el-divider />

        <el-row :gutter="20">
          <el-col :xs="24" :md="12">
            <el-card>
              <template #header>
                <span>站点信息</span>
              </template>
              <el-descriptions :column="1" border>
                <el-descriptions-item label="站点ID">{{ stopStore.currentStop.stop_id }}</el-descriptions-item>
                <el-descriptions-item label="站点名称">{{ stopStore.currentStop.stop_name }}</el-descriptions-item>
                <el-descriptions-item v-if="stopStore.currentStop.stop_code" label="站点编号">{{ stopStore.currentStop.stop_code }}</el-descriptions-item>
                <el-descriptions-item label="纬度">{{ stopStore.currentStop.stop_lat.toFixed(6) }}</el-descriptions-item>
                <el-descriptions-item label="经度">{{ stopStore.currentStop.stop_lon.toFixed(6) }}</el-descriptions-item>
                <el-descriptions-item v-if="stopStore.currentStop.stop_desc" label="描述">{{ stopStore.currentStop.stop_desc }}</el-descriptions-item>
                <el-descriptions-item v-if="stopStore.currentStop.wheelchair_boarding !== null" label="无障碍">
                  {{ getWheelchairText(stopStore.currentStop.wheelchair_boarding) }}
                </el-descriptions-item>
              </el-descriptions>
            </el-card>
          </el-col>

          <el-col :xs="24" :md="12">
            <el-card>
              <template #header>
                <span>地图位置</span>
              </template>
              <div class="map-placeholder">
                <el-icon :size="60"><MapLocation /></el-icon>
                <p>地图功能开发中...</p>
                <p class="coordinates">
                  {{ stopStore.currentStop.stop_lat.toFixed(6) }}, {{ stopStore.currentStop.stop_lon.toFixed(6) }}
                </p>
              </div>
            </el-card>
          </el-col>
        </el-row>

        <el-card class="routes-card">
          <template #header>
            <span>经过的线路</span>
          </template>
          <div v-loading="loadingRoutes">
            <div v-if="stopStore.stopRoutes.length > 0" class="routes-list">
              <el-card
                v-for="route in stopStore.stopRoutes"
                :key="route.route_id"
                shadow="hover"
                class="route-item"
                @click="handleRouteClick(route)"
              >
                <div class="route-item-content">
                  <div class="route-badge" :style="{ backgroundColor: `#${route.route_color || '005596'}` }">
                    <span :style="{ color: `#${route.route_text_color || 'FFFFFF'}` }">
                      {{ route.route_short_name || 'N/A' }}
                    </span>
                  </div>
                  <div class="route-info">
                    <div class="route-name">{{ route.route_long_name }}</div>
                    <div class="route-type">{{ getRouteTypeName(route.route_type) }}</div>
                  </div>
                </div>
              </el-card>
            </div>
            <el-empty v-else description="暂无线路信息" />
          </div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useStopStore } from '@/stores/stopStore'
import { Location, MapLocation } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const stopStore = useStopStore()

const loadingRoutes = ref(false)

const routeTypeNames = {
  0: '轻轨/地铁',
  1: '地铁',
  2: '铁路',
  3: '公交',
  4: '轮渡',
  5: '有轨电车',
  6: '缆车',
  7: '索道'
}

const getRouteTypeName = (type) => {
  return routeTypeNames[type] || '未知'
}

const getWheelchairText = (value) => {
  const map = {
    0: '无信息',
    1: '可用',
    2: '不可用'
  }
  return map[value] || '未知'
}

const handleRouteClick = (route) => {
  router.push(`/routes/${route.route_id}`)
}

onMounted(async () => {
  try {
    await stopStore.fetchStopById(route.params.id)

    loadingRoutes.value = true
    await stopStore.fetchStopRoutes(route.params.id)
  } catch (error) {
    console.error('加载站点详情失败:', error)
  } finally {
    loadingRoutes.value = false
  }
})
</script>

<style scoped>
.stop-detail-page {
  padding: 20px;
}

.stop-title {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 20px;
  font-weight: 600;
}

.map-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: #909399;
  text-align: center;
}

.coordinates {
  font-size: 12px;
  margin-top: 8px;
}

.routes-card {
  margin-top: 20px;
}

.routes-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
}

.route-item {
  cursor: pointer;
  transition: transform 0.2s;
}

.route-item:hover {
  transform: translateY(-2px);
}

.route-item-content {
  display: flex;
  align-items: center;
  gap: 12px;
}

.route-badge {
  width: 40px;
  height: 40px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 14px;
  flex-shrink: 0;
}

.route-info {
  flex: 1;
  min-width: 0;
}

.route-name {
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.route-type {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

@media (max-width: 768px) {
  .routes-list {
    grid-template-columns: 1fr;
  }
}
</style>
