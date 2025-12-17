<template>
  <div class="home">
    <!-- 欢迎区域 -->
    <div class="welcome-section">
      <h1 class="welcome-title">GTFS 公交数据分析系统</h1>
      <p class="welcome-subtitle">公交数据实时监控与分析平台</p>
    </div>

    <!-- 统计数据卡片 -->
    <div class="stats-section">
      <div class="section-title">数据概览</div>
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
        <!-- 基础功能 -->
        <el-col :xs="24" :md="12">
          <div class="feature-card">
            <div class="feature-header">
              <el-icon :size="20" color="#409eff"><Guide /></el-icon>
              <span class="feature-title">基础功能</span>
            </div>
            <div class="feature-content">
              <div class="feature-item" @click="$router.push('/routes')">
                <div class="feature-item-icon" style="background-color: #e3f2fd;">
                  <el-icon :size="20" color="#409eff"><Guide /></el-icon>
                </div>
                <div class="feature-item-text">
                  <div class="feature-item-title">浏览线路</div>
                  <div class="feature-item-desc">查看所有公交线路信息</div>
                </div>
                <el-icon class="feature-item-arrow"><ArrowRight /></el-icon>
              </div>

              <div class="feature-item" @click="$router.push('/stops')">
                <div class="feature-item-icon" style="background-color: #e8f5e9;">
                  <el-icon :size="20" color="#67c23a"><Location /></el-icon>
                </div>
                <div class="feature-item-text">
                  <div class="feature-item-title">查找站点</div>
                  <div class="feature-item-desc">搜索和定位公交站点</div>
                </div>
                <el-icon class="feature-item-arrow"><ArrowRight /></el-icon>
              </div>

              <div class="feature-item" @click="$router.push('/map')">
                <div class="feature-item-icon" style="background-color: #f3e5f5;">
                  <el-icon :size="20" color="#909399"><MapLocation /></el-icon>
                </div>
                <div class="feature-item-text">
                  <div class="feature-item-title">地图视图</div>
                  <div class="feature-item-desc">在地图上查看线路和站点</div>
                </div>
                <el-icon class="feature-item-arrow"><ArrowRight /></el-icon>
              </div>
            </div>
          </div>
        </el-col>

        <!-- 准点率分析 -->
        <el-col :xs="24" :md="12">
          <div class="feature-card">
            <div class="feature-header">
              <el-icon :size="20" color="#e6a23c"><TrendCharts /></el-icon>
              <span class="feature-title">准点率分析</span>
            </div>
            <div class="feature-content">
              <div class="feature-item" @click="$router.push('/punctuality')">
                <div class="feature-item-icon" style="background-color: #fef0e6;">
                  <el-icon :size="20" color="#e6a23c"><TrendCharts /></el-icon>
                </div>
                <div class="feature-item-text">
                  <div class="feature-item-title">准点率概览</div>
                  <div class="feature-item-desc">查看整体准点率统计</div>
                </div>
                <el-icon class="feature-item-arrow"><ArrowRight /></el-icon>
              </div>

              <div class="feature-item" @click="$router.push('/punctuality/routes')">
                <div class="feature-item-icon" style="background-color: #e3f2fd;">
                  <el-icon :size="20" color="#409eff"><Guide /></el-icon>
                </div>
                <div class="feature-item-text">
                  <div class="feature-item-title">线路准点率</div>
                  <div class="feature-item-desc">分析各线路准点情况</div>
                </div>
                <el-icon class="feature-item-arrow"><ArrowRight /></el-icon>
              </div>

              <div class="feature-item" @click="$router.push('/punctuality/stops')">
                <div class="feature-item-icon" style="background-color: #e8f5e9;">
                  <el-icon :size="20" color="#67c23a"><Location /></el-icon>
                </div>
                <div class="feature-item-text">
                  <div class="feature-item-title">站点准点率</div>
                  <div class="feature-item-desc">查看站点到达准点率</div>
                </div>
                <el-icon class="feature-item-arrow"><ArrowRight /></el-icon>
              </div>

              <div class="feature-item" @click="$router.push('/punctuality/realtime')">
                <div class="feature-item-icon" style="background-color: #fee;">
                  <el-icon :size="20" color="#f56c6c"><Monitor /></el-icon>
                </div>
                <div class="feature-item-text">
                  <div class="feature-item-title">实时监控</div>
                  <div class="feature-item-desc">实时车辆位置和状态</div>
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
          <span class="info-label">数据来源</span>
          <span class="info-value">511 SF Bay API</span>
        </div>
        <div class="info-divider"></div>
        <div class="info-item">
          <span class="info-label">覆盖区域</span>
          <span class="info-value">旧金山湾区</span>
        </div>
        <div class="info-divider"></div>
        <div class="info-item">
          <span class="info-label">数据类型</span>
          <span class="info-value">GTFS 静态 + 实时数据</span>
        </div>
        <div class="info-divider"></div>
        <div class="info-item">
          <span class="info-label">更新频率</span>
          <span class="info-value">每周更新</span>
        </div>
      </div>
    </div>
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
  DataLine,
  Monitor,
  ArrowRight
} from '@element-plus/icons-vue'

const router = useRouter()
const appStore = useAppStore()

const stats = ref({})

// 统计数据配置
const statsData = {
  agencies: {
    label: '运营机构',
    icon: TrendCharts,
    color: '#e3f2fd'
  },
  routes: {
    label: '线路数量',
    icon: Guide,
    color: '#e8f5e9'
  },
  stops: {
    label: '站点数量',
    icon: Location,
    color: '#fef0e6'
  },
  trips: {
    label: '班次数量',
    icon: Timer,
    color: '#f3e5f5'
  },
  stop_times: {
    label: '时刻表记录',
    icon: DataLine,
    color: '#e0f2f1'
  },
  shapes: {
    label: '轨迹数量',
    icon: Position,
    color: '#fce4ec'
  }
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
  min-height: 100vh;
  background: linear-gradient(to bottom, #f8f9fa 0%, #ffffff 100%);
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
  color: #2c3e50;
  margin-bottom: 12px;
  letter-spacing: 0.5px;
}

.welcome-subtitle {
  font-size: 16px;
  color: #6c757d;
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
  color: #2c3e50;
  margin-bottom: 24px;
  padding-left: 12px;
  border-left: 4px solid #409eff;
}

.stat-card {
  background: white;
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
  color: #2c3e50;
  margin-bottom: 8px;
  line-height: 1;
}

.stat-label {
  font-size: 13px;
  color: #6c757d;
  font-weight: 500;
}

/* 功能导航区域 */
.features-section {
  max-width: 1200px;
  margin: 0 auto 48px;
}

.feature-card {
  background: white;
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
  border-bottom: 2px solid #f5f7fa;
}

.feature-title {
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
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
  background: #fafbfc;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid transparent;
}

.feature-item:hover {
  background: #f5f7fa;
  border-color: #e4e7ed;
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
  color: #2c3e50;
  margin-bottom: 4px;
}

.feature-item-desc {
  font-size: 13px;
  color: #6c757d;
}

.feature-item-arrow {
  color: #c0c4cc;
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
  background: white;
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
  color: #6c757d;
  font-weight: 500;
}

.info-value {
  font-size: 15px;
  color: #2c3e50;
  font-weight: 600;
}

.info-divider {
  width: 1px;
  height: 40px;
  background: #e4e7ed;
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
