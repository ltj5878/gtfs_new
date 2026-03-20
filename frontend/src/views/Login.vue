<template>
  <div class="auth-page">
    <div class="auth-card">
      <div class="auth-header">
        <div class="logo">
          <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"/>
            <polyline points="12 6 12 12 16 14"/>
          </svg>
        </div>
        <h1>公交准点率分析系统</h1>
      </div>

      <!-- 登录/注册切换 -->
      <div class="tab-bar">
        <button :class="{ active: !isRegister }" @click="switchMode(false)">登录</button>
        <button :class="{ active: isRegister }" @click="switchMode(true)">注册</button>
      </div>

      <!-- 登录表单 -->
      <form v-if="!isRegister" @submit.prevent="handleLogin" class="auth-form">
        <div class="field">
          <label for="login-user">用户名</label>
          <input
            id="login-user"
            v-model="form.username"
            type="text"
            autocomplete="username"
            placeholder="请输入用户名"
            required
          />
        </div>
        <div class="field">
          <label for="login-pwd">密码</label>
          <div class="pwd-wrap">
            <input
              id="login-pwd"
              v-model="form.password"
              :type="showPwd ? 'text' : 'password'"
              autocomplete="current-password"
              placeholder="请输入密码"
              required
            />
            <button type="button" class="eye-btn" @click="showPwd = !showPwd" tabindex="-1">
              <svg v-if="showPwd" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
              <svg v-else viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
            </button>
          </div>
        </div>
        <p v-if="errorMsg" class="msg msg-error">{{ errorMsg }}</p>
        <p v-if="successMsg" class="msg msg-ok">{{ successMsg }}</p>
        <button type="submit" class="submit-btn" :disabled="loading">
          {{ loading ? '登录中...' : '登录' }}
        </button>
      </form>

      <!-- 注册表单 -->
      <form v-else @submit.prevent="handleRegister" class="auth-form">
        <div class="field">
          <label for="reg-user">用户名</label>
          <input
            id="reg-user"
            v-model="regForm.username"
            type="text"
            autocomplete="username"
            placeholder="4-20 个字符"
            required
            minlength="4"
            maxlength="20"
          />
        </div>
        <div class="field">
          <label for="reg-pwd">密码</label>
          <div class="pwd-wrap">
            <input
              id="reg-pwd"
              v-model="regForm.password"
              :type="showPwd ? 'text' : 'password'"
              autocomplete="new-password"
              placeholder="至少 6 位"
              required
              minlength="6"
            />
            <button type="button" class="eye-btn" @click="showPwd = !showPwd" tabindex="-1">
              <svg v-if="showPwd" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
              <svg v-else viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
            </button>
          </div>
        </div>
        <div class="field">
          <label for="reg-pwd2">确认密码</label>
          <div class="pwd-wrap">
            <input
              id="reg-pwd2"
              v-model="regForm.confirmPassword"
              :type="showPwd2 ? 'text' : 'password'"
              autocomplete="new-password"
              placeholder="再次输入密码"
              required
            />
            <button type="button" class="eye-btn" @click="showPwd2 = !showPwd2" tabindex="-1">
              <svg v-if="showPwd2" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
              <svg v-else viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
            </button>
          </div>
        </div>
        <p v-if="errorMsg" class="msg msg-error">{{ errorMsg }}</p>
        <button type="submit" class="submit-btn" :disabled="loading">
          {{ loading ? '注册中...' : '注册' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore.js'
import { register } from '@/api/auth.js'

const router = useRouter()
const authStore = useAuthStore()

const isRegister = ref(false)
const loading = ref(false)
const errorMsg = ref('')
const successMsg = ref('')
const showPwd = ref(false)
const showPwd2 = ref(false)

const form = reactive({ username: '', password: '' })
const regForm = reactive({ username: '', password: '', confirmPassword: '' })

function switchMode(toRegister) {
  isRegister.value = toRegister
  errorMsg.value = ''
  successMsg.value = ''
}

async function handleLogin() {
  errorMsg.value = ''
  successMsg.value = ''
  if (!form.username || !form.password) {
    errorMsg.value = '请填写用户名和密码'
    return
  }
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
  if (!regForm.username || !regForm.password || !regForm.confirmPassword) {
    errorMsg.value = '请填写所有字段'
    return
  }
  if (regForm.username.length < 4 || regForm.username.length > 20) {
    errorMsg.value = '用户名长度须在 4-20 个字符之间'
    return
  }
  if (regForm.password.length < 6) {
    errorMsg.value = '密码长度不能少于 6 位'
    return
  }
  if (regForm.password !== regForm.confirmPassword) {
    errorMsg.value = '两次输入的密码不一致'
    return
  }
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
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f6f8;
  padding: 20px;
}

.auth-card {
  width: 100%;
  max-width: 400px;
  background: #fff;
  border-radius: 12px;
  padding: 40px 32px 36px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06), 0 8px 24px rgba(0, 0, 0, 0.06);
}

/* 头部 */
.auth-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 32px;
}

.logo {
  width: 44px;
  height: 44px;
  background: #1a1a2e;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}

.auth-header h1 {
  font-size: 18px;
  font-weight: 600;
  color: #1a1a2e;
  margin: 0;
  line-height: 1.3;
}

/* Tab 切换 */
.tab-bar {
  display: flex;
  background: #f5f6f8;
  border-radius: 8px;
  padding: 3px;
  margin-bottom: 28px;
}

.tab-bar button {
  flex: 1;
  padding: 8px 0;
  border: none;
  background: transparent;
  font-size: 14px;
  color: #888;
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.2s;
  font-weight: 500;
}

.tab-bar button.active {
  background: #fff;
  color: #1a1a2e;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

/* 表单 */
.auth-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field label {
  font-size: 13px;
  font-weight: 500;
  color: #444;
}

.field input {
  width: 100%;
  height: 42px;
  padding: 0 12px;
  border: 1px solid #dcdfe6;
  border-radius: 8px;
  font-size: 14px;
  color: #1a1a2e;
  background: #fff;
  outline: none;
  transition: border-color 0.2s;
  box-sizing: border-box;
}

.field input::placeholder {
  color: #bbb;
}

.field input:focus {
  border-color: #1a1a2e;
}

/* 密码输入框 */
.pwd-wrap {
  position: relative;
}

.pwd-wrap input {
  padding-right: 40px;
}

.eye-btn {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  cursor: pointer;
  color: #999;
  padding: 2px;
  display: flex;
  align-items: center;
}

.eye-btn:hover {
  color: #555;
}

/* 提示信息 */
.msg {
  margin: 0;
  padding: 10px 12px;
  border-radius: 6px;
  font-size: 13px;
  line-height: 1.4;
}

.msg-error {
  background: #fef2f2;
  color: #b91c1c;
}

.msg-ok {
  background: #f0fdf4;
  color: #15803d;
}

/* 提交按钮 */
.submit-btn {
  width: 100%;
  height: 42px;
  border: none;
  border-radius: 8px;
  background: #1a1a2e;
  color: #fff;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
  margin-top: 4px;
}

.submit-btn:hover:not(:disabled) {
  background: #2d2d44;
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 移动端适配 */
@media (max-width: 480px) {
  .auth-card {
    padding: 32px 24px 28px;
  }
}
</style>
