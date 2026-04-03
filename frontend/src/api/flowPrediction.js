import apiClient from './index.js'

// 获取站点全天客流预测
export const getStopFlowPrediction = (stopId, params = {}) => apiClient.get(`/stops/${stopId}/flow-prediction`, { params })

// 获取最佳到站时间
export const getStopBestTime = (stopId, params = {}) => apiClient.get(`/stops/${stopId}/best-time`, { params })

// 获取全站点客流热力图数据
export const getFlowHeatmap = (params = {}) => apiClient.get('/stops/flow-heatmap', { params })
