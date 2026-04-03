<template>
  <div class="recommendations-page">
    <div class="page-header">
      <h1>{{ $t('recommendations.title') }}</h1>
      <div class="header-actions">
        <el-button :icon="Refresh" @click="loadData" :loading="loading" size="small">{{ $t('common.refresh') }}</el-button>
      </div>
    </div>
    <p class="page-subtitle">{{ $t('recommendations.subtitle') }}</p>

    <!-- 推荐卡片列表 -->
    <div v-loading="loading">
      <el-empty v-if="!loading && !recommendations.length" :description="$t('recommendations.noData')" />
      <div class="rec-grid">
        <div v-for="(rec, idx) in recommendations" :key="rec.route_id" class="rec-card" @click="goToRoute(rec.route_id)">
          <div class="rec-rank">{{ idx + 1 }}</div>
          <div class="rec-body">
            <div class="rec-header">
              <span class="rec-route-badge" :style="{ background: routeTypeColor(rec.route_type) }">
                {{ rec.route_short_name || rec.route_id }}
              </span>
              <span class="rec-route-name">{{ rec.route_long_name }}</span>
            </div>
            <div class="rec-meta">
              <el-tag v-if="rec.punctuality_rate != null" size="small"
                :type="rec.punctuality_rate >= 80 ? 'success' : rec.punctuality_rate >= 60 ? 'warning' : 'danger'">
                {{ $t('recommendations.punctuality') }}: {{ rec.punctuality_rate?.toFixed(1) }}%
              </el-tag>
              <span class="rec-reason">{{ rec.reason }}</span>
            </div>
          </div>
          <el-icon class="rec-arrow"><ArrowRight /></el-icon>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Refresh, ArrowRight } from '@element-plus/icons-vue'
import { useI18n } from 'vue-i18n'
import { getRecommendations } from '@/api/recommendations.js'
import { useRegionStore } from '@/stores/regionStore'

const { t } = useI18n()
const router = useRouter()
const regionStore = useRegionStore()

const loading = ref(false)
const recommendations = ref([])

const ROUTE_TYPE_COLORS = {
  0: '#9c27b0', 1: '#1565c0', 2: '#2e7d32', 3: '#f57c00',
  4: '#0097a7', 5: '#d32f2f', 6: '#5d4037', 7: '#455a64'
}
function routeTypeColor(t_) {
  return ROUTE_TYPE_COLORS[t_] || '#909399'
}

async function loadData() {
  loading.value = true
  try {
    recommendations.value = await getRecommendations({
      region: regionStore.selectedRegion,
      limit: 10
    }) || []
  } catch (e) {
    console.error(e)
    recommendations.value = []
  } finally {
    loading.value = false
  }
}

function goToRoute(routeId) {
  router.push(`/routes/${routeId}`)
}

watch(() => regionStore.selectedRegion, () => loadData())
onMounted(() => loadData())
</script>

<style scoped>
.recommendations-page { padding: 20px; max-width: 1000px; margin: 0 auto; }
.page-header { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; }
.page-header h1 { margin: 0; font-size: 22px; }
.header-actions { display: flex; gap: 8px; }
.page-subtitle { color: #909399; font-size: 14px; margin: 4px 0 16px; }
.rec-grid { display: flex; flex-direction: column; gap: 12px; }
.rec-card {
  display: flex; align-items: center; gap: 16px; padding: 16px 20px;
  background: #fff; border-radius: 10px; border: 1px solid #ebeef5;
  cursor: pointer; transition: all 0.2s;
}
.rec-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.08); transform: translateY(-1px); }
.rec-rank {
  width: 36px; height: 36px; border-radius: 50%; background: #f5f7fa;
  display: flex; align-items: center; justify-content: center;
  font-weight: bold; font-size: 16px; color: #409eff; flex-shrink: 0;
}
.rec-card:nth-child(1) .rec-rank { background: #fef0e6; color: #e6a23c; }
.rec-card:nth-child(2) .rec-rank { background: #f5f7fa; color: #909399; }
.rec-card:nth-child(3) .rec-rank { background: #fef0e6; color: #cd7f32; }
.rec-body { flex: 1; min-width: 0; }
.rec-header { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.rec-route-badge {
  display: inline-block; padding: 3px 10px; border-radius: 4px;
  color: #fff; font-weight: 600; font-size: 13px; flex-shrink: 0;
}
.rec-route-name { font-size: 14px; color: #606266; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.rec-meta { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.rec-reason { font-size: 12px; color: #909399; }
.rec-arrow { color: #c0c4cc; font-size: 18px; flex-shrink: 0; }

html.dark .rec-card { background: #1a1a2e; border-color: #333; }
html.dark .rec-rank { background: #2a2a3e; }
</style>
