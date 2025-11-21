import apiClient from './index'

/**
 * 准点率相关的API请求
 */

// 获取实时车辆位置
export const getRealtimeVehicles = (params = {}) => {
  return apiClient.get('/realtime/vehicles', { params })
}

// 获取实时延误信息
export const getRealtimeDelays = (params = {}) => {
  return apiClient.get('/realtime/delays', { params })
}

// 获取实时数据汇总
export const getRealtimeSummary = () => {
  return apiClient.get('/realtime/summary')
}

// 获取系统准点率概览
export const getPunctualityOverview = (params = {}) => {
  return apiClient.get('/punctuality/overview', { params })
}

// 获取线路准点率统计
export const getRoutePunctuality = (params = {}) => {
  return apiClient.get('/punctuality/routes', { params })
}

// 获取站点准点率统计
export const getStopPunctuality = (params = {}) => {
  return apiClient.get('/punctuality/stops', { params })
}

// 获取时段准点率统计
export const getHourlyPunctuality = (params = {}) => {
  return apiClient.get('/punctuality/hourly', { params })
}

// 获取准点率配置
export const getPunctualityConfig = () => {
  return apiClient.get('/punctuality/config')
}

// 更新准点率配置
export const updatePunctualityConfig = (configData) => {
  return apiClient.put('/punctuality/config', configData)
}