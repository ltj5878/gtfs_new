import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import { getRegions } from '@/api/common'

export const useRegionStore = defineStore('region', () => {
  // 从 localStorage 恢复上次选择的地区，默认 sf
  const selectedRegion = ref(localStorage.getItem('selected_region') || 'sf')
  const regions = ref([])
  const loading = ref(false)

  // 持久化到 localStorage
  watch(selectedRegion, (val) => {
    localStorage.setItem('selected_region', val)
  })

  const fetchRegions = async () => {
    loading.value = true
    try {
      const data = await getRegions()
      // 屏蔽纽约地区，只保留旧金山湾区和悉尼
      regions.value = data.filter(r => r.region_id !== 'nyc')
      return data
    } catch (error) {
      console.error('获取地区列表失败:', error)
      // 降级到默认地区列表
      regions.value = [
        { region_id: 'sf', region_name: '旧金山湾区', country: 'US' },
        { region_id: 'sydney', region_name: '悉尼', country: 'AU' },
      ]
    } finally {
      loading.value = false
    }
  }

  const setRegion = (regionId) => {
    selectedRegion.value = regionId
  }

  const currentRegion = () => {
    return regions.value.find(r => r.region_id === selectedRegion.value) || null
  }

  return {
    selectedRegion,
    regions,
    loading,
    fetchRegions,
    setRegion,
    currentRegion,
  }
})
