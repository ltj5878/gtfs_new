import axios from 'axios'
import { useRegionStore } from '@/stores/regionStore'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5001/api'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

apiClient.interceptors.request.use(
  config => {
    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    // 自动附加当前选中的地区参数（排除 /regions 和 /health 接口）
    const skipRegionPaths = ['/regions', '/health', '/auth']
    const shouldSkip = skipRegionPaths.some(p => config.url?.startsWith(p))
    if (!shouldSkip) {
      const regionStore = useRegionStore()
      const region = regionStore.selectedRegion
      if (region) {
        config.params = { ...config.params, region }
      }
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

apiClient.interceptors.response.use(
  response => {
    // 如果响应数据有code字段，则返回data字段
    if (response.data && typeof response.data === 'object' && 'code' in response.data) {
      if (response.data.code === 200) {
        // 返回 data 字段，如果 data 不存在则返回整个响应对象
        return 'data' in response.data ? response.data.data : response.data
      } else {
        // API返回错误状态码
        return Promise.reject(new Error(response.data.message || 'API错误'))
      }
    }
    // 否则返回完整响应
    return response.data
  },
  error => {
    console.error('API请求错误:', error)
    if (error.response?.status === 401 && window.location.pathname !== '/login') {
      localStorage.removeItem('auth_token')
      localStorage.removeItem('auth_username')
      window.location.href = '/login'
    }
    const message = error.response?.data?.message || error.message || '网络错误'
    return Promise.reject(new Error(message))
  }
)

export default apiClient
