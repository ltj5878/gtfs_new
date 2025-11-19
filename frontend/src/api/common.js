import apiClient from './index'

/**
 * 健康检查
 * @returns {Promise}
 */
export const healthCheck = () => {
  return apiClient.get('/health')
}

/**
 * 获取所有运营机构
 * @returns {Promise}
 */
export const getAgencies = () => {
  return apiClient.get('/agencies')
}

/**
 * 获取指定运营机构详情
 * @param {string} agencyId - 运营机构ID
 * @returns {Promise}
 */
export const getAgencyById = (agencyId) => {
  return apiClient.get(`/agencies/${agencyId}`)
}

/**
 * 获取线路轨迹
 * @param {string} shapeId - 轨迹ID
 * @returns {Promise}
 */
export const getShape = (shapeId) => {
  return apiClient.get(`/shapes/${shapeId}`)
}

/**
 * 获取服务日历
 * @returns {Promise}
 */
export const getCalendar = () => {
  return apiClient.get('/calendar')
}

/**
 * 获取数据统计信息
 * @returns {Promise}
 */
export const getStats = () => {
  return apiClient.get('/stats')
}
