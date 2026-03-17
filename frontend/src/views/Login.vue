<template>
  <div class="login-page">
    <div class="login-bg">
      <div class="bg-circle bg-circle-1"></div>
      <div class="bg-circle bg-circle-2"></div>
      <div class="bg-circle bg-circle-3"></div>
    </div>

    <div class="login-container">
      <!-- 左侧品牌区 -->
      <div class="login-brand">
        <div class="brand-icon">
          <el-icon :size="48" color="#fff"><TrendCharts /></el-icon>
        </div>
        <h1 class="brand-title">公交准点率分析系统</h1>
        <p class="brand-desc">实时监控 · 数据分析 · 智能预测</p>
        <div class="brand-features">
          <div class="brand-feature-item">
            <el-icon color="rgba(255,255,255,0.8)"><Guide /></el-icon>
            <span>多城市线路覆盖</span>
          </div>
          <div class="brand-feature-item">
            <el-icon color="rgba(255,255,255,0.8)"><TrendCharts /></el-icon>
            <span>准点率实时统计</span>
          </div>
          <div class="brand-feature-item">
            <el-icon color="rgba(255,255,255,0.8)"><Monitor /></el-icon>
            <span>车辆位置实时追踪</span>
          </div>
        </div>
      </div>

      <!-- 右侧表单区 -->
      <div class="login-form-area">
        <div class="form-header">
          <h2>{{ isRegister ? '创建账号' : '欢迎回来' }}</h2>
          <p>{{ isRegister ? '填写信息完成注册' : '登录以访问完整功能' }}</p>
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
          <el-button type="primary" size="large" class="submit-btn" :loading="loading" @click="handleLogin">
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
          <el-button type="primary" size="large" class="submit-btn" :loading="loading" @click="handleRegister">
            注册
          </el-button>
          <div class="switch-link">
            已有账号？<el-link type="primary" @click="switchMode(false)">返回登录</el-link>
          </div>
        </el-form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { TrendCharts, User, Lock, Guide, Monitor } from '@element-plus/icons-vue'
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
  background: #f0f4ff;
  position: relative;
  overflow: hidden;
}

/* 背景装饰圆 */
.login-bg {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.bg-circle {
  position: absolute;
  border-radius: 50%;
  opacity: 0.12;
}

.bg-circle-1 {
  width: 500px;
  height: 500px;
  background: #409eff;
  top: -150px;
  left: -100px;
}

.bg-circle-2 {
  width: 350px;
  height: 350px;
  background: #67c23a;
  bottom: -80px;
  right: -60px;
}

.bg-circle-3 {
  width: 200px;
  height: 200px;
  background: #e6a23c;
  top: 40%;
  right: 20%;
}

/* 主容器 */
.login-container {
  display: flex;
  width: 860px;
  min-height: 520px;
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 24px 64px rgba(0, 0, 0, 0.12);
  position: relative;
  z-index: 1;
}

/* 左侧品牌区 */
.login-brand {
  width: 340px;
  flex-shrink: 0;
  background: linear-gradient(145deg, #2563eb 0%, #1d4ed8 50%, #1e40af 100%);
  padding: 48px 36px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  color: #fff;
}

.brand-icon {
  width: 80px;
  height: 80px;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 28px;
  backdrop-filter: blur(4px);
}

.brand-title {
  font-size: 22px;
  font-weight: 700;
  margin-bottom: 10px;
  line-height: 1.4;
  letter-spacing: 0.5px;
}

.brand-desc {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 40px;
  letter-spacing: 1px;
}

.brand-features {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.brand-feature-item {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.85);
}

/* 右侧表单区 */
.login-form-area {
  flex: 1;
  background: #fff;
  padding: 48px 44px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.form-header {
  margin-bottom: 32px;
}

.form-header h2 {
  font-size: 26px;
  font-weight: 700;
  color: #1a1a2e;
  margin-bottom: 8px;
}

.form-header p {
  font-size: 14px;
  color: #909399;
}

.submit-btn {
  width: 100%;
  height: 44px;
  font-size: 15px;
  font-weight: 600;
  border-radius: 8px;
  background: linear-gradient(135deg, #2563eb, #1d4ed8);
  border: none;
  letter-spacing: 1px;
}

.submit-btn:hover {
  background: linear-gradient(135deg, #1d4ed8, #1e40af);
}

.switch-link {
  text-align: center;
  margin-top: 20px;
  font-size: 14px;
  color: #606266;
}

/* 响应式 */
@media (max-width: 768px) {
  .login-container {
    flex-direction: column;
    width: 92vw;
    min-height: unset;
  }

  .login-brand {
    width: 100%;
    padding: 32px 28px;
  }

  .brand-features {
    display: none;
  }

  .login-form-area {
    padding: 32px 28px;
  }
}
</style>
