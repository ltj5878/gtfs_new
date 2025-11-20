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
    }
  ]
})

export default router
