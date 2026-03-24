<template>
  <div class="favorites-page">
    <div class="page-header">
      <h1>我的收藏</h1>
    </div>

    <el-divider />

    <div v-if="favoriteStore.favorites.length === 0 && !loading" class="empty-state">
      <el-empty description="暂无收藏，去线路或站点页面收藏吧" />
    </div>

    <div v-else>
      <el-tabs v-model="activeTab">
        <!-- 线路收藏 -->
        <el-tab-pane :label="`线路 (${routeFavorites.length})`" name="route">
          <div v-if="routeFavorites.length === 0" class="tab-empty">
            <el-empty description="暂无收藏线路" />
          </div>
          <div v-else class="favorites-list">
            <div
              v-for="item in routeFavorites"
              :key="item.id"
              class="favorite-item"
            >
              <div class="favorite-icon route-icon">
                <el-icon :size="20" color="#409eff"><Guide /></el-icon>
              </div>
              <div class="favorite-info">
                <div class="favorite-name">{{ item.item_name || item.item_id }}</div>
                <div class="favorite-meta">
                  <el-tag size="small" type="info">{{ regionLabel(item.region) }}</el-tag>
                  <span class="favorite-time">{{ formatTime(item.created_at) }}</span>
                </div>
              </div>
              <div class="favorite-actions">
                <el-button size="small" type="primary" plain @click="goToRoute(item)">
                  查看详情
                </el-button>
                <el-button size="small" type="danger" plain @click="removeFav(item)">
                  取消收藏
                </el-button>
              </div>
            </div>
          </div>
        </el-tab-pane>

        <!-- 站点收藏 -->
        <el-tab-pane :label="`站点 (${stopFavorites.length})`" name="stop">
          <div v-if="stopFavorites.length === 0" class="tab-empty">
            <el-empty description="暂无收藏站点" />
          </div>
          <div v-else class="favorites-list">
            <div
              v-for="item in stopFavorites"
              :key="item.id"
              class="favorite-item"
            >
              <div class="favorite-icon stop-icon">
                <el-icon :size="20" color="#67c23a"><Location /></el-icon>
              </div>
              <div class="favorite-info">
                <div class="favorite-name">{{ item.item_name || item.item_id }}</div>
                <div class="favorite-meta">
                  <el-tag size="small" type="success">{{ regionLabel(item.region) }}</el-tag>
                  <span class="favorite-time">{{ formatTime(item.created_at) }}</span>
                </div>
              </div>
              <div class="favorite-actions">
                <el-button size="small" type="primary" plain @click="goToStop(item)">
                  查看详情
                </el-button>
                <el-button size="small" type="danger" plain @click="removeFav(item)">
                  取消收藏
                </el-button>
              </div>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Guide, Location } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useFavoriteStore } from '@/stores/favoriteStore.js'
import { useRegionStore } from '@/stores/regionStore.js'

const router = useRouter()
const favoriteStore = useFavoriteStore()
const regionStore = useRegionStore()

const activeTab = ref('route')
const loading = ref(false)

const REGION_LABELS = {
  sf: '旧金山',
  nyc: '纽约',
  sydney: '悉尼'
}

const regionLabel = (region) => REGION_LABELS[region] || region

const routeFavorites = computed(() =>
  favoriteStore.favorites.filter(f => f.item_type === 'route')
)

const stopFavorites = computed(() =>
  favoriteStore.favorites.filter(f => f.item_type === 'stop')
)

const formatTime = (ts) => {
  if (!ts) return ''
  const d = new Date(ts)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

const goToRoute = (item) => {
  regionStore.setRegion(item.region)
  router.push(`/routes/${item.item_id}`)
}

const goToStop = (item) => {
  regionStore.setRegion(item.region)
  router.push(`/stops/${item.item_id}`)
}

const removeFav = async (item) => {
  try {
    await favoriteStore.toggleFavorite({
      region: item.region,
      item_type: item.item_type,
      item_id: item.item_id,
      item_name: item.item_name
    })
    ElMessage.success('已取消收藏')
  } catch (e) {
    ElMessage.error('操作失败，请重试')
  }
}

onMounted(async () => {
  loading.value = true
  await favoriteStore.fetchFavorites()
  loading.value = false
})
</script>

<style scoped>
.favorites-page {
  padding: 20px;
}

.page-header h1 {
  margin: 0 0 16px;
  font-size: 28px;
  font-weight: 600;
}

.empty-state {
  margin-top: 60px;
}

.tab-empty {
  margin-top: 40px;
}

.favorites-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 16px;
}

.favorite-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: #fafbfc;
  border-radius: 10px;
  border: 1px solid #f0f0f0;
  transition: box-shadow 0.2s;
}

.favorite-item:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.favorite-icon {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.route-icon {
  background-color: #e3f2fd;
}

.stop-icon {
  background-color: #e8f5e9;
}

.favorite-info {
  flex: 1;
  min-width: 0;
}

.favorite-name {
  font-size: 15px;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 6px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.favorite-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.favorite-time {
  font-size: 12px;
  color: #909399;
}

.favorite-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

@media (max-width: 600px) {
  .favorite-item {
    flex-wrap: wrap;
  }
  .favorite-actions {
    width: 100%;
    justify-content: flex-end;
  }
}
</style>
