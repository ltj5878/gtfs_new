<template>
  <el-popover
    :visible="popoverVisible"
    placement="bottom-end"
    :width="380"
    trigger="click"
    @show="onShow"
  >
    <template #reference>
      <el-badge :value="notificationStore.unreadCount" :hidden="notificationStore.unreadCount === 0" :max="99">
        <el-button text size="small" class="bell-btn" @click="popoverVisible = !popoverVisible">
          <el-icon :size="18"><Bell /></el-icon>
        </el-button>
      </el-badge>
    </template>

    <div class="notification-panel">
      <!-- 头部 -->
      <div class="panel-header">
        <span class="panel-title">{{ $t('notification.title') }}</span>
        <el-button
          v-if="notificationStore.unreadCount > 0"
          link type="primary" size="small"
          @click="handleMarkAllRead"
        >
          {{ $t('notification.markAllRead') }}
        </el-button>
      </div>

      <!-- 通知列表 -->
      <el-scrollbar max-height="400px">
        <div v-if="notificationStore.notifications.length === 0" class="panel-empty">
          <el-empty :description="$t('notification.noNotifications')" :image-size="60" />
        </div>
        <div
          v-for="item in notificationStore.notifications"
          :key="item.id"
          class="notification-item"
          :class="{ unread: !item.is_read }"
          @click="handleClickItem(item)"
        >
          <div class="item-dot" v-if="!item.is_read"></div>
          <div class="item-content">
            <div class="item-header">
              <el-tag :type="item.type === 'alert' ? 'warning' : 'info'" size="small">
                {{ item.type === 'alert' ? $t('notification.alert') : $t('notification.announcement') }}
              </el-tag>
              <span class="item-time">{{ timeAgo(item.created_at) }}</span>
            </div>
            <div class="item-title">{{ item.title }}</div>
            <div class="item-text" v-if="item.content">{{ item.content }}</div>
          </div>
        </div>
      </el-scrollbar>
    </div>
  </el-popover>
</template>

<script setup>
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { Bell } from '@element-plus/icons-vue'
import { useNotificationStore } from '@/stores/notificationStore.js'

const { t } = useI18n()
const notificationStore = useNotificationStore()
const popoverVisible = ref(false)

const onShow = () => {
  notificationStore.fetchNotifications()
}

const handleMarkAllRead = () => {
  notificationStore.markAllRead()
}

const handleClickItem = (item) => {
  if (!item.is_read) {
    notificationStore.markAsRead(item.id)
  }
}

// 相对时间
const timeAgo = (ts) => {
  if (!ts) return ''
  const now = Date.now()
  const diff = now - new Date(ts).getTime()
  const minutes = Math.floor(diff / 60000)
  if (minutes < 1) return t('notification.justNow')
  if (minutes < 60) return t('notification.minutesAgo', { n: minutes })
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return t('notification.hoursAgo', { n: hours })
  const days = Math.floor(hours / 24)
  return t('notification.daysAgo', { n: days })
}
</script>

<style scoped>
.bell-btn {
  font-size: 18px;
  min-width: 32px;
}

.notification-panel {
  margin: -12px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.panel-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.panel-empty {
  padding: 20px 0;
}

.notification-item {
  display: flex;
  gap: 10px;
  padding: 12px 16px;
  cursor: pointer;
  transition: background 0.2s;
  border-bottom: 1px solid var(--el-border-color-extra-light);
}

.notification-item:hover {
  background: var(--el-fill-color-light);
}

.notification-item.unread {
  background: var(--el-color-primary-light-9);
}

.item-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--el-color-primary);
  flex-shrink: 0;
  margin-top: 6px;
}

.item-content {
  flex: 1;
  min-width: 0;
}

.item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.item-time {
  font-size: 11px;
  color: var(--el-text-color-placeholder);
}

.item-title {
  font-size: 13px;
  font-weight: 500;
  color: var(--el-text-color-primary);
  margin-bottom: 2px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.item-text {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
