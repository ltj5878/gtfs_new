<template>
  <div class="admin-page">
    <div class="page-header">
      <h1>运维监控看板</h1>
      <div class="header-actions">
        <el-button :icon="Bell" @click="handleCheckPunctuality" :loading="checkingAlerts" size="small">检查准点率告警</el-button>
        <el-button :icon="ChatDotRound" type="warning" @click="announcementVisible = true" size="small">发布公告</el-button>
        <el-button :icon="Refresh" @click="loadAll" :loading="loading" size="small">刷新</el-button>
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

    <!-- 顶部指标卡片 -->
    <el-row :gutter="16" class="metric-row">
      <el-col :xs="12" :sm="6">
        <div class="metric-card">
          <div class="metric-icon" style="background:#e3f2fd">
            <el-icon :size="22" color="#409eff"><DataLine /></el-icon>
          </div>
          <div class="metric-value">{{ dbStats.db_size || '--' }}</div>
          <div class="metric-label">数据库总大小</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="metric-card">
          <div class="metric-icon" style="background:#e8f5e9">
            <el-icon :size="22" color="#67c23a"><Grid /></el-icon>
          </div>
          <div class="metric-value">{{ largestTableRows }}</div>
          <div class="metric-label">最大表记录数</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="metric-card">
          <div class="metric-icon" style="background:#fef0e6">
            <el-icon :size="22" color="#e6a23c"><Connection /></el-icon>
          </div>
          <div class="metric-value">{{ apiHealth.total_calls_24h ?? '--' }}</div>
          <div class="metric-label">24h API 调用</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="metric-card" :class="{ 'metric-card--danger': errorRate > 5 }">
          <div class="metric-icon" :style="{ background: errorRate > 5 ? '#fef0f0' : '#f0f9ff' }">
            <el-icon :size="22" :color="errorRate > 5 ? '#f56c6c' : '#409eff'"><Warning /></el-icon>
          </div>
          <div class="metric-value" :style="{ color: errorRate > 5 ? '#f56c6c' : '#2c3e50' }">
            {{ apiHealth.total_calls_24h ? errorRate + '%' : '--' }}
          </div>
          <div class="metric-label">24h 错误率</div>
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
          <template #header><span>各地区数据时效</span></template>
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

    <!-- API 健康度表格 -->
    <el-card class="api-health-card">
      <template #header>
        <div class="card-header-row">
          <span>API 调用健康度（近24小时）</span>
          <el-tag v-if="apiHealth.total_calls_24h === 0" type="info" size="small">暂无调用记录</el-tag>
        </div>
      </template>
      <div v-loading="loadingApi">
        <el-table :data="apiHealth.stats || []" stripe size="small" v-if="(apiHealth.stats || []).length > 0">
          <el-table-column prop="region" label="地区" width="80">
            <template #default="{ row }">
              <el-tag :type="regionTagType(row.region)" size="small">{{ regionLabel(row.region) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="api_name" label="API 名称" width="140" />
          <el-table-column prop="total_calls" label="调用次数" width="90" align="right" />
          <el-table-column prop="avg_latency_ms" label="平均延迟" width="100" align="right">
            <template #default="{ row }">
              <span :style="{ color: row.avg_latency_ms > 3000 ? '#f56c6c' : row.avg_latency_ms > 1000 ? '#e6a23c' : '#67c23a' }">
                {{ row.avg_latency_ms }} ms
              </span>
            </template>
          </el-table-column>
          <el-table-column label="成功率" width="120">
            <template #default="{ row }">
              <el-progress
                :percentage="Math.round(row.success_count / row.total_calls * 100)"
                :color="row.success_count / row.total_calls > 0.95 ? '#67c23a' : '#f56c6c'"
                :stroke-width="8"
              />
            </template>
          </el-table-column>
          <el-table-column prop="error_count" label="错误次数" width="90" align="right">
            <template #default="{ row }">
              <span :style="{ color: row.error_count > 0 ? '#f56c6c' : '#67c23a' }">{{ row.error_count }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="max_latency_ms" label="最大延迟" align="right">
            <template #default="{ row }">{{ row.max_latency_ms }} ms</template>
          </el-table-column>
        </el-table>
        <el-empty v-else-if="!loadingApi" description="暂无 API 调用记录，启动准点率服务后将自动记录" />

        <!-- 最近错误 -->
        <div v-if="(apiHealth.recent_errors || []).length > 0" class="recent-errors">
          <div class="section-subtitle">最近错误记录</div>
          <el-table :data="apiHealth.recent_errors" size="small" stripe>
            <el-table-column prop="region" label="地区" width="70">
              <template #default="{ row }">
                <el-tag :type="regionTagType(row.region)" size="small">{{ regionLabel(row.region) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="api_name" label="API" width="120" />
            <el-table-column prop="endpoint" label="接口" show-overflow-tooltip />
            <el-table-column prop="status_code" label="状态码" width="80" align="center">
              <template #default="{ row }">
                <el-tag type="danger" size="small">{{ row.status_code }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="error_msg" label="错误信息" show-overflow-tooltip />
            <el-table-column label="时间" width="160">
              <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
            </el-table-column>
          </el-table>
        </div>
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
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import {
  Refresh, DataLine, Grid, Connection, Warning,
  CircleCheck, CircleClose, QuestionFilled, Bell, ChatDotRound
} from '@element-plus/icons-vue'
import { getDbStats, getApiHealth, getDataFreshness } from '@/api/admin.js'
import { publishAnnouncement, checkPunctualityAlerts } from '@/api/notification.js'

const loading = ref(false)
const loadingDb = ref(false)
const loadingApi = ref(false)
const loadingFreshness = ref(false)

const dbStats = ref({ db_size: '', db_bytes: 0, tables: [], active_connections: 0 })
const apiHealth = ref({ total_calls_24h: 0, error_calls_24h: 0, stats: [], recent_errors: [] })
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

const errorRate = computed(() => {
  const total = apiHealth.value.total_calls_24h
  if (!total) return 0
  return Math.round(apiHealth.value.error_calls_24h / total * 100)
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

const loadDbStats = async () => {
  loadingDb.value = true
  try {
    dbStats.value = await getDbStats()
    await nextTick()
    renderPieChart()
  } catch (e) {
    ElMessage.error('加载数据库统计失败')
  } finally {
    loadingDb.value = false
  }
}

const loadApiHealth = async () => {
  loadingApi.value = true
  try {
    apiHealth.value = await getApiHealth()
  } catch (e) {
    ElMessage.error('加载API健康度失败')
  } finally {
    loadingApi.value = false
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

const loadAll = async () => {
  loading.value = true
  await Promise.all([loadDbStats(), loadApiHealth(), loadFreshness()])
  loading.value = false
}

onMounted(() => {
  loadAll()
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
</style>
