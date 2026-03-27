<template>
  <div class="user-management-page">
    <div class="page-header">
      <h1>用户管理</h1>
      <el-button type="primary" :icon="Plus" @click="showCreateDialog = true">新建用户</el-button>
    </div>

    <el-divider />

    <el-table :data="users" v-loading="loading" stripe>
      <el-table-column prop="id" label="ID" width="60" align="center" />
      <el-table-column prop="username" label="用户名" />
      <el-table-column label="角色" width="100">
        <template #default="{ row }">
          <el-tag :type="row.role === 'admin' ? 'danger' : 'info'" size="small">
            {{ row.role === 'admin' ? '管理员' : '普通用户' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100" align="center">
        <template #default="{ row }">
          <el-switch
            v-model="row.is_active"
            :disabled="row.role === 'admin'"
            @change="(val) => handleToggleActive(row, val)"
          />
        </template>
      </el-table-column>
      <el-table-column label="创建时间" width="180">
        <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="160" align="center">
        <template #default="{ row }">
          <el-button
            type="primary"
            size="small"
            link
            :disabled="row.role === 'admin'"
            @click="handleOpenPassword(row)"
          >密码</el-button>
          <el-button
            type="danger"
            size="small"
            link
            :disabled="row.role === 'admin'"
            @click="handleDelete(row)"
          >删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 新建用户对话框 -->
    <el-dialog v-model="showCreateDialog" title="新建用户" width="400px" @close="resetForm">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="80px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="4-20 个字符" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" placeholder="至少 6 位" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="handleCreate">创建</el-button>
      </template>
    </el-dialog>

    <!-- 密码管理对话框 -->
    <el-dialog v-model="showPasswordDialog" :title="`密码管理 — ${passwordTarget?.username}`" width="440px" @close="resetPasswordForm">
      <el-tabs v-model="passwordTab">
        <el-tab-pane label="查看/重置密码" name="reset">
          <div class="password-section">
            <p class="password-tip">点击下方按钮将为该用户生成一个新的临时密码，原密码将立即失效。</p>
            <el-button type="warning" :loading="resetting" @click="handleResetPassword">生成临时密码</el-button>
            <div v-if="tempPassword" class="temp-password-box">
              <span class="temp-label">临时密码：</span>
              <el-tag type="success" size="large" class="temp-value">{{ tempPassword }}</el-tag>
              <el-button size="small" link @click="copyPassword">复制</el-button>
            </div>
          </div>
        </el-tab-pane>
        <el-tab-pane label="直接修改密码" name="change">
          <el-form :model="pwForm" :rules="pwRules" ref="pwFormRef" label-width="90px" style="margin-top:12px">
            <el-form-item label="新密码" prop="password">
              <el-input v-model="pwForm.password" type="password" placeholder="至少 6 位" show-password />
            </el-form-item>
            <el-form-item label="确认密码" prop="confirm">
              <el-input v-model="pwForm.confirm" type="password" placeholder="再次输入新密码" show-password />
            </el-form-item>
          </el-form>
          <div style="text-align:right;margin-top:8px">
            <el-button type="primary" :loading="changing" @click="handleChangePassword">确认修改</el-button>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { getUsers, createUser, updateUser, deleteUser, resetUserPassword, updateUserPassword } from '@/api/users.js'

const users = ref([])
const loading = ref(false)
const creating = ref(false)
const showCreateDialog = ref(false)
const formRef = ref(null)

// 密码管理
const showPasswordDialog = ref(false)
const passwordTarget = ref(null)
const passwordTab = ref('reset')
const tempPassword = ref('')
const resetting = ref(false)
const changing = ref(false)
const pwFormRef = ref(null)
const pwForm = ref({ password: '', confirm: '' })
const pwRules = {
  password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码至少 6 位', trigger: 'blur' }
  ],
  confirm: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    {
      validator: (_, val, cb) => {
        if (val !== pwForm.value.password) cb(new Error('两次密码不一致'))
        else cb()
      },
      trigger: 'blur'
    }
  ]
}

const form = ref({ username: '', password: '' })
const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 4, max: 20, message: '长度在 4-20 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少 6 位', trigger: 'blur' }
  ]
}

const formatTime = (ts) => {
  if (!ts) return '--'
  const d = new Date(ts)
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')} ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`
}

const loadUsers = async () => {
  loading.value = true
  try {
    users.value = await getUsers()
  } catch (e) {
    ElMessage.error('加载用户列表失败')
  } finally {
    loading.value = false
  }
}

const handleToggleActive = async (row, val) => {
  try {
    await updateUser(row.id, { is_active: val })
    ElMessage.success(val ? '已启用' : '已停用')
  } catch (e) {
    row.is_active = !val
    ElMessage.error('操作失败')
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要删除用户 "${row.username}" 吗？`, '确认删除', {
      type: 'warning',
      confirmButtonText: '删除',
      confirmButtonClass: 'el-button--danger'
    })
    await deleteUser(row.id)
    ElMessage.success('删除成功')
    await loadUsers()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}

const handleCreate = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    creating.value = true
    try {
      await createUser({ username: form.value.username, password: form.value.password })
      ElMessage.success('用户创建成功')
      showCreateDialog.value = false
      await loadUsers()
    } catch (e) {
      ElMessage.error(e?.response?.data?.message || '创建失败')
    } finally {
      creating.value = false
    }
  })
}

const resetForm = () => {
  form.value = { username: '', password: '' }
  formRef.value?.resetFields()
}

const handleOpenPassword = (row) => {
  passwordTarget.value = row
  passwordTab.value = 'reset'
  tempPassword.value = ''
  showPasswordDialog.value = true
}

const resetPasswordForm = () => {
  tempPassword.value = ''
  pwForm.value = { password: '', confirm: '' }
  pwFormRef.value?.resetFields()
}

const handleResetPassword = async () => {
  resetting.value = true
  try {
    const data = await resetUserPassword(passwordTarget.value.id)
    tempPassword.value = data.temp_password
    ElMessage.success('临时密码已生成，请及时告知用户')
  } catch (e) {
    ElMessage.error('操作失败')
  } finally {
    resetting.value = false
  }
}

const copyPassword = () => {
  navigator.clipboard.writeText(tempPassword.value)
  ElMessage.success('已复制到剪贴板')
}

const handleChangePassword = async () => {
  if (!pwFormRef.value) return
  await pwFormRef.value.validate(async (valid) => {
    if (!valid) return
    changing.value = true
    try {
      await updateUserPassword(passwordTarget.value.id, pwForm.value.password)
      ElMessage.success('密码修改成功')
      showPasswordDialog.value = false
    } catch (e) {
      ElMessage.error(e?.response?.data?.message || '修改失败')
    } finally {
      changing.value = false
    }
  })
}

onMounted(loadUsers)
</script>

<style scoped>
.user-management-page {
  padding: 20px;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.page-header h1 {
  margin: 0;
  font-size: 28px;
  font-weight: 600;
}

.password-section {
  padding: 8px 0;
}

.password-tip {
  color: #606266;
  font-size: 13px;
  margin-bottom: 16px;
}

.temp-password-box {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 16px;
  padding: 12px 16px;
  background: #f0f9eb;
  border-radius: 8px;
  border: 1px solid #b3e19d;
}

.temp-label {
  font-size: 13px;
  color: #606266;
}

.temp-value {
  font-size: 16px;
  font-family: monospace;
  letter-spacing: 1px;
}
</style>
