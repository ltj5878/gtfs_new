import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getFavorites, addFavorite, removeFavorite } from '@/api/favorites.js'

export const useFavoriteStore = defineStore('favorite', () => {
  // 收藏列表，每项包含 { id, region, item_type, item_id, item_name, created_at }
  const favorites = ref([])

  // 从后端拉取收藏列表
  async function fetchFavorites() {
    try {
      const data = await getFavorites()
      favorites.value = Array.isArray(data) ? data : []
    } catch (e) {
      console.error('获取收藏列表失败:', e)
      favorites.value = []
    }
  }

  // 判断某项是否已收藏（本地快速判断）
  function isFavorite(region, itemType, itemId) {
    return favorites.value.some(
      f => f.region === region && f.item_type === itemType && f.item_id === String(itemId)
    )
  }

  // 切换收藏状态
  async function toggleFavorite(item) {
    // item: { region, item_type, item_id, item_name }
    const { region, item_type, item_id, item_name } = item
    if (isFavorite(region, item_type, item_id)) {
      // 乐观更新：先从本地移除
      favorites.value = favorites.value.filter(
        f => !(f.region === region && f.item_type === item_type && f.item_id === String(item_id))
      )
      try {
        await removeFavorite({ region, item_type, item_id })
      } catch (e) {
        // 失败时回滚
        await fetchFavorites()
        throw e
      }
    } else {
      // 乐观更新：先添加到本地
      const tempItem = { id: null, region, item_type, item_id: String(item_id), item_name, created_at: new Date().toISOString() }
      favorites.value.unshift(tempItem)
      try {
        const result = await addFavorite({ region, item_type, item_id: String(item_id), item_name })
        // 更新本地 id
        const idx = favorites.value.findIndex(
          f => f.region === region && f.item_type === item_type && f.item_id === String(item_id) && f.id === null
        )
        if (idx !== -1 && result?.id) {
          favorites.value[idx].id = result.id
        }
      } catch (e) {
        // 失败时回滚
        await fetchFavorites()
        throw e
      }
    }
  }

  // 登出时清空
  function clearFavorites() {
    favorites.value = []
  }

  return { favorites, fetchFavorites, isFavorite, toggleFavorite, clearFavorites }
})
