<template>
  <el-container class="app-shell">
    <el-header class="app-header">
      <div class="header-inner">
        <div class="brand-block">
          <span class="brand-title">Job Observer</span>
        </div>
        <el-menu mode="horizontal" :router="true" class="nav-menu" :ellipsis="false">
          <el-menu-item index="/">概览</el-menu-item>
          <el-menu-item index="/jobs">职位</el-menu-item>
          <div class="menu-spacer"></div>
          <el-menu-item index="/login" v-if="!isAuthed">登录</el-menu-item>
          <el-menu-item v-else @click="logout">退出</el-menu-item>
        </el-menu>
      </div>
    </el-header>
    <el-main class="app-main">
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup>
import { computed } from "vue"
import { useRouter } from "vue-router"
import { useAuthStore } from "./store/auth"
const router = useRouter()
const auth = useAuthStore()
const isAuthed = computed(() => !!auth.accessToken)
function logout() {
  auth.logout()
  router.push("/login")
}
</script>

<style scoped>
.app-shell {
  min-height: 100vh;
  background: var(--color-bg-secondary);
}

.app-header {
  height: 52px;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  position: sticky;
  top: 0;
  z-index: 100;
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
  padding: 0;
}

.header-inner {
  max-width: 1200px;
  margin: 0 auto;
  height: 100%;
  display: flex;
  align-items: center;
  padding: 0 var(--spacing-lg);
}

.brand-block {
  margin-right: var(--spacing-xl);
  display: flex;
  align-items: center;
}

.brand-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
  letter-spacing: -0.5px;
}

.nav-menu {
  flex: 1;
  border-bottom: 0;
  background: transparent;
  height: 100%;
  display: flex;
  align-items: center;
}

.menu-spacer {
  flex: 1;
}

.app-main {
  max-width: 1200px;
  margin: 0 auto;
  padding: var(--spacing-xl) var(--spacing-lg);
  width: 100%;
}

:deep(.el-menu-item) {
  color: var(--color-text-secondary);
  border-bottom: none !important;
  background: transparent !important;
  font-size: 13px;
  font-weight: 500;
  height: 32px;
  line-height: 32px;
  border-radius: 6px;
  margin: 0 4px;
  padding: 0 12px;
  transition: all 0.2s ease;
}

:deep(.el-menu-item.is-active) {
  color: var(--color-text-primary);
  background: rgba(0, 0, 0, 0.05) !important;
}

:deep(.el-menu-item:hover) {
  color: var(--color-text-primary);
  background: rgba(0, 0, 0, 0.03) !important;
}
</style>
