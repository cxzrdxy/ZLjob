<template>
  <div class="jobs-container">
    <div class="page-header">
      <h2 class="page-title">职位探索</h2>
      <p class="page-subtitle">发现并筛选您感兴趣的机会</p>
    </div>

    <el-card class="filter-card" shadow="never">
      <div class="filter-bar">
        <el-input
          v-model="query.keyword"
          placeholder="搜索职位关键词..."
          class="search-input"
          clearable
          @keyup.enter="load"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-input
          v-model="query.city"
          placeholder="城市"
          class="city-input"
          clearable
          @keyup.enter="load"
        >
          <template #prefix>
            <el-icon><Location /></el-icon>
          </template>
        </el-input>
        <el-button type="primary" @click="load" :loading="loading" class="search-btn">
          搜索
        </el-button>
      </div>
    </el-card>

    <div class="jobs-content">
      <el-table
        :data="items"
        v-loading="loading"
        class="jobs-table"
        :header-cell-style="{ background: 'transparent' }"
      >
        <el-table-column prop="title" label="职位名称" min-width="200">
          <template #default="{ row }">
            <span class="job-title">{{ row.title }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="company" label="公司" min-width="180">
          <template #default="{ row }">
            <span class="company-name">{{ row.company }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="city" label="城市" width="120">
          <template #default="{ row }">
            <el-tag size="small" type="info" effect="plain" class="city-tag">{{ row.city }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="salary" label="薪资范围" width="160" align="right">
          <template #default="{ row }">
            <span class="salary-text">{{ row.salary }}</span>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-container" v-if="total > 0">
        <el-pagination
          background
          layout="prev, pager, next"
          :total="total"
          :page-size="20"
          @current-change="handlePageChange"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue"
import { Search, Location } from "@element-plus/icons-vue"
import { fetchJobs } from "../api"

const loading = ref(false)
const items = ref([])
const total = ref(0)
const query = ref({ keyword: "", city: "", page: 1 })

async function load() {
  loading.value = true
  try {
    const { data } = await fetchJobs(query.value)
    items.value = data.data.results || []
    total.value = data.data.count || 0
  } finally {
    loading.value = false
  }
}

function handlePageChange(page) {
  query.value.page = page
  load()
}

onMounted(load)
</script>

<style scoped>
.jobs-container {
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 32px;
}

.page-title {
  font-size: 28px;
  font-weight: 600;
  margin: 0 0 8px;
  letter-spacing: -0.5px;
}

.page-subtitle {
  color: var(--color-text-secondary);
  font-size: 15px;
  margin: 0;
}

.filter-card {
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(0, 0, 0, 0.05);
  border-radius: 16px;
  margin-bottom: 24px;
  position: sticky;
  top: 72px;
  z-index: 90;
}

.filter-bar {
  display: flex;
  gap: 16px;
  padding: 4px;
}

.search-input {
  flex: 2;
}

.city-input {
  flex: 1;
}

.search-btn {
  width: 100px;
  border-radius: 8px;
  background: #000;
  border-color: #000;
  font-weight: 500;
}

.search-btn:hover {
  background: #333;
  border-color: #333;
}

.jobs-content {
  background: #fff;
  border-radius: 16px;
  border: 1px solid rgba(0, 0, 0, 0.05);
  overflow: hidden;
  padding: 8px 24px;
}

.job-title {
  font-weight: 600;
  color: var(--color-text-primary);
}

.company-name {
  color: var(--color-text-secondary);
}

.salary-text {
  font-family: var(--font-family-mono);
  font-weight: 600;
  color: var(--color-text-primary);
}

.city-tag {
  border: none;
  background: var(--color-bg-secondary);
  color: var(--color-text-secondary);
  font-weight: 500;
}

.pagination-container {
  padding: 24px 0;
  display: flex;
  justify-content: center;
  border-top: 1px solid var(--color-bg-secondary);
}

:deep(.el-card__body) {
  padding: 16px;
}

:deep(.el-input__wrapper) {
  box-shadow: none !important;
  background-color: var(--color-bg-secondary) !important;
  border-radius: 8px !important;
  padding: 4px 12px;
  transition: all 0.2s;
}

:deep(.el-input__wrapper:hover) {
  background-color: #e8e8ed !important;
}

:deep(.el-input__wrapper.is-focus) {
  background-color: #fff !important;
  box-shadow: 0 0 0 2px var(--color-accent) !important;
}

:deep(.el-table) {
  --el-table-border-color: transparent;
  --el-table-header-bg-color: transparent;
  --el-table-row-hover-bg-color: var(--color-bg-secondary);
}

:deep(.el-table th.el-table__cell) {
  font-weight: 500;
  color: var(--color-text-secondary);
  font-size: 13px;
  border-bottom: 1px solid var(--color-bg-secondary);
  padding: 16px 0;
}

:deep(.el-table td.el-table__cell) {
  border-bottom: 1px solid var(--color-bg-secondary);
  padding: 16px 0;
}

:deep(.el-pagination.is-background .el-pager li:not(.is-disabled).is-active) {
  background-color: #000;
  color: #fff;
}

:deep(.el-pagination.is-background .el-pager li) {
  background-color: var(--color-bg-secondary);
  border-radius: 6px;
  font-weight: 500;
}
</style>
