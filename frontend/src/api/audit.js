import apiClient from './index.js'

// 获取审计日志列表（分页 + 筛选）
export const getAuditLogs = (params) => apiClient.get('/admin/audit-logs', { params })

// 前端行为追踪（页面访问、数据导出等）
export const trackAudit = (action, target, detail) =>
  apiClient.post('/audit/track', { action, target, detail })
