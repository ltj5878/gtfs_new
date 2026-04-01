import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/Login.vue'),
      meta: { requiresAuth: false }
    },
    {
      path: '/',
      name: 'home',
      component: () => import('@/views/Home.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/routes',
      name: 'routes',
      component: () => import('@/views/Routes.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/routes/:id',
      name: 'route-detail',
      component: () => import('@/views/RouteDetail.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/stops',
      name: 'stops',
      component: () => import('@/views/Stops.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/stops/:id',
      name: 'stop-detail',
      component: () => import('@/views/StopDetail.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/map',
      name: 'map',
      component: () => import('@/views/Map.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/punctuality',
      name: 'punctuality-overview',
      component: () => import('@/views/PunctualityOverview.vue'),
      meta: { requiresAuth: true, title: '准点率概览', icon: 'TrendCharts' }
    },
    {
      path: '/punctuality/routes',
      name: 'route-punctuality',
      component: () => import('@/views/RoutePunctuality.vue'),
      meta: { requiresAuth: true, title: '线路准点率', icon: 'Bus' }
    },
    {
      path: '/punctuality/routes/:routeId',
      name: 'route-punctuality-detail',
      component: () => import('@/views/RoutePunctualityDetail.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/punctuality/stops',
      name: 'stop-punctuality',
      component: () => import('@/views/StopPunctuality.vue'),
      meta: { requiresAuth: true, title: '站点准点率', icon: 'MapLocation' }
    },
    {
      path: '/punctuality/stops/:stopId',
      name: 'stop-punctuality-detail',
      component: () => import('@/views/StopPunctualityDetail.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/punctuality/realtime',
      name: 'realtime-monitor',
      component: () => import('@/views/RealtimeMonitor.vue'),
      meta: { requiresAuth: true, title: '实时监控', icon: 'Monitor' }
    },
    {
      path: '/punctuality/trends',
      name: 'punctuality-trends',
      component: () => import('@/views/PunctualityTrends.vue'),
      meta: { requiresAuth: true, title: '准点率趋势总览', icon: 'DataLine' }
    },
    {
      path: '/favorites',
      name: 'favorites',
      component: () => import('@/views/Favorites.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/planner/transfer',
      name: 'transfer-planner',
      component: () => import('@/views/TransferPlanner.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/compare/routes',
      name: 'route-compare',
      component: () => import('@/views/RouteCompare.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/export',
      name: 'data-export',
      component: () => import('@/views/DataExport.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/admin',
      name: 'admin',
      component: () => import('@/views/AdminDashboard.vue'),
      meta: { requiresAuth: true, requiresAdmin: true }
    },
    {
      path: '/users',
      name: 'users',
      component: () => import('@/views/UserManagement.vue'),
      meta: { requiresAuth: true, requiresAdmin: true }
    },
    {
      path: '/admin/audit-logs',
      name: 'audit-logs',
      component: () => import('@/views/AuditLog.vue'),
      meta: { requiresAuth: true, requiresAdmin: true }
    }
  ]
})

router.beforeEach((to, _from) => {
  const token = localStorage.getItem('auth_token')
  const role = localStorage.getItem('auth_role')

  if (to.meta.requiresAuth && !token) {
    return { name: 'login' }
  }
  if (to.name === 'login' && token) {
    return { name: 'home' }
  }
  // 管理员专属页面，非管理员重定向到首页
  if (to.meta.requiresAdmin && role !== 'admin') {
    return { name: 'home' }
  }
})

export default router
