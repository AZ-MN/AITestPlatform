<template>
  <div>
    <div class="page-header">
      <h2>用例库 <span class="ai-badge">AI</span></h2>
      <div>
        <el-button icon="MagicStick" type="success" @click="showAiDialog = true">AI生成用例</el-button>
        <el-button type="primary" icon="Plus" @click="showDialog = true">手动新建</el-button>
        <el-button icon="Download" @click="exportCases">导出Excel</el-button>
      </div>
    </div>

    <div class="filter-bar">
      <el-select v-model="filterPriority" placeholder="优先级" clearable @change="fetchList" style="width: 110px">
        <el-option v-for="p in ['P0','P1','P2','P3']" :key="p" :label="p" :value="p" />
      </el-select>
      <el-select v-model="filterType" placeholder="用例类型" clearable @change="fetchList" style="width: 130px">
        <el-option label="功能" value="functional" />
        <el-option label="异常" value="exception" />
        <el-option label="边界" value="boundary" />
        <el-option label="性能" value="performance" />
        <el-option label="安全" value="security" />
      </el-select>
    </div>

    <el-table :data="list" border stripe v-loading="loading">
      <el-table-column type="selection" width="50" />
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="title" label="用例标题" min-width="250" show-overflow-tooltip />
      <el-table-column prop="module" label="模块" width="120" />
      <el-table-column prop="case_type" label="类型" width="90">
        <template #default="{ row }">
          <el-tag size="small" type="info">{{ row.case_type }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="priority" label="优先级" width="90">
        <template #default="{ row }">
          <el-tag :type="{ P0: 'danger', P1: 'warning', P2: '', P3: 'info' }[row.priority] || ''" size="small">{{ row.priority }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="AI生成" width="90">
        <template #default="{ row }">
          <el-tag v-if="row.is_ai_generated" size="small" color="#722ed1" style="color:#fff">AI</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="150">
        <template #default="{ row }">{{ row.created_at?.substring(0, 16) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="150">
        <template #default="{ row }">
          <el-button link type="primary" @click="viewCase(row)">查看</el-button>
          <el-button link type="primary" @click="editCase(row)">编辑</el-button>
          <el-button link type="danger" @click="deleteCase(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- AI生成对话框 -->
    <el-dialog v-model="showAiDialog" title="AI生成测试用例" width="600px">
      <el-form label-width="90px">
        <el-form-item label="需求内容">
          <el-input v-model="aiContent" type="textarea" :rows="8" placeholder="粘贴需求文档内容，AI将自动生成测试用例..." />
        </el-form-item>
        <el-form-item label="保存到库">
          <el-switch v-model="aiSaveToDB" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAiDialog = false">取消</el-button>
        <el-button type="primary" :loading="aiGenerating" @click="aiGenerate">
          <el-icon><MagicStick /></el-icon>&nbsp;开始生成
        </el-button>
      </template>
    </el-dialog>

    <!-- 查看用例详情 -->
    <el-drawer v-model="showDetail" :title="currentCase?.title" size="600px">
      <div v-if="currentCase">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="模块">{{ currentCase.module }}</el-descriptions-item>
          <el-descriptions-item label="优先级"><el-tag>{{ currentCase.priority }}</el-tag></el-descriptions-item>
          <el-descriptions-item label="类型">{{ currentCase.case_type }}</el-descriptions-item>
          <el-descriptions-item label="AI生成">{{ currentCase.is_ai_generated ? '是' : '否' }}</el-descriptions-item>
          <el-descriptions-item label="前置条件" :span="2">{{ currentCase.preconditions || '-' }}</el-descriptions-item>
          <el-descriptions-item label="预期结果" :span="2">{{ currentCase.expected_result || '-' }}</el-descriptions-item>
        </el-descriptions>
        <div style="margin-top: 16px">
          <h4 style="margin-bottom: 8px">测试步骤</h4>
          <el-timeline>
            <el-timeline-item v-for="(s, i) in currentCase.steps" :key="i" :timestamp="`步骤${i+1}`">
              <div>{{ s.step }}</div>
              <div style="color:#909399; font-size:13px">期望: {{ s.expected }}</div>
            </el-timeline-item>
          </el-timeline>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { testcaseApi } from '@/api/modules'
import { useProjectStore } from '@/stores/project'

const route = useRoute()
const projectStore = useProjectStore()
const list = ref<any[]>([])
const loading = ref(false)
const aiGenerating = ref(false)
const showDialog = ref(false)
const showAiDialog = ref(false)
const showDetail = ref(false)
const currentCase = ref<any>(null)
const filterPriority = ref('')
const filterType = ref('')
const aiContent = ref('')
const aiSaveToDB = ref(true)

const fetchList = async () => {
  if (!projectStore.currentProject) return
  loading.value = true
  try {
    const params: any = { project_id: projectStore.currentProject.id }
    if (filterPriority.value) params.priority = filterPriority.value
    if (filterType.value) params.case_type = filterType.value
    if (route.query.requirement_id) params.requirement_id = route.query.requirement_id
    list.value = (await testcaseApi.list(params)) as any[]
  } finally { loading.value = false }
}

const aiGenerate = async () => {
  if (!aiContent.value.trim()) { ElMessage.warning('请输入需求内容'); return }
  aiGenerating.value = true
  try {
    const res: any = await testcaseApi.aiGenerate({
      project_id: projectStore.currentProject!.id,
      content: aiContent.value,
      save_to_db: aiSaveToDB.value,
    })
    ElMessage.success(`AI生成 ${res.length} 条测试用例`)
    showAiDialog.value = false
    fetchList()
  } finally { aiGenerating.value = false }
}

const viewCase = (row: any) => { currentCase.value = row; showDetail.value = true }
const editCase = (row: any) => { currentCase.value = row; showDialog.value = true }
const deleteCase = async (id: number) => {
  await ElMessageBox.confirm('确认删除？', '提示', { type: 'warning' })
  await testcaseApi.delete(id)
  ElMessage.success('删除成功')
  fetchList()
}
const exportCases = () => ElMessage.info('导出功能开发中...')

onMounted(fetchList)
</script>
