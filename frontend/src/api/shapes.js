import apiClient from './index'

/**
 * 获取线路轨迹数据
 * @param {string} shapeId - 轨迹ID
 * @returns {Promise}
 */
export const getShapeById = (shapeId) => {
  return apiClient.get(`/shapes/${shapeId}`)
}

/**
 * 获取指定线路的所有轨迹
 * @param {string} routeId - 线路ID
 * @param {number} directionId - 方向ID（可选）
 * @returns {Promise}
 */
export const getRouteShapes = (routeId, directionId = null) => {
  return apiClient.get(`/routes/${routeId}/shapes`, {
    params: directionId !== null ? { direction_id: directionId } : {}
  })
}