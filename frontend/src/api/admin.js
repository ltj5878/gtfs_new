import apiClient from './index.js'

// 获取数据库存储统计
export const getDbStats = () => apiClient.get('/admin/db-stats')

// 获取第三方 API 健康度统计
export const getApiHealth = () => apiClient.get('/admin/api-health')

// 获取各地区数据时效性
export const getDataFreshness = () => apiClient.get('/admin/data-freshness')
