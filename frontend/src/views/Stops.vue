<template>
  <div class="stops-page">
    <div class="page-header">
      <h1>站点列表</h1>
      <div class="toolbar">
        <SearchBar
          v-model="searchKeyword"
          placeholder="搜索站点名称..."
          @search="handleSearch"
          class="toolbar-search"
        />
        <el-select
          v-model="selectedAgency"
          placeholder="运营机构"
          clearable
          @change="handleFilter"
          style="width: 160px"
        >
          <el-option
            v-for="a in agencies"
            :key="a.agency_id"
            :label="a.agency_name"
            :value="a.agency_id"
          />
        </el-select>
      </div>
    </div>

    <el-divider />

    <div v-loading="stopStore.loading" class="stops-content">
      <el-empty v-if="!stopStore.loading && stopStore.stops.length === 0" description="暂无站点数据" />

      <div v-else class="stops-grid">
        <StopCard
          v-for="stop in stopStore.stops"
          :key="stop.stop_id"
          :stop="stop"
          @click="handleStopClick"
        />
      </div>

      <div v-if="stopStore.stops.length > 0" class="pagination-section">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="stopStore.pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useStopStore } from '@/stores/stopStore'
import { useRegionStore } from '@/stores/regionStore'
import { getAgencies } from '@/api/common'
import SearchBar from '@/components/SearchBar.vue'
import StopCard from '@/components/StopCard.vue'

const router = useRouter()
const stopStore = useStopStore()
const regionStore = useRegionStore()

const searchKeyword = ref('')
const selectedAgency = ref(null)
const agencies = ref([])
const currentPage = ref(1)
const pageSize = ref(20)

const fetchAgencies = async () => {
  try {
    const data = await getAgencies()
    agencies.value = data
  } catch (e) {
    console.error('加载运营机构失败:', e)
  }
}

const fetchStops = async () => {
  const params = {
    page: currentPage.value,
    page_size: pageSize.value
  }

  if (searchKeyword.value) {
    params.search = searchKeyword.value
  }

  if (selectedAgency.value) {
    params.agency_id = selectedAgency.value
  }

  try {
    await stopStore.fetchStops(params)
  } catch (error) {
    console.error('加载站点失败:', error)
  }
}

const handleSearch = () => {
  currentPage.value = 1
  fetchStops()
}

const handleFilter = () => {
  currentPage.value = 1
  fetchStops()
}

const handlePageChange = () => {
  fetchStops()
}

const handleSizeChange = () => {
  currentPage.value = 1
  fetchStops()
}

const handleStopClick = (stop) => {
  router.push(`/stops/${stop.stop_id}`)
}

onMounted(() => {
  fetchAgencies()
  fetchStops()
})

watch(() => regionStore.selectedRegion, () => {
  currentPage.value = 1
  searchKeyword.value = ''
  selectedAgency.value = null
  fetchAgencies()
  fetchStops()
})
</script>

<style scoped>
.stops-page {
  padding: 20px;
}

.page-header h1 {
  margin: 0 0 16px;
  font-size: 28px;
  font-weight: 600;
}

.toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 8px;
}

.toolbar-search {
  flex: 1;
  min-width: 200px;
}

.stops-content {
  min-height: 400px;
}

.stops-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
  margin-bottom: 20px;
}

.pagination-section {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

@media (max-width: 768px) {
  .toolbar {
    flex-direction: column;
    align-items: stretch;
  }
  .toolbar-search {
    min-width: unset;
  }
  .stops-grid {
    grid-template-columns: 1fr;
  }
}
</style>
