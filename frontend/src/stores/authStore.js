import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as apiLogin, logout as apiLogout } from '@/api/auth.js'
import { useFavoriteStore } from '@/stores/favoriteStore.js'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('auth_token') || '')
  const username = ref(localStorage.getItem('auth_username') || '')

  const isLoggedIn = computed(() => !!token.value)

  async function login(usernameVal, password) {
    const data = await apiLogin(usernameVal, password)
    token.value = data.token
    username.value = data.username
    localStorage.setItem('auth_token', data.token)
    localStorage.setItem('auth_username', data.username)
    // 登录成功后拉取收藏列表
    const favoriteStore = useFavoriteStore()
    favoriteStore.fetchFavorites()
  }

  async function logout() {
    try {
      await apiLogout()
    } catch (_) {
      // 忽略退出时的网络错误
    }
    token.value = ''
    username.value = ''
    localStorage.removeItem('auth_token')
    localStorage.removeItem('auth_username')
    // 登出时清空收藏
    const favoriteStore = useFavoriteStore()
    favoriteStore.clearFavorites()
  }

  return { token, username, isLoggedIn, login, logout }
})
