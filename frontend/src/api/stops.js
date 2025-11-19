import apiClient from './index'

/**
 * 获取所有站点
 * @param {Object} params - 查询参数
 * @param {number} params.page - 页码
 * @param {number} params.page_size - 每页数量
 * @param {string} params.search - 搜索关键词
 * @param {number} params.lat - 纬度
 * @param {number} params.lon - 经度
 * @param {number} params.radius - 半径（公里）
 * @returns {Promise}
 */
export const getStops = (params = {}) => {
  return apiClient.get('/stops', { params })
}

/**
 * 获取指定站点详情
 * @param {string} stopId - 站点ID
 * @returns {Promise}
 */
export const getStopById = (stopId) => {
  return apiClient.get(`/stops/${stopId}`)
}

/**
 * 获取经过指定站点的所有线路
 * @param {string} stopId - 站点ID
 * @returns {Promise}
 */
export const getStopRoutes = (stopId) => {
  return apiClient.get(`/stops/${stopId}/routes`)
}
