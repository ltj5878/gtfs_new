import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

apiClient.interceptors.request.use(
  config => {
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
    const message = error.response?.data?.message || error.message || '网络错误'
    return Promise.reject(new Error(message))
  }
)

export default apiClient
