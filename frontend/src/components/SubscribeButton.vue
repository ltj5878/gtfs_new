<template>
  <el-popover
    :visible="popoverVisible"
    placement="bottom"
    :width="240"
    trigger="click"
  >
    <template #reference>
      <el-button
        text
        :type="subscribed ? 'warning' : ''"
        size="small"
        class="subscribe-btn"
        @click="popoverVisible = !popoverVisible"
        :title="subscribed ? $t('notification.subscribed') : $t('notification.subscribe')"
      >
        <el-icon :size="18">
          <BellFilled v-if="subscribed" />
          <Bell v-else />
        </el-icon>
      </el-button>
    </template>

    <div class="subscribe-panel">
      <div class="panel-label">{{ $t('notification.threshold') }}</div>
      <div class="panel-hint">{{ $t('notification.thresholdHint') }}</div>
      <el-input-number
        v-model="threshold"
        :min="0"
        :max="100"
        :step="5"
        size="small"
        style="width: 100%; margin: 10px 0"
      />
      <div class="panel-actions">
        <el-button
          v-if="subscribed"
          size="small"
          type="danger"
          plain
          @click="handleUnsubscribe"
          :loading="loading"
        >
          {{ $t('notification.unsubscribe') }}
        </el-button>
        <el-button
          size="small"
          type="primary"
          @click="handleSubscribe"
          :loading="loading"
        >
          {{ subscribed ? $t('notification.subscribe') : $t('notification.subscribe') }}
        </el-button>
      </div>
    </div>
  </el-popover>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { Bell, BellFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { checkSubscription, addSubscription, removeSubscription } from '@/api/subscription.js'

const { t } = useI18n()

const props = defineProps({
  region: { type: String, required: true },
  routeId: { type: String, required: true },
  routeName: { type: String, default: '' },
})

const subscribed = ref(false)
const threshold = ref(80)
const loading = ref(false)
const popoverVisible = ref(false)

// 挂载时检查订阅状态
onMounted(async () => {
  if (!props.region || !props.routeId) return
  try {
    const data = await checkSubscription({ region: props.region, route_id: props.routeId })
    subscribed.value = data?.subscribed || false
    if (data?.threshold != null) threshold.value = data.threshold
  } catch {
    // 静默
  }
})

const handleSubscribe = async () => {
  loading.value = true
  try {
    await addSubscription({ region: props.region, route_id: props.routeId, threshold: threshold.value })
    subscribed.value = true
    popoverVisible.value = false
    ElMessage.success(t('notification.subscribeSuccess'))
  } catch {
    ElMessage.error(t('common.operationFailed'))
  } finally {
    loading.value = false
  }
}

const handleUnsubscribe = async () => {
  loading.value = true
  try {
    await removeSubscription({ region: props.region, route_id: props.routeId })
    subscribed.value = false
    threshold.value = 80
    popoverVisible.value = false
    ElMessage.success(t('notification.unsubscribeSuccess'))
  } catch {
    ElMessage.error(t('common.operationFailed'))
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.subscribe-btn {
  min-width: 32px;
}

.subscribe-panel {
  padding: 4px 0;
}

.panel-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.panel-hint {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 2px;
}

.panel-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>
