import apiClient from './index.js'

// 获取线路碳排放对比
export const getRouteCarbonData = (routeId, params = {}) => apiClient.get(`/carbon/route/${routeId}`, { params })

// 记录一次绿色出行
export const recordCarbonTrip = (data) => apiClient.post('/carbon/record', data)

// 获取个人碳排放统计
export const getMyCarbonStats = (params = {}) => apiClient.get('/carbon/my-stats', { params })

// 获取个人录入记录
export const getMyCarbonRecords = (params = {}) => apiClient.get('/carbon/my-records', { params })

// 删除个人录入记录
export const deleteCarbonRecord = (recordId) => apiClient.delete(`/carbon/records/${recordId}`)

// 获取绿色出行排行榜
export const getCarbonLeaderboard = (params = {}) => apiClient.get('/carbon/leaderboard', { params })
