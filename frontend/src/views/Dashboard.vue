<template>
  <div class="dashboard-container">
    <div class="section-header">
      <h2 class="section-title">概览</h2>
      <p class="section-subtitle">查看职位统计与趋势分析</p>
    </div>

    <el-row :gutter="24">
      <el-col :xs="24" :lg="14">
        <el-card class="dashboard-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span>薪资分布</span>
              <el-tag size="small" type="info" effect="plain">TOP 10</el-tag>
            </div>
          </template>
          <el-table :data="salary" height="360" style="width: 100%" :header-cell-style="{ background: 'transparent' }">
            <el-table-column prop="city" label="城市" width="120" />
            <el-table-column prop="job_count" label="职位数" align="right" />
            <el-table-column prop="avg_salary" label="平均薪资" align="right">
              <template #default="{ row }">
                <span class="salary-text">¥{{ row.avg_salary?.toLocaleString() }}</span>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :lg="10">
        <el-card class="dashboard-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span>新建任务</span>
            </div>
          </template>
          <el-form :model="form" label-position="top" class="task-form">
            <el-form-item label="任务名称">
              <el-input v-model="form.task_name" placeholder="输入任务名称" />
            </el-form-item>
            <el-row :gutter="12">
              <el-col :span="12">
                <el-form-item label="关键词">
                  <el-input v-model="form.keyword" placeholder="例如：Python" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="城市">
                  <el-input v-model="form.city" placeholder="例如：北京" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-form-item label="采集页数">
              <el-input-number v-model="form.max_pages" :min="1" :max="20" style="width: 100%" />
            </el-form-item>
            <div class="form-actions">
              <el-button type="primary" @click="createTask" :loading="loading" class="submit-btn">
                开始采集
              </el-button>
            </div>
          </el-form>
        </el-card>
      </el-col>
    </el-row>

    <el-row class="trend-section">
      <el-col :span="24">
        <el-card class="dashboard-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span>采集任务状态</span>
            </div>
          </template>
          <el-empty v-if="tasks.length === 0" description="暂无任务记录" />
          <el-table v-else :data="tasks" style="width: 100%" :header-cell-style="{ background: 'transparent' }">
            <el-table-column prop="task_name" label="任务名称" min-width="180" />
            <el-table-column prop="keyword" label="关键词" width="120" />
            <el-table-column prop="city" label="城市" width="100" />
            <el-table-column label="状态" width="120">
              <template #default="{ row }">
                <el-tag :type="statusTagType(row.status)" effect="plain">{{ statusLabel(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="total_count" label="总数" width="90" align="right" />
            <el-table-column prop="success_count" label="成功" width="90" align="right" />
            <el-table-column prop="fail_count" label="失败" width="90" align="right" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <el-row class="trend-section">
      <el-col :span="24">
        <el-card class="dashboard-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span>发布趋势</span>
            </div>
          </template>
          <div class="chart-container">
            <v-chart :option="trendOption" autoresize />
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from "vue"
import { ElMessage } from "element-plus"
import VChart from "vue-echarts"
import { use } from "echarts/core"
import { CanvasRenderer } from "echarts/renderers"
import { LineChart } from "echarts/charts"
import { GridComponent, TooltipComponent, LegendComponent } from "echarts/components"
import { fetchSalaryStats, fetchTrendStats, createCrawlTask, fetchCrawlTasks } from "../api"

use([CanvasRenderer, LineChart, GridComponent, TooltipComponent, LegendComponent])

const salary = ref([])
const trend = ref([])
const tasks = ref([])
const loading = ref(false)
const form = ref({ task_name: "Python 职位采集", keyword: "Python", city: "北京", max_pages: 5 })
let taskTimer = null

function normalizeTaskList(payload) {
  if (Array.isArray(payload)) return payload
  if (Array.isArray(payload?.results)) return payload.results
  return []
}

const trendOption = computed(() => ({
  color: ["#000000"],
  tooltip: {
    trigger: "axis",
    backgroundColor: "rgba(255, 255, 255, 0.9)",
    borderColor: "#e5e5ea",
    textStyle: { color: "#1d1d1f" },
    extraCssText: "box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); border-radius: 8px;"
  },
  grid: { left: 20, right: 20, top: 20, bottom: 20, containLabel: true },
  xAxis: {
    type: "category",
    data: trend.value.map((x) => x.day || ""),
    axisLine: { show: false },
    axisTick: { show: false },
    axisLabel: { color: "#86868b", fontSize: 12, margin: 16 }
  },
  yAxis: {
    type: "value",
    splitLine: { lineStyle: { color: "#f5f5f7" } },
    axisLabel: { color: "#86868b", fontSize: 12 }
  },
  series: [{
    name: "职位数",
    type: "line",
    smooth: true,
    showSymbol: false,
    symbolSize: 8,
    itemStyle: { color: "#000" },
    lineStyle: { width: 2 },
    areaStyle: {
      color: {
        type: "linear",
        x: 0, y: 0, x2: 0, y2: 1,
        colorStops: [
          { offset: 0, color: "rgba(0, 0, 0, 0.1)" },
          { offset: 1, color: "rgba(0, 0, 0, 0)" }
        ]
      }
    },
    data: trend.value.map((x) => x.job_count || 0)
  }]
}))

async function load() {
  try {
    const [salaryResp, trendResp, taskResp] = await Promise.all([fetchSalaryStats(), fetchTrendStats(), fetchCrawlTasks()])
    salary.value = salaryResp.data.data || []
    trend.value = trendResp.data.data || []
    tasks.value = normalizeTaskList(taskResp.data.data)
    syncTaskPolling()
  } catch (e) {
    console.error(e)
  }
}

function statusLabel(status) {
  if (status === "pending") return "排队中"
  if (status === "running") return "采集中"
  if (status === "success") return "已完成"
  if (status === "failed") return "失败"
  return "未知"
}

function statusTagType(status) {
  if (status === "success") return "success"
  if (status === "failed") return "danger"
  if (status === "running") return "warning"
  return "info"
}

function stopTaskPolling() {
  if (taskTimer) {
    clearInterval(taskTimer)
    taskTimer = null
  }
}

function syncTaskPolling() {
  const list = normalizeTaskList(tasks.value)
  const hasRunningTask = list.some((task) => task.status === "pending" || task.status === "running")
  if (!hasRunningTask) {
    stopTaskPolling()
    return
  }
  if (!taskTimer) {
    taskTimer = setInterval(loadTasks, 4000)
  }
}

async function loadTasks() {
  try {
    const taskResp = await fetchCrawlTasks()
    tasks.value = normalizeTaskList(taskResp.data.data)
    syncTaskPolling()
  } catch (e) {
    stopTaskPolling()
  }
}

async function createTask() {
  if (!form.value.task_name) {
    ElMessage.warning("请输入任务名称")
    return
  }
  if (!form.value.keyword) {
    ElMessage.warning("请输入关键词")
    return
  }
  if (!form.value.city) {
    ElMessage.warning("请输入城市")
    return
  }
  loading.value = true
  try {
    const resp = await createCrawlTask(form.value)
    const current = normalizeTaskList(tasks.value)
    tasks.value = [resp.data.data, ...current]
    syncTaskPolling()
    ElMessage.success("已创建采集任务")
    await load()
  } catch (e) {
    const data = e?.response?.data
    const code = e?.code
    const networkError = !e?.response && (code === "ERR_NETWORK" || code === "ECONNREFUSED")
    const detail = data?.detail
    const message = data?.message
    const fieldError = Object.values(data || {})
      .flatMap((value) => (Array.isArray(value) ? value : [value]))
      .find((value) => typeof value === "string" && value)
    if (networkError) {
      ElMessage.error("创建失败：后端服务暂不可用，请确认 Docker 中 backend 服务已就绪")
      return
    }
    if (typeof detail === "string" && detail) {
      ElMessage.error(detail)
      return
    }
    if (message) {
      ElMessage.error(message)
      return
    }
    if (fieldError) {
      ElMessage.error(fieldError)
      return
    }
    ElMessage.error("创建失败，请稍后重试")
  } finally {
    loading.value = false
  }
}

onMounted(load)
onUnmounted(stopTaskPolling)
</script>

<style scoped>
.dashboard-container {
  max-width: 1200px;
  margin: 0 auto;
}

.section-header {
  margin-bottom: 32px;
}

.section-title {
  font-size: 28px;
  font-weight: 600;
  margin: 0 0 8px;
  letter-spacing: -0.5px;
}

.section-subtitle {
  color: var(--color-text-secondary);
  font-size: 15px;
  margin: 0;
}

.dashboard-card {
  height: 100%;
  border-radius: 16px;
  border: 1px solid rgba(0, 0, 0, 0.05);
  background: #fff;
  overflow: hidden;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.salary-text {
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.task-form {
  padding: 8px 0;
}

.form-actions {
  margin-top: 32px;
}

.submit-btn {
  width: 100%;
  height: 40px;
  border-radius: 8px;
  font-weight: 500;
  background: #000;
  border-color: #000;
}

.submit-btn:hover {
  background: #333;
  border-color: #333;
}

.trend-section {
  margin-top: 24px;
}

.chart-container {
  height: 360px;
  width: 100%;
}

:deep(.el-card__header) {
  padding: 20px 24px;
  border-bottom: 1px solid var(--color-bg-secondary);
  font-size: 16px;
  font-weight: 600;
}

:deep(.el-card__body) {
  padding: 24px;
}

:deep(.el-table) {
  --el-table-border-color: transparent;
  --el-table-header-bg-color: transparent;
}

:deep(.el-table th.el-table__cell) {
  font-weight: 500;
  color: var(--color-text-secondary);
  font-size: 13px;
  border-bottom: 1px solid var(--color-bg-secondary);
}

:deep(.el-table td.el-table__cell) {
  border-bottom: 1px solid var(--color-bg-secondary);
  padding: 12px 0;
}

:deep(.el-input__wrapper),
:deep(.el-input-number__wrapper) {
  box-shadow: none !important;
  background-color: var(--color-bg-secondary) !important;
  border-radius: 8px !important;
  padding: 4px 12px;
  transition: all 0.2s;
}

:deep(.el-input__wrapper:hover),
:deep(.el-input-number__wrapper:hover) {
  background-color: #e8e8ed !important;
}

:deep(.el-input__wrapper.is-focus) {
  background-color: #fff !important;
  box-shadow: 0 0 0 2px var(--color-accent) !important;
}
</style>
