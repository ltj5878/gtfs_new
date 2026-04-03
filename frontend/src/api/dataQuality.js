import apiClient from './index.js'

// 获取最新数据质量检查结果
export const getLatestCheck = (params = {}) => apiClient.get('/admin/data-quality/latest', { params })

// 获取问题详情列表
export const getQualityIssues = (params = {}) => apiClient.get('/admin/data-quality/issues', { params })

// 获取质量分数历史趋势
export const getQualityHistory = (params = {}) => apiClient.get('/admin/data-quality/history', { params })

// 触发数据质量检查
export const runQualityCheck = (params = {}) => apiClient.post('/admin/data-quality/run', null, { params })

// 获取检查规则说明
export const getQualityRules = () => apiClient.get('/admin/data-quality/rules')
