import apiClient from './index.js'

// 获取所有线路健康度评分
export const getHealthScores = (params = {}) => apiClient.get('/routes/health-scores', { params })

// 获取单条线路健康度详情
export const getRouteHealthDetail = (routeId, params = {}) => apiClient.get(`/routes/${routeId}/health-score`, { params })

// 管理员触发重新计算
export const recalculateScores = (params = {}) => apiClient.post('/admin/recalculate-health-scores', null, { params })
