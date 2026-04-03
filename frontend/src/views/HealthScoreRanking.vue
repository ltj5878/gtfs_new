<template>
  <div class="health-score-page">
    <div class="page-header">
      <h1>{{ $t('healthScore.title') }}</h1>
      <div class="header-actions">
        <el-select v-model="sortBy" size="small" style="width:160px" @change="loadScores">
          <el-option :label="$t('healthScore.sortTotal')" value="total_score" />
          <el-option :label="$t('healthScore.sortPunctuality')" value="punctuality_score" />
          <el-option :label="$t('healthScore.sortFrequency')" value="frequency_score" />
          <el-option :label="$t('healthScore.sortCoverage')" value="coverage_score" />
          <el-option :label="$t('healthScore.sortDelay')" value="delay_dist_score" />
        </el-select>
        <el-button :icon="Refresh" @click="handleRefresh" :loading="loading" size="small">{{ $t('common.refresh') }}</el-button>
      </div>
    </div>
    <p class="page-subtitle">{{ $t('healthScore.subtitle') }}</p>

    <!-- 排行榜 -->
    <el-card v-loading="loading">
      <el-table :data="scores" stripe size="small" @row-click="showDetail">
        <el-table-column type="index" label="#" width="50" />
        <el-table-column :label="$t('healthScore.route')" min-width="160">
          <template #default="{ row }">
            <span class="route-badge" :style="{ background: routeColor(row.total_score) }">
              {{ row.route_short_name || row.route_id }}
            </span>
            <span class="route-name">{{ row.route_long_name }}</span>
          </template>
        </el-table-column>
        <el-table-column :label="$t('healthScore.totalScore')" width="110" align="center" sortable prop="total_score">
          <template #default="{ row }">
            <span class="score-badge" :style="{ color: scoreColor(row.total_score) }">
              {{ row.total_score?.toFixed(1) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column :label="$t('healthScore.punctuality')" width="120" align="center">
          <template #default="{ row }">
            <el-progress :percentage="row.punctuality_score" :color="scoreColor(row.punctuality_score)"
              :stroke-width="6" :show-text="false" style="width:60px;display:inline-block" />
            <span class="dim-score">{{ row.punctuality_score?.toFixed(0) }}</span>
          </template>
        </el-table-column>
        <el-table-column :label="$t('healthScore.frequency')" width="120" align="center">
          <template #default="{ row }">
            <el-progress :percentage="row.frequency_score" :color="scoreColor(row.frequency_score)"
              :stroke-width="6" :show-text="false" style="width:60px;display:inline-block" />
            <span class="dim-score">{{ row.frequency_score?.toFixed(0) }}</span>
          </template>
        </el-table-column>
        <el-table-column :label="$t('healthScore.coverage')" width="120" align="center">
          <template #default="{ row }">
            <el-progress :percentage="Math.min(row.coverage_score, 100)" :color="scoreColor(row.coverage_score)"
              :stroke-width="6" :show-text="false" style="width:60px;display:inline-block" />
            <span class="dim-score">{{ row.coverage_score?.toFixed(0) }}</span>
          </template>
        </el-table-column>
        <el-table-column :label="$t('healthScore.delayDist')" width="120" align="center">
          <template #default="{ row }">
            <el-progress :percentage="row.delay_dist_score" :color="scoreColor(row.delay_dist_score)"
              :stroke-width="6" :show-text="false" style="width:60px;display:inline-block" />
            <span class="dim-score">{{ row.delay_dist_score?.toFixed(0) }}</span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 详情抽屉 -->
    <el-drawer v-model="drawerVisible" :title="detailTitle" size="500px">
      <div v-if="detailData" class="detail-content">
        <!-- 雷达图 -->
        <div ref="radarRef" class="radar-chart"></div>
        <!-- 历史趋势 -->
        <h4>{{ $t('healthScore.historyTrend') }}</h4>
        <div ref="historyRef" class="history-chart"></div>
      </div>
      <el-empty v-else :description="$t('common.noData')" />
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import { useI18n } from 'vue-i18n'
import * as echarts from 'echarts'
import { getHealthScores, getRouteHealthDetail } from '@/api/healthScore.js'
import { useRegionStore } from '@/stores/regionStore'

const { t } = useI18n()
const regionStore = useRegionStore()

const loading = ref(false)
const scores = ref([])
const sortBy = ref('total_score')
const drawerVisible = ref(false)
const detailData = ref(null)
const detailTitle = ref('')
const radarRef = ref(null)
const historyRef = ref(null)
let radarChart = null
let historyChart = null

function normalizeScore(item) {
  if (!item) return null
  return {
    ...item,
    punctuality_score: Number(item.punctuality_score ?? 0),
    frequency_score: Number(item.frequency_score ?? 0),
    coverage_score: Number(item.coverage_score ?? 0),
    delay_dist_score: Number(item.delay_dist_score ?? 0),
    total_score: Number(item.total_score ?? 0)
  }
}

function scoreColor(v) {
  if (v >= 80) return '#67c23a'
  if (v >= 60) return '#e6a23c'
  return '#f56c6c'
}
function routeColor(v) {
  if (v >= 80) return '#f0f9eb'
  if (v >= 60) return '#fdf6ec'
  return '#fef0f0'
}

async function loadScores(forceRefresh = false) {
  loading.value = true
  try {
    const data = await getHealthScores({
      region: regionStore.selectedRegion,
      sort_by: sortBy.value,
      order: 'desc',
      limit: 100,
      ...(forceRefresh ? { refresh: 1 } : {})
    })
    scores.value = Array.isArray(data) ? data.map(normalizeScore) : []
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

function handleRefresh() {
  loadScores(true)
}

async function showDetail(row) {
  detailTitle.value = `${row.route_short_name || row.route_id} - ${row.route_long_name || ''}`
  drawerVisible.value = true
  try {
    const data = await getRouteHealthDetail(row.route_id, {
      region: regionStore.selectedRegion
    })
    detailData.value = {
      latest: normalizeScore(data?.latest),
      history: Array.isArray(data?.history) ? data.history.map(normalizeScore) : []
    }
    renderRadar(detailData.value?.latest)
    renderHistory(detailData.value?.history || [])
  } catch (e) {
    console.error(e)
  }
}

function renderRadar(data) {
  nextTick(() => {
    if (!radarRef.value || !data) return
    if (!radarChart) radarChart = echarts.init(radarRef.value)
    radarChart.setOption({
      radar: {
        indicator: [
          { name: t('healthScore.punctuality'), max: 100 },
          { name: t('healthScore.frequency'), max: 100 },
          { name: t('healthScore.coverage'), max: 100 },
          { name: t('healthScore.delayDist'), max: 100 }
        ],
        shape: 'circle'
      },
      series: [{
        type: 'radar',
        data: [{
          value: [
            data.punctuality_score,
            data.frequency_score,
            data.coverage_score,
            data.delay_dist_score
          ],
          name: t('healthScore.totalScore'),
          areaStyle: { opacity: 0.2 }
        }]
      }]
    })
  })
}

function renderHistory(data) {
  nextTick(() => {
    if (!historyRef.value || !data.length) return
    if (!historyChart) historyChart = echarts.init(historyRef.value)
    const sorted = [...data].reverse()
    historyChart.setOption({
      tooltip: { trigger: 'axis' },
      grid: { left: 40, right: 20, top: 10, bottom: 30 },
      xAxis: {
        type: 'category',
        data: sorted.map(h => h.score_date)
      },
      yAxis: { type: 'value', min: 0, max: 100 },
      series: [{
        type: 'line',
        data: sorted.map(h => h.total_score),
        smooth: true,
        areaStyle: { opacity: 0.1 },
        itemStyle: { color: '#409eff' }
      }]
    })
  })
}

watch(() => regionStore.selectedRegion, () => loadScores())
onMounted(() => loadScores())
</script>

<style scoped>
.health-score-page { padding: 20px; max-width: 1200px; margin: 0 auto; }
.page-header { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; }
.page-header h1 { margin: 0; font-size: 22px; }
.header-actions { display: flex; gap: 8px; }
.page-subtitle { color: #909399; font-size: 14px; margin: 4px 0 16px; }
.route-badge {
  display: inline-block; padding: 2px 8px; border-radius: 4px;
  font-weight: 600; font-size: 13px; margin-right: 8px;
}
.route-name { color: #606266; font-size: 13px; }
.score-badge { font-size: 18px; font-weight: bold; }
.dim-score { font-size: 12px; color: #909399; margin-left: 4px; }
.detail-content { padding: 0 8px; }
.radar-chart { width: 100%; height: 300px; }
.history-chart { width: 100%; height: 200px; }
.history-chart + h4 { margin-top: 20px; }
h4 { margin: 16px 0 8px; font-size: 15px; color: #303133; }

html.dark .route-badge { color: #303133; }
</style>
