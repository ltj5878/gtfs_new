import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  getRealtimeVehicles,
  getRealtimeDelays,
  getRealtimeSummary,
  getPunctualityOverview,
  getRoutePunctuality,
  getStopPunctuality,
  getHourlyPunctuality,
  getPunctualityConfig,
  updatePunctualityConfig
} from '../api/punctuality'

export const usePunctualityStore = defineStore('punctuality', () => {
  // 状态
  const loading = ref(false)
  const error = ref(null)

  // 实时数据
  const realtimeVehicles = ref([])
  const realtimeDelays = ref([])
  const realtimeSummary = ref({})

  // 准点率概览
  const punctualityOverview = ref({})
  const routePunctuality = ref([])
  const stopPunctuality = ref([])
  const hourlyPunctuality = ref([])

  // 配置
  const punctualityConfig = ref({})

  // 计算属性
  const hasRealtimeData = computed(() => {
    return realtimeVehicles.value.length > 0 || realtimeDelays.value.length > 0
  })

  const hasPunctualityData = computed(() => {
    return punctualityOverview.value.data_available === true
  })

  const systemStats = computed(() => {
    const overview = punctualityOverview.value
    return {
      totalRoutes: overview.total_routes || 0,
      totalTrips: overview.total_trips || 0,
      systemPunctualityRate: overview.system_punctuality_rate || 0,
      systemAvgDelay: overview.system_avg_delay_minutes || 0,
      dataAvailable: overview.data_available || false
    }
  })

  // 实时数据相关方法
  const fetchRealtimeVehicles = async (params = {}) => {
    try {
      loading.value = true
      const response = await getRealtimeVehicles(params)
      realtimeVehicles.value = response.data || []
      return realtimeVehicles.value
    } catch (err) {
      console.error('获取实时车辆数据失败:', err)
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const fetchRealtimeDelays = async (params = {}) => {
    try {
      loading.value = true
      const response = await getRealtimeDelays(params)
      realtimeDelays.value = response.data || []
      return realtimeDelays.value
    } catch (err) {
      console.error('获取实时延误数据失败:', err)
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const fetchRealtimeSummary = async () => {
    try {
      loading.value = true
      const response = await getRealtimeSummary()
      realtimeSummary.value = response.data || {}
      return realtimeSummary.value
    } catch (err) {
      console.error('获取实时数据汇总失败:', err)
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  // 准点率相关方法
  const fetchPunctualityOverview = async (params = {}) => {
    try {
      loading.value = true
      const response = await getPunctualityOverview(params)
      punctualityOverview.value = response.data || {}
      return punctualityOverview.value
    } catch (err) {
      console.error('获取准点率概览失败:', err)
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const fetchRoutePunctuality = async (params = {}) => {
    try {
      loading.value = true
      const response = await getRoutePunctuality(params)
      routePunctuality.value = response.data || []
      return routePunctuality.value
    } catch (err) {
      console.error('获取线路准点率失败:', err)
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const fetchStopPunctuality = async (params = {}) => {
    try {
      loading.value = true
      const response = await getStopPunctuality(params)
      stopPunctuality.value = response.data || []
      return stopPunctuality.value
    } catch (err) {
      console.error('获取站点准点率失败:', err)
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const fetchHourlyPunctuality = async (params = {}) => {
    try {
      loading.value = true
      const response = await getHourlyPunctuality(params)
      hourlyPunctuality.value = response.data || []
      return hourlyPunctuality.value
    } catch (err) {
      console.error('获取时段准点率失败:', err)
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  // 配置相关方法
  const fetchPunctualityConfig = async () => {
    try {
      loading.value = true
      const response = await getPunctualityConfig()
      punctualityConfig.value = response.data || {}
      return punctualityConfig.value
    } catch (err) {
      console.error('获取准点率配置失败:', err)
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const updatePunctualityConfig = async (configData) => {
    try {
      loading.value = true
      const response = await updatePunctualityConfig(configData)
      // 更新本地配置
      punctualityConfig.value = { ...punctualityConfig.value, ...configData }
      return response.data
    } catch (err) {
      console.error('更新准点率配置失败:', err)
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  // 批量获取数据
  const fetchAllPunctualityData = async () => {
    try {
      loading.value = true
      error.value = null

      // 并行获取数据
      const [
        overviewData,
        routeData,
        summaryData
      ] = await Promise.allSettled([
        fetchPunctualityOverview(),
        fetchRoutePunctuality({ limit: 20 }),
        fetchRealtimeSummary()
      ])

      // 检查是否有失败的请求
      const errors = []
      if (overviewData.status === 'rejected') errors.push('准点率概览')
      if (routeData.status === 'rejected') errors.push('线路准点率')
      if (summaryData.status === 'rejected') errors.push('实时数据汇总')

      if (errors.length > 0) {
        throw new Error(`获取以下数据失败: ${errors.join(', ')}`)
      }

      return {
        overview: punctualityOverview.value,
        routes: routePunctuality.value,
        summary: realtimeSummary.value
      }
    } catch (err) {
      console.error('批量获取数据失败:', err)
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  // 刷新实时数据
  const refreshRealtimeData = async () => {
    try {
      const [vehicles, delays, summary] = await Promise.all([
        fetchRealtimeVehicles({ limit: 100 }),
        fetchRealtimeDelays({ limit: 50 }),
        fetchRealtimeSummary()
      ])
      return { vehicles, delays, summary }
    } catch (err) {
      console.error('刷新实时数据失败:', err)
      error.value = err.message
      throw err
    }
  }

  // 工具方法
  const clearError = () => {
    error.value = null
  }

  const resetStore = () => {
    realtimeVehicles.value = []
    realtimeDelays.value = []
    realtimeSummary.value = {}
    punctualityOverview.value = {}
    routePunctuality.value = []
    stopPunctuality.value = []
    hourlyPunctuality.value = []
    punctualityConfig.value = {}
    error.value = null
  }

  // 格式化数据
  const formatDelayTime = (seconds) => {
    if (!seconds) return '0分钟'
    const minutes = Math.abs(seconds / 60)
    if (seconds < 0) {
      return `提前${minutes.toFixed(1)}分钟`
    } else {
      return `延误${minutes.toFixed(1)}分钟`
    }
  }

  const formatPunctualityRate = (rate) => {
    return `${(rate || 0).toFixed(1)}%`
  }

  const getPunctualityStatus = (delaySeconds) => {
    const config = punctualityConfig.value
    const onTimeThreshold = config.on_time_threshold_seconds || 120
    const earlyThreshold = config.early_threshold_seconds || 60
    const veryLateThreshold = config.very_late_threshold_seconds || 300

    if (delaySeconds < -earlyThreshold) {
      return { status: 'early', label: '提前', color: 'success' }
    } else if (Math.abs(delaySeconds) <= onTimeThreshold) {
      return { status: 'onTime', label: '准点', color: 'success' }
    } else if (delaySeconds <= veryLateThreshold) {
      return { status: 'late', label: '延误', color: 'warning' }
    } else {
      return { status: 'veryLate', label: '严重延误', color: 'danger' }
    }
  }

  return {
    // 状态
    loading,
    error,
    realtimeVehicles,
    realtimeDelays,
    realtimeSummary,
    punctualityOverview,
    routePunctuality,
    stopPunctuality,
    hourlyPunctuality,
    punctualityConfig,

    // 计算属性
    hasRealtimeData,
    hasPunctualityData,
    systemStats,

    // 方法
    fetchRealtimeVehicles,
    fetchRealtimeDelays,
    fetchRealtimeSummary,
    fetchPunctualityOverview,
    fetchRoutePunctuality,
    fetchStopPunctuality,
    fetchHourlyPunctuality,
    fetchPunctualityConfig,
    updatePunctualityConfig,
    fetchAllPunctualityData,
    refreshRealtimeData,

    // 工具方法
    clearError,
    resetStore,
    formatDelayTime,
    formatPunctualityRate,
    getPunctualityStatus
  }
})