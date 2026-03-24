import apiClient from './index.js'

// 获取当前用户所有收藏
export const getFavorites = () => apiClient.get('/favorites')

// 添加收藏
export const addFavorite = (data) => apiClient.post('/favorites', data)

// 取消收藏
export const removeFavorite = (params) => apiClient.delete('/favorites', { params })
