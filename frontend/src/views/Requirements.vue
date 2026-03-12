<template>
  <div class="req-page">
    <div class="page-header">
      <h2>需求管理</h2>
      <div class="header-actions">
        <el-button :icon="Upload" @click="showUpload = true">上传文档</el-button>
        <el-button type="primary" :icon="Plus" @click="showText = true">手动输入</el-button>
      </div>
    </div>

    <!-- 需求列表 -->
    <div v-if="!loading && requirements.length === 0" class="empty-state">
      <div class="empty-icon">📄</div>
      <h3>暂无需求</h3>
      <p>上传需求文档或手动输入需求，平台将自动解析需求点用于生成测试用例</p>
      <div style="display:flex;gap:12px;justify-content:center;margin-top:16px">
        <el-button type="primary" @click="showUpload = true">上传文档</el-button>
        <el-button @click="showText = true">手动输入</el-button>
      </div>
    </div>

    <el-table v-else v-loading="loading" :data="requirements" row-class-name="req-row" @row-click="handleReqRowClick">
      <el-table-column label="需求标题" prop="title" min-width="200" show-overflow-tooltip />
      <el-table-column label="来源" width="90">
        <template #default="{ row }">
          <el-tag size="small" :type="row.source_type === 'file' ? 'primary' : 'success'">
            {{ row.source_type === 'file' ? '文档' : '手动' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="需求点数" width="90" align="center">
        <template #default="{ row }">
          <el-tag size="small" type="warning">{{ row.req_points_count }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="row.status === 'parsed' ? 'success' : row.status === 'parsing' ? 'warning' : 'danger'" size="small">
            {{ ({'parsed':'已解析', 'parsing':'解析中', 'failed':'失败'} as Record<string,string>)[row.status] || row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="创建人" prop="creator_name" width="100" />
      <el-table-column label="创建时间" width="160">
        <template #default="{ row }">{{ fmtDate(row.created_at) }}</template>
      </el-table-column>
    </el-table>

    <!-- 上传文档弹窗 -->
    <el-dialog v-model="showUpload" title="上传需求文档" width="500px" :close-on-click-modal="false">
      <el-form :model="uploadForm" label-width="90px">
        <el-form-item label="需求标题">
          <el-input v-model="uploadForm.title" placeholder="如：用户中心 V2.0 需求" />
        </el-form-item>
        <el-form-item label="需求文档">
          <el-upload drag :before-upload="beforeUpload" :on-change="onFileChange" :auto-upload="false"
            accept=".pdf,.docx,.doc,.xlsx,.xls,.md,.txt" :limit="1">
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">拖拽或 <em>点击上传</em></div>
            <template #tip>
              <div class="el-upload__tip">支持 PDF / Word / Excel / Markdown / TXT，最大 500MB</div>
            </template>
          </el-upload>
        </el-form-item>
        <el-form-item label="AI解析">
          <el-switch v-model="uploadForm.useAi" active-text="AI智能解析需求点" inactive-text="规则解析" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showUpload = false">取消</el-button>
        <el-button type="primary" :loading="uploading" @click="handleUpload">上传并解析</el-button>
      </template>
    </el-dialog>

    <!-- 手动输入弹窗 -->
    <el-dialog v-model="showText" title="手动输入需求" width="600px" :close-on-click-modal="false">
      <el-form :model="textForm" label-width="90px">
        <el-form-item label="需求标题">
          <el-input v-model="textForm.title" placeholder="需求标题" />
        </el-form-item>
        <el-form-item label="需求内容">
          <el-input v-model="textForm.content" type="textarea" :rows="10"
            placeholder="粘贴需求文档内容，或直接描述需求..." />
        </el-form-item>
        <el-form-item label="AI解析">
          <el-switch v-model="textForm.useAi" active-text="AI智能解析需求点" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showText = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleTextSave">保存并解析</el-button>
      </template>
    </el-dialog>

    <!-- 需求点查看抽屉 -->
    <el-drawer v-model="showPoints" :title="`需求点 - ${currentReq?.title}`" size="760px" :close-on-click-modal="true">
      <div class="points-toolbar">
        <span class="points-count">共 {{ currentPoints.length }} 个需求点</span>
        <div style="display:flex;align-items:center;gap:6px">
          <el-tooltip :content="editingReq ? '取消编辑' : '编辑需求'" placement="top">
            <el-button text circle @click="toggleEditReq">
              <el-icon><Edit /></el-icon>
            </el-button>
          </el-tooltip>
          <el-tooltip content="删除需求" placement="top">
            <el-button text circle type="danger" @click="deleteCurrentReq">
              <el-icon><Delete /></el-icon>
            </el-button>
          </el-tooltip>
        </div>
      </div>
      <div v-if="editingReq" class="req-edit-form">
        <el-form label-width="90px">
          <el-form-item label="需求标题">
            <el-input v-model="editingTitle" />
          </el-form-item>
          <el-form-item label="需求点JSON">
            <el-input v-model="editingPointsJson" type="textarea" :rows="16" />
          </el-form-item>
        </el-form>
      </div>
      <div v-else class="points-list">
        <div v-for="(p, i) in currentPoints" :key="i" class="point-item">
          <div class="point-header">
            <span class="point-id">{{ p.id || `REQ-${i+1}` }}</span>
            <el-tag :class="`tag-${p.priority?.toLowerCase()}`" size="small">{{ p.priority }}</el-tag>
            <span class="point-module">{{ p.module }}</span>
          </div>
          <div class="point-title">{{ p.title }}</div>
          <div class="point-desc">{{ p.description }}</div>
          <div v-if="p.rules?.length" class="point-rules">
            <span v-for="r in p.rules" :key="r" class="rule-tag">{{ r }}</span>
          </div>
        </div>
      </div>
      <div class="points-actions">
        <el-button v-if="editingReq" @click="toggleEditReq">取消</el-button>
        <el-button v-if="editingReq" type="primary" :loading="savingReqEdit" @click="saveReqEdit">保存需求</el-button>
        <el-button size="small" type="success"
          @click="$router.push(`/projects/${projectId}/generate?req_id=${currentReq?.id}`); showPoints=false">
          生成测试用例
        </el-button>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Plus, Upload, Delete, Edit } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { requirementApi } from '@/api/requirements'
import type { Requirement, RequirementPoint } from '@/api/types'

const route = useRoute()
const router = useRouter()
const projectId = computed(() => Number(route.params.id))
const requirements = ref<Requirement[]>([])
const loading = ref(false)
const uploading = ref(false)
const saving = ref(false)
const showUpload = ref(false)
const showText = ref(false)
const showPoints = ref(false)
const currentReq = ref<Requirement | null>(null)
const currentPoints = computed<RequirementPoint[]>(() => (currentReq.value?.parse_result as RequirementPoint[]) || [])
const editingReq = ref(false)
const savingReqEdit = ref(false)
const editingTitle = ref('')
const editingPointsJson = ref('')
const uploadFile = ref<File | null>(null)

const uploadForm = reactive({ title: '', useAi: true })
const textForm = reactive({ title: '', content: '', useAi: true })

onMounted(fetchReqs)

async function fetchReqs() {
  loading.value = true
  try { requirements.value = await requirementApi.list(projectId.value) }
  finally { loading.value = false }
}

function beforeUpload() { return false }
function onFileChange(file: any) { uploadFile.value = file.raw }

async function handleUpload() {
  if (!uploadFile.value) return ElMessage.warning('请选择文件')
  if (!uploadForm.title) return ElMessage.warning('请输入需求标题')
  uploading.value = true
  const fd = new FormData()
  fd.append('file', uploadFile.value)
  fd.append('project_id', String(projectId.value))
  fd.append('title', uploadForm.title)
  fd.append('use_ai', String(uploadForm.useAi))
  try {
    await requirementApi.upload(fd)
    ElMessage.success('上传解析成功')
    showUpload.value = false
    uploadForm.title = ''
    uploadFile.value = null
    fetchReqs()
  } finally { uploading.value = false }
}

async function handleTextSave() {
  if (!textForm.title) return ElMessage.warning('请输入需求标题')
  saving.value = true
  try {
    await requirementApi.createText(
      { project_id: projectId.value, title: textForm.title, content: textForm.content },
      textForm.useAi
    )
    ElMessage.success('需求解析成功')
    showText.value = false
    Object.assign(textForm, { title: '', content: '', useAi: true })
    fetchReqs()
  } finally { saving.value = false }
}

function viewReq(req: Requirement) {
  currentReq.value = req
  editingReq.value = false
  editingTitle.value = req.title
  editingPointsJson.value = JSON.stringify((req.parse_result as RequirementPoint[]) || [], null, 2)
  showPoints.value = true
}

function handleReqRowClick(row: Requirement, column: any) {
  if (column?.type === 'selection') return
  viewReq(row)
}

async function deleteReq(req: Requirement) {
  await ElMessageBox.confirm(`确认删除需求「${req.title}」？`, '删除确认', {
    type: 'warning',
    closeOnClickModal: false,
    closeOnPressEscape: false,
  })
  await requirementApi.remove(req.id)
  ElMessage.success('删除成功')
  fetchReqs()
}

async function deleteCurrentReq() {
  if (!currentReq.value) return
  await deleteReq(currentReq.value)
  showPoints.value = false
}

function toggleEditReq() {
  if (!currentReq.value) return
  editingReq.value = !editingReq.value
  if (editingReq.value) {
    editingTitle.value = currentReq.value.title
    editingPointsJson.value = JSON.stringify((currentReq.value.parse_result as RequirementPoint[]) || [], null, 2)
  }
}

async function saveReqEdit() {
  if (!currentReq.value) return
  let parsed: RequirementPoint[] = []
  try {
    parsed = JSON.parse(editingPointsJson.value || '[]')
  } catch {
    ElMessage.error('需求点 JSON 格式错误')
    return
  }
  savingReqEdit.value = true
  try {
    const updated = await requirementApi.update(currentReq.value.id, {
      title: editingTitle.value,
      parse_result: parsed,
      status: 'parsed',
    })
    currentReq.value = updated
    await fetchReqs()
    editingReq.value = false
    ElMessage.success('需求已更新')
  } finally {
    savingReqEdit.value = false
  }
}

function fmtDate(s: string) {
  return new Date(s).toLocaleString('zh-CN', { dateStyle: 'short', timeStyle: 'short' })
}
</script>

<style scoped>
.req-page { width: 100%; max-width: none; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-header h2 { font-size: 22px; font-weight: 700; }
.header-actions { display: flex; gap: 8px; }

.empty-state { text-align: center; padding: 60px 20px; background: #fff; border-radius: 12px; border: 1px solid var(--border); }
.empty-icon { font-size: 48px; margin-bottom: 12px; }
.empty-state h3 { font-size: 18px; margin-bottom: 8px; }
.empty-state p { color: var(--text-secondary); font-size: 14px; }

:deep(.req-row) { cursor: pointer; }

.points-toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.points-count { font-size: 13px; color: var(--text-secondary); }
.points-list { max-height: 65vh; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; }
.req-edit-form { padding-top: 8px; }
.points-actions {
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px solid var(--border);
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}
.point-item { border: 1px solid var(--border); border-radius: 8px; padding: 12px 14px; }
.point-header { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.point-id { font-size: 11px; color: #9ca3af; font-family: monospace; }
.point-module { font-size: 11px; color: #9ca3af; }
.point-title { font-weight: 600; font-size: 14px; margin-bottom: 4px; }
.point-desc { font-size: 13px; color: var(--text-secondary); line-height: 1.5; }
.point-rules { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 6px; }
.rule-tag { font-size: 11px; background: #f3f4f6; color: #6b7280; padding: 2px 8px; border-radius: 4px; }
</style>
