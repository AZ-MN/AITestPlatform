<template>
  <div>
    <div class="page-header">
      <h2>缺陷管理</h2>
      <el-button type="primary" icon="Plus" @click="showDialog = true">提报缺陷</el-button>
    </div>

    <el-tabs v-model="activeStatus" @tab-change="fetchList">
      <el-tab-pane label="全部" name="" />
      <el-tab-pane label="新建" name="new" />
      <el-tab-pane label="已确认" name="confirmed" />
      <el-tab-pane label="修复中" name="fixing" />
      <el-tab-pane label="待验证" name="pending_verify" />
      <el-tab-pane label="已关闭" name="closed" />
    </el-tabs>

    <div class="filter-bar">
      <el-select v-model="filterSeverity" placeholder="严重程度" clearable @change="fetchList" style="width:130px">
        <el-option label="致命" value="blocker" />
        <el-option label="严重" value="critical" />
        <el-option label="一般" value="normal" />
        <el-option label="轻微" value="minor" />
        <el-option label="建议" value="trivial" />
      </el-select>
      <el-input v-model="keyword" placeholder="搜索缺陷标题" prefix-icon="Search" clearable style="width:220px" @change="fetchList" />
    </div>

    <el-table :data="list" border stripe v-loading="loading">
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="title" label="缺陷标题" min-width="250" show-overflow-tooltip>
        <template #default="{ row }">
          <router-link :to="`/defects/${row.id}`" style="color:#1890ff">{{ row.title }}</router-link>
        </template>
      </el-table-column>
      <el-table-column prop="module" label="模块" width="110" />
      <el-table-column prop="severity" label="严重程度" width="100">
        <template #default="{ row }">
          <el-tag :type="{ blocker:'danger', critical:'danger', normal:'warning', minor:'', trivial:'info' }[row.severity] || ''" size="small">
            {{ { blocker:'致命', critical:'严重', normal:'一般', minor:'轻微', trivial:'建议' }[row.severity] || row.severity }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="priority" label="优先级" width="90">
        <template #default="{ row }">
          <el-tag :type="{ P0:'danger', P1:'warning', P2:'', P3:'info' }[row.priority] || ''" size="small">{{ row.priority }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="{ new:'info', confirmed:'warning', fixing:'', pending_verify:'success', closed:'info' }[row.status] || ''" size="small">
            {{ { new:'新建', confirmed:'已确认', fixing:'修复中', pending_verify:'待验证', closed:'已关闭', reopened:'重新打开' }[row.status] || row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="AI分析" width="90">
        <template #default="{ row }">
          <el-tag v-if="row.ai_category" size="small" type="success">已分析</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="提报时间" width="150">
        <template #default="{ row }">{{ row.created_at?.substring(0, 16) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="180">
        <template #default="{ row }">
          <el-button link type="primary" @click="aiAnalyze(row)" :loading="row._analyzing">AI分析</el-button>
          <el-button link type="primary" @click="changeStatus(row)">变更状态</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 新建缺陷 -->
    <el-dialog v-model="showDialog" title="提报缺陷" width="700px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="缺陷标题" required><el-input v-model="form.title" /></el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="严重程度">
              <el-select v-model="form.severity">
                <el-option label="致命" value="blocker" />
                <el-option label="严重" value="critical" />
                <el-option label="一般" value="normal" />
                <el-option label="轻微" value="minor" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="优先级">
              <el-select v-model="form.priority">
                <el-option v-for="p in ['P0','P1','P2','P3']" :key="p" :label="p" :value="p" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="所属模块"><el-input v-model="form.module" /></el-form-item>
        <el-form-item label="复现步骤"><el-input v-model="form.steps_to_reproduce" type="textarea" :rows="4" /></el-form-item>
        <el-form-item label="实际结果"><el-input v-model="form.actual_result" type="textarea" :rows="3" /></el-form-item>
        <el-form-item label="预期结果"><el-input v-model="form.expected_result" type="textarea" :rows="3" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveDefect">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { defectApi } from '@/api/modules'
import { useProjectStore } from '@/stores/project'

const projectStore = useProjectStore()
const list = ref<any[]>([])
const loading = ref(false)
const saving = ref(false)
const showDialog = ref(false)
const activeStatus = ref('')
const filterSeverity = ref('')
const keyword = ref('')
const form = reactive({ title: '', severity: 'normal', priority: 'P2', module: '', steps_to_reproduce: '', actual_result: '', expected_result: '' })

const fetchList = async () => {
  if (!projectStore.currentProject) return
  loading.value = true
  try {
    const params: any = { project_id: projectStore.currentProject.id }
    if (activeStatus.value) params.status = activeStatus.value
    if (filterSeverity.value) params.severity = filterSeverity.value
    if (keyword.value) params.keyword = keyword.value
    list.value = (await defectApi.list(params)) as any[]
  } finally { loading.value = false }
}

const saveDefect = async () => {
  saving.value = true
  try {
    await defectApi.create({ ...form, project_id: projectStore.currentProject!.id })
    ElMessage.success('缺陷提报成功')
    showDialog.value = false
    fetchList()
  } finally { saving.value = false }
}

const aiAnalyze = async (row: any) => {
  row._analyzing = true
  try {
    const res: any = await defectApi.aiAnalyze({ defect_id: row.id, description: row.title + '\n' + (row.steps_to_reproduce || '') })
    ElMessage.success('AI分析完成')
    fetchList()
  } finally { row._analyzing = false }
}

const changeStatus = async (row: any) => {
  const statusMap = { new: '确认', confirmed: '开始修复', fixing: '提交验证', pending_verify: '关闭' }
  const nextStatus = { new: 'confirmed', confirmed: 'fixing', fixing: 'pending_verify', pending_verify: 'closed' }[row.status]
  if (!nextStatus) { ElMessage.info('缺陷已关闭'); return }
  await defectApi.changeStatus(row.id, { status: nextStatus, comment: `状态流转: ${row.status} → ${nextStatus}` })
  ElMessage.success('状态已更新')
  fetchList()
}

onMounted(fetchList)
</script>
