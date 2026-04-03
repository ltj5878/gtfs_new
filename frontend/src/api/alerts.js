import apiClient from './index.js'

// 获取活跃告警
export const getActiveAlerts = (params = {}) => apiClient.get('/alerts/active', { params })

// 获取历史告警
export const getAlertHistory = (params = {}) => apiClient.get('/alerts/history', { params })

// 标记告警已解决
export const resolveAlert = (id) => apiClient.patch(`/alerts/${id}/resolve`)

// 获取告警统计
export const getAlertStats = (params = {}) => apiClient.get('/alerts/stats', { params })
