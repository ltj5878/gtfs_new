<template>
  <div class="transfer-planner">
    <!-- 搜索区域 -->
    <div class="search-section">
      <div class="section-title">{{ $t('transfer.title') }}</div>
      <div class="search-card">
        <el-row :gutter="16" align="middle">
          <el-col :xs="24" :sm="8">
            <div class="stop-label">{{ $t('transfer.fromStop') }}</div>
            <el-select
              v-model="fromStopId"
              filterable
              clearable
              :placeholder="$t('transfer.fromPlaceholder')"
              :loading="stopsLoading"
              style="width: 100%"
              @change="onFromChange"
            >
              <el-option
                v-for="s in stopOptions"
                :key="s.stop_id"
                :label="s.stop_name"
                :value="s.stop_id"
              >
                <span>{{ s.stop_name }}</span>
                <span style="color:#999;font-size:12px;margin-left:8px">{{ s.stop_id }}</span>
              </el-option>
            </el-select>
          </el-col>

          <el-col :xs="24" :sm="1" class="swap-col">
            <el-button circle :icon="Sort" @click="swapStops" :title="$t('transfer.swapStops')" />
          </el-col>

          <el-col :xs="24" :sm="8">
            <div class="stop-label">{{ $t('transfer.toStop') }} <span v-if="reachableLoading" style="color:#909399;font-size:12px">{{ $t('transfer.loadingReachable') }}</span></div>
            <el-select
              v-model="toStopId"
              filterable
              clearable
              :placeholder="$t('transfer.toPlaceholder')"
              :loading="stopsLoading"
              style="width: 100%"
              @change="onToChange"
            >
              <el-option-group v-if="fromStopId && reachableStopIds.size > 0" :label="$t('transfer.directReachable')">
                <el-option
                  v-for="s in toStopOptions.filter(s => reachableStopIds.has(s.stop_id))"
                  :key="s.stop_id"
                  :label="s.stop_name"
                  :value="s.stop_id"
                >
                  <span>{{ s.stop_name }}</span>
                  <span style="color:#999;font-size:12px;margin-left:8px">{{ s.stop_id }}</span>
                </el-option>
              </el-option-group>
              <el-option-group :label="fromStopId && reachableStopIds.size > 0 ? t('transfer.otherStops') : t('transfer.allStops')">
                <el-option
                  v-for="s in (fromStopId && reachableStopIds.size > 0 ? toStopOptions.filter(s => !reachableStopIds.has(s.stop_id)) : toStopOptions)"
                  :key="s.stop_id"
                  :label="s.stop_name"
                  :value="s.stop_id"
                >
                  <span>{{ s.stop_name }}</span>
                  <span style="color:#999;font-size:12px;margin-left:8px">{{ s.stop_id }}</span>
                </el-option>
              </el-option-group>
            </el-select>
          </el-col>

          <el-col :xs="24" :sm="4">
            <div class="stop-label">{{ $t('transfer.strategy') }}</div>
            <el-select v-model="strategy" style="width: 100%">
              <el-option :label="$t('transfer.minTransfer')" value="min_transfer" />
              <el-option :label="$t('transfer.minTime')" value="min_time" />
            </el-select>
          </el-col>

          <el-col :xs="24" :sm="3">
            <div class="stop-label">&nbsp;</div>
            <el-button
              type="primary"
              :loading="searching"
              :disabled="!fromStopId || !toStopId"
              style="width: 100%"
              @click="doSearch"
            >
              {{ $t('transfer.search') }}
            </el-button>
          </el-col>
        </el-row>
      </div>
    </div>

    <!-- 结果区域 -->
    <div class="result-section" v-if="searched">
      <!-- 加载中 -->
      <div v-if="searching" class="status-box">
        <el-icon class="spinning"><Loading /></el-icon>
        <span>{{ $t('transfer.planning') }}</span>
      </div>

      <!-- 无结果 -->
      <div v-else-if="!searching && plans.length === 0" class="status-box empty">
        <el-icon :size="48" color="#c0c4cc"><Warning /></el-icon>
        <p>{{ $t('transfer.noResult') }}</p>
        <p class="hint">{{ $t('transfer.noResultHint') }}</p>

        <!-- 起点站和终点站经过的线路 -->
        <div v-if="fromRoutes.length > 0 || toRoutes.length > 0" class="from-routes">
          <div v-if="fromRoutes.length > 0" class="route-info-block">
            <div class="from-routes-title">{{ $t('transfer.fromRoutes', { name: fromStopName }) }}</div>
            <div class="from-routes-tags">
              <el-tag
                v-for="r in fromRoutes"
                :key="r.route_id"
                :color="r.route_color ? '#' + r.route_color : ''"
                :style="r.route_color ? { color: '#fff', borderColor: 'transparent' } : {}"
                size="default"
              >
                {{ r.route_short_name || r.route_id }}
                <span v-if="r.route_long_name" style="font-weight:400;margin-left:4px">{{ r.route_long_name }}</span>
              </el-tag>
            </div>
          </div>

          <div v-if="toRoutes.length > 0" class="route-info-block">
            <div class="from-routes-title">{{ $t('transfer.toRoutes', { name: toStopName }) }}</div>
            <div class="from-routes-tags">
              <el-tag
                v-for="r in toRoutes"
                :key="r.route_id"
                :color="r.route_color ? '#' + r.route_color : ''"
                :style="r.route_color ? { color: '#fff', borderColor: 'transparent' } : {}"
                size="default"
              >
                {{ r.route_short_name || r.route_id }}
                <span v-if="r.route_long_name" style="font-weight:400;margin-left:4px">{{ r.route_long_name }}</span>
              </el-tag>
            </div>
          </div>

          <div v-if="commonRoutes.length > 0" class="route-info-block">
            <div class="from-routes-title" style="color:#e6a23c">{{ $t('transfer.commonRoutes') }}</div>
            <div class="from-routes-tags">
              <el-tag
                v-for="r in commonRoutes"
                :key="r.route_id"
                type="warning"
                size="default"
              >
                {{ r.route_short_name || r.route_id }} {{ r.route_long_name }}
              </el-tag>
            </div>
          </div>
        </div>
      </div>

      <!-- 方案列表 -->
      <template v-else>
        <div class="result-header">
          {{ $t('transfer.foundPlans') }} <strong>{{ plans.length }}</strong> {{ $t('transfer.plansUnit') }}
          （{{ fromStopName }} → {{ toStopName }}）
        </div>

        <div
          v-for="(plan, idx) in plans"
          :key="idx"
          class="plan-card"
        >
          <!-- 方案头部 -->
          <div class="plan-header">
            <div class="plan-badges">
              <el-tag type="success" size="small" v-if="plan.transfer_count === 0">{{ $t('transfer.direct') }}</el-tag>
              <el-tag type="warning" size="small" v-else>{{ $t('transfer.transferCount', { n: plan.transfer_count }) }}</el-tag>
              <el-tag type="info" size="small">{{ $t('transfer.aboutMinutes', { n: plan.total_minutes }) }}</el-tag>
            </div>
            <div class="plan-index">{{ $t('transfer.plan') }} {{ idx + 1 }}</div>
          </div>

          <!-- 步骤时间线 -->
          <el-timeline class="plan-timeline">
            <el-timeline-item
              v-for="(seg, si) in plan.segments"
              :key="si"
              :color="seg.route_color ? '#' + seg.route_color : '#409eff'"
              size="large"
            >
              <div class="seg-content">
                <div class="seg-route">
                  <el-tag
                    size="small"
                    :color="seg.route_color ? '#' + seg.route_color : ''"
                    :style="seg.route_color ? { color: '#fff', borderColor: 'transparent' } : {}"
                  >
                    {{ seg.route_short_name || seg.route_id }}
                  </el-tag>
                  <span class="seg-route-name">{{ seg.route_long_name || seg.route_name }}</span>
                </div>
                <div class="seg-stops">
                  <span class="seg-stop from">{{ seg.from_stop_name }}</span>
                  <el-icon class="seg-arrow"><ArrowRight /></el-icon>
                  <span class="seg-stop to">{{ seg.to_stop_name }}</span>
                </div>
                <div class="seg-meta">
                  {{ $t('transfer.passingStops', { n: seg.stop_count }) }}
                  <span v-if="seg.minutes > 0">· {{ $t('transfer.aboutMinutes', { n: seg.minutes }) }}</span>
                  <span v-if="seg.depart_time" class="seg-time">
                    · {{ $t('transfer.depart') }} {{ seg.depart_time.slice(0, 5) }}
                  </span>
                </div>
              </div>
            </el-timeline-item>

            <!-- 终点 -->
            <el-timeline-item color="#67c23a" size="large">
              <div class="seg-content">
                <div class="seg-stop to" style="font-weight:600">
                  <el-icon color="#67c23a"><Location /></el-icon>
                  {{ toStopName }} {{ $t('transfer.destination') }}
                </div>
              </div>
            </el-timeline-item>
          </el-timeline>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRegionStore } from '@/stores/regionStore'
import { getStops, getStopRoutes } from '@/api/stops'
import { getRouteStops } from '@/api/routes'
import { planTransfer } from '@/api/planner'
import { ArrowRight, Location, Sort, Loading, Warning } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const regionStore = useRegionStore()
const { t } = useI18n()

const fromStopId = ref('')
const toStopId = ref('')
const strategy = ref('min_transfer')

// 全部站点列表
const stopOptions = ref([])
const stopsLoading = ref(false)

// 起点站直达可达站点 ID 集合（用于终点站分组排序）
const reachableStopIds = ref(new Set())
const reachableLoading = ref(false)

const searching = ref(false)
const searched = ref(false)
const plans = ref([])
const fromRoutes = ref([])  // 起点站线路（无结果时展示）
const toRoutes = ref([])    // 终点站线路（无结果时展示）

// 两站共同线路
const commonRoutes = computed(() => {
  if (!fromRoutes.value.length || !toRoutes.value.length) return []
  const toIds = new Set(toRoutes.value.map(r => r.route_id))
  return fromRoutes.value.filter(r => toIds.has(r.route_id))
})

const fromStopName = ref('')
const toStopName = ref('')

// 终点站列表：直达可达站点排前面
const toStopOptions = computed(() => {
  if (!fromStopId.value || reachableStopIds.value.size === 0) {
    return stopOptions.value
  }
  const reachable = []
  const others = []
  for (const s of stopOptions.value) {
    if (s.stop_id === fromStopId.value) continue  // 排除起点自身
    if (reachableStopIds.value.has(s.stop_id)) {
      reachable.push(s)
    } else {
      others.push(s)
    }
  }
  return [...reachable, ...others]
})

// 加载站点列表
const loadStops = async () => {
  stopsLoading.value = true
  fromStopId.value = ''
  toStopId.value = ''
  fromStopName.value = ''
  toStopName.value = ''
  plans.value = []
  searched.value = false
  reachableStopIds.value = new Set()
  try {
    const data = await getStops({ page_size: 500 })
    stopOptions.value = data?.stops || []
  } catch {
    ElMessage.error(t('transfer.stopsLoadFailed'))
  } finally {
    stopsLoading.value = false
  }
}

onMounted(loadStops)
watch(() => regionStore.selectedRegion, loadStops)

// 选择起点后，异步加载直达可达站点（用于终点排序）
const onFromChange = async (val) => {
  const found = stopOptions.value.find(s => s.stop_id === val)
  fromStopName.value = found ? found.stop_name : val

  // 清空终点和结果
  toStopId.value = ''
  toStopName.value = ''
  plans.value = []
  searched.value = false
  reachableStopIds.value = new Set()

  if (!val) return

  // 后台加载直达可达站点（不阻塞用户操作）
  reachableLoading.value = true
  try {
    const routes = await getStopRoutes(val) || []
    const allStopIds = new Set()
    await Promise.all(
      routes.map(async (r) => {
        try {
          const stops = await getRouteStops(r.route_id) || []
          stops.forEach(s => allStopIds.add(s.stop_id))
        } catch { /* 忽略 */ }
      })
    )
    allStopIds.delete(val)  // 排除起点自身
    reachableStopIds.value = allStopIds
  } catch { /* 忽略 */ }
  finally {
    reachableLoading.value = false
  }
}

const onToChange = (val) => {
  const found = stopOptions.value.find(s => s.stop_id === val)
  toStopName.value = found ? found.stop_name : val
}

// 交换起终点
const swapStops = () => {
  const tmpId = fromStopId.value
  const tmpName = fromStopName.value
  fromStopId.value = toStopId.value
  fromStopName.value = toStopName.value
  toStopId.value = tmpId
  toStopName.value = tmpName
  // 交换后重新加载可达站点
  if (fromStopId.value) {
    onFromChange(fromStopId.value)
  } else {
    reachableStopIds.value = new Set()
  }
}

// 执行查询
const doSearch = async () => {
  if (!fromStopId.value || !toStopId.value) return
  if (fromStopId.value === toStopId.value) {
    ElMessage.warning(t('transfer.sameStopError'))
    return
  }

  searching.value = true
  searched.value = true
  plans.value = []
  fromRoutes.value = []
  toRoutes.value = []

  try {
    const result = await planTransfer({
      from_stop_id: fromStopId.value,
      to_stop_id: toStopId.value,
      region: regionStore.selectedRegion,
      strategy: strategy.value
    })
    plans.value = result?.plans || []
    if (result?.from_stop?.stop_name) fromStopName.value = result.from_stop.stop_name
    if (result?.to_stop?.stop_name) toStopName.value = result.to_stop.stop_name

    // 无结果时并发加载起终点站经过的线路
    if (plans.value.length === 0) {
      const [fRoutes, tRoutes] = await Promise.all([
        getStopRoutes(fromStopId.value).catch(() => []),
        getStopRoutes(toStopId.value).catch(() => [])
      ])
      fromRoutes.value = fRoutes || []
      toRoutes.value = tRoutes || []
    }
  } catch {
    plans.value = []
  } finally {
    searching.value = false
  }
}
</script>

<style scoped>
.transfer-planner {
  min-height: 100vh;
  background: #f5f7fa;
  padding: 32px 20px;
}

.section-title {
  font-size: 20px;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 20px;
  padding-left: 12px;
  border-left: 4px solid #409eff;
}

.search-section {
  max-width: 1100px;
  margin: 0 auto 32px;
}

.search-card {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.stop-label {
  font-size: 13px;
  color: #606266;
  margin-bottom: 6px;
  font-weight: 500;
}

.swap-col {
  display: flex;
  align-items: flex-end;
  justify-content: center;
  padding-bottom: 2px;
}

.result-section {
  max-width: 1100px;
  margin: 0 auto;
}

.result-header {
  font-size: 15px;
  color: #606266;
  margin-bottom: 16px;
}

.status-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #909399;
  gap: 12px;
  font-size: 15px;
}

.status-box .hint {
  font-size: 13px;
  color: #c0c4cc;
}

.from-routes {
  margin-top: 20px;
  text-align: left;
  max-width: 800px;
  width: 100%;
}

.route-info-block {
  margin-bottom: 16px;
}

.from-routes-title {
  font-size: 14px;
  color: #606266;
  margin-bottom: 8px;
  font-weight: 500;
}

.from-routes-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.spinning {
  animation: spin 1s linear infinite;
  font-size: 32px;
  color: #409eff;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.plan-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px 24px;
  margin-bottom: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  transition: box-shadow 0.2s;
}

.plan-card:hover {
  box-shadow: 0 4px 16px rgba(0,0,0,0.1);
}

.plan-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f2f5;
}

.plan-badges {
  display: flex;
  gap: 8px;
}

.plan-index {
  font-size: 13px;
  color: #c0c4cc;
}

.plan-timeline {
  padding-left: 4px;
}

.seg-content {
  padding: 2px 0 8px;
}

.seg-route {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.seg-route-name {
  font-size: 14px;
  color: #606266;
}

.seg-stops {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.seg-stop {
  font-size: 14px;
  color: #2c3e50;
}

.seg-stop.from {
  font-weight: 600;
}

.seg-stop.to {
  font-weight: 600;
}

.seg-arrow {
  color: #c0c4cc;
  font-size: 14px;
}

.seg-meta {
  font-size: 12px;
  color: #909399;
}

.seg-time {
  color: #409eff;
}

@media (max-width: 768px) {
  .transfer-planner {
    padding: 20px 12px;
  }

  .swap-col {
    justify-content: flex-start;
    padding: 8px 0;
  }
}
</style>
