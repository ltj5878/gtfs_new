import apiClient from './index.js'

/**
 * 换乘规划接口
 * @param {Object} params - { from_stop_id, to_stop_id, region, strategy }
 */
export const planTransfer = (params) => apiClient.get('/planner/transfer', { params })
