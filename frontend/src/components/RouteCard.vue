<template>
  <el-card class="route-card" shadow="hover" @click="handleClick">
    <div class="route-header">
      <div class="route-badge" :style="{ backgroundColor: `#${route.route_color || '005596'}` }">
        <span :style="{ color: `#${route.route_text_color || 'FFFFFF'}` }">
          {{ route.route_short_name || 'N/A' }}
        </span>
      </div>
      <div class="route-info">
        <h3>{{ route.route_long_name }}</h3>
        <p class="route-type">{{ getRouteTypeName(route.route_type) }}</p>
      </div>
    </div>
    <div v-if="route.category || route.subcategory" class="route-meta">
      <el-tag v-if="route.category" size="small">{{ route.category }}</el-tag>
      <el-tag v-if="route.subcategory" size="small" type="info">{{ route.subcategory }}</el-tag>
    </div>
  </el-card>
</template>

<script setup>
const props = defineProps({
  route: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['click'])

const routeTypeNames = {
  0: '轻轨/地铁',
  1: '地铁',
  2: '铁路',
  3: '公交',
  4: '轮渡',
  5: '有轨电车',
  6: '缆车',
  7: '索道'
}

const getRouteTypeName = (type) => {
  return routeTypeNames[type] || '未知'
}

const handleClick = () => {
  emit('click', props.route)
}
</script>

<style scoped>
.route-card {
  cursor: pointer;
  transition: transform 0.2s;
}

.route-card:hover {
  transform: translateY(-2px);
}

.route-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.route-badge {
  width: 50px;
  height: 50px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 16px;
  flex-shrink: 0;
}

.route-info {
  flex: 1;
  min-width: 0;
}

.route-info h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.route-type {
  margin: 4px 0 0;
  font-size: 12px;
  color: #909399;
}

.route-meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
</style>
