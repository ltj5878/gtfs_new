import apiClient from './index'

/**
 * 获取班次列表
 * @param {Object} params - 查询参数
 * @param {string} params.route_id - 线路ID
 * @param {string} params.service_id - 服务ID
 * @param {number} params.direction_id - 方向ID
 * @param {number} params.page - 页码
 * @param {number} params.page_size - 每页数量
 * @returns {Promise}
 */
export const getTrips = (params = {}) => {
  return apiClient.get('/trips', { params })
}

/**
 * 获取指定班次详情
 * @param {string} tripId - 班次ID
 * @returns {Promise}
 */
export const getTripById = (tripId) => {
  return apiClient.get(`/trips/${tripId}`)
}

/**
 * 获取班次的所有站点时刻表
 * @param {string} tripId - 班次ID
 * @returns {Promise}
 */
export const getTripStopTimes = (tripId) => {
  return apiClient.get(`/trips/${tripId}/stop_times`)
}
