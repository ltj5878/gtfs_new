<template>
  <el-config-provider :locale="elementLocale">
  <el-container class="app-container">
    <el-header class="app-header">
      <div class="header-content">
        <div class="logo" @click="$router.push('/')" style="cursor: pointer">
          <el-icon :size="28"><TrendCharts /></el-icon>
          <span>{{ $t('app.title') }}</span>
        </div>
        <el-menu
          :default-active="activeMenu"
          mode="horizontal"
          :ellipsis="false"
          @select="handleMenuSelect"
        >
          <el-menu-item index="/">{{ $t('common.home') }}</el-menu-item>
          <el-sub-menu index="/browse">
            <template #title>{{ $t('nav.routesAndStops') }}</template>
            <el-menu-item index="/routes">{{ $t('common.routes') }}</el-menu-item>
            <el-menu-item index="/stops">{{ $t('common.stops') }}</el-menu-item>
            <el-menu-item index="/map">{{ $t('nav.mapView') }}</el-menu-item>
            <el-menu-item index="/heatmap">{{ $t('nav.stopHeatmap') }}</el-menu-item>
            <el-menu-item index="/schedule">{{ $t('nav.routeSchedule') }}</el-menu-item>
            <el-menu-item index="/playback">{{ $t('nav.vehiclePlayback') }}</el-menu-item>
          </el-sub-menu>
          <el-sub-menu index="/tools">
            <template #title>{{ $t('nav.travelTools') }}</template>
            <el-menu-item index="/favorites">{{ $t('nav.favorites') }}</el-menu-item>
            <el-menu-item index="/planner/transfer">{{ $t('nav.transferPlanner') }}</el-menu-item>
            <el-menu-item index="/analysis/reachability">{{ $t('nav.stopReachability') }}</el-menu-item>
            <el-menu-item index="/compare/routes">{{ $t('nav.routeCompare') }}</el-menu-item>
          </el-sub-menu>
          <el-sub-menu index="/punctuality">
            <template #title>{{ $t('nav.punctuality') }}</template>
            <el-menu-item index="/punctuality/routes">{{ $t('nav.routePunctuality') }}</el-menu-item>
            <el-menu-item index="/punctuality/stops">{{ $t('nav.stopPunctuality') }}</el-menu-item>
            <el-menu-item index="/punctuality/trends">{{ $t('nav.punctualityTrends') }}</el-menu-item>
            <el-menu-item index="/export">{{ $t('nav.dataExport') }}</el-menu-item>
          </el-sub-menu>
          <el-sub-menu v-if="authStore.isAdmin" index="/manage">
            <template #title>{{ $t('nav.manage') }}</template>
            <el-menu-item index="/admin">{{ $t('nav.adminDashboard') }}</el-menu-item>
            <el-menu-item index="/users">{{ $t('nav.userManagement') }}</el-menu-item>
            <el-menu-item index="/admin/audit-logs">{{ $t('nav.auditLog') }}</el-menu-item>
          </el-sub-menu>
        </el-menu>
        <div class="header-right">
          <RegionSelector />
          <NotificationBell v-if="authStore.isLoggedIn" />
          <el-button
            size="small"
            text
            @click="themeStore.toggleTheme()"
            class="theme-btn"
            :title="themeStore.isDark ? '切换到浅色模式' : '切换到深色模式'"
          >
            <el-icon><component :is="themeStore.isDark ? Sunny : Moon" /></el-icon>
          </el-button>
          <el-button
            size="small"
            text
            @click="toggleLocale"
            class="lang-btn"
          >
            {{ currentLocale === 'zh-CN' ? 'EN' : '中' }}
          </el-button>
          <div class="header-user" v-if="authStore.isLoggedIn">
            <el-icon><User /></el-icon>
            <span>{{ authStore.username }}</span>
            <el-tag v-if="authStore.isAdmin" type="danger" size="small" style="margin-left:4px">{{ $t('app.admin') }}</el-tag>
            <el-button link type="primary" @click="handleLogout">{{ $t('app.logout') }}</el-button>
          </div>
        </div>
      </div>
    </el-header>

    <el-main class="app-main">
      <router-view :key="$route.fullPath" />
    </el-main>

    <el-footer class="app-footer">
      <div class="footer-content">
        <p>{{ $t('app.footerCopyright') }}</p>
        <p>{{ $t('app.footerDataSource', { name: currentRegionName }) }}</p>
      </div>
    </el-footer>
  </el-container>
  </el-config-provider>
</template>

<script setup>
import { computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { TrendCharts, User, Sunny, Moon } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/authStore.js'
import { useRegionStore } from '@/stores/regionStore.js'
import { useFavoriteStore } from '@/stores/favoriteStore.js'
import { useThemeStore } from '@/stores/themeStore.js'
import { useNotificationStore } from '@/stores/notificationStore.js'
import RegionSelector from '@/components/RegionSelector.vue'
import NotificationBell from '@/components/NotificationBell.vue'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import en from 'element-plus/es/locale/lang/en'

const { locale: currentLocale } = useI18n()
const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const regionStore = useRegionStore()
const favoriteStore = useFavoriteStore()
const themeStore = useThemeStore()
const notificationStore = useNotificationStore()

// Element Plus 语言切换
const elementLocale = computed(() => currentLocale.value === 'en' ? en : zhCn)

// 切换语言
const toggleLocale = () => {
  const next = currentLocale.value === 'zh-CN' ? 'en' : 'zh-CN'
  currentLocale.value = next
  localStorage.setItem('locale', next)
}

// 页面刷新后若已登录，自动拉取收藏列表和未读通知数
let _notificationTimer = null
onMounted(() => {
  if (authStore.isLoggedIn) {
    favoriteStore.fetchFavorites()
    notificationStore.fetchUnreadCount()
    _notificationTimer = setInterval(() => notificationStore.fetchUnreadCount(), 60000)
  }
})

onUnmounted(() => {
  if (_notificationTimer) clearInterval(_notificationTimer)
})

const activeMenu = computed(() => {
  const path = route.path
  if (path.startsWith('/punctuality')) return path
  if (path.startsWith('/routes')) return '/routes'
  if (path.startsWith('/stops')) return '/stops'
  if (path.startsWith('/heatmap')) return '/heatmap'
  if (path.startsWith('/schedule')) return '/schedule'
  if (path.startsWith('/playback')) return '/playback'
  if (path.startsWith('/favorites')) return '/favorites'
  if (path.startsWith('/planner')) return '/planner/transfer'
  if (path.startsWith('/analysis')) return '/analysis/reachability'
  if (path.startsWith('/compare')) return '/compare/routes'
  if (path.startsWith('/export')) return '/export'
  if (path.startsWith('/admin/audit')) return '/admin/audit-logs'
  if (path.startsWith('/admin')) return '/admin'
  if (path.startsWith('/users')) return '/users'
  return '/'
})

const currentRegionName = computed(() => {
  const r = regionStore.currentRegion()
  return r ? r.region_name : ''
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
  background-color: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color-light);
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
  background-color: var(--el-bg-color-page);
  padding: 0;
  overflow-y: auto;
}

.app-main > div {
  max-width: 1400px;
  margin: 0 auto;
}

.app-footer {
  background-color: var(--el-bg-color);
  border-top: 1px solid var(--el-border-color-light);
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
  color: var(--el-text-color-regular);
  white-space: nowrap;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.lang-btn {
  font-weight: 600;
  font-size: 14px;
  min-width: 32px;
}

.theme-btn {
  font-size: 16px;
  min-width: 32px;
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
