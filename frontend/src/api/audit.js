import apiClient from './index.js'

// 获取审计日志列表（分页 + 筛选）
export const getAuditLogs = (params) => apiClient.get('/admin/audit-logs', { params })
