<template>
  <div class="home">
    <!-- 欢迎区域 -->
    <div class="welcome-section">
      <h1 class="welcome-title">{{ $t('app.title') }}</h1>
      <p class="welcome-subtitle">{{ $t('app.subtitle') }}</p>
    </div>

    <!-- 统计数据卡片 -->
    <div class="stats-section">
      <div class="section-title">{{ $t('home.dataOverview') }}</div>
      <el-row :gutter="20">
        <el-col :xs="12" :sm="8" :md="4" v-for="(item, key) in statsData" :key="key">
          <div class="stat-card">
            <div class="stat-icon" :style="{ backgroundColor: item.color }">
              <el-icon :size="24">
                <component :is="item.icon" />
              </el-icon>
            </div>
            <div class="stat-value">{{ stats[key] || 0 }}</div>
            <div class="stat-label">{{ item.label }}</div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 功能导航区域 -->
    <div class="features-section">
      <el-row :gutter="20">
        <!-- 线路与站点 -->
        <el-col :xs="24" :md="8">
          <div class="feature-card">
            <div class="feature-header">
              <el-icon :size="20" color="#409eff"><Guide /></el-icon>
              <span class="feature-title">{{ $t('home.routesAndStops') }}</span>
            </div>
            <div class="feature-content">
              <div class="feature-item" @click="$router.push('/heatmap')">
                <div class="feature-item-icon" style="background-color: #fee2e2;">
                  <el-icon :size="20" color="#ef4444"><DataLine /></el-icon>
                </div>
                <div class="feature-item-text">
                  <div class="feature-item-title">{{ $t('home.stopHeatmap') }}</div>
                  <div class="feature-item-desc">{{ $t('home.stopHeatmapDesc') }}</div>
                </div>
                <el-icon class="feature-item-arrow"><ArrowRight /></el-icon>
              </div>

              <div class="feature-item" @click="$router.push('/playback')">
                <div class="feature-item-icon" style="background-color: #e8f5e9;">
                  <el-icon :size="20" color="#16a34a"><Timer /></el-icon>
                </div>
                <div class="feature-item-text">
                  <div class="feature-item-title">{{ $t('home.vehiclePlayback') }}</div>
                  <div class="feature-item-desc">{{ $t('home.vehiclePlaybackDesc') }}</div>
                </div>
                <el-icon class="feature-item-arrow"><ArrowRight /></el-icon>
              </div>

              <div class="feature-item" @click="$router.push('/map')">
                <div class="feature-item-icon" style="background-color: #f3e5f5;">
                  <el-icon :size="20" color="#909399"><MapLocation /></el-icon>
                </div>
                <div class="feature-item-text">
                  <div class="feature-item-title">{{ $t('home.mapView') }}</div>
                  <div class="feature-item-desc">{{ $t('home.mapViewDesc') }}</div>
                </div>
                <el-icon class="feature-item-arrow"><ArrowRight /></el-icon>
              </div>

              <div class="feature-item" @click="$router.push('/schedule')">
                <div class="feature-item-icon" style="background-color: #ede9fe;">
                  <el-icon :size="20" color="#7c3aed"><Timer /></el-icon>
                </div>
                <div class="feature-item-text">
                  <div class="feature-item-title">{{ $t('home.routeSchedule') }}</div>
                  <div class="feature-item-desc">{{ $t('home.routeScheduleDesc') }}</div>
                </div>
                <el-icon class="feature-item-arrow"><ArrowRight /></el-icon>
              </div>
            </div>
          </div>
        </el-col>

        <!-- 出行工具 -->
        <el-col :xs="24" :md="8">
          <div class="feature-card">
            <div class="feature-header">
              <el-icon :size="20" color="#0288d1"><Promotion /></el-icon>
              <span class="feature-title">{{ $t('home.travelTools') }}</span>
            </div>
            <div class="feature-content">
              <div class="feature-item" @click="$router.push('/favorites')">
                <div class="feature-item-icon" style="background-color: #fff8e1;">
                  <el-icon :size="20" color="#f0a020"><Star /></el-icon>
                </div>
                <div class="feature-item-text">
                  <div class="feature-item-title">{{ $t('home.myFavorites') }}</div>
                  <div class="feature-item-desc">{{ $t('home.myFavoritesDesc') }}</div>
                </div>
                <el-icon class="feature-item-arrow"><ArrowRight /></el-icon>
              </div>

              <div class="feature-item" @click="$router.push('/planner/transfer')">
                <div class="feature-item-icon" style="background-color: #e1f5fe;">
                  <el-icon :size="20" color="#0288d1"><Promotion /></el-icon>
                </div>
                <div class="feature-item-text">
                  <div class="feature-item-title">{{ $t('home.transferPlanner') }}</div>
                  <div class="feature-item-desc">{{ $t('home.transferPlannerDesc') }}</div>
                </div>
                <el-icon class="feature-item-arrow"><ArrowRight /></el-icon>
              </div>

              <div class="feature-item" @click="$router.push('/compare/routes')">
                <div class="feature-item-icon" style="background-color: #e8f5e9;">
                  <el-icon :size="20" color="#67c23a"><DataAnalysis /></el-icon>
                </div>
                <div class="feature-item-text">
                  <div class="feature-item-title">{{ $t('home.routeCompare') }}</div>
                  <div class="feature-item-desc">{{ $t('home.routeCompareDesc') }}</div>
                </div>
                <el-icon class="feature-item-arrow"><ArrowRight /></el-icon>
              </div>

              <div class="feature-item" @click="$router.push('/analysis/reachability')">
                <div class="feature-item-icon" style="background-color: #dbeafe;">
                  <el-icon :size="20" color="#2563eb"><MapLocation /></el-icon>
                </div>
                <div class="feature-item-text">
                  <div class="feature-item-title">{{ $t('home.stopReachability') }}</div>
                  <div class="feature-item-desc">{{ $t('home.stopReachabilityDesc') }}</div>
                </div>
                <el-icon class="feature-item-arrow"><ArrowRight /></el-icon>
              </div>
            </div>
          </div>
        </el-col>

        <!-- 准点率分析 -->
        <el-col :xs="24" :md="8">
          <div class="feature-card">
            <div class="feature-header">
              <el-icon :size="20" color="#e6a23c"><TrendCharts /></el-icon>
              <span class="feature-title">{{ $t('home.punctualityAnalysis') }}</span>
            </div>
            <div class="feature-content">
<!--              <div class="feature-item" @click="navigate('/punctuality')">-->
<!--                <div class="feature-item-icon" style="background-color: #fef0e6;">-->
<!--                  <el-icon :size="20" color="#e6a23c"><TrendCharts /></el-icon>-->
<!--                </div>-->
<!--                <div class="feature-item-text">-->
<!--                  <div class="feature-item-title">准点率概览</div>-->
<!--                  <div class="feature-item-desc">查看整体准点率统计</div>-->
<!--                </div>-->
<!--                <el-icon class="feature-item-arrow"><ArrowRight /></el-icon>-->
<!--              </div>-->

              <div class="feature-item" @click="navigate('/punctuality/routes')">
                <div class="feature-item-icon" style="background-color: #e3f2fd;">
                  <el-icon :size="20" color="#409eff"><Guide /></el-icon>
                </div>
                <div class="feature-item-text">
                  <div class="feature-item-title">{{ $t('home.routePunctuality') }}</div>
                  <div class="feature-item-desc">{{ $t('home.routePunctualityDesc') }}</div>
                </div>
                <el-icon class="feature-item-arrow"><ArrowRight /></el-icon>
              </div>

              <div class="feature-item" @click="navigate('/punctuality/stops')">
                <div class="feature-item-icon" style="background-color: #e8f5e9;">
                  <el-icon :size="20" color="#67c23a"><Location /></el-icon>
                </div>
                <div class="feature-item-text">
                  <div class="feature-item-title">{{ $t('home.stopPunctuality') }}</div>
                  <div class="feature-item-desc">{{ $t('home.stopPunctualityDesc') }}</div>
                </div>
                <el-icon class="feature-item-arrow"><ArrowRight /></el-icon>
              </div>

              <div class="feature-item" @click="navigate('/punctuality/trends')">
                <div class="feature-item-icon" style="background-color: #e8eaf6;">
                  <el-icon :size="20" color="#5c6bc0"><DataLine /></el-icon>
                </div>
                <div class="feature-item-text">
                  <div class="feature-item-title">{{ $t('home.punctualityTrends') }}</div>
                  <div class="feature-item-desc">{{ $t('home.punctualityTrendsDesc') }}</div>
                </div>
                <el-icon class="feature-item-arrow"><ArrowRight /></el-icon>
              </div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 系统信息 -->
    <div class="info-section">
      <div class="info-card">
        <div class="info-item">
          <span class="info-label">{{ $t('home.dataSource') }}</span>
          <span class="info-value">{{ regionInfo.source }}</span>
        </div>
        <div class="info-divider"></div>
        <div class="info-item">
          <span class="info-label">{{ $t('home.coverageArea') }}</span>
          <span class="info-value">{{ regionInfo.name }}</span>
        </div>
        <div class="info-divider"></div>
        <div class="info-item">
          <span class="info-label">{{ $t('home.dataType') }}</span>
          <span class="info-value">{{ $t('home.dataTypeValue') }}</span>
        </div>
        <div class="info-divider"></div>
        <div class="info-item">
          <span class="info-label">{{ $t('home.updateFrequency') }}</span>
          <span class="info-value">{{ $t('home.updateFrequencyValue') }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAppStore } from '@/stores/appStore'
import { useRegionStore } from '@/stores/regionStore'
import {
  Guide,
  Location,
  MapLocation,
  TrendCharts,
  Position,
  Timer,
  DataLine,
  ArrowRight,
  Star,
  Promotion,
  DataAnalysis
} from '@element-plus/icons-vue'

const router = useRouter()
const { t } = useI18n()
const appStore = useAppStore()
const regionStore = useRegionStore()

const navigate = (path) => { window.location.href = path }

const stats = ref({})

// 地区信息映射
const REGION_INFO = computed(() => ({
  sf: { name: t('region.sf'), source: t('region.sfSource') },
  nyc: { name: t('region.nyc'), source: t('region.nycSource') },
  sydney: { name: t('region.sydney'), source: t('region.sydneySource') },
}))

const regionInfo = computed(() => {
  return REGION_INFO.value[regionStore.selectedRegion] || { name: t('region.sf'), source: t('region.sfSource') }
})

// 统计数据配置
const statsData = computed(() => ({
  agencies: {
    label: t('home.agencies'),
    icon: TrendCharts,
    color: '#e3f2fd'
  },
  routes: {
    label: t('home.routeCount'),
    icon: Guide,
    color: '#e8f5e9'
  },
  stops: {
    label: t('home.stopCount'),
    icon: Location,
    color: '#fef0e6'
  },
  trips: {
    label: t('home.tripCount'),
    icon: Timer,
    color: '#f3e5f5'
  },
  stop_times: {
    label: t('home.stopTimeRecords'),
    icon: DataLine,
    color: '#e0f2f1'
  },
  shapes: {
    label: t('home.shapeCount'),
    icon: Position,
    color: '#fce4ec'
  }
}))

onMounted(async () => {
  try {
    stats.value = await appStore.fetchStats()
  } catch (error) {
    console.error('加载统计信息失败:', error)
  }
})

watch(() => regionStore.selectedRegion, async () => {
  try {
    stats.value = await appStore.fetchStats()
  } catch (error) {
    console.error('加载统计信息失败:', error)
  }
})
</script>

<style scoped>
.home {
  min-height: 100vh;
  background: var(--el-bg-color-page);
  padding: 40px 20px;
}

/* 欢迎区域 */
.welcome-section {
  text-align: center;
  margin-bottom: 48px;
  padding: 20px;
}

.welcome-title {
  font-size: 32px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin-bottom: 12px;
  letter-spacing: 0.5px;
}

.welcome-subtitle {
  font-size: 16px;
  color: var(--el-text-color-secondary);
  font-weight: 400;
}

/* 统计数据区域 */
.stats-section {
  max-width: 1200px;
  margin: 0 auto 48px;
}

.section-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin-bottom: 24px;
  padding-left: 12px;
  border-left: 4px solid #409eff;
}

.stat-card {
  background: var(--el-bg-color);
  border-radius: 12px;
  padding: 24px 16px;
  text-align: center;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  cursor: default;
  margin-bottom: 20px;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 16px;
  color: #409eff;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--el-text-color-primary);
  margin-bottom: 8px;
  line-height: 1;
}

.stat-label {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  font-weight: 500;
}

/* 功能导航区域 */
.features-section {
  max-width: 1200px;
  margin: 0 auto 48px;
}

.feature-card {
  background: var(--el-bg-color);
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  margin-bottom: 20px;
  height: 100%;
}

.feature-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 2px solid var(--el-border-color-lighter);
}

.feature-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.feature-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  border-radius: 8px;
  background: var(--el-fill-color-light);
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid transparent;
}

.feature-item:hover {
  background: var(--el-fill-color);
  border-color: var(--el-border-color-light);
  transform: translateX(4px);
}

.feature-item-icon {
  width: 48px;
  height: 48px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.feature-item-text {
  flex: 1;
}

.feature-item-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin-bottom: 4px;
}

.feature-item-desc {
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.feature-item-arrow {
  color: var(--el-text-color-placeholder);
  transition: all 0.3s ease;
  flex-shrink: 0;
}

.feature-item:hover .feature-item-arrow {
  color: #409eff;
  transform: translateX(4px);
}

/* 系统信息区域 */
.info-section {
  max-width: 1200px;
  margin: 0 auto;
}

.info-card {
  background: var(--el-bg-color);
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  display: flex;
  align-items: center;
  justify-content: space-around;
  flex-wrap: wrap;
  gap: 20px;
}

.info-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 0 20px;
}

.info-label {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  font-weight: 500;
}

.info-value {
  font-size: 15px;
  color: var(--el-text-color-primary);
  font-weight: 600;
}

.info-divider {
  width: 1px;
  height: 40px;
  background: var(--el-border-color-light);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .home {
    padding: 24px 12px;
  }

  .welcome-title {
    font-size: 24px;
  }

  .welcome-subtitle {
    font-size: 14px;
  }

  .section-title {
    font-size: 18px;
  }

  .stat-card {
    padding: 20px 12px;
  }

  .stat-icon {
    width: 48px;
    height: 48px;
  }

  .stat-value {
    font-size: 24px;
  }

  .feature-card {
    padding: 20px;
  }

  .feature-item {
    padding: 12px;
  }

  .feature-item-icon {
    width: 40px;
    height: 40px;
  }

  .info-card {
    flex-direction: column;
    gap: 16px;
  }

  .info-divider {
    width: 100%;
    height: 1px;
  }

  .info-item {
    padding: 0;
  }
}

@media (max-width: 576px) {
  .welcome-section {
    margin-bottom: 32px;
  }

  .stats-section,
  .features-section,
  .info-section {
    margin-bottom: 32px;
  }
}
</style>
