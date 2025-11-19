import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getStops, getStopById, getStopRoutes } from '@/api/stops'

export const useStopStore = defineStore('stop', () => {
  const stops = ref([])
  const currentStop = ref(null)
  const stopRoutes = ref([])
  const loading = ref(false)
  const pagination = ref({
    page: 1,
    page_size: 20,
    total: 0,
    total_pages: 0
  })

  const fetchStops = async (params = {}) => {
    loading.value = true
    try {
      const data = await getStops(params)
      stops.value = data.stops
      pagination.value = data.pagination
      return data
    } catch (error) {
      console.error('获取站点列表失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  const fetchStopById = async (stopId) => {
    loading.value = true
    try {
      const data = await getStopById(stopId)
      currentStop.value = data
      return data
    } catch (error) {
      console.error('获取站点详情失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  const fetchStopRoutes = async (stopId) => {
    loading.value = true
    try {
      const data = await getStopRoutes(stopId)
      stopRoutes.value = data
      return data
    } catch (error) {
      console.error('获取站点线路失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  const clearCurrentStop = () => {
    currentStop.value = null
    stopRoutes.value = []
  }

  return {
    stops,
    currentStop,
    stopRoutes,
    loading,
    pagination,
    fetchStops,
    fetchStopById,
    fetchStopRoutes,
    clearCurrentStop
  }
})
