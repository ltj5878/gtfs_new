<template>
  <el-card class="route-card" shadow="hover" @click="handleClick">
    <div class="route-header">
      <div class="route-badge" :style="{ backgroundColor: `#${route.route_color || '005596'}` }">
        <span :style="{ color: `#${route.route_text_color || 'FFFFFF'}` }">
          {{ route.route_short_name || 'N/A' }}
        </span>
      </div>
      <div class="route-info">
        <h3>{{ route.route_long_name }}</h3>
        <p class="route-type">{{ getRouteTypeName(route.route_type) }}</p>
      </div>
      <!-- 收藏按钮 -->
      <el-icon
        class="favorite-btn"
        :class="{ 'is-favorited': favorited }"
        :size="20"
        @click.stop="handleFavorite"
        :title="favorited ? $t('common.unfavorite') : $t('common.favorite')"
      >
        <Star />
      </el-icon>
    </div>
    <div v-if="route.category || route.subcategory || route.running_way" class="route-meta">
      <el-tag v-if="route.category" size="small" type="success">
        {{ route.category_text || route.category }}
      </el-tag>
      <el-tag v-if="route.subcategory" size="small" type="info">
        {{ route.subcategory_text || route.subcategory }}
      </el-tag>
      <el-tag v-if="route.running_way" size="small" type="warning">
        {{ route.running_way_text || route.running_way }}
      </el-tag>
    </div>
  </el-card>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { Star } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useFavoriteStore } from '@/stores/favoriteStore.js'
import { useAuthStore } from '@/stores/authStore.js'

const { t } = useI18n()

const props = defineProps({
  route: {
    type: Object,
    required: true
  },
  region: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['click'])

const favoriteStore = useFavoriteStore()
const authStore = useAuthStore()

const routeTypeNames = computed(() => ({
  0: t('routeType.0'),
  1: t('routeType.1'),
  2: t('routeType.2'),
  3: t('routeType.3'),
  4: t('routeType.4'),
  5: t('routeType.5'),
  6: t('routeType.6'),
  7: t('routeType.7')
}))

const getRouteTypeName = (type) => {
  return routeTypeNames.value[type] || t('common.unknown')
}

const favorited = computed(() =>
  favoriteStore.isFavorite(props.region, 'route', props.route.route_id)
)

const handleClick = () => {
  emit('click', props.route)
}

const handleFavorite = async () => {
  if (!authStore.isLoggedIn) {
    ElMessage.warning(t('common.loginFirst'))
    return
  }
  try {
    await favoriteStore.toggleFavorite({
      region: props.region,
      item_type: 'route',
      item_id: props.route.route_id,
      item_name: props.route.route_long_name || props.route.route_short_name || props.route.route_id
    })
  } catch (e) {
    ElMessage.error(t('common.operationFailed'))
  }
}
</script>

<style scoped>
.route-card {
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border-radius: 12px;
  border: 1px solid #f0f0f0;
  overflow: hidden;
}

.route-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  border-color: #e0e0e0;
}

.route-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}

.route-badge {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 18px;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  position: relative;
  overflow: hidden;
}

.route-badge::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.2) 0%, rgba(255, 255, 255, 0) 100%);
  pointer-events: none;
}

.route-info {
  flex: 1;
  min-width: 0;
}

.route-info h3 {
  margin: 0 0 6px 0;
  font-size: 17px;
  font-weight: 600;
  color: #1a1a1a;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  letter-spacing: -0.01em;
}

.route-type {
  margin: 0;
  font-size: 13px;
  color: #8a8a8a;
  font-weight: 500;
}

.route-meta {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  padding-top: 4px;
}

.route-meta :deep(.el-tag) {
  border-radius: 6px;
  border: none;
  font-weight: 500;
  font-size: 12px;
  padding: 4px 10px;
  height: auto;
}

.route-meta :deep(.el-tag.el-tag--success) {
  background-color: #f0f9ff;
  color: #0369a1;
}

.route-meta :deep(.el-tag.el-tag--info) {
  background-color: #f5f3ff;
  color: #6d28d9;
}

.route-meta :deep(.el-tag.el-tag--warning) {
  background-color: #fffbeb;
  color: #d97706;
}

/* 收藏按钮 */
.favorite-btn {
  flex-shrink: 0;
  color: #c0c4cc;
  cursor: pointer;
  transition: color 0.2s, transform 0.2s;
}

.favorite-btn:hover {
  color: #f0a020;
  transform: scale(1.2);
}

.favorite-btn.is-favorited {
  color: #f0a020;
}
</style>
