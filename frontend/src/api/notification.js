import apiClient from './index.js'

// 获取通知列表（分页）
export const getNotifications = (params = {}) => apiClient.get('/notifications', { params })

// 标记通知已读（单条 { id } 或全部 { all: true }）
export const markRead = (data) => apiClient.patch('/notifications/read', data)

// 获取未读通知数量
export const getUnreadCount = () => apiClient.get('/notifications/unread-count')

// 管理员发布公告
export const publishAnnouncement = (data) => apiClient.post('/notifications/announcement', data)

// 触发准点率检查告警
export const checkPunctualityAlerts = () => apiClient.post('/notifications/check-punctuality')
