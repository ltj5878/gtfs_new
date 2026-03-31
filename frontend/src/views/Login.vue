<template>
  <div class="auth-page">
    <!-- 背景装饰 -->
    <div class="bg-decoration">
      <div class="bg-circle bg-circle-1"></div>
      <div class="bg-circle bg-circle-2"></div>
      <div class="bg-circle bg-circle-3"></div>
    </div>

    <div class="auth-card">
      <!-- 头部 -->
      <div class="auth-header">
        <div class="logo">
          <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"/>
            <polyline points="12 6 12 12 16 14"/>
          </svg>
        </div>
        <div class="header-text">
          <h1>{{ $t('login.title') }}</h1>
          <p class="subtitle">{{ $t('login.subtitle') }}</p>
        </div>
      </div>

      <!-- 登录/注册切换 -->
      <div class="tab-bar">
        <button :class="{ active: !isRegister }" @click="switchMode(false)">{{ $t('login.loginTab') }}</button>
        <button :class="{ active: isRegister }" @click="switchMode(true)">{{ $t('login.registerTab') }}</button>
        <div class="tab-indicator" :style="{ left: isRegister ? '50%' : '0' }"></div>
      </div>

      <!-- 登录表单 -->
      <form v-if="!isRegister" @submit.prevent="handleLogin" class="auth-form">
        <div class="field">
          <label for="login-user">{{ $t('login.username') }}</label>
          <div class="input-wrap">
            <svg class="field-icon" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
            <input
              id="login-user"
              v-model="form.username"
              type="text"
              autocomplete="username"
              :placeholder="$t('login.usernamePlaceholder')"
              required
            />
          </div>
        </div>
        <div class="field">
          <label for="login-pwd">{{ $t('login.password') }}</label>
          <div class="input-wrap">
            <svg class="field-icon" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
            <input
              id="login-pwd"
              v-model="form.password"
              :type="showPwd ? 'text' : 'password'"
              autocomplete="current-password"
              :placeholder="$t('login.passwordPlaceholder')"
              required
            />
            <button type="button" class="eye-btn" @click="showPwd = !showPwd" tabindex="-1" :aria-label="$t('login.togglePassword')">
              <svg v-if="showPwd" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
              <svg v-else viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
            </button>
          </div>
        </div>
        <p v-if="errorMsg" class="msg msg-error">{{ errorMsg }}</p>
        <p v-if="successMsg" class="msg msg-ok">{{ successMsg }}</p>
        <button type="submit" class="submit-btn" :disabled="loading">
          <span v-if="loading" class="btn-loading"></span>
          {{ loading ? $t('login.loginLoading') : $t('login.loginBtn') }}
        </button>
      </form>

      <!-- 注册表单 -->
      <form v-else @submit.prevent="handleRegister" class="auth-form">
        <div class="field">
          <label for="reg-user">{{ $t('login.username') }}</label>
          <div class="input-wrap">
            <svg class="field-icon" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
            <input
              id="reg-user"
              v-model="regForm.username"
              type="text"
              autocomplete="username"
              :placeholder="$t('login.usernameHint')"
              required
              minlength="4"
              maxlength="20"
            />
          </div>
        </div>
        <div class="field">
          <label for="reg-pwd">{{ $t('login.password') }}</label>
          <div class="input-wrap">
            <svg class="field-icon" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
            <input
              id="reg-pwd"
              v-model="regForm.password"
              :type="showPwd ? 'text' : 'password'"
              autocomplete="new-password"
              :placeholder="$t('login.passwordHint')"
              required
              minlength="6"
            />
            <button type="button" class="eye-btn" @click="showPwd = !showPwd" tabindex="-1" :aria-label="$t('login.togglePassword')">
              <svg v-if="showPwd" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
              <svg v-else viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
            </button>
          </div>
        </div>
        <div class="field">
          <label for="reg-pwd2">{{ $t('login.confirmPassword') }}</label>
          <div class="input-wrap">
            <svg class="field-icon" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
            <input
              id="reg-pwd2"
              v-model="regForm.confirmPassword"
              :type="showPwd2 ? 'text' : 'password'"
              autocomplete="new-password"
              :placeholder="$t('login.confirmHint')"
              required
            />
            <button type="button" class="eye-btn" @click="showPwd2 = !showPwd2" tabindex="-1" :aria-label="$t('login.togglePassword')">
              <svg v-if="showPwd2" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
              <svg v-else viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
            </button>
          </div>
        </div>
        <p v-if="errorMsg" class="msg msg-error">{{ errorMsg }}</p>
        <button type="submit" class="submit-btn" :disabled="loading">
          <span v-if="loading" class="btn-loading"></span>
          {{ loading ? $t('login.registerLoading') : $t('login.registerBtn') }}
        </button>
      </form>

      <div class="auth-footer">
        <span>Transit Data Powered by GTFS</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/stores/authStore.js'
import { register } from '@/api/auth.js'

const { t } = useI18n()
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
    errorMsg.value = t('login.fillUsernameAndPassword')
    return
  }
  loading.value = true
  try {
    await authStore.login(form.username, form.password)
    router.push('/')
  } catch (e) {
    errorMsg.value = e.message || t('login.loginFailed')
  } finally {
    loading.value = false
  }
}

async function handleRegister() {
  errorMsg.value = ''
  if (!regForm.username || !regForm.password || !regForm.confirmPassword) {
    errorMsg.value = t('login.fillAllFields')
    return
  }
  if (regForm.username.length < 4 || regForm.username.length > 20) {
    errorMsg.value = t('login.usernameLengthError')
    return
  }
  if (regForm.password.length < 6) {
    errorMsg.value = t('login.passwordLengthError')
    return
  }
  if (regForm.password !== regForm.confirmPassword) {
    errorMsg.value = t('login.passwordMismatch')
    return
  }
  loading.value = true
  try {
    await register(regForm.username, regForm.password)
    switchMode(false)
    successMsg.value = t('login.registerSuccess')
    form.username = regForm.username
  } catch (e) {
    errorMsg.value = e.message || t('login.registerFailed')
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
  background: linear-gradient(135deg, #e8edf2 0%, #d5dce6 30%, #e2e8f0 60%, #dde4ed 100%);
  padding: 20px;
  position: relative;
  overflow: hidden;
}

/* 背景装饰圆 */
.bg-decoration {
  position: absolute;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
}

.bg-circle {
  position: absolute;
  border-radius: 50%;
  opacity: 0.35;
}

.bg-circle-1 {
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, #b8cce0 0%, transparent 70%);
  top: -120px;
  right: -80px;
}

.bg-circle-2 {
  width: 300px;
  height: 300px;
  background: radial-gradient(circle, #c4d4e4 0%, transparent 70%);
  bottom: -60px;
  left: -60px;
}

.bg-circle-3 {
  width: 200px;
  height: 200px;
  background: radial-gradient(circle, #a8bdd0 0%, transparent 70%);
  top: 40%;
  left: 15%;
}

/* 卡片 */
.auth-card {
  width: 100%;
  max-width: 400px;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-radius: 16px;
  padding: 36px 32px 28px;
  box-shadow:
    0 1px 2px rgba(0, 0, 0, 0.04),
    0 4px 16px rgba(0, 0, 0, 0.06),
    0 12px 40px rgba(0, 0, 0, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.6);
  position: relative;
  z-index: 1;
}

/* 头部 */
.auth-header {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 28px;
}

.logo {
  width: 42px;
  height: 42px;
  background: linear-gradient(135deg, #5b7a9d 0%, #3d5a80 100%);
  border-radius: 11px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}

.header-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.auth-header h1 {
  font-size: 17px;
  font-weight: 600;
  color: #2c3e50;
  margin: 0;
  line-height: 1.3;
  letter-spacing: 0.3px;
}

.subtitle {
  font-size: 11px;
  color: #8899a6;
  margin: 0;
  letter-spacing: 0.5px;
  font-weight: 400;
}

/* Tab 切换 */
.tab-bar {
  display: flex;
  background: #edf1f5;
  border-radius: 10px;
  padding: 3px;
  margin-bottom: 24px;
  position: relative;
}

.tab-bar button {
  flex: 1;
  padding: 9px 0;
  border: none;
  background: transparent;
  font-size: 13.5px;
  color: #7a8a9a;
  cursor: pointer;
  border-radius: 8px;
  transition: color 0.25s;
  font-weight: 500;
  position: relative;
  z-index: 1;
}

.tab-bar button.active {
  color: #2c3e50;
}

.tab-indicator {
  position: absolute;
  top: 3px;
  bottom: 3px;
  width: calc(50% - 3px);
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  transition: left 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 0;
}

/* 表单 */
.auth-form {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field label {
  font-size: 12.5px;
  font-weight: 500;
  color: #4a5c6d;
  padding-left: 2px;
}

.input-wrap {
  position: relative;
  display: flex;
  align-items: center;
}

.field-icon {
  position: absolute;
  left: 12px;
  color: #94a3b8;
  pointer-events: none;
  flex-shrink: 0;
}

.field input {
  width: 100%;
  height: 42px;
  padding: 0 12px 0 36px;
  border: 1px solid #d4dbe4;
  border-radius: 10px;
  font-size: 14px;
  color: #2c3e50;
  background: rgba(255, 255, 255, 0.7);
  outline: none;
  transition: border-color 0.2s, background 0.2s, box-shadow 0.2s;
  box-sizing: border-box;
}

.field input::placeholder {
  color: #a8b5c2;
}

.field input:focus {
  border-color: #5b7a9d;
  background: #fff;
  box-shadow: 0 0 0 3px rgba(91, 122, 157, 0.1);
}

/* 密码可见按钮 */
.eye-btn {
  position: absolute;
  right: 10px;
  background: none;
  border: none;
  cursor: pointer;
  color: #94a3b8;
  padding: 4px;
  display: flex;
  align-items: center;
  border-radius: 4px;
  transition: color 0.2s;
}

.eye-btn:hover {
  color: #5b7a9d;
}

/* 提示信息 */
.msg {
  margin: 0;
  padding: 10px 14px;
  border-radius: 8px;
  font-size: 13px;
  line-height: 1.4;
}

.msg-error {
  background: #fef2f2;
  color: #b91c1c;
  border: 1px solid #fecaca;
}

.msg-ok {
  background: #f0fdf4;
  color: #15803d;
  border: 1px solid #bbf7d0;
}

/* 提交按钮 */
.submit-btn {
  width: 100%;
  height: 44px;
  border: none;
  border-radius: 10px;
  background: linear-gradient(135deg, #5b7a9d 0%, #3d5a80 100%);
  color: #fff;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: opacity 0.2s, transform 0.1s;
  margin-top: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  letter-spacing: 0.5px;
}

.submit-btn:hover:not(:disabled) {
  opacity: 0.9;
}

.submit-btn:active:not(:disabled) {
  transform: scale(0.99);
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 加载动画 */
.btn-loading {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 底部 */
.auth-footer {
  text-align: center;
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #e8ecf0;
}

.auth-footer span {
  font-size: 11px;
  color: #a0adb8;
  letter-spacing: 0.5px;
}

/* 移动端适配 */
@media (max-width: 480px) {
  .auth-card {
    padding: 28px 22px 24px;
    border-radius: 14px;
  }

  .auth-header h1 {
    font-size: 16px;
  }

  .bg-circle-1 {
    width: 250px;
    height: 250px;
  }

  .bg-circle-2 {
    width: 180px;
    height: 180px;
  }

  .bg-circle-3 {
    display: none;
  }
}
</style>
