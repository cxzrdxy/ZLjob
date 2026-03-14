<template>
  <div class="login-container">
    <div class="login-card">
      <h3 class="login-title">登录 Job Observer</h3>
      <p class="login-subtitle">请使用您的管理员账号访问</p>
      
      <el-form :model="form" class="login-form" @submit.prevent="onSubmit" data-testid="login-form">
        <el-form-item>
          <el-input
            v-model="form.username"
            name="username"
            autocomplete="username"
            placeholder="用户名"
            data-testid="username-input"
            class="custom-input"
          />
        </el-form-item>
        <el-form-item>
          <el-input
            type="password"
            v-model="form.password"
            name="password"
            autocomplete="current-password"
            placeholder="密码"
            show-password
            data-testid="password-input"
            class="custom-input"
          />
        </el-form-item>
        <div class="form-actions">
          <el-button
            type="primary"
            native-type="submit"
            :loading="loading"
            data-testid="login-submit"
            class="login-btn"
          >
            登录
          </el-button>
        </div>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue"
import { useRoute, useRouter } from "vue-router"
import { ElMessage } from "element-plus"
import { useAuthStore } from "../store/auth"
import { loginApi } from "../api"

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const loading = ref(false)
const form = ref({ username: "", password: "" })

async function onSubmit() {
  if (!form.value.username || !form.value.password) {
    ElMessage.warning("请输入用户名和密码")
    return
  }
  loading.value = true
  try {
    const { data } = await loginApi(form.value)
    const tokens = data.data
    auth.setTokens({ access: tokens.access, refresh: tokens.refresh })
    const redirect = route.query.redirect || "/"
    router.push(redirect)
  } catch (error) {
    const message = error?.response?.data?.message || "登录失败，请检查账号密码或后端服务"
    ElMessage.error(message)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  padding-top: 80px;
  min-height: calc(100vh - 52px);
}

.login-card {
  width: 100%;
  max-width: 400px;
  padding: 40px;
  text-align: center;
}

.login-title {
  font-size: 24px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 8px;
  letter-spacing: -0.5px;
}

.login-subtitle {
  font-size: 15px;
  color: var(--color-text-secondary);
  margin: 0 0 32px;
}

.login-form {
  margin: 0 auto;
}

:deep(.el-form-item) {
  margin-bottom: 16px;
}

:deep(.el-input__wrapper) {
  padding: 8px 16px;
  height: 44px;
  border-radius: 12px !important;
  background-color: transparent !important;
  border: 1px solid var(--color-border);
  box-shadow: none !important;
  transition: all 0.2s ease;
}

:deep(.el-input__wrapper:hover) {
  border-color: #86868b;
}

:deep(.el-input__wrapper.is-focus) {
  border-color: #0066cc;
  box-shadow: 0 0 0 4px rgba(0, 102, 204, 0.1) !important;
}

:deep(.el-input__inner) {
  font-size: 16px;
  color: var(--color-text-primary);
}

.form-actions {
  margin-top: 24px;
}

.login-btn {
  width: 100%;
  height: 44px;
  font-size: 15px;
  font-weight: 500;
  border-radius: 12px;
  background: linear-gradient(180deg, #333 0%, #000 100%);
  border: none;
  transition: all 0.2s ease;
}

.login-btn:hover {
  transform: scale(1.01);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.login-btn:active {
  transform: scale(0.98);
}
</style>
