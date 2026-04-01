import apiClient from './index.js'

export const getReachability = (params) => {
  return apiClient.get('/analysis/reachability', {
    params,
    timeout: 60000
  })
}
