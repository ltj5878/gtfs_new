<template>
  <div class="data-export-page">
    <div class="page-header">
      <div class="header-content">
        <h1>{{ $t('dataExportPage.title') }}</h1>
        <p>{{ $t('dataExportPage.subtitle') }}</p>
      </div>
    </div>

    <div class="export-cards">
      <div v-for="item in exportItems" :key="item.key" class="export-card">
        <div class="card-icon" :style="{ backgroundColor: item.iconBg }">
          <el-icon :size="24" :color="item.iconColor"><component :is="item.icon" /></el-icon>
        </div>
        <div class="card-body">
          <div class="card-title">{{ item.name }}</div>
          <div class="card-desc">{{ item.desc }}</div>
          <div class="card-options" v-if="item.hasDays">
            <span class="option-label">{{ $t('dataExportPage.timeRange') }}</span>
            <el-select v-model="item.days" size="small" style="width: 130px">
              <el-option :label="$t('dataExportPage.last7Days')" :value="7" />
              <el-option :label="$t('dataExportPage.last30Days')" :value="30" />
              <el-option :label="$t('dataExportPage.last90Days')" :value="90" />
            </el-select>
          </div>
          <div class="card-actions">
            <el-button size="small" @click="doExport(item, 'csv')" :loading="item.loading === 'csv'">
              <el-icon><Document /></el-icon> CSV
            </el-button>
            <el-button size="small" type="success" @click="doExport(item, 'excel')" :loading="item.loading === 'excel'">
              <el-icon><Grid /></el-icon> Excel
            </el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/stores/authStore.js'
import { useRegionStore } from '@/stores/regionStore.js'
import { Guide, Location, TrendCharts, DataLine, Document, Grid, EditPen } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getRoutes } from '@/api/routes.js'
import { getStops } from '@/api/stops.js'
import { getRoutePunctuality, getStopPunctuality } from '@/api/punctuality.js'
import { getAuditLogs } from '@/api/audit.js'
import { exportCSV, exportExcel } from '@/utils/exportHelper.js'

const { t } = useI18n()
const authStore = useAuthStore()
const regionStore = useRegionStore()

// 各导出项配置
const exportItems = reactive([
  {
    key: 'routes', icon: Guide, iconBg: '#e3f2fd', iconColor: '#409eff',
    get name() { return t('dataExportPage.routes') },
    get desc() { return t('dataExportPage.routesDesc') },
    hasDays: false, loading: false,
  },
  {
    key: 'stops', icon: Location, iconBg: '#e8f5e9', iconColor: '#67c23a',
    get name() { return t('dataExportPage.stops') },
    get desc() { return t('dataExportPage.stopsDesc') },
    hasDays: false, loading: false,
  },
  {
    key: 'routePunctuality', icon: TrendCharts, iconBg: '#fef0e6', iconColor: '#e6a23c',
    get name() { return t('dataExportPage.routePunctuality') },
    get desc() { return t('dataExportPage.routePunctualityDesc') },
    hasDays: true, days: 7, loading: false,
  },
  {
    key: 'stopPunctuality', icon: Location, iconBg: '#f3e5f5', iconColor: '#9c27b0',
    get name() { return t('dataExportPage.stopPunctuality') },
    get desc() { return t('dataExportPage.stopPunctualityDesc') },
    hasDays: true, days: 7, loading: false,
  },
  {
    key: 'trends', icon: DataLine, iconBg: '#e8eaf6', iconColor: '#5c6bc0',
    get name() { return t('dataExportPage.trends') },
    get desc() { return t('dataExportPage.trendsDesc') },
    hasDays: true, days: 30, loading: false,
  },
  ...(authStore.isAdmin ? [{
    key: 'auditLogs', icon: EditPen, iconBg: '#fff3e0', iconColor: '#ff9800',
    get name() { return t('dataExportPage.auditLogs') },
    get desc() { return t('dataExportPage.auditLogsDesc') },
    hasDays: true, days: 7, loading: false,
  }] : []),
])

// 获取数据并导出
const doExport = async (item, format) => {
  item.loading = format
  try {
    const { headers, rows, filename } = await fetchExportData(item)
    if (!rows.length) {
      ElMessage.warning(t('dataExportPage.noData'))
      return
    }
    if (format === 'csv') exportCSV(headers, rows, filename)
    else if (format === 'excel') exportExcel(headers, rows, filename, item.name)
    ElMessage.success(t('dataExportPage.exportSuccess', { count: rows.length }))
  } catch (e) {
    console.error('导出失败:', e)
    ElMessage.error(t('dataExportPage.exportFailed'))
  } finally {
    item.loading = false
  }
}

// 根据数据类型获取数据并转换为 headers + rows
const fetchExportData = async (item) => {
  const region = regionStore.selectedRegion
  const date = new Date().toISOString().slice(0, 10)

  switch (item.key) {
    case 'routes': {
      const data = await getRoutes({ page_size: 500 })
      const list = data?.routes || []
      const headers = [t('dataExportPage.hRouteId'), t('dataExportPage.hShortName'), t('dataExportPage.hLongName'), t('dataExportPage.hRouteType'), t('dataExportPage.hAgency')]
      const rows = list.map(r => [r.route_id, r.route_short_name || '', r.route_long_name || '', r.route_type, r.agency_id || ''])
      return { headers, rows, filename: `routes_${region}_${date}` }
    }
    case 'stops': {
      const data = await getStops({ page_size: 500 })
      const list = data?.stops || []
      const headers = [t('dataExportPage.hStopId'), t('dataExportPage.hStopName'), t('dataExportPage.hLat'), t('dataExportPage.hLon')]
      const rows = list.map(s => [s.stop_id, s.stop_name || '', s.stop_lat || '', s.stop_lon || ''])
      return { headers, rows, filename: `stops_${region}_${date}` }
    }
    case 'routePunctuality': {
      const list = await getRoutePunctuality({ days: item.days, limit: 1000 }) || []
      const headers = [t('dataExportPage.hRouteId'), t('dataExportPage.hShortName'), t('dataExportPage.hLongName'), t('dataExportPage.hRate'), t('dataExportPage.hTrips'), t('dataExportPage.hOnTime'), t('dataExportPage.hLate'), t('dataExportPage.hVeryLate'), t('dataExportPage.hAvgDelay')]
      const rows = list.map(r => [r.route_id, r.route_short_name || '', r.route_long_name || '', (r.avg_punctuality_rate || 0).toFixed(1), r.total_trips || 0, r.on_time_trips || 0, r.late_trips || 0, r.very_late_trips || 0, (r.avg_delay_minutes || 0).toFixed(1)])
      return { headers, rows, filename: `route_punctuality_${region}_${item.days}d_${date}` }
    }
    case 'stopPunctuality': {
      const list = await getStopPunctuality({ days: item.days, limit: 10000 }) || []
      const headers = [t('dataExportPage.hStopId'), t('dataExportPage.hStopName'), t('dataExportPage.hRate'), t('dataExportPage.hVisits'), t('dataExportPage.hAvgDelay')]
      const rows = list.map(s => [s.stop_id, s.stop_name || '', (s.avg_punctuality_rate || 0).toFixed(1), s.total_visits || 0, (s.avg_delay_minutes || 0).toFixed(1)])
      return { headers, rows, filename: `stop_punctuality_${region}_${item.days}d_${date}` }
    }
    case 'trends': {
      const { getRoutePunctuality: getTrends } = await import('@/api/punctuality.js')
      const list = await getTrends({ days: item.days, limit: 1000 }) || []
      const headers = [t('dataExportPage.hDate'), t('dataExportPage.hRate'), t('dataExportPage.hTrips')]
      const rows = list.map(r => [r.stat_date || '', (r.avg_punctuality_rate || r.punctuality_rate || 0).toFixed(1), r.total_trips || 0])
      return { headers, rows, filename: `punctuality_trends_${region}_${item.days}d_${date}` }
    }
    case 'auditLogs': {
      const now = new Date()
      const start = new Date(now.getTime() - item.days * 86400000)
      const pad = (n) => String(n).padStart(2, '0')
      const startStr = `${start.getFullYear()}-${pad(start.getMonth() + 1)}-${pad(start.getDate())} 00:00:00`
      const res = await getAuditLogs({ page: 1, page_size: 10000, start_time: startStr })
      const data = res?.data || res
      const list = data?.list || []
      const headers = ['ID', t('dataExportPage.hUser'), t('dataExportPage.hAction'), t('dataExportPage.hTarget'), t('dataExportPage.hDetail'), t('dataExportPage.hIp'), t('dataExportPage.hTime')]
      const rows = list.map(r => [r.id, r.username || '', r.action, r.target || '', typeof r.detail === 'object' ? JSON.stringify(r.detail) : (r.detail || ''), r.ip_address || '', r.created_at || ''])
      return { headers, rows, filename: `audit_logs_${item.days}d_${date}` }
    }
    default:
      return { headers: [], rows: [], filename: 'export' }
  }
}
</script>

<style scoped>
.data-export-page {
  padding: 20px;
  background: var(--el-bg-color-page);
  min-height: 100vh;
}

.page-header {
  margin-bottom: 24px;
  padding: 24px;
  background: var(--el-bg-color);
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.header-content h1 {
  margin: 0 0 8px 0;
  color: var(--el-text-color-primary);
  font-size: 28px;
  font-weight: 600;
}

.header-content p {
  margin: 0;
  color: var(--el-text-color-secondary);
  font-size: 14px;
}

.export-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.export-card {
  display: flex;
  gap: 16px;
  padding: 24px;
  background: var(--el-bg-color);
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  transition: box-shadow 0.2s;
}

.export-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.card-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.card-body {
  flex: 1;
  min-width: 0;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin-bottom: 4px;
}

.card-desc {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  margin-bottom: 12px;
}

.card-options {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.option-label {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  white-space: nowrap;
}

.card-actions {
  display: flex;
  gap: 8px;
}

@media (max-width: 768px) {
  .export-cards {
    grid-template-columns: 1fr;
  }
}

</style>
