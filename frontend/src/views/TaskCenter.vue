<template>
  <div class="task-page">
    <div class="page-header">
      <h2>任务中心</h2>
      <div class="actions">
        <el-select v-model="taskType" placeholder="全部类型" clearable style="width:140px" @change="fetchTasks">
          <el-option label="用例生成" value="generate_cases" />
          <el-option label="需求重解析" value="reparse_requirement" />
        </el-select>
        <el-select v-model="status" placeholder="全部状态" clearable style="width:140px" @change="fetchTasks">
          <el-option label="排队中" value="queued" />
          <el-option label="执行中" value="running" />
          <el-option label="成功" value="success" />
          <el-option label="失败" value="failed" />
          <el-option label="已停止" value="stopped" />
        </el-select>
        <el-switch v-model="autoRefresh" active-text="自动刷新" @change="toggleRefresh" />
        <el-button @click="fetchTasks">刷新</el-button>
      </div>
    </div>

    <div class="stats-row">
      <div class="stat"><strong>{{ tasks.length }}</strong><span>总任务</span></div>
      <div class="stat"><strong>{{ queuedCount }}</strong><span>排队中</span></div>
      <div class="stat"><strong>{{ runningCount }}</strong><span>执行中</span></div>
      <div class="stat"><strong>{{ failedCount }}</strong><span>失败/停止</span></div>
    </div>

    <div class="page-card">
      <el-table :data="filteredTasks" v-loading="loading">
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
      <el-empty v-if="!loading && !filteredTasks.length" description="暂无匹配任务" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { taskApi } from '@/api/tasks'
import type { TaskJob } from '@/api/types'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const tasks = ref<TaskJob[]>([])
const status = ref<string>()
const taskType = ref<string>()
const autoRefresh = ref(true)
const projectId = computed(() => Number(route.query.project_id || 0) || undefined)
let timer: number | undefined

onMounted(() => {
  fetchTasks()
  timer = window.setInterval(fetchTasks, 3000)
})
onUnmounted(() => {
  if (timer) window.clearInterval(timer)
})

const filteredTasks = computed(() => {
  if (!taskType.value) return tasks.value
  return tasks.value.filter(t => t.task_type === taskType.value)
})
const queuedCount = computed(() => tasks.value.filter(t => t.status === 'queued').length)
const runningCount = computed(() => tasks.value.filter(t => t.status === 'running').length)
const failedCount = computed(() => tasks.value.filter(t => t.status === 'failed' || t.status === 'stopped').length)

function toggleRefresh() {
  if (timer) window.clearInterval(timer)
  if (autoRefresh.value) timer = window.setInterval(fetchTasks, 3000)
}

async function fetchTasks() {
  loading.value = true
  try {
    tasks.value = await taskApi.list({ project_id: projectId.value, status: status.value })
  } finally {
    loading.value = false
  }
}

async function stopTask(id: number) {
  await ElMessageBox.confirm('确认强制停止该任务？', '停止任务', { type: 'warning' })
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
.stats-row { display: flex; gap: 10px; margin-bottom: 12px; }
.stat {
  min-width: 120px;
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.stat strong { font-size: 18px; }
.stat span { font-size: 12px; color: var(--text-secondary); }
</style>
