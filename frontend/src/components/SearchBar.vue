<template>
  <div class="search-bar">
    <el-input
      v-model="searchText"
      :placeholder="placeholder"
      clearable
      @input="handleInput"
      @clear="handleClear"
    >
      <template #prefix>
        <el-icon><Search /></el-icon>
      </template>
    </el-input>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { Search } from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  placeholder: {
    type: String,
    default: '搜索...'
  },
  debounce: {
    type: Number,
    default: 300
  }
})

const emit = defineEmits(['update:modelValue', 'search', 'clear'])

const searchText = ref(props.modelValue)
let debounceTimer = null

watch(() => props.modelValue, (newVal) => {
  searchText.value = newVal
})

const handleInput = (value) => {
  emit('update:modelValue', value)

  if (debounceTimer) {
    clearTimeout(debounceTimer)
  }

  debounceTimer = setTimeout(() => {
    emit('search', value)
  }, props.debounce)
}

const handleClear = () => {
  emit('update:modelValue', '')
  emit('clear')
}
</script>

<style scoped>
.search-bar {
  width: 100%;
}
</style>
