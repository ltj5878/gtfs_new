<template>
  <div class="data-quality-page">
    <div class="page-header">
      <h1>{{ $t('dataQuality.title') }}</h1>
      <div class="header-actions">
        <el-button :icon="Refresh" @click="loadData" :loading="loading" size="small">{{ $t('common.refresh') }}</el-button>
        <el-button type="primary" :icon="CaretRight" @click="handleRunCheck" :loading="running" size="small">
          {{ $t('dataQuality.runCheck') }}
        </el-button>
      </div>
    </div>
    <p class="page-subtitle">{{ $t('dataQuality.subtitle') }}</p>

    <!-- 质量分仪表盘 + 统计卡片 -->
    <el-row :gutter="16" class="metric-row">
      <el-col :xs="24" :sm="8">
        <el-card class="gauge-card" v-loading="loading">
          <div ref="gaugeRef" class="gauge-chart"></div>
          <div class="gauge-label">{{ $t('dataQuality.qualityScore') }}</div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="16">
        <el-row :gutter="16">
          <el-col :xs="8" :sm="8">
            <div class="stat-card stat-error">
              <div class="stat-value">{{ latestCheck?.total_errors ?? '--' }}</div>
              <div class="stat-label">{{ $t('dataQuality.errors') }}</div>
            </div>
          </el-col>
          <el-col :xs="8" :sm="8">
            <div class="stat-card stat-warning">
              <div class="stat-value">{{ latestCheck?.total_warnings ?? '--' }}</div>
              <div class="stat-label">{{ $t('dataQuality.warnings') }}</div>
            </div>
          </el-col>
          <el-col :xs="8" :sm="8">
            <div class="stat-card stat-info">
              <div class="stat-value">{{ latestCheck?.total_infos ?? '--' }}</div>
              <div class="stat-label">{{ $t('dataQuality.infos') }}</div>
            </div>
          </el-col>
        </el-row>
        <div class="check-meta" v-if="latestCheck">
          <span>{{ $t('dataQuality.lastCheck') }}{{ formatTime(latestCheck.check_time) }}</span>
          <span>{{ $t('dataQuality.duration') }}{{ latestCheck.check_duration_ms }}ms</span>
          <span v-if="latestCheck.feed_version">Feed: {{ latestCheck.feed_version }}</span>
        </div>
      </el-col>
    </el-row>

    <!-- 历史趋势 -->
    <el-card class="trend-card" v-if="history.length > 1">
      <template #header><span>{{ $t('dataQuality.historyTrend') }}</span></template>
      <div ref="trendRef" class="trend-chart"></div>
    </el-card>

    <!-- 问题列表 -->
    <el-card class="issues-card">
      <template #header>
        <div class="card-header-row">
          <span>{{ $t('dataQuality.issueList') }}</span>
          <el-radio-group v-model="severityFilter" size="small" @change="loadIssues">
            <el-radio-button value="">{{ $t('dataQuality.all') }}</el-radio-button>
            <el-radio-button value="ERROR">{{ $t('dataQuality.errors') }}</el-radio-button>
            <el-radio-button value="WARNING">{{ $t('dataQuality.warnings') }}</el-radio-button>
            <el-radio-button value="INFO">{{ $t('dataQuality.infos') }}</el-radio-button>
          </el-radio-group>
        </div>
      </template>
      <el-table :data="issues" stripe size="small" v-loading="loadingIssues">
        <el-table-column prop="rule_code" :label="$t('dataQuality.ruleCode')" width="90" />
        <el-table-column prop="severity" :label="$t('dataQuality.severity')" width="100">
          <template #default="{ row }">
            <el-tag :type="severityTagType(row.severity)" size="small">{{ row.severity }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="entity_type" :label="$t('dataQuality.entityType')" width="100" />
        <el-table-column prop="description" :label="$t('dataQuality.description')" show-overflow-tooltip />
        <el-table-column prop="affected_count" :label="$t('dataQuality.affected')" width="100" align="right">
          <template #default="{ row }">{{ row.affected_count?.toLocaleString() }}</template>
        </el-table-column>
        <el-table-column prop="suggestion" :label="$t('dataQuality.suggestion')" show-overflow-tooltip />
      </el-table>
      <div class="pagination-row" v-if="issueTotal > issuePageSize">
        <el-pagination
          v-model:current-page="issuePage"
          :page-size="issuePageSize"
          :total="issueTotal"
          layout="prev, pager, next"
          @current-change="loadIssues"
        />
      </div>
    </el-card>

    <!-- 规则说明 -->
    <el-card>
      <template #header>
        <div class="card-header-row" style="cursor:pointer" @click="showRules = !showRules">
          <span>{{ $t('dataQuality.ruleReference') }}</span>
          <el-icon><ArrowDown v-if="!showRules" /><ArrowUp v-else /></el-icon>
        </div>
      </template>
      <el-table v-if="showRules" :data="rules" stripe size="small">
        <el-table-column prop="code" :label="$t('dataQuality.ruleCode')" width="90" />
        <el-table-column prop="severity" :label="$t('dataQuality.severity')" width="100">
          <template #default="{ row }">
            <el-tag :type="severityTagType(row.severity)" size="small">{{ row.severity }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="category" :label="$t('dataQuality.category')" width="120" />
        <el-table-column prop="description" :label="$t('dataQuality.description')" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch } from 'vue'
import { Refresh, CaretRight, ArrowDown, ArrowUp } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import * as echarts from 'echarts'
import { getLatestCheck, getQualityIssues, getQualityHistory, runQualityCheck, getQualityRules } from '@/api/dataQuality.js'
import { useRegionStore } from '@/stores/regionStore'

const { t } = useI18n()
const regionStore = useRegionStore()

const loading = ref(false)
const running = ref(false)
const loadingIssues = ref(false)
const latestCheck = ref(null)
const history = ref([])
const issues = ref([])
const rules = ref([])
const showRules = ref(false)
const severityFilter = ref('')
const issuePage = ref(1)
const issuePageSize = 20
const issueTotal = ref(0)

const gaugeRef = ref(null)
const trendRef = ref(null)
let gaugeChart = null
let trendChart = null

function severityTagType(s) {
  if (s === 'ERROR') return 'danger'
  if (s === 'WARNING') return 'warning'
  return 'info'
}

function formatTime(t) {
  if (!t) return ''
  return new Date(t).toLocaleString('zh-CN')
}

async function loadData() {
  loading.value = true
  try {
    const region = regionStore.selectedRegion
    const [checkData, historyData, rulesData] = await Promise.all([
      getLatestCheck({ region }),
      getQualityHistory({ region }),
      getQualityRules()
    ])
    latestCheck.value = checkData
    history.value = historyData || []
    rules.value = rulesData || []
    renderGauge()
    renderTrend()
    await loadIssues()
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function loadIssues() {
  loadingIssues.value = true
  try {
    const data = await getQualityIssues({
      region: regionStore.selectedRegion,
      severity: severityFilter.value,
      page: issuePage.value,
      page_size: issuePageSize
    })
    issues.value = data?.items || []
    issueTotal.value = data?.total || 0
  } catch (e) {
    console.error(e)
  } finally {
    loadingIssues.value = false
  }
}

async function handleRunCheck() {
  running.value = true
  try {
    await runQualityCheck({ region: regionStore.selectedRegion })
    ElMessage.success(t('dataQuality.checkComplete'))
    await loadData()
  } catch (e) {
    ElMessage.error(t('dataQuality.checkFailed'))
  } finally {
    running.value = false
  }
}

function renderGauge() {
  nextTick(() => {
    if (!gaugeRef.value) return
    if (!gaugeChart) gaugeChart = echarts.init(gaugeRef.value)
    const score = latestCheck.value?.quality_score ?? 0
    gaugeChart.setOption({
      series: [{
        type: 'gauge',
        startAngle: 200,
        endAngle: -20,
        min: 0,
        max: 100,
        splitNumber: 10,
        itemStyle: {
          color: score >= 80 ? '#67c23a' : score >= 60 ? '#e6a23c' : '#f56c6c'
        },
        progress: { show: true, roundCap: true, width: 14 },
        pointer: { show: false },
        axisLine: { lineStyle: { width: 14, color: [[1, '#e0e0e0']] } },
        axisTick: { show: false },
        splitLine: { show: false },
        axisLabel: { show: false },
        title: { show: false },
        detail: {
          valueAnimation: true,
          fontSize: 36,
          fontWeight: 'bold',
          offsetCenter: [0, '0%'],
          formatter: '{value}',
          color: score >= 80 ? '#67c23a' : score >= 60 ? '#e6a23c' : '#f56c6c'
        },
        data: [{ value: score }]
      }]
    })
  })
}

function renderTrend() {
  nextTick(() => {
    if (!trendRef.value || history.value.length < 2) return
    if (!trendChart) trendChart = echarts.init(trendRef.value)
    const sorted = [...history.value].reverse()
    trendChart.setOption({
      tooltip: { trigger: 'axis' },
      grid: { left: 50, right: 20, top: 20, bottom: 30 },
      xAxis: {
        type: 'category',
        data: sorted.map(h => new Date(h.check_time).toLocaleDateString('zh-CN'))
      },
      yAxis: { type: 'value', min: 0, max: 100 },
      series: [{
        name: t('dataQuality.qualityScore'),
        type: 'line',
        data: sorted.map(h => h.quality_score),
        smooth: true,
        areaStyle: { opacity: 0.15 },
        lineStyle: { width: 2 },
        itemStyle: { color: '#409eff' }
      }]
    })
  })
}

watch(() => regionStore.selectedRegion, () => loadData())

onMounted(() => {
  loadData()
  window.addEventListener('resize', () => {
    gaugeChart?.resize()
    trendChart?.resize()
  })
})
</script>

<style scoped>
.data-quality-page { padding: 20px; max-width: 1200px; margin: 0 auto; }
.page-header { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; }
.page-header h1 { margin: 0; font-size: 22px; }
.header-actions { display: flex; gap: 8px; }
.page-subtitle { color: #909399; font-size: 14px; margin: 4px 0 16px; }
.metric-row { margin-bottom: 16px; }
.gauge-card { text-align: center; }
.gauge-chart { width: 100%; height: 200px; }
.gauge-label { font-size: 14px; color: #606266; margin-top: -10px; }
.stat-card {
  text-align: center; padding: 20px; border-radius: 8px;
  margin-bottom: 12px; background: #f5f7fa;
}
.stat-card .stat-value { font-size: 32px; font-weight: bold; }
.stat-card .stat-label { font-size: 13px; color: #909399; margin-top: 4px; }
.stat-error .stat-value { color: #f56c6c; }
.stat-warning .stat-value { color: #e6a23c; }
.stat-info .stat-value { color: #409eff; }
.check-meta { display: flex; gap: 16px; font-size: 13px; color: #909399; margin-top: 8px; flex-wrap: wrap; }
.trend-card { margin-bottom: 16px; }
.trend-chart { width: 100%; height: 250px; }
.issues-card { margin-bottom: 16px; }
.card-header-row { display: flex; justify-content: space-between; align-items: center; }
.pagination-row { display: flex; justify-content: center; margin-top: 12px; }

/* 深色模式 */
html.dark .stat-card { background: #1a1a2e; }
html.dark .data-quality-page { color: #e0e0e0; }
</style>
