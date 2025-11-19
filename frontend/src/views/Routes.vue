<template>
  <div class="routes-page">
    <div class="page-header">
      <h1>线路列表</h1>
      <div class="search-section">
        <SearchBar
          v-model="searchKeyword"
          placeholder="搜索线路名称..."
          @search="handleSearch"
        />
      </div>
      <div class="filter-section">
        <el-select
          v-model="selectedRouteType"
          placeholder="线路类型"
          clearable
          @change="handleFilter"
        >
          <el-option label="全部类型" :value="null" />
          <el-option label="公交" :value="3" />
          <el-option label="轻轨/地铁" :value="0" />
          <el-option label="有轨电车" :value="5" />
          <el-option label="缆车" :value="6" />
        </el-select>
      </div>
    </div>

    <el-divider />

    <div v-loading="routeStore.loading" class="routes-content">
      <el-empty v-if="!routeStore.loading && routeStore.routes.length === 0" description="暂无线路数据" />

      <div v-else class="routes-grid">
        <RouteCard
          v-for="route in routeStore.routes"
          :key="route.route_id"
          :route="route"
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
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useRouteStore } from '@/stores/routeStore'
import SearchBar from '@/components/SearchBar.vue'
import RouteCard from '@/components/RouteCard.vue'

const router = useRouter()
const routeStore = useRouteStore()

const searchKeyword = ref('')
const selectedRouteType = ref(null)
const currentPage = ref(1)
const pageSize = ref(20)

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
  fetchRoutes()
})
</script>

<style scoped>
.routes-page {
  padding: 20px;
}

.page-header h1 {
  margin: 0 0 20px;
  font-size: 28px;
  font-weight: 600;
}

.search-section {
  margin-bottom: 16px;
}

.filter-section {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
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
  .routes-grid {
    grid-template-columns: 1fr;
  }
}
</style>
