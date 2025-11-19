<template>
  <div class="map-page">
    <el-card class="map-card">
      <template #header>
        <div class="map-header">
          <span>地图视图</span>
          <el-tag type="info">开发中</el-tag>
        </div>
      </template>
      <div class="map-container">
        <div class="map-placeholder">
          <el-icon :size="80"><MapLocation /></el-icon>
          <h2>地图功能开发中</h2>
          <p>即将支持以下功能：</p>
          <ul class="feature-list">
            <li>在地图上显示所有站点</li>
            <li>显示线路轨迹</li>
            <li>实时车辆位置</li>
            <li>点击站点查看详情</li>
            <li>按线路筛选显示</li>
          </ul>
          <el-button type="primary" @click="$router.push('/')">返回首页</el-button>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { MapLocation } from '@element-plus/icons-vue'
</script>

<style scoped>
.map-page {
  padding: 20px;
  height: calc(100vh - 120px);
}

.map-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.map-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.map-container {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.map-placeholder {
  text-align: center;
  color: #909399;
  max-width: 500px;
}

.map-placeholder h2 {
  margin: 20px 0;
  color: #606266;
}

.map-placeholder p {
  margin: 16px 0;
}

.feature-list {
  text-align: left;
  margin: 20px auto;
  display: inline-block;
}

.feature-list li {
  margin: 8px 0;
  list-style-position: inside;
}
</style>
