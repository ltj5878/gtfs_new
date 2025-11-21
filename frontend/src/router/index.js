import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('@/views/Home.vue')
    },
    {
      path: '/routes',
      name: 'routes',
      component: () => import('@/views/Routes.vue')
    },
    {
      path: '/routes/:id',
      name: 'route-detail',
      component: () => import('@/views/RouteDetail.vue')
    },
    {
      path: '/stops',
      name: 'stops',
      component: () => import('@/views/Stops.vue')
    },
    {
      path: '/stops/:id',
      name: 'stop-detail',
      component: () => import('@/views/StopDetail.vue')
    },
    // 准点率分析页面
    {
      path: '/punctuality',
      name: 'punctuality-overview',
      component: () => import('@/views/PunctualityOverview.vue'),
      meta: {
        title: '准点率概览',
        icon: 'TrendCharts'
      }
    },
    {
      path: '/punctuality/routes',
      name: 'route-punctuality',
      component: () => import('@/views/RoutePunctuality.vue'),
      meta: {
        title: '线路准点率',
        icon: 'Bus'
      }
    },
    {
      path: '/punctuality/stops',
      name: 'stop-punctuality',
      component: () => import('@/views/StopPunctuality.vue'),
      meta: {
        title: '站点准点率',
        icon: 'MapLocation'
      }
    },
    {
      path: '/punctuality/realtime',
      name: 'realtime-monitor',
      component: () => import('@/views/RealtimeMonitor.vue'),
      meta: {
        title: '实时监控',
        icon: 'Monitor'
      }
    }
  ]
})

export default router
