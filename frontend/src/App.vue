<template>
  <el-container class="app-container">
    <el-header class="app-header">
      <div class="header-content">
        <div class="logo" @click="$router.push('/')" style="cursor: pointer">
          <el-icon :size="28"><TrendCharts /></el-icon>
          <span>公交准点率分析系统</span>
        </div>
        <el-menu
          :default-active="activeMenu"
          mode="horizontal"
          :ellipsis="false"
          @select="handleMenuSelect"
        >
          <el-menu-item index="/">首页</el-menu-item>
          <el-sub-menu index="/browse">
            <template #title>线路与站点</template>
            <el-menu-item index="/routes">线路</el-menu-item>
            <el-menu-item index="/stops">站点</el-menu-item>
          </el-sub-menu>
          <el-sub-menu index="/tools">
            <template #title>出行工具</template>
            <el-menu-item index="/favorites">我的收藏</el-menu-item>
            <el-menu-item index="/planner/transfer">换乘规划</el-menu-item>
            <el-menu-item index="/compare/routes">线路对比</el-menu-item>
          </el-sub-menu>
          <el-sub-menu index="/punctuality">
            <template #title>准点率</template>
            <el-menu-item index="/punctuality">准点率概览</el-menu-item>
            <el-menu-item index="/punctuality/routes">线路准点率</el-menu-item>
            <el-menu-item index="/punctuality/stops">站点准点率</el-menu-item>
            <el-menu-item index="/punctuality/trends">准点率趋势总览</el-menu-item>
          </el-sub-menu>
          <el-sub-menu v-if="authStore.isAdmin" index="/manage">
            <template #title>管理</template>
            <el-menu-item index="/admin">运维看板</el-menu-item>
            <el-menu-item index="/users">用户管理</el-menu-item>
          </el-sub-menu>
        </el-menu>
        <div class="header-right">
          <RegionSelector />
          <div class="header-user" v-if="authStore.isLoggedIn">
            <el-icon><User /></el-icon>
            <span>{{ authStore.username }}</span>
            <el-tag v-if="authStore.isAdmin" type="danger" size="small" style="margin-left:4px">管理员</el-tag>
            <el-button link type="primary" @click="handleLogout">退出</el-button>
          </div>
        </div>
      </div>
    </el-header>

    <el-main class="app-main">
      <router-view :key="$route.fullPath" />
    </el-main>

    <el-footer class="app-footer">
      <div class="footer-content">
        <p>&copy; 2026 公交准点率分析系统</p>
        <p>数据来源: {{ currentRegionName }} GTFS + GTFS Realtim数据</p>
      </div>
    </el-footer>
  </el-container>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { TrendCharts, User } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/authStore.js'
import { useRegionStore } from '@/stores/regionStore.js'
import { useFavoriteStore } from '@/stores/favoriteStore.js'
import RegionSelector from '@/components/RegionSelector.vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const regionStore = useRegionStore()
const favoriteStore = useFavoriteStore()

// 页面刷新后若已登录，自动拉取收藏列表
onMounted(() => {
  if (authStore.isLoggedIn) {
    favoriteStore.fetchFavorites()
  }
})

const activeMenu = computed(() => {
  const path = route.path
  if (path.startsWith('/punctuality')) return path
  if (path.startsWith('/routes')) return '/routes'
  if (path.startsWith('/stops')) return '/stops'
  if (path.startsWith('/favorites')) return '/favorites'
  if (path.startsWith('/planner')) return '/planner/transfer'
  if (path.startsWith('/compare')) return '/compare/routes'
  if (path.startsWith('/admin')) return '/admin'
  if (path.startsWith('/users')) return '/users'
  return '/'
})

const currentRegionName = computed(() => {
  const r = regionStore.currentRegion()
  return r ? r.region_name : '旧金山湾区'
})

const handleMenuSelect = (index) => {
  window.location.href = index
}

const handleLogout = async () => {
  await authStore.logout()
  router.push('/login')
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body, #app {
  height: 100%;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

.app-container {
  height: 100%;
}

.app-header {
  background-color: #fff;
  border-bottom: 1px solid #e4e7ed;
  padding: 0;
  height: 60px;
  display: flex;
  align-items: center;
}

.header-content {
  width: 100%;
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 18px;
  font-weight: 600;
  color: #409eff;
  cursor: pointer;
  user-select: none;
}

.logo:hover {
  opacity: 0.8;
}

.app-main {
  background-color: #f5f7fa;
  padding: 0;
  overflow-y: auto;
}

.app-main > div {
  max-width: 1400px;
  margin: 0 auto;
}

.app-footer {
  background-color: #fff;
  border-top: 1px solid #e4e7ed;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.footer-content {
  text-align: center;
  color: #909399;
  font-size: 12px;
}

.footer-content p {
  margin: 2px 0;
}

.header-user {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: #606266;
  white-space: nowrap;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@media (max-width: 768px) {
  .logo span {
    display: none;
  }

  .header-content {
    padding: 0 10px;
  }
}
</style>
