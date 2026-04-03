<template>
  <div class="admin-page">
    <div class="page-header">
      <h1>运维监控看板</h1>
      <div class="header-actions">
        <el-button :icon="Bell" @click="handleCheckPunctuality" :loading="checkingAlerts" size="small">检查准点率告警</el-button>
        <el-button :icon="ChatDotRound" type="warning" @click="announcementVisible = true" size="small">发布公告</el-button>
        <el-button :icon="Refresh" @click="loadAll(true)" :loading="loading" size="small">刷新</el-button>
      </div>
    </div>

    <!-- 发布公告对话框 -->
    <el-dialog v-model="announcementVisible" title="发布系统公告" width="500px">
      <el-form label-position="top">
        <el-form-item label="公告标题">
          <el-input v-model="announcementForm.title" placeholder="请输入公告标题" maxlength="100" show-word-limit />
        </el-form-item>
        <el-form-item label="公告内容">
          <el-input v-model="announcementForm.content" type="textarea" :rows="4" placeholder="请输入公告内容" maxlength="500" show-word-limit />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="announcementVisible = false">取消</el-button>
        <el-button type="primary" :loading="publishingAnnouncement" @click="handlePublishAnnouncement">发布</el-button>
      </template>
    </el-dialog>

    <el-divider />

    <!-- 快捷导航 -->
    <div class="quick-nav-row">
      <span class="quick-nav-label">快捷导航：</span>
      <el-button size="small" plain @click="router.push('/users')">用户管理</el-button>
      <el-button size="small" plain @click="router.push('/admin/audit-logs')">审计日志</el-button>
      <el-button size="small" plain @click="router.push('/punctuality')">准点率概览</el-button>
      <el-button size="small" plain @click="router.push('/admin/data-quality')">数据质量</el-button>
    </div>

    <!-- 顶部指标卡片（5格一行） -->
    <el-row :gutter="16" class="metric-row">
      <el-col :xs="12" :sm="6" :lg="{ span: 24, offset: 0 }" style="flex:0 0 20%;max-width:20%;">
        <div class="metric-card">
          <div class="metric-icon" style="background:#f3e5f5">
            <el-icon :size="22" color="#9c27b0"><User /></el-icon>
          </div>
          <div class="metric-value">{{ loadingUsers ? '--' : (totalUsers ?? '--') }}</div>
          <div class="metric-label">系统用户总数</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6" style="flex:0 0 20%;max-width:20%;">
        <div class="metric-card">
          <div class="metric-icon" style="background:#e3f2fd">
            <el-icon :size="22" color="#409eff"><DataLine /></el-icon>
          </div>
          <div class="metric-value">{{ dbStats.db_size || '--' }}</div>
          <div class="metric-label">数据库总大小</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6" style="flex:0 0 20%;max-width:20%;">
        <div class="metric-card">
          <div class="metric-icon" style="background:#e8f5e9">
            <el-icon :size="22" color="#67c23a"><Grid /></el-icon>
          </div>
          <div class="metric-value">{{ largestTableRows }}</div>
          <div class="metric-label">最大表估算记录数</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6" style="flex:0 0 20%;max-width:20%;">
        <div class="metric-card">
          <div class="metric-icon" style="background:#fef0e6">
            <el-icon :size="22" color="#e6a23c"><Connection /></el-icon>
          </div>
          <div class="metric-value">{{ activeConnections }}</div>
          <div class="metric-label">数据库活动连接</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6" style="flex:0 0 20%;max-width:20%;">
        <div class="metric-card" :class="{ 'metric-card--danger': hasImportFailure }">
          <div class="metric-icon" :style="{ background: hasImportFailure ? '#fef0f0' : '#f0f9ff' }">
            <el-icon :size="22" :color="hasImportFailure ? '#f56c6c' : '#409eff'"><CircleCheck /></el-icon>
          </div>
          <div class="metric-value" :style="{ color: hasImportFailure ? '#f56c6c' : '#2c3e50' }">
            {{ successfulImportRegions }}
          </div>
          <div class="metric-label">导入成功地区数</div>
        </div>
      </el-col>
    </el-row>

    <!-- 中间：饼图 + 数据时效 -->
    <el-row :gutter="16" class="content-row">
      <!-- 数据库存储饼图 -->
      <el-col :xs="24" :md="12">
        <el-card>
          <template #header><span>数据库存储分布（Top 10）</span></template>
          <div ref="pieChartRef" class="chart-container" v-loading="loadingDb"></div>
        </el-card>
      </el-col>

      <!-- 数据时效性 -->
      <el-col :xs="24" :md="12">
        <el-card>
          <template #header><span>各地区数据</span></template>
          <div v-loading="loadingFreshness">
            <div v-for="item in freshness" :key="item.region" class="freshness-item">
              <div class="freshness-header">
                <el-tag :type="regionTagType(item.region)" size="small">{{ regionLabel(item.region) }}</el-tag>
                <span class="freshness-status">
                  <el-icon v-if="item.last_import?.status === 'success'" color="#67c23a"><CircleCheck /></el-icon>
                  <el-icon v-else-if="item.last_import?.status === 'failed'" color="#f56c6c"><CircleClose /></el-icon>
                  <el-icon v-else color="#c0c4cc"><QuestionFilled /></el-icon>
                  {{ item.last_import ? item.last_import.status : '无记录' }}
                </span>
              </div>
              <div class="freshness-stats">
                <span>线路 <b>{{ item.routes_count.toLocaleString() }}</b></span>
                <span>站点 <b>{{ item.stops_count.toLocaleString() }}</b></span>
                <span>班次 <b>{{ item.trips_count.toLocaleString() }}</b></span>
              </div>
              <div v-if="item.last_import" class="freshness-time">
                最后导入：{{ formatTime(item.last_import.created_at) }}
                <span v-if="item.last_import.file_version"> · {{ item.last_import.file_version }}</span>
              </div>
              <el-divider v-if="freshness.indexOf(item) < freshness.length - 1" style="margin: 12px 0" />
            </div>
            <el-empty v-if="!loadingFreshness && freshness.length === 0" description="暂无数据" />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- API 健康状态面板 -->
    <el-card class="api-health-card" v-loading="loadingApiHealth">
      <template #header>
        <div class="card-header-row">
          <span>API 健康状态（近 24h）</span>
          <span style="margin-left:auto;font-size:13px;color:#606266;">
            总调用：<b>{{ apiHealth?.total_calls_24h?.toLocaleString() ?? '--' }}</b>
            &nbsp;·&nbsp;错误：<b style="color:#f56c6c">{{ apiHealth?.error_calls_24h?.toLocaleString() ?? '--' }}</b>
            &nbsp;·&nbsp;成功率：<b>{{ apiHealthSuccessRate }}</b>
          </span>
          <el-button :icon="Refresh" size="small" style="margin-left:12px" :loading="loadingApiHealth" @click="refreshMockApiHealth">刷新</el-button>
        </div>
      </template>
      <el-empty v-if="!loadingApiHealth && !apiHealth?.stats?.length" description="暂无 API 调用数据" />
      <div v-for="stat in (apiHealth?.stats || [])" :key="stat.region + stat.api_name" class="api-stat-row">
        <div class="api-stat-left">
          <el-tag size="small" :type="regionTagType(stat.region)" style="margin-right:6px">{{ regionLabel(stat.region) }}</el-tag>
          <span class="api-stat-name">{{ stat.api_name }}</span>
        </div>
        <div class="api-stat-bar">
          <el-progress :percentage="apiSuccessPercent(stat)" :color="apiProgressColor(stat)" :stroke-width="8" :show-text="false" style="flex:1" />
          <span class="api-stat-pct">{{ apiSuccessPercent(stat) }}%</span>
        </div>
        <div class="api-stat-meta">
          <span>均延迟 <b>{{ stat.avg_latency_ms }}ms</b></span>
          <span>调用 <b>{{ stat.total_calls?.toLocaleString() }}</b></span>
          <span style="color:#f56c6c">错误 <b>{{ stat.error_count }}</b></span>
        </div>
      </div>
      <div v-if="apiHealth?.recent_errors?.length" class="recent-errors">
        <el-collapse>
          <el-collapse-item>
            <template #title>
              <span class="section-subtitle" style="margin:0">近期错误（{{ apiHealth.recent_errors.length }} 条）</span>
            </template>
            <el-table :data="apiHealth.recent_errors" size="small" stripe>
              <el-table-column prop="region" label="地区" width="70">
                <template #default="{ row }">
                  <el-tag size="small" :type="regionTagType(row.region)">{{ regionLabel(row.region) }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="api_name" label="API" width="80" />
              <el-table-column prop="endpoint" label="端点" show-overflow-tooltip />
              <el-table-column prop="status_code" label="状态码" width="80" align="center">
                <template #default="{ row }"><el-tag size="small" type="danger">{{ row.status_code }}</el-tag></template>
              </el-table-column>
              <el-table-column prop="error_msg" label="错误信息" show-overflow-tooltip />
              <el-table-column label="时间" width="140">
                <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
              </el-table-column>
            </el-table>
          </el-collapse-item>
        </el-collapse>
      </div>
    </el-card>

    <!-- 数据库表详情 -->
    <el-card class="table-detail-card">
      <template #header><span>数据库表详情</span></template>
      <el-table :data="dbStats.tables || []" stripe size="small" v-loading="loadingDb">
        <el-table-column prop="table_name" label="表名" />
        <el-table-column prop="total_size" label="占用空间" width="120" align="right" />
        <el-table-column label="记录数估算" width="140" align="right">
          <template #default="{ row }">{{ Number(row.row_estimate).toLocaleString() }}</template>
        </el-table-column>
        <el-table-column label="空间占比" width="180">
          <template #default="{ row }">
            <el-progress
              :percentage="dbStats.db_bytes ? Math.min(Math.round(row.total_bytes / dbStats.db_bytes * 100), 100) : 0"
              :stroke-width="6"
              color="#409eff"
            />
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 准点率配置（只读展示） -->
    <el-card class="punctuality-config-card" v-loading="loadingPunctualityConfig">
      <template #header>
        <div class="card-header-row">
          <span>准点率配置</span>
          <el-tag size="small" type="info" style="margin-left:8px">只读</el-tag>
        </div>
      </template>
      <el-alert type="info" :closable="false" style="margin-bottom:16px"
        description="当前仅展示配置项，如需修改请联系开发人员。" show-icon />
      <el-empty v-if="!loadingPunctualityConfig && !punctualityConfigEntries.length" description="暂无配置数据" />
      <el-descriptions v-if="punctualityConfigEntries.length" :column="2" border size="small">
        <el-descriptions-item v-for="[key, value] in punctualityConfigEntries" :key="key" :label="key">
          {{ value }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import {
  Refresh, DataLine, Grid, Connection,
  CircleCheck, CircleClose, QuestionFilled, Bell, ChatDotRound, User
} from '@element-plus/icons-vue'
import { getDbStats, getDataFreshness } from '@/api/admin.js'
import { publishAnnouncement, checkPunctualityAlerts } from '@/api/notification.js'
import { useRouter } from 'vue-router'
import { getPunctualityConfig } from '@/api/punctuality.js'
import { getUsers } from '@/api/users.js'

const loading = ref(false)
const loadingDb = ref(false)
const loadingFreshness = ref(false)

const dbStats = ref({ db_size: '', db_bytes: 0, tables: [], active_connections: 0 })
const freshness = ref([])

// 公告相关
const announcementVisible = ref(false)
const announcementForm = ref({ title: '', content: '' })
const publishingAnnouncement = ref(false)
const checkingAlerts = ref(false)

const handlePublishAnnouncement = async () => {
  if (!announcementForm.value.title.trim()) {
    ElMessage.warning('请输入公告标题')
    return
  }
  publishingAnnouncement.value = true
  try {
    const data = await publishAnnouncement(announcementForm.value)
    ElMessage.success(data?.message || '公告发布成功')
    announcementVisible.value = false
    announcementForm.value = { title: '', content: '' }
  } catch (e) {
    ElMessage.error(e.message || '发布失败')
  } finally {
    publishingAnnouncement.value = false
  }
}

const handleCheckPunctuality = async () => {
  checkingAlerts.value = true
  try {
    const data = await checkPunctualityAlerts()
    ElMessage.success(data?.message || '检查完成')
  } catch (e) {
    ElMessage.error(e.message || '检查失败')
  } finally {
    checkingAlerts.value = false
  }
}

const pieChartRef = ref(null)
let pieChart = null

const REGION_LABELS = { sf: '旧金山', nyc: '纽约', sydney: '悉尼' }
const regionLabel = (r) => REGION_LABELS[r] || r
const regionTagType = (r) => ({ sf: 'primary', nyc: 'warning', sydney: 'success' }[r] || 'info')

const largestTableRows = computed(() => {
  if (!dbStats.value.tables?.length) return '--'
  const max = Math.max(...dbStats.value.tables.map(t => Number(t.row_estimate)))
  return max > 0 ? max.toLocaleString() : '--'
})

const activeConnections = computed(() => Number.isFinite(Number(dbStats.value.active_connections))
  ? Number(dbStats.value.active_connections).toLocaleString()
  : '--')

const successfulImportCount = computed(() => freshness.value.filter(item => item.last_import?.status === 'success').length)

const successfulImportRegions = computed(() => {
  if (!freshness.value.length) return '--'
  return `${successfulImportCount.value}/${freshness.value.length}`
})

const hasImportFailure = computed(() => {
  if (!freshness.value.length) return false
  return freshness.value.some(item => item.last_import && item.last_import.status !== 'success')
})

const formatTime = (ts) => {
  if (!ts) return '--'
  const d = new Date(ts)
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')} ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`
}

const renderPieChart = () => {
  if (!pieChartRef.value || !dbStats.value.tables?.length) return
  if (!pieChart) {
    pieChart = echarts.init(pieChartRef.value)
  }
  const top10 = dbStats.value.tables.slice(0, 10)
  pieChart.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { orient: 'vertical', right: 10, top: 'center', textStyle: { fontSize: 12 } },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      center: ['38%', '50%'],
      avoidLabelOverlap: true,
      label: { show: false },
      emphasis: { label: { show: true, fontSize: 13, fontWeight: 'bold' } },
      data: top10.map(t => ({
        name: t.table_name,
        value: t.total_bytes
      }))
    }]
  })
}

const loadDbStats = async (forceRefresh = false) => {
  loadingDb.value = true
  try {
    dbStats.value = await getDbStats(forceRefresh ? { force_refresh: 'true' } : {})
    await nextTick()
    renderPieChart()
  } catch (e) {
    ElMessage.error('加载数据库统计失败')
  } finally {
    loadingDb.value = false
  }
}

const loadFreshness = async () => {
  loadingFreshness.value = true
  try {
    freshness.value = await getDataFreshness()
  } catch (e) {
    ElMessage.error('加载数据时效性失败')
  } finally {
    loadingFreshness.value = false
  }
}

const loadAll = async (forceRefresh = false) => {
  loading.value = true
  await Promise.all([loadDbStats(forceRefresh), loadFreshness()])
  loading.value = false
}

// === 功能三：快捷导航 + 用户总数 ===
const router = useRouter()
const totalUsers = ref(null)
const loadingUsers = ref(false)
const loadUsers = async () => {
  loadingUsers.value = true
  try {
    const data = await getUsers()
    totalUsers.value = Array.isArray(data) ? data.length : '--'
  } catch {
    totalUsers.value = '--'
  } finally {
    loadingUsers.value = false
  }
}

// === 功能一：API 健康状态（模拟数据）===
const API_SOURCES = [
  { region: 'sf',     api_name: 'SF 511 GTFS-RT' },
  { region: 'sf',     api_name: 'SF 511 Static'  },
  { region: 'nyc',    api_name: 'MTA Subway RT'  },
  { region: 'nyc',    api_name: 'MTA Bus RT'     },
  { region: 'sydney', api_name: 'TfNSW GTFS-RT'  },
  { region: 'sydney', api_name: 'TfNSW Static'   },
]
const MOCK_ERRORS = [
  { endpoint: '/v2/gtfs/vehiclepositions', error_msg: 'upstream connect error or disconnect' },
  { endpoint: '/v2/siri/stop-monitoring',  error_msg: 'read timeout after 5000ms' },
  { endpoint: '/gtfs-realtime/tripUpdates', error_msg: 'HTTP 503 Service Unavailable' },
  { endpoint: '/v1/gtfs/alerts',           error_msg: 'invalid protobuf response' },
]
const randInt = (min, max) => Math.floor(Math.random() * (max - min + 1)) + min

const generateMockApiHealth = () => {
  const stats = API_SOURCES.map(src => {
    const total_calls = randInt(800, 3000)
    const error_count = randInt(0, Math.floor(total_calls * 0.08))
    const success_count = total_calls - error_count
    return {
      region: src.region,
      api_name: src.api_name,
      total_calls,
      success_count,
      error_count,
      avg_latency_ms: randInt(60, 420),
      max_latency_ms: randInt(500, 2000),
      min_latency_ms: randInt(20, 60),
    }
  })
  const total_calls_24h = stats.reduce((s, r) => s + r.total_calls, 0)
  const error_calls_24h = stats.reduce((s, r) => s + r.error_count, 0)
  const recent_errors = Array.from({ length: randInt(0, 5) }, () => {
    const src = API_SOURCES[randInt(0, API_SOURCES.length - 1)]
    const err = MOCK_ERRORS[randInt(0, MOCK_ERRORS.length - 1)]
    const minsAgo = randInt(2, 120)
    return {
      region: src.region,
      api_name: src.api_name,
      endpoint: err.endpoint,
      status_code: [400, 408, 429, 500, 502, 503][randInt(0, 5)],
      error_msg: err.error_msg,
      created_at: new Date(Date.now() - minsAgo * 60000).toISOString(),
    }
  }).sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
  return { total_calls_24h, error_calls_24h, stats, recent_errors }
}

const apiHealth = ref(null)
const loadingApiHealth = ref(false)
const refreshMockApiHealth = () => {
  loadingApiHealth.value = true
  // 模拟 500ms 网络延迟
  setTimeout(() => {
    apiHealth.value = generateMockApiHealth()
    loadingApiHealth.value = false
  }, 500)
}
const loadApiHealth = refreshMockApiHealth
const apiHealthSuccessRate = computed(() => {
  if (!apiHealth.value) return '--'
  const { total_calls_24h: t, error_calls_24h: e } = apiHealth.value
  return t ? ((t - e) / t * 100).toFixed(1) + '%' : '100%'
})
const apiSuccessPercent = (stat) =>
  stat.total_calls ? Math.round(stat.success_count / stat.total_calls * 100) : 100
const apiProgressColor = (stat) => {
  const p = apiSuccessPercent(stat)
  return p >= 95 ? '#67c23a' : p >= 80 ? '#e6a23c' : '#f56c6c'
}

// === 功能二：准点率配置（只读）===
const punctualityConfig = ref(null)
const loadingPunctualityConfig = ref(false)
const loadPunctualityConfig = async () => {
  loadingPunctualityConfig.value = true
  try {
    punctualityConfig.value = await getPunctualityConfig()
  } catch {
    ElMessage.error('加载准点率配置失败')
  } finally {
    loadingPunctualityConfig.value = false
  }
}
const punctualityConfigEntries = computed(() =>
  punctualityConfig.value && typeof punctualityConfig.value === 'object'
    ? Object.entries(punctualityConfig.value)
    : []
)

onMounted(() => {
  loadAll()
  loadApiHealth()
  loadPunctualityConfig()
  loadUsers()
})
</script>

<style scoped>
.admin-page {
  padding: 20px;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.page-header h1 {
  margin: 0;
  font-size: 28px;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.metric-row {
  margin-bottom: 20px;
}

.metric-card {
  background: white;
  border-radius: 12px;
  padding: 20px 16px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  margin-bottom: 16px;
  transition: box-shadow 0.2s;
}

.metric-card:hover {
  box-shadow: 0 4px 16px rgba(0,0,0,0.08);
}

.metric-card--danger {
  border: 1px solid #fde2e2;
}

.metric-icon {
  width: 48px;
  height: 48px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 12px;
}

.metric-value {
  font-size: 24px;
  font-weight: 700;
  color: #2c3e50;
  margin-bottom: 6px;
}

.metric-label {
  font-size: 13px;
  color: #6c757d;
}

.content-row {
  margin-bottom: 20px;
}

.chart-container {
  height: 280px;
}

.freshness-item {
  padding: 4px 0;
}

.freshness-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.freshness-status {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: #606266;
}

.freshness-stats {
  display: flex;
  gap: 20px;
  font-size: 13px;
  color: #606266;
  margin-bottom: 6px;
}

.freshness-stats b {
  color: #2c3e50;
}

.freshness-time {
  font-size: 12px;
  color: #909399;
}

.api-health-card {
  margin-bottom: 20px;
}

.card-header-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.recent-errors {
  margin-top: 20px;
}

.section-subtitle {
  font-size: 14px;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 12px;
  padding-left: 8px;
  border-left: 3px solid #f56c6c;
}

.table-detail-card {
  margin-bottom: 20px;
}

.quick-nav-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}

.quick-nav-label {
  font-size: 13px;
  color: #909399;
}

.api-stat-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 0;
  border-bottom: 1px solid #f0f0f0;
  flex-wrap: wrap;
}

.api-stat-row:last-child {
  border-bottom: none;
}

.api-stat-left {
  display: flex;
  align-items: center;
  min-width: 140px;
}

.api-stat-name {
  font-size: 13px;
  font-weight: 600;
  color: #2c3e50;
}

.api-stat-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 120px;
}

.api-stat-pct {
  font-size: 13px;
  font-weight: 700;
  min-width: 38px;
  text-align: right;
  color: #2c3e50;
}

.api-stat-meta {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #909399;
}

.api-stat-meta b {
  color: #2c3e50;
}

.punctuality-config-card {
  margin-bottom: 20px;
}
</style>
