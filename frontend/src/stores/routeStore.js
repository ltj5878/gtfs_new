import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getRoutes, getRouteById, getRouteDirections, getRouteStops } from '@/api/routes'

export const useRouteStore = defineStore('route', () => {
  const routes = ref([])
  const currentRoute = ref(null)
  const directions = ref([])
  const stops = ref([])
  const loading = ref(false)
  const pagination = ref({
    page: 1,
    page_size: 20,
    total: 0,
    total_pages: 0
  })

  const fetchRoutes = async (params = {}) => {
    loading.value = true
    try {
      const data = await getRoutes(params)
      routes.value = data.routes
      pagination.value = data.pagination
      return data
    } catch (error) {
      console.error('获取线路列表失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  const fetchRouteById = async (routeId) => {
    loading.value = true
    try {
      const data = await getRouteById(routeId)
      currentRoute.value = data
      return data
    } catch (error) {
      console.error('获取线路详情失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  const fetchRouteDirections = async (routeId) => {
    loading.value = true
    try {
      const data = await getRouteDirections(routeId)
      directions.value = data
      return data
    } catch (error) {
      console.error('获取线路方向失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  const fetchRouteStops = async (routeId, directionId = null) => {
    loading.value = true
    try {
      const data = await getRouteStops(routeId, directionId)
      stops.value = data
      return data
    } catch (error) {
      console.error('获取线路站点失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  const clearCurrentRoute = () => {
    currentRoute.value = null
    directions.value = []
    stops.value = []
  }

  return {
    routes,
    currentRoute,
    directions,
    stops,
    loading,
    pagination,
    fetchRoutes,
    fetchRouteById,
    fetchRouteDirections,
    fetchRouteStops,
    clearCurrentRoute
  }
})
