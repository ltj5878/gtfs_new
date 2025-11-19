<template>
  <div class="route-detail-page">
    <div v-loading="routeStore.loading" class="detail-content">
      <div v-if="routeStore.currentRoute" class="route-detail">
        <el-page-header @back="$router.back()" title="返回">
          <template #content>
            <div class="route-title">
              <div class="route-badge" :style="{ backgroundColor: `#${routeStore.currentRoute.route_color || '005596'}` }">
                <span :style="{ color: `#${routeStore.currentRoute.route_text_color || 'FFFFFF'}` }">
                  {{ routeStore.currentRoute.route_short_name || 'N/A' }}
                </span>
              </div>
              <span>{{ routeStore.currentRoute.route_long_name }}</span>
            </div>
          </template>
        </el-page-header>

        <el-divider />

        <el-row :gutter="20">
          <el-col :xs="24" :md="12">
            <el-card>
              <template #header>
                <span>线路信息</span>
              </template>
              <el-descriptions :column="1" border>
                <el-descriptions-item label="线路ID">{{ routeStore.currentRoute.route_id }}</el-descriptions-item>
                <el-descriptions-item label="线路名称">{{ routeStore.currentRoute.route_long_name }}</el-descriptions-item>
                <el-descriptions-item label="线路编号">{{ routeStore.currentRoute.route_short_name }}</el-descriptions-item>
                <el-descriptions-item label="线路类型">{{ getRouteTypeName(routeStore.currentRoute.route_type) }}</el-descriptions-item>
                <el-descriptions-item v-if="routeStore.currentRoute.category" label="类别">{{ routeStore.currentRoute.category }}</el-descriptions-item>
                <el-descriptions-item v-if="routeStore.currentRoute.subcategory" label="子类别">{{ routeStore.currentRoute.subcategory }}</el-descriptions-item>
                <el-descriptions-item v-if="routeStore.currentRoute.running_way" label="运行方式">{{ routeStore.currentRoute.running_way }}</el-descriptions-item>
              </el-descriptions>
            </el-card>
          </el-col>

          <el-col :xs="24" :md="12">
            <el-card>
              <template #header>
                <span>方向信息</span>
              </template>
              <div v-if="routeStore.directions.length > 0">
                <el-radio-group v-model="selectedDirection" @change="handleDirectionChange">
                  <el-radio-button
                    v-for="dir in routeStore.directions"
                    :key="dir.direction_id"
                    :label="dir.direction_id"
                  >
                    {{ dir.direction }}
                  </el-radio-button>
                </el-radio-group>
              </div>
              <el-empty v-else description="暂无方向信息" :image-size="80" />
            </el-card>
          </el-col>
        </el-row>

        <el-card class="stops-card">
          <template #header>
            <span>站点列表</span>
          </template>
          <div v-loading="loadingStops">
            <el-timeline v-if="routeStore.stops.length > 0">
              <el-timeline-item
                v-for="(stop, index) in routeStore.stops"
                :key="stop.stop_id"
                :timestamp="`站点 ${index + 1}`"
              >
                <el-card shadow="hover" class="stop-item" @click="handleStopClick(stop)">
                  <div class="stop-item-content">
                    <div class="stop-name">{{ stop.stop_name }}</div>
                    <div class="stop-code">{{ stop.stop_code }}</div>
                  </div>
                </el-card>
              </el-timeline-item>
            </el-timeline>
            <el-empty v-else description="暂无站点信息" />
          </div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useRouteStore } from '@/stores/routeStore'

const route = useRoute()
const router = useRouter()
const routeStore = useRouteStore()

const selectedDirection = ref(null)
const loadingStops = ref(false)

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

const loadRouteStops = async (directionId = null) => {
  loadingStops.value = true
  try {
    await routeStore.fetchRouteStops(route.params.id, directionId)
  } catch (error) {
    console.error('加载站点失败:', error)
  } finally {
    loadingStops.value = false
  }
}

const handleDirectionChange = (directionId) => {
  loadRouteStops(directionId)
}

const handleStopClick = (stop) => {
  router.push(`/stops/${stop.stop_id}`)
}

onMounted(async () => {
  try {
    await routeStore.fetchRouteById(route.params.id)
    await routeStore.fetchRouteDirections(route.params.id)

    if (routeStore.directions.length > 0) {
      selectedDirection.value = routeStore.directions[0].direction_id
      await loadRouteStops(selectedDirection.value)
    } else {
      await loadRouteStops()
    }
  } catch (error) {
    console.error('加载线路详情失败:', error)
  }
})
</script>

<style scoped>
.route-detail-page {
  padding: 20px;
}

.route-title {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 20px;
  font-weight: 600;
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
}

.stops-card {
  margin-top: 20px;
}

.stop-item {
  cursor: pointer;
  transition: transform 0.2s;
}

.stop-item:hover {
  transform: translateX(4px);
}

.stop-item-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stop-name {
  font-weight: 500;
}

.stop-code {
  font-size: 12px;
  color: #909399;
}
</style>
