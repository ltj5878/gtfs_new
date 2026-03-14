<template>
  <el-select
    v-model="regionStore.selectedRegion"
    size="small"
    style="width: 140px"
    :loading="regionStore.loading"
    @change="handleChange"
  >
    <el-option
      v-for="region in regionStore.regions"
      :key="region.region_id"
      :label="region.region_name"
      :value="region.region_id"
    />
  </el-select>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRegionStore } from '@/stores/regionStore'
import { useAppStore } from '@/stores/appStore'

const regionStore = useRegionStore()
const appStore = useAppStore()

onMounted(async () => {
  if (regionStore.regions.length === 0) {
    await regionStore.fetchRegions()
  }
})

const handleChange = () => {
  // 切换地区后重新加载统计和机构数据
  appStore.fetchStats()
  appStore.fetchAgencies()
}
</script>
