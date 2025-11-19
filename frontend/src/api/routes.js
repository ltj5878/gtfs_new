import apiClient from './index'

/**
 * 获取所有线路
 * @param {Object} params - 查询参数
 * @param {number} params.page - 页码
 * @param {number} params.page_size - 每页数量
 * @param {string} params.agency_id - 运营机构ID
 * @param {number} params.route_type - 线路类型
 * @param {string} params.search - 搜索关键词
 * @returns {Promise}
 */
export const getRoutes = (params = {}) => {
  return apiClient.get('/routes', { params })
}

/**
 * 获取指定线路详情
 * @param {string} routeId - 线路ID
 * @returns {Promise}
 */
export const getRouteById = (routeId) => {
  return apiClient.get(`/routes/${routeId}`)
}

/**
 * 获取线路的所有方向
 * @param {string} routeId - 线路ID
 * @returns {Promise}
 */
export const getRouteDirections = (routeId) => {
  return apiClient.get(`/routes/${routeId}/directions`)
}

/**
 * 获取线路的所有站点
 * @param {string} routeId - 线路ID
 * @param {number} directionId - 方向ID（可选）
 * @returns {Promise}
 */
export const getRouteStops = (routeId, directionId = null) => {
  const params = directionId !== null ? { direction_id: directionId } : {}
  return apiClient.get(`/routes/${routeId}/stops`, { params })
}
