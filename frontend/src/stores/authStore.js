import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as apiLogin, logout as apiLogout } from '@/api/auth.js'
import { useFavoriteStore } from '@/stores/favoriteStore.js'
import { useNotificationStore } from '@/stores/notificationStore.js'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('auth_token') || '')
  const username = ref(localStorage.getItem('auth_username') || '')
  const role = ref(localStorage.getItem('auth_role') || 'user')

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => role.value === 'admin')

  async function login(usernameVal, password) {
    const data = await apiLogin(usernameVal, password)
    token.value = data.token
    username.value = data.username
    role.value = data.role || 'user'
    localStorage.setItem('auth_token', data.token)
    localStorage.setItem('auth_username', data.username)
    localStorage.setItem('auth_role', data.role || 'user')
    // 登录成功后拉取收藏列表和未读通知数
    const favoriteStore = useFavoriteStore()
    favoriteStore.fetchFavorites()
    const notificationStore = useNotificationStore()
    notificationStore.fetchUnreadCount()
  }

  async function logout() {
    try {
      await apiLogout()
    } catch (_) {
      // 忽略退出时的网络错误
    }
    token.value = ''
    username.value = ''
    role.value = 'user'
    localStorage.removeItem('auth_token')
    localStorage.removeItem('auth_username')
    localStorage.removeItem('auth_role')
    // 登出时清空收藏和通知
    const favoriteStore = useFavoriteStore()
    favoriteStore.clearFavorites()
    const notificationStore = useNotificationStore()
    notificationStore.clearNotifications()
  }

  return { token, username, role, isLoggedIn, isAdmin, login, logout }
})
