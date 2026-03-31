<template>
  <div class="routes-page">
    <div class="page-header">
      <h1>{{ $t('routeList.title') }}</h1>
      <div class="toolbar">
        <SearchBar
          v-model="searchKeyword"
          :placeholder="$t('routeList.searchPlaceholder')"
          @search="handleSearch"
          class="toolbar-search"
        />
        <el-select
          v-model="selectedAgency"
          :placeholder="$t('routeList.agencyPlaceholder')"
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
        <el-select
          v-model="selectedRouteType"
          :placeholder="$t('routeList.typePlaceholder')"
          clearable
          @change="handleFilter"
          style="width: 130px"
        >
          <el-option :label="$t('routeList.allTypes')" :value="null" />
          <el-option :label="$t('routeList.bus')" :value="3" />
          <el-option :label="$t('routeList.lightRail')" :value="0" />
          <el-option :label="$t('routeList.tram')" :value="5" />
          <el-option :label="$t('routeList.cableCar')" :value="6" />
        </el-select>
      </div>
    </div>

    <el-divider />

    <div v-loading="routeStore.loading" class="routes-content">
      <el-empty v-if="!routeStore.loading && routeStore.routes.length === 0" :description="$t('routeList.noData')" />

      <div v-else class="routes-grid">
        <RouteCard
          v-for="route in routeStore.routes"
          :key="route.route_id"
          :route="route"
          :region="regionStore.selectedRegion"
          @click="handleRouteClick"
        />
      </div>

      <div v-if="routeStore.routes.length > 0" class="pagination-section">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="routeStore.pagination.total"
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
import { useRouteStore } from '@/stores/routeStore'
import { useRegionStore } from '@/stores/regionStore'
import { getAgencies } from '@/api/common'
import SearchBar from '@/components/SearchBar.vue'
import RouteCard from '@/components/RouteCard.vue'

const router = useRouter()
const routeStore = useRouteStore()
const regionStore = useRegionStore()

const searchKeyword = ref('')
const selectedRouteType = ref(null)
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

const fetchRoutes = async () => {
  const params = {
    page: currentPage.value,
    page_size: pageSize.value
  }

  if (searchKeyword.value) {
    params.search = searchKeyword.value
  }

  if (selectedRouteType.value !== null) {
    params.route_type = selectedRouteType.value
  }

  if (selectedAgency.value) {
    params.agency_id = selectedAgency.value
  }

  try {
    await routeStore.fetchRoutes(params)
  } catch (error) {
    console.error('加载线路失败:', error)
  }
}

const handleSearch = () => {
  currentPage.value = 1
  fetchRoutes()
}

const handleFilter = () => {
  currentPage.value = 1
  fetchRoutes()
}

const handlePageChange = () => {
  fetchRoutes()
}

const handleSizeChange = () => {
  currentPage.value = 1
  fetchRoutes()
}

const handleRouteClick = (route) => {
  router.push(`/routes/${route.route_id}`)
}

onMounted(() => {
  fetchAgencies()
  fetchRoutes()
})

watch(() => regionStore.selectedRegion, () => {
  currentPage.value = 1
  searchKeyword.value = ''
  selectedRouteType.value = null
  selectedAgency.value = null
  fetchAgencies()
  fetchRoutes()
})
</script>

<style scoped>
.routes-page {
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

.routes-content {
  min-height: 400px;
}

.routes-grid {
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
  .routes-grid {
    grid-template-columns: 1fr;
  }
}
</style>
