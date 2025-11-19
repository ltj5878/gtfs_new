import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getAgencies, getStats } from '@/api/common'

export const useAppStore = defineStore('app', () => {
  const agencies = ref([])
  const stats = ref(null)
  const loading = ref(false)

  const fetchAgencies = async () => {
    loading.value = true
    try {
      const data = await getAgencies()
      agencies.value = data
      return data
    } catch (error) {
      console.error('获取运营机构失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  const fetchStats = async () => {
    loading.value = true
    try {
      const data = await getStats()
      stats.value = data
      return data
    } catch (error) {
      console.error('获取统计信息失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  return {
    agencies,
    stats,
    loading,
    fetchAgencies,
    fetchStats
  }
})
