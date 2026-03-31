import apiClient from './index.js'

// 获取用户订阅列表
export const getSubscriptions = () => apiClient.get('/subscriptions')

// 添加/更新订阅
export const addSubscription = (data) => apiClient.post('/subscriptions', data)

// 取消订阅
export const removeSubscription = (params) => apiClient.delete('/subscriptions', { params })

// 检查单条订阅状态
export const checkSubscription = (params) => apiClient.get('/subscriptions/check', { params })
