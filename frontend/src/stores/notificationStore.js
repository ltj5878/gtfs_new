import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getNotifications, markRead, getUnreadCount } from '@/api/notification.js'

export const useNotificationStore = defineStore('notification', () => {
  const notifications = ref([])
  const unreadCount = ref(0)
  const total = ref(0)

  // 获取通知列表
  const fetchNotifications = async (page = 1) => {
    try {
      const data = await getNotifications({ page, page_size: 20 })
      notifications.value = data?.items || []
      unreadCount.value = data?.unread_count || 0
      total.value = data?.total || 0
    } catch {
      // 静默失败
    }
  }

  // 轻量级获取未读数
  const fetchUnreadCount = async () => {
    try {
      const data = await getUnreadCount()
      unreadCount.value = data?.unread_count || 0
    } catch {
      // 静默失败
    }
  }

  // 标记单条已读
  const markAsRead = async (id) => {
    // 乐观更新
    const item = notifications.value.find(n => n.id === id)
    if (item && !item.is_read) {
      item.is_read = true
      unreadCount.value = Math.max(0, unreadCount.value - 1)
    }
    try {
      await markRead({ id })
    } catch {
      // 回滚
      if (item) {
        item.is_read = false
        unreadCount.value += 1
      }
    }
  }

  // 全部标记已读
  const markAllRead = async () => {
    const prevCount = unreadCount.value
    const prevItems = notifications.value.map(n => ({ ...n }))
    // 乐观更新
    notifications.value.forEach(n => { n.is_read = true })
    unreadCount.value = 0
    try {
      await markRead({ all: true })
    } catch {
      // 回滚
      unreadCount.value = prevCount
      notifications.value = prevItems
    }
  }

  // 清空状态（退出登录时调用）
  const clearNotifications = () => {
    notifications.value = []
    unreadCount.value = 0
    total.value = 0
  }

  return { notifications, unreadCount, total, fetchNotifications, fetchUnreadCount, markAsRead, markAllRead, clearNotifications }
})
