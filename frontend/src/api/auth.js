import apiClient from './index.js'

export const login = (username, password) => apiClient.post('/auth/login', { username, password })
export const logout = () => apiClient.post('/auth/logout')
export const getMe = () => apiClient.get('/auth/me')
export const register = (username, password) => apiClient.post('/auth/register', { username, password })
