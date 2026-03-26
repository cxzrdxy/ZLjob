import axios from "axios"

const api = axios.create({
  baseURL: "/api"
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("accessToken")
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error?.response?.status === 401) {
      localStorage.removeItem("accessToken")
      localStorage.removeItem("refreshToken")
      if (typeof window !== "undefined") {
        const current = `${window.location.pathname}${window.location.search}`
        if (!window.location.pathname.startsWith("/login")) {
          window.location.href = `/login?redirect=${encodeURIComponent(current)}`
        }
      }
    }
    return Promise.reject(error)
  }
)

export function loginApi(data) {
  return api.post("/auth/login", data)
}

export function registerApi(data) {
  return api.post("/auth/register", data)
}

export function fetchJobs(params) {
  return api.get("/jobs", { params })
}

export function fetchSalaryStats() {
  return api.get("/statistics/salary")
}

export function fetchTrendStats() {
  return api.get("/statistics/trend")
}

export function createCrawlTask(data) {
  return api.post("/crawl/tasks", data)
}

export function fetchCrawlTasks() {
  return api.get("/crawl/tasks")
}

export default api
