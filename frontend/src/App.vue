<template>
  <el-container class="app-container">
    <el-header class="app-header">
      <div class="header-content">
        <div class="logo" @click="$router.push('/')">
          <el-icon :size="28"><TrendCharts /></el-icon>
          <span>GTFS 公交数据分析系统</span>
        </div>
        <el-menu
          :default-active="activeMenu"
          mode="horizontal"
          :ellipsis="false"
          @select="handleMenuSelect"
        >
          <el-menu-item index="/">首页</el-menu-item>
          <el-menu-item index="/routes">线路</el-menu-item>
          <el-menu-item index="/stops">站点</el-menu-item>
          <el-menu-item index="/map">地图</el-menu-item>
        </el-menu>
      </div>
    </el-header>

    <el-main class="app-main">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </el-main>

    <el-footer class="app-footer">
      <div class="footer-content">
        <p>&copy; 2025 GTFS 公交数据分析系统</p>
        <p>数据来源: 511 SF Bay API</p>
      </div>
    </el-footer>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { TrendCharts } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()

const activeMenu = computed(() => {
  const path = route.path
  if (path.startsWith('/routes')) return '/routes'
  if (path.startsWith('/stops')) return '/stops'
  if (path.startsWith('/map')) return '/map'
  return '/'
})

const handleMenuSelect = (index) => {
  router.push(index)
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
