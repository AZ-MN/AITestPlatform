<template>
  <div class="task-page">
    <div class="page-header">
      <h2>任务中心</h2>
      <div class="actions">
        <el-select v-model="status" placeholder="全部状态" clearable style="width:140px" @change="fetchTasks">
          <el-option label="排队中" value="queued" />
          <el-option label="执行中" value="running" />
          <el-option label="成功" value="success" />
          <el-option label="失败" value="failed" />
          <el-option label="已停止" value="stopped" />
        </el-select>
        <el-button @click="fetchTasks">刷新</el-button>
      </div>
    </div>

    <div class="page-card">
      <el-table :data="tasks" v-loading="loading">
        <el-table-column prop="id" label="任务ID" width="90" />
        <el-table-column label="类型" width="140">
          <template #default="{ row }">{{ typeLabel(row.task_type) }}</template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="进度" width="220">
          <template #default="{ row }">
            <el-progress :percentage="row.progress || 0" :status="row.status === 'failed' ? 'exception' : undefined" />
          </template>
        </el-table-column>
        <el-table-column label="队列" width="80">
          <template #default="{ row }">{{ row.queue_position || '-' }}</template>
        </el-table-column>
        <el-table-column label="信息" min-width="220">
          <template #default="{ row }">{{ row.error || row.message || '-' }}</template>
        </el-table-column>
        <el-table-column label="创建时间" width="160">
          <template #default="{ row }">{{ fmt(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button v-if="row.status === 'queued' || row.status === 'running'" size="small" type="danger" link @click="stopTask(row.id)">停止</el-button>
            <el-button v-if="row.status === 'failed' || row.status === 'stopped'" size="small" type="primary" link @click="retryTask(row.id)">重试</el-button>
            <el-button v-if="row.result?.batch_id" size="small" link @click="openBatch(row)">结果</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { taskApi } from '@/api/tasks'
import type { TaskJob } from '@/api/types'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const tasks = ref<TaskJob[]>([])
const status = ref<string>()
const projectId = computed(() => Number(route.query.project_id || 0) || undefined)
let timer: number | undefined

onMounted(() => {
  fetchTasks()
  timer = window.setInterval(fetchTasks, 3000)
})
onUnmounted(() => {
  if (timer) window.clearInterval(timer)
})

async function fetchTasks() {
  loading.value = true
  try {
    tasks.value = await taskApi.list({ project_id: projectId.value, status: status.value })
  } finally {
    loading.value = false
  }
}

async function stopTask(id: number) {
  await taskApi.stop(id)
  ElMessage.success('已请求停止任务')
  fetchTasks()
}

async function retryTask(id: number) {
  await taskApi.retry(id)
  ElMessage.success('重试任务已入队')
  fetchTasks()
}

function openBatch(task: TaskJob) {
  if (!task.result?.batch_id || !task.project_id) return
  router.push(`/projects/${task.project_id}/cases?batch=${task.result.batch_id}`)
}

function fmt(s?: string) {
  if (!s) return '-'
  return new Date(s).toLocaleString('zh-CN', { dateStyle: 'short', timeStyle: 'short' })
}
const typeLabel = (t: string) => ({ generate_cases: '用例生成', reparse_requirement: '需求重解析' } as Record<string, string>)[t] || t
const statusLabel = (s: string) => ({ queued: '排队中', running: '执行中', success: '成功', failed: '失败', stopped: '已停止' } as Record<string, string>)[s] || s
const statusType = (s: string) => ({ queued: 'info', running: 'warning', success: 'success', failed: 'danger', stopped: 'info' } as Record<string, any>)[s] || 'info'
</script>

<style scoped>
.task-page { max-width: 1300px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.actions { display: flex; gap: 8px; }
</style>
