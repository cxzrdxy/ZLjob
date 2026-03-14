import { createRouter, createWebHistory } from "vue-router"
import { useAuthStore } from "../store/auth"
import Dashboard from "../views/Dashboard.vue"
import Jobs from "../views/Jobs.vue"
import Login from "../views/Login.vue"

const routes = [
  { path: "/", component: Dashboard, meta: { requiresAuth: true } },
  { path: "/jobs", component: Jobs, meta: { requiresAuth: true } },
  { path: "/login", component: Login }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export function resolveAuthRedirect(to, isAuthed) {
  if (to.meta?.requiresAuth && !isAuthed) {
    return { path: "/login", query: { redirect: to.fullPath } }
  }
  if (to.path === "/login" && isAuthed) {
    return { path: "/" }
  }
  return true
}

router.beforeEach((to) => {
  const auth = useAuthStore()
  const isAuthed = !!auth.accessToken
  return resolveAuthRedirect(to, isAuthed)
})

export default router
