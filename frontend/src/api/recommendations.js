import apiClient from './index.js'

// 获取个性化行程推荐
export const getRecommendations = (params = {}) => apiClient.get('/recommendations', { params })
