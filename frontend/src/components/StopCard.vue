<template>
  <el-card class="stop-card" shadow="hover" @click="handleClick">
    <div class="stop-header">
      <el-icon class="stop-icon" :size="24"><Location /></el-icon>
      <div class="stop-info">
        <h3>{{ stop.stop_name }}</h3>
        <p v-if="stop.stop_code" class="stop-code">{{ $t('stopList.stopCode') }}: {{ stop.stop_code }}</p>
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
    <div class="stop-location">
      <span class="location-text">
        <el-icon><Position /></el-icon>
        {{ stop.stop_lat.toFixed(5) }}, {{ stop.stop_lon.toFixed(5) }}
      </span>
    </div>
    <p v-if="stop.stop_desc" class="stop-desc">{{ stop.stop_desc }}</p>
  </el-card>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { Location, Position, Star } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useFavoriteStore } from '@/stores/favoriteStore.js'
import { useAuthStore } from '@/stores/authStore.js'

const { t } = useI18n()

const props = defineProps({
  stop: {
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

const favorited = computed(() =>
  favoriteStore.isFavorite(props.region, 'stop', props.stop.stop_id)
)

const handleClick = () => {
  emit('click', props.stop)
}

const handleFavorite = async () => {
  if (!authStore.isLoggedIn) {
    ElMessage.warning(t('common.loginFirst'))
    return
  }
  try {
    await favoriteStore.toggleFavorite({
      region: props.region,
      item_type: 'stop',
      item_id: props.stop.stop_id,
      item_name: props.stop.stop_name || props.stop.stop_id
    })
  } catch (e) {
    ElMessage.error(t('common.operationFailed'))
  }
}
</script>

<style scoped>
.stop-card {
  cursor: pointer;
  transition: transform 0.2s;
}

.stop-card:hover {
  transform: translateY(-2px);
}

.stop-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.stop-icon {
  color: #409eff;
  flex-shrink: 0;
}

.stop-info {
  flex: 1;
  min-width: 0;
}

.stop-info h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.stop-code {
  margin: 4px 0 0;
  font-size: 12px;
  color: #909399;
}

.stop-location {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 8px;
}

.location-text {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #606266;
}

.stop-desc {
  margin: 8px 0 0;
  font-size: 13px;
  color: #606266;
  line-height: 1.5;
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
