import axios from "axios"

const api = axios.create({
  baseURL: "/api"
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("accessToken")
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

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
