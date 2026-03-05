<template>
  <div>
    <div class="page-header">
      <h2>需求管理</h2>
      <div>
        <el-button icon="Upload" @click="showUpload = true">上传需求文件</el-button>
        <el-button type="primary" icon="Plus" @click="showDialog = true">新建需求</el-button>
      </div>
    </div>

    <div class="filter-bar">
      <el-input v-model="keyword" placeholder="搜索需求" prefix-icon="Search" clearable style="width: 220px" @change="fetchList" />
      <el-select v-model="filterStatus" placeholder="状态" clearable @change="fetchList" style="width: 130px">
        <el-option label="草稿" value="draft" />
        <el-option label="已解析" value="parsed" />
        <el-option label="评审中" value="reviewing" />
        <el-option label="已批准" value="approved" />
      </el-select>
    </div>

    <el-table :data="list" border stripe v-loading="loading">
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="title" label="需求标题" min-width="200" show-overflow-tooltip>
        <template #default="{ row }">
          <router-link :to="`/requirements/${row.id}`" style="color: #1890ff">{{ row.title }}</router-link>
        </template>
      </el-table-column>
      <el-table-column prop="module" label="模块" width="120" />
      <el-table-column prop="priority" label="优先级" width="90">
        <template #default="{ row }">
          <el-tag :type="{ P0: 'danger', P1: 'warning', P2: '', P3: 'info' }[row.priority] || ''" size="small">{{ row.priority }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="{ draft: 'info', parsed: 'success', reviewing: 'warning', approved: 'success' }[row.status] || ''" size="small">
            {{ { draft: '草稿', parsed: '已解析', reviewing: '评审中', approved: '已批准' }[row.status] || row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="source_type" label="来源" width="80" />
      <el-table-column prop="created_at" label="创建时间" width="160">
        <template #default="{ row }">{{ row.created_at?.substring(0, 16) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="200">
        <template #default="{ row }">
          <el-button link type="primary" @click="aiParse(row)">AI解析</el-button>
          <el-button link type="primary" @click="goGenerateCases(row)">生成用例</el-button>
          <el-button link type="danger" @click="deleteReq(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 新建需求对话框 -->
    <el-dialog v-model="showDialog" title="新建需求" width="600px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="需求标题" required><el-input v-model="form.title" /></el-form-item>
        <el-form-item label="所属模块"><el-input v-model="form.module" /></el-form-item>
        <el-form-item label="优先级">
          <el-select v-model="form.priority">
            <el-option v-for="p in ['P0','P1','P2','P3']" :key="p" :label="p" :value="p" />
          </el-select>
        </el-form-item>
        <el-form-item label="需求描述">
          <el-input v-model="form.description" type="textarea" :rows="6" placeholder="粘贴需求文档内容..." />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveReq">保存</el-button>
      </template>
    </el-dialog>

    <!-- 上传文件 -->
    <el-dialog v-model="showUpload" title="上传需求文件" width="500px">
      <el-upload
        drag accept=".txt,.md,.docx,.pdf"
        :auto-upload="false" :on-change="onFileChange" :file-list="fileList"
      >
        <el-icon size="48"><UploadFilled /></el-icon>
        <div>拖拽或点击上传需求文档</div>
        <div style="color:#909399;font-size:12px">支持 .txt / .md / .docx / .pdf</div>
      </el-upload>
      <template #footer>
        <el-button @click="showUpload = false">取消</el-button>
        <el-button type="primary" :loading="uploading" @click="uploadFile">上传并解析</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { requirementApi } from '@/api/modules'
import { useProjectStore } from '@/stores/project'

const router = useRouter()
const projectStore = useProjectStore()
const list = ref<any[]>([])
const loading = ref(false)
const saving = ref(false)
const uploading = ref(false)
const showDialog = ref(false)
const showUpload = ref(false)
const keyword = ref('')
const filterStatus = ref('')
const fileList = ref<any[]>([])
const selectedFile = ref<File | null>(null)
const form = reactive({ title: '', module: '', priority: 'P1', description: '' })

const fetchList = async () => {
  if (!projectStore.currentProject) return
  loading.value = true
  try {
    list.value = (await requirementApi.list({ project_id: projectStore.currentProject.id })) as any[]
  } finally { loading.value = false }
}

const saveReq = async () => {
  saving.value = true
  try {
    await requirementApi.create({ ...form, project_id: projectStore.currentProject!.id })
    ElMessage.success('创建成功')
    showDialog.value = false
    fetchList()
  } finally { saving.value = false }
}

const aiParse = async (row: any) => {
  const loading = ElMessage({ message: 'AI解析中...', duration: 0 })
  try {
    const res: any = await requirementApi.aiParse(row.id)
    ElMessage.success('AI解析完成')
    fetchList()
  } finally { (loading as any).close?.() }
}

const goGenerateCases = (row: any) => {
  router.push({ path: '/testcases', query: { requirement_id: row.id } })
}

const deleteReq = async (id: number) => {
  await ElMessageBox.confirm('确认删除？', '提示', { type: 'warning' })
  ElMessage.success('删除成功')
  fetchList()
}

const onFileChange = (file: any) => {
  selectedFile.value = file.raw
}

const uploadFile = async () => {
  if (!selectedFile.value || !projectStore.currentProject) return
  uploading.value = true
  try {
    const res: any = await requirementApi.upload(projectStore.currentProject.id, selectedFile.value)
    ElMessage.success(`上传成功，需求ID: ${res.requirement_id}`)
    showUpload.value = false
    fetchList()
  } finally { uploading.value = false }
}

onMounted(fetchList)
</script>
