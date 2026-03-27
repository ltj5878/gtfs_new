import apiClient from './index.js'

// 获取所有用户列表
export const getUsers = () => apiClient.get('/users')

// 创建新用户
export const createUser = (data) => apiClient.post('/users', data)

// 更新用户状态（启用/停用）
export const updateUser = (id, data) => apiClient.patch(`/users/${id}`, data)

// 删除用户
export const deleteUser = (id) => apiClient.delete(`/users/${id}`)

// 重置密码（返回临时密码）
export const resetUserPassword = (id) => apiClient.get(`/users/${id}/password`)

// 修改用户密码
export const updateUserPassword = (id, password) => apiClient.put(`/users/${id}/password`, { password })
