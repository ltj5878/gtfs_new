<template>
  <div class="audit-log-page">
    <div class="page-header">
      <div class="header-content">
        <h1>{{ $t('auditLog.title') }}</h1>
        <p>{{ $t('auditLog.subtitle') }}</p>
      </div>
      <div class="header-actions">
        <el-button type="primary" :loading="loading" :icon="Refresh" @click="fetchData">
          {{ $t('auditLog.search') }}
        </el-button>
      </div>
    </div>

    <!-- 筛选栏 -->
    <el-card class="filter-card">
      <el-row :gutter="16" align="middle">
        <el-col :xs="24" :sm="6">
          <el-select
            v-model="filters.action"
            :placeholder="$t('auditLog.allActions')"
            clearable
            style="width: 100%"
          >
            <el-option
              v-for="item in actionOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-col>
        <el-col :xs="24" :sm="6">
          <el-input
            v-model="filters.username"
            :placeholder="$t('auditLog.searchUsername')"
            :prefix-icon="Search"
            clearable
          />
        </el-col>
        <el-col :xs="24" :sm="8">
          <el-date-picker
            v-model="filters.dateRange"
            type="datetimerange"
            :range-separator="'-'"
            :start-placeholder="$t('auditLog.timeRange')"
            end-placeholder=""
            value-format="YYYY-MM-DD HH:mm:ss"
            style="width: 100%"
          />
        </el-col>
        <el-col :xs="24" :sm="4">
          <el-button @click="resetFilters" style="width: 100%">
            {{ $t('auditLog.reset') }}
          </el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- 数据表格 -->
    <el-card class="table-card">
      <el-table :data="logs" v-loading="loading" stripe>
        <template #empty>
          <el-empty :description="$t('auditLog.noData')" />
        </template>

        <el-table-column prop="id" label="ID" width="70" />

        <el-table-column prop="username" :label="$t('auditLog.username')" width="120">
          <template #default="{ row }">
            <span>{{ row.username || '—' }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="action" :label="$t('auditLog.action')" width="130">
          <template #default="{ row }">
            <el-tag :type="actionTagType(row.action)" size="small">
              {{ actionLabel(row.action) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="target" :label="$t('auditLog.target')" width="160" show-overflow-tooltip />

        <el-table-column prop="detail" :label="$t('auditLog.detail')" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <span>{{ formatDetail(row.detail) }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="ip_address" :label="$t('auditLog.ipAddress')" width="140" />

        <el-table-column prop="created_at" :label="$t('auditLog.time')" width="180">
          <template #default="{ row }">
            <span>{{ formatTime(row.created_at) }}</span>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="fetchData"
          @current-change="fetchData"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { Refresh, Search } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getAuditLogs } from '@/api/audit.js'

const { t } = useI18n()

const loading = ref(false)
const logs = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)

const filters = ref({
  action: '',
  username: '',
  dateRange: null,
})

// 操作类型选项
const actionOptions = computed(() => [
  { value: 'login', label: t('auditLog.actionLogin') },
  { value: 'login_failed', label: t('auditLog.actionLoginFailed') },
  { value: 'register', label: t('auditLog.actionRegister') },
  { value: 'logout', label: t('auditLog.actionLogout') },
  { value: 'create_user', label: t('auditLog.actionCreateUser') },
  { value: 'toggle_user', label: t('auditLog.actionToggleUser') },
  { value: 'delete_user', label: t('auditLog.actionDeleteUser') },
  { value: 'reset_password', label: t('auditLog.actionResetPassword') },
  { value: 'change_password', label: t('auditLog.actionChangePassword') },
  { value: 'refresh_punctuality', label: t('auditLog.actionRefreshPunctuality') },
])

// 操作类型 → 标签颜色
const actionTagType = (action) => {
  const map = {
    login: 'success',
    login_failed: 'danger',
    register: '',
    logout: 'info',
    create_user: 'success',
    toggle_user: 'warning',
    delete_user: 'danger',
    reset_password: 'warning',
    change_password: 'warning',
    refresh_punctuality: '',
  }
  return map[action] || 'info'
}

// 操作类型 → 显示文字
const actionLabel = (action) => {
  const map = {
    login: t('auditLog.actionLogin'),
    login_failed: t('auditLog.actionLoginFailed'),
    register: t('auditLog.actionRegister'),
    logout: t('auditLog.actionLogout'),
    create_user: t('auditLog.actionCreateUser'),
    toggle_user: t('auditLog.actionToggleUser'),
    delete_user: t('auditLog.actionDeleteUser'),
    reset_password: t('auditLog.actionResetPassword'),
    change_password: t('auditLog.actionChangePassword'),
    refresh_punctuality: t('auditLog.actionRefreshPunctuality'),
  }
  return map[action] || action
}

const formatDetail = (detail) => {
  if (!detail || typeof detail === 'string') return detail || ''
  try {
    return JSON.stringify(detail, null, 0)
  } catch {
    return String(detail)
  }
}

const formatTime = (ts) => {
  if (!ts) return '—'
  const d = new Date(ts)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

const fetchData = async () => {
  loading.value = true
  try {
    const params = {
      page: page.value,
      page_size: pageSize.value,
    }
    if (filters.value.action) params.action = filters.value.action
    if (filters.value.username) params.username = filters.value.username
    if (filters.value.dateRange && filters.value.dateRange.length === 2) {
      params.start_time = filters.value.dateRange[0]
      params.end_time = filters.value.dateRange[1]
    }

    const res = await getAuditLogs(params)
    const data = res?.data || res
    logs.value = data.list || []
    total.value = data.total || 0
  } catch {
    ElMessage.error(t('auditLog.loadFailed'))
  } finally {
    loading.value = false
  }
}

const resetFilters = () => {
  filters.value = { action: '', username: '', dateRange: null }
  page.value = 1
  fetchData()
}

// 筛选条件变化时重新查询
watch(() => filters.value.action, () => { page.value = 1; fetchData() })

onMounted(fetchData)
</script>

<style scoped>
.audit-log-page {
  padding: 20px;
  background: var(--el-bg-color-page);
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
  padding: 24px;
  background: var(--el-bg-color);
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.header-content h1 {
  margin: 0 0 8px 0;
  color: var(--el-text-color-primary);
  font-size: 28px;
  font-weight: 600;
}

.header-content p {
  margin: 0;
  color: var(--el-text-color-secondary);
  font-size: 14px;
}

.filter-card {
  margin-bottom: 20px;
}

.table-card {
  margin-bottom: 20px;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    gap: 16px;
  }
}
</style>
