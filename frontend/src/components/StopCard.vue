<template>
  <el-card class="stop-card" shadow="hover" @click="handleClick">
    <div class="stop-header">
      <el-icon class="stop-icon" :size="24"><Location /></el-icon>
      <div class="stop-info">
        <h3>{{ stop.stop_name }}</h3>
        <p v-if="stop.stop_code" class="stop-code">站点编号: {{ stop.stop_code }}</p>
      </div>
    </div>
    <div class="stop-location">
      <span class="location-text">
        <el-icon><Position /></el-icon>
        {{ stop.stop_lat.toFixed(5) }}, {{ stop.stop_lon.toFixed(5) }}
      </span>
    </div>
    <p v-if="stop.stop_desc" class="stop-desc">{{ stop.stop_desc }}</p>
  </el-card>
</template>

<script setup>
import { Location, Position } from '@element-plus/icons-vue'

const props = defineProps({
  stop: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['click'])

const handleClick = () => {
  emit('click', props.stop)
}
</script>

<style scoped>
.stop-card {
  cursor: pointer;
  transition: transform 0.2s;
}

.stop-card:hover {
  transform: translateY(-2px);
}

.stop-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.stop-icon {
  color: #409eff;
  flex-shrink: 0;
}

.stop-info {
  flex: 1;
  min-width: 0;
}

.stop-info h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.stop-code {
  margin: 4px 0 0;
  font-size: 12px;
  color: #909399;
}

.stop-location {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 8px;
}

.location-text {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #606266;
}

.stop-desc {
  margin: 8px 0 0;
  font-size: 13px;
  color: #606266;
  line-height: 1.5;
}
</style>
