<template>
  <div class="alert-center-page">
    <div class="page-header">
      <h1>{{ $t('alertCenter.title') }}</h1>
      <div class="header-actions">
        <el-button :icon="Refresh" @click="handleRefresh" :loading="loading" size="small">{{ $t('common.refresh') }}</el-button>
      </div>
    </div>
    <p class="page-subtitle">{{ $t('alertCenter.subtitle') }}</p>

    <!-- 统计卡片 -->
    <el-row :gutter="16" class="stat-row">
      <el-col :xs="12" :sm="6">
        <div class="stat-card" :class="{ 'stat-danger': stats.active_count > 0 }">
          <div class="stat-value">{{ stats.active_count ?? '--' }}</div>
          <div class="stat-label">{{ $t('alertCenter.activeAlerts') }}</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-value">{{ stats.today_count ?? '--' }}</div>
          <div class="stat-label">{{ $t('alertCenter.todayAlerts') }}</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-value">{{ criticalCount }}</div>
          <div class="stat-label">{{ $t('alertCenter.criticalAlerts') }}</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-value">{{ historyTotal }}</div>
          <div class="stat-label">{{ $t('alertCenter.weekTotal') }}</div>
        </div>
      </el-col>
    </el-row>

    <!-- 趋势图 -->
    <el-card class="trend-card" v-if="stats.by_day?.length">
      <template #header><span>{{ $t('alertCenter.trendChart') }}</span></template>
      <div ref="trendRef" class="trend-chart"></div>
    </el-card>

    <!-- 活跃告警 -->
    <el-card class="alert-list-card">
      <template #header>
        <div class="card-header-row">
          <span>{{ $t('alertCenter.activeAlerts') }} ({{ activeAlerts.length }})</span>
        </div>
      </template>
      <div v-if="activeAlerts.length === 0 && !loading" class="empty-tip">
        {{ $t('alertCenter.noActiveAlerts') }}
      </div>
      <div v-for="alert in activeAlerts" :key="alert.id" class="alert-item" :class="'alert-' + alert.severity">
        <div class="alert-header">
          <el-tag :type="severityType(alert.severity)" size="small">{{ severityLabel(alert.severity) }}</el-tag>
          <span class="alert-type-badge">{{ alertTypeLabel(alert.alert_type) }}</span>
          <span class="alert-time">{{ formatTime(alert.triggered_at) }}</span>
          <el-button v-if="authStore.isAdmin" size="small" type="success" plain @click.stop="handleResolve(alert.id)">
            {{ $t('alertCenter.resolve') }}
          </el-button>
        </div>
        <div class="alert-title">{{ alert.title }}</div>
        <div class="alert-entity" v-if="alert.entity_name">
          {{ alert.entity_type }}: {{ alert.entity_name }} ({{ alert.entity_id }})
        </div>
      </div>
    </el-card>

    <!-- 历史告警 -->
    <el-card>
      <template #header>
        <div class="card-header-row">
          <span>{{ $t('alertCenter.historyAlerts') }}</span>
          <el-select v-model="historyDays" size="small" style="width:120px" @change="loadHistory">
            <el-option :label="$t('alertCenter.last7Days')" :value="7" />
            <el-option :label="$t('alertCenter.last30Days')" :value="30" />
          </el-select>
        </div>
      </template>
      <el-table :data="historyAlerts" stripe size="small" v-loading="loadingHistory">
        <el-table-column prop="severity" :label="$t('alertCenter.severityCol')" width="90">
          <template #default="{ row }">
            <el-tag :type="severityType(row.severity)" size="small">{{ severityLabel(row.severity) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="alert_type" :label="$t('alertCenter.typeCol')" width="120">
          <template #default="{ row }">{{ alertTypeLabel(row.alert_type) }}</template>
        </el-table-column>
        <el-table-column prop="title" :label="$t('alertCenter.titleCol')" show-overflow-tooltip />
        <el-table-column prop="entity_name" :label="$t('alertCenter.entityCol')" width="150" show-overflow-tooltip />
        <el-table-column :label="$t('alertCenter.triggeredAt')" width="160">
          <template #default="{ row }">{{ formatTime(row.triggered_at) }}</template>
        </el-table-column>
        <el-table-column :label="$t('alertCenter.statusCol')" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.resolved_at" type="success" size="small">{{ $t('alertCenter.resolved') }}</el-tag>
            <el-tag v-else type="danger" size="small">{{ $t('alertCenter.active') }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination-row" v-if="historyTotal > historyPageSize">
        <el-pagination
          v-model:current-page="historyPage"
          :page-size="historyPageSize"
          :total="historyTotal"
          layout="prev, pager, next"
          @current-change="loadHistory"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import * as echarts from 'echarts'
import { getActiveAlerts, getAlertHistory, resolveAlert, getAlertStats } from '@/api/alerts.js'
import { useRegionStore } from '@/stores/regionStore'
import { useAuthStore } from '@/stores/authStore'

const { t } = useI18n()
const regionStore = useRegionStore()
const authStore = useAuthStore()

const loading = ref(false)
const loadingHistory = ref(false)
const activeAlerts = ref([])
const historyAlerts = ref([])
const stats = ref({})
const historyDays = ref(7)
const historyPage = ref(1)
const historyPageSize = 20
const historyTotal = ref(0)
const trendRef = ref(null)
let trendChart = null

const criticalCount = computed(() =>
  activeAlerts.value.filter(a => a.severity === 'critical' || a.severity === 'high').length
)

function severityType(s) {
  if (s === 'critical') return 'danger'
  if (s === 'high') return 'warning'
  if (s === 'medium') return 'info'
  return 'info'
}
function severityLabel(s) {
  const map = { critical: t('alertCenter.critical'), high: t('alertCenter.high'), medium: t('alertCenter.medium'), low: t('alertCenter.low') }
  return map[s] || s
}
function alertTypeLabel(t_) {
  const map = {
    vehicle_stall: t('alertCenter.typeVehicleStall'),
    route_delay: t('alertCenter.typeRouteDelay'),
    stop_congestion: t('alertCenter.typeStopCongestion'),
    segment_slow: t('alertCenter.typeSegmentSlow')
  }
  return map[t_] || t_
}
function formatTime(t_) {
  if (!t_) return ''
  return new Date(t_).toLocaleString('zh-CN')
}

async function loadAll(forceRefresh = false) {
  loading.value = true
  try {
    const region = regionStore.selectedRegion
    const active = await getActiveAlerts({
      region,
      ...(forceRefresh ? { refresh: 1 } : {})
    })
    const [statsData] = await Promise.all([
      getAlertStats({ region }),
      loadHistory()
    ])
    activeAlerts.value = active || []
    stats.value = statsData || {}
    renderTrend()
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

function handleRefresh() {
  loadAll(true)
}

async function loadHistory() {
  loadingHistory.value = true
  try {
    const data = await getAlertHistory({
      region: regionStore.selectedRegion,
      days: historyDays.value,
      page: historyPage.value,
      page_size: historyPageSize
    })
    historyAlerts.value = data?.items || []
    historyTotal.value = data?.total || 0
  } catch (e) {
    console.error(e)
  } finally {
    loadingHistory.value = false
  }
}

async function handleResolve(id) {
  try {
    await resolveAlert(id)
    ElMessage.success(t('alertCenter.resolveSuccess'))
    await loadAll()
  } catch (e) {
    ElMessage.error(t('common.operationFailed'))
  }
}

function renderTrend() {
  nextTick(() => {
    if (!trendRef.value) return
    const byDay = stats.value.by_day || []
    if (!byDay.length) return
    if (!trendChart) trendChart = echarts.init(trendRef.value)
    trendChart.setOption({
      tooltip: { trigger: 'axis' },
      grid: { left: 40, right: 20, top: 10, bottom: 30 },
      xAxis: { type: 'category', data: byDay.map(d => d.day) },
      yAxis: { type: 'value', minInterval: 1 },
      series: [{
        type: 'bar',
        data: byDay.map(d => d.cnt),
        itemStyle: { color: '#f56c6c', borderRadius: [4, 4, 0, 0] }
      }]
    })
  })
}

watch(() => regionStore.selectedRegion, () => loadAll())
onMounted(() => loadAll())
</script>

<style scoped>
.alert-center-page { padding: 20px; max-width: 1200px; margin: 0 auto; }
.page-header { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; }
.page-header h1 { margin: 0; font-size: 22px; }
.header-actions { display: flex; gap: 8px; }
.page-subtitle { color: #909399; font-size: 14px; margin: 4px 0 16px; }
.stat-row { margin-bottom: 16px; }
.stat-card {
  text-align: center; padding: 16px; border-radius: 8px; background: #f5f7fa;
}
.stat-card .stat-value { font-size: 28px; font-weight: bold; color: #303133; }
.stat-card .stat-label { font-size: 13px; color: #909399; margin-top: 4px; }
.stat-danger .stat-value { color: #f56c6c; }
.trend-card { margin-bottom: 16px; }
.trend-chart { width: 100%; height: 200px; }
.alert-list-card { margin-bottom: 16px; }
.card-header-row { display: flex; justify-content: space-between; align-items: center; }
.empty-tip { text-align: center; color: #909399; padding: 20px; }
.alert-item {
  padding: 12px; border-left: 4px solid #dcdfe6; margin-bottom: 8px;
  border-radius: 4px; background: #fafafa;
}
.alert-critical { border-left-color: #f56c6c; background: #fef0f0; }
.alert-high { border-left-color: #e6a23c; background: #fdf6ec; }
.alert-medium { border-left-color: #409eff; background: #ecf5ff; }
.alert-low { border-left-color: #909399; }
.alert-header { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.alert-type-badge { font-size: 12px; color: #606266; background: #e8e8e8; padding: 2px 6px; border-radius: 3px; }
.alert-time { font-size: 12px; color: #909399; margin-left: auto; }
.alert-title { font-size: 14px; font-weight: 500; margin-top: 6px; }
.alert-entity { font-size: 12px; color: #909399; margin-top: 4px; }
.pagination-row { display: flex; justify-content: center; margin-top: 12px; }

html.dark .stat-card { background: #1a1a2e; }
html.dark .alert-item { background: #1a1a2e; }
html.dark .alert-critical { background: #2a1a1a; }
html.dark .alert-high { background: #2a2a1a; }
html.dark .alert-medium { background: #1a1a2a; }
</style>
