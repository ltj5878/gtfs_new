<template>
  <div class="login-page">
    <el-card class="login-card">
      <div class="login-header">
        <el-icon :size="36" color="#409eff"><TrendCharts /></el-icon>
        <h2>GTFS 公交数据分析系统</h2>
        <p>{{ isRegister ? '创建新账号' : '请登录以继续' }}</p>
      </div>

      <!-- 登录表单 -->
      <el-form v-if="!isRegister" :model="form" :rules="loginRules" ref="loginFormRef" @submit.prevent="handleLogin">
        <el-form-item prop="username">
          <el-input
            v-model="form.username"
            placeholder="用户名"
            size="large"
            :prefix-icon="User"
            autocomplete="username"
          />
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="密码"
            size="large"
            :prefix-icon="Lock"
            show-password
            autocomplete="current-password"
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        <el-alert v-if="errorMsg" :title="errorMsg" type="error" show-icon :closable="false" style="margin-bottom: 16px" />
        <el-alert v-if="successMsg" :title="successMsg" type="success" show-icon :closable="false" style="margin-bottom: 16px" />
        <el-button type="primary" size="large" style="width: 100%" :loading="loading" @click="handleLogin">
          登录
        </el-button>
        <div class="switch-link">
          没有账号？<el-link type="primary" @click="switchMode(true)">立即注册</el-link>
        </div>
      </el-form>

      <!-- 注册表单 -->
      <el-form v-else :model="regForm" :rules="registerRules" ref="regFormRef" @submit.prevent="handleRegister">
        <el-form-item prop="username">
          <el-input
            v-model="regForm.username"
            placeholder="用户名（4-20 个字符）"
            size="large"
            :prefix-icon="User"
            autocomplete="username"
          />
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            v-model="regForm.password"
            type="password"
            placeholder="密码（至少 6 位）"
            size="large"
            :prefix-icon="Lock"
            show-password
            autocomplete="new-password"
          />
        </el-form-item>
        <el-form-item prop="confirmPassword">
          <el-input
            v-model="regForm.confirmPassword"
            type="password"
            placeholder="确认密码"
            size="large"
            :prefix-icon="Lock"
            show-password
            autocomplete="new-password"
            @keyup.enter="handleRegister"
          />
        </el-form-item>
        <el-alert v-if="errorMsg" :title="errorMsg" type="error" show-icon :closable="false" style="margin-bottom: 16px" />
        <el-button type="primary" size="large" style="width: 100%" :loading="loading" @click="handleRegister">
          注册
        </el-button>
        <div class="switch-link">
          已有账号？<el-link type="primary" @click="switchMode(false)">返回登录</el-link>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { TrendCharts, User, Lock } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/authStore.js'
import { register } from '@/api/auth.js'

const router = useRouter()
const authStore = useAuthStore()

const isRegister = ref(false)
const loginFormRef = ref(null)
const regFormRef = ref(null)
const loading = ref(false)
const errorMsg = ref('')
const successMsg = ref('')

const form = reactive({ username: '', password: '' })
const regForm = reactive({ username: '', password: '', confirmPassword: '' })

const loginRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const registerRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 4, max: 20, message: '用户名长度须在 4-20 个字符之间', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于 6 位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== regForm.password) callback(new Error('两次输入的密码不一致'))
        else callback()
      },
      trigger: 'blur'
    }
  ]
}

function switchMode(toRegister) {
  isRegister.value = toRegister
  errorMsg.value = ''
  successMsg.value = ''
}

async function handleLogin() {
  errorMsg.value = ''
  successMsg.value = ''
  const valid = await loginFormRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await authStore.login(form.username, form.password)
    router.push('/')
  } catch (e) {
    errorMsg.value = e.message || '登录失败，请检查用户名和密码'
  } finally {
    loading.value = false
  }
}

async function handleRegister() {
  errorMsg.value = ''
  const valid = await regFormRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await register(regForm.username, regForm.password)
    switchMode(false)
    successMsg.value = '注册成功，请登录'
    form.username = regForm.username
  } catch (e) {
    errorMsg.value = e.message || '注册失败，请稍后重试'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f5f7fa;
}

.login-card {
  width: 380px;
  padding: 16px;
}

.login-header {
  text-align: center;
  margin-bottom: 28px;
}

.login-header h2 {
  margin: 12px 0 6px;
  font-size: 18px;
  color: #303133;
}

.login-header p {
  color: #909399;
  font-size: 14px;
}

.switch-link {
  text-align: center;
  margin-top: 16px;
  font-size: 14px;
  color: #606266;
}
</style>
