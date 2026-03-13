<template>
  <div class="req-container">
    <!-- Header -->
    <div class="page-header">
      <div class="header-content">
        <h2>需求管理</h2>
        <p class="subtitle">集中管理项目需求文档，支持 AI 智能解析与结构化预览。</p>
      </div>
      <div class="header-actions">
        <el-button :icon="Upload" @click="showUpload = true">上传文档</el-button>
        <el-button type="primary" :icon="Plus" @click="showText = true">手动输入</el-button>
      </div>
    </div>

    <!-- Stats Bar -->
    <div class="stats-bar">
      <div class="stat-item">
        <span class="stat-label">需求总数</span>
        <span class="stat-value">{{ requirements.length }}</span>
      </div>
      <div class="stat-divider"></div>
      <div class="stat-item">
        <span class="stat-label">已解析</span>
        <span class="stat-value success">{{ parsedCount }}</span>
      </div>
      <div class="stat-divider"></div>
      <div class="stat-item">
        <span class="stat-label">解析中/失败</span>
        <span class="stat-value warning">{{ pendingCount }} / {{ failedCount }}</span>
      </div>
      <div class="stat-divider"></div>
      <div class="stat-item">
        <span class="stat-label">需求点总数</span>
        <span class="stat-value primary">{{ pointsTotal }}</span>
      </div>
    </div>

    <!-- Requirements Table -->
    <div class="table-container">
      <div v-if="!loading && requirements.length === 0" class="empty-state">
        <el-icon class="empty-icon"><Document /></el-icon>
        <h3>暂无需求文档</h3>
        <p>上传文档或手动录入，AI 将自动为您解析需求点。</p>
        <div class="empty-actions">
          <el-button type="primary" @click="showUpload = true">上传文档</el-button>
          <el-button @click="showText = true">手动输入</el-button>
        </div>
      </div>

      <el-table
        v-else
        v-loading="loading"
        :data="requirements"
        stripe
        height="100%"
        @row-click="handleReqRowClick"
        class="req-table"
      >
        <el-table-column label="需求标题" prop="title" min-width="240" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="req-title-cell">{{ row.title }}</span>
          </template>
        </el-table-column>
        <el-table-column label="来源" width="100" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="row.source_type === 'file' ? 'primary' : 'info'" effect="light" round>
              {{ row.source_type === 'file' ? '文档' : '手动' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="需求点" width="100" align="center">
          <template #default="{ row }">
            <span class="points-badge">{{ row.req_points_count || 0 }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="110" align="center">
          <template #default="{ row }">
             <div class="status-indicator">
                <span :class="['status-dot', row.status]"></span>
                {{ statusLabel(row.status) }}
             </div>
          </template>
        </el-table-column>
        <el-table-column label="创建人" prop="creator_name" width="120" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="creator-text">{{ row.creator_name || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="160" align="right">
          <template #default="{ row }">
            <span class="time-text">{{ fmtDate(row.created_at) }}</span>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- Upload Dialog -->
    <el-dialog v-model="showUpload" title="上传需求文档" width="480px" align-center destroy-on-close>
      <el-form :model="uploadForm" label-position="top">
        <el-form-item label="需求标题" required>
          <el-input v-model="uploadForm.title" placeholder="例如：用户中心 V2.0 PRD" />
        </el-form-item>
        <el-form-item label="文档文件" required>
          <el-upload
            drag
            action="#"
            :before-upload="beforeUpload"
            :on-change="onFileChange"
            :auto-upload="false"
            accept=".pdf,.docx,.doc,.xlsx,.xls,.md,.txt"
            :limit="1"
            class="upload-area"
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">拖拽文件到此处或 <em>点击上传</em></div>
            <template #tip>
              <div class="el-upload__tip">支持 PDF, Word, Excel, Markdown, TXT (Max 50MB)</div>
            </template>
          </el-upload>
        </el-form-item>
        <el-form-item>
           <el-checkbox v-model="uploadForm.useAi">启用 AI 智能解析 (推荐)</el-checkbox>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showUpload = false">取消</el-button>
        <el-button type="primary" :loading="uploading" @click="handleUpload">开始解析</el-button>
      </template>
    </el-dialog>

    <!-- Manual Input Dialog -->
    <el-dialog v-model="showText" title="手动录入需求" width="600px" align-center destroy-on-close>
      <el-form :model="textForm" label-position="top">
        <el-form-item label="需求标题" required>
          <el-input v-model="textForm.title" placeholder="需求标题" />
        </el-form-item>
        <el-form-item label="需求内容" required>
          <el-input
            v-model="textForm.content"
            type="textarea"
            :rows="12"
            placeholder="请粘贴需求文本..."
            resize="none"
          />
        </el-form-item>
        <el-form-item>
           <el-checkbox v-model="textForm.useAi">启用 AI 智能解析 (推荐)</el-checkbox>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showText = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleTextSave">保存并解析</el-button>
      </template>
    </el-dialog>

    <!-- Detail Drawer -->
    <el-drawer v-model="showPoints" :title="currentReq?.title || '需求详情'" size="600px" class="detail-drawer">
      <div class="drawer-content">
        <div class="drawer-header-actions">
           <div class="meta-info">
             <span class="meta-label">包含 {{ currentPoints.length }} 个需求点</span>
           </div>
           <div class="actions">
             <el-button v-if="!editingReq" :icon="Edit" circle @click="toggleEditReq" />
             <el-button :icon="Delete" circle type="danger" plain @click="deleteCurrentReq" />
           </div>
        </div>

        <div v-if="editingReq" class="edit-mode">
          <el-form label-position="top">
             <el-form-item label="标题"><el-input v-model="editingTitle" /></el-form-item>
             <el-form-item label="需求点 JSON 数据">
               <el-input v-model="editingPointsJson" type="textarea" :rows="20" />
             </el-form-item>
             <div class="form-actions">
               <el-button @click="toggleEditReq">取消</el-button>
               <el-button type="primary" :loading="savingReqEdit" @click="saveReqEdit">保存修改</el-button>
             </div>
          </el-form>
        </div>

        <div v-else class="points-list">
           <div v-for="(p, i) in currentPoints" :key="i" class="point-card">
              <div class="point-head">
                 <span class="point-idx">{{ p.id || `#${i+1}` }}</span>
                 <el-tag size="small" :type="priorityType(p.priority)">{{ p.priority || 'P1' }}</el-tag>
                 <span class="point-mod">{{ p.module || '通用' }}</span>
              </div>
              <div class="point-body">
                 <div class="point-t">{{ p.title }}</div>
                 <div class="point-d">{{ p.description }}</div>
              </div>
           </div>
           <div v-if="!currentPoints.length" class="empty-points">
              未解析出需求点，请检查文档内容或尝试重新解析。
           </div>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { Plus, Upload, Delete, Edit, Document, UploadFilled } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { requirementApi } from '@/api/requirements'
import type { Requirement, RequirementPoint } from '@/api/types'

const route = useRoute()
const projectId = computed(() => Number(route.params.id))

// State
const requirements = ref<Requirement[]>([])
const loading = ref(false)
const uploading = ref(false)
const saving = ref(false)
const showUpload = ref(false)
const showText = ref(false)
const showPoints = ref(false)
const currentReq = ref<Requirement | null>(null)
const editingReq = ref(false)
const savingReqEdit = ref(false)
const editingTitle = ref('')
const editingPointsJson = ref('')
const uploadFile = ref<File | null>(null)

const uploadForm = reactive({ title: '', useAi: true })
const textForm = reactive({ title: '', content: '', useAi: true })

// Computed
const currentPoints = computed<RequirementPoint[]>(() => (currentReq.value?.parse_result as RequirementPoint[]) || [])
const parsedCount = computed(() => requirements.value.filter(r => r.status === 'parsed').length)
const pendingCount = computed(() => requirements.value.filter(r => r.status === 'parsing').length)
const failedCount = computed(() => requirements.value.filter(r => r.status === 'failed').length)
const pointsTotal = computed(() => requirements.value.reduce((s, r) => s + (r.req_points_count || 0), 0))

// Lifecycle
onMounted(fetchReqs)

// Actions
async function fetchReqs() {
  loading.value = true
  try { requirements.value = await requirementApi.list(projectId.value) }
  finally { loading.value = false }
}

function beforeUpload() { return false }
function onFileChange(file: any) { uploadFile.value = file.raw }

async function handleUpload() {
  if (!uploadFile.value) return ElMessage.warning('请选择文件')
  if (!uploadForm.title) return ElMessage.warning('请输入标题')
  uploading.value = true
  
  const fd = new FormData()
  fd.append('file', uploadFile.value)
  fd.append('project_id', String(projectId.value))
  fd.append('title', uploadForm.title)
  fd.append('use_ai', String(uploadForm.useAi))
  
  try {
    await requirementApi.upload(fd)
    ElMessage.success('上传成功，正在解析...')
    showUpload.value = false
    uploadForm.title = ''
    uploadFile.value = null
    fetchReqs()
  } catch(e) { ElMessage.error('上传失败') }
  finally { uploading.value = false }
}

async function handleTextSave() {
  if (!textForm.title) return ElMessage.warning('请输入标题')
  saving.value = true
  try {
    await requirementApi.createText(
      { project_id: projectId.value, title: textForm.title, content: textForm.content },
      textForm.useAi
    )
    ElMessage.success('已保存并开始解析')
    showText.value = false
    textForm.title = ''
    textForm.content = ''
    fetchReqs()
  } catch(e) { ElMessage.error('保存失败') }
  finally { saving.value = false }
}

function handleReqRowClick(row: Requirement, column: any) {
  if (column?.type === 'selection') return
  viewReq(row)
}

function viewReq(req: Requirement) {
  currentReq.value = req
  editingReq.value = false
  editingTitle.value = req.title
  editingPointsJson.value = JSON.stringify((req.parse_result as RequirementPoint[]) || [], null, 2)
  showPoints.value = true
}

async function deleteCurrentReq() {
  if (!currentReq.value) return
  try {
    await ElMessageBox.confirm('确定删除该需求文档吗？', '删除确认', { type: 'warning' })
    await requirementApi.remove(currentReq.value.id)
    ElMessage.success('删除成功')
    showPoints.value = false
    fetchReqs()
  } catch(e) {}
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
  try { parsed = JSON.parse(editingPointsJson.value || '[]') }
  catch { return ElMessage.error('JSON 格式错误') }
  
  savingReqEdit.value = true
  try {
    const updated = await requirementApi.update(currentReq.value.id, {
      title: editingTitle.value,
      parse_result: parsed,
      status: 'parsed',
    })
    currentReq.value = updated
    fetchReqs()
    editingReq.value = false
    ElMessage.success('更新成功')
  } catch(e) { ElMessage.error('更新失败') }
  finally { savingReqEdit.value = false }
}

// Helpers
const fmtDate = (s: string) => new Date(s).toLocaleString('zh-CN', { dateStyle: 'short', timeStyle: 'short' })
const statusLabel = (s: string) => ({parsed:'已解析', parsing:'解析中', failed:'失败'})[s] || s
const priorityType = (p: string): any => ({P0:'danger', P1:'warning', P2:'primary'})[p] || 'info'
</script>

<style scoped>
.req-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  max-width: 100%;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  flex-shrink: 0;
}
.page-header h2 {
  font-size: 24px;
  font-weight: 800;
  color: var(--text-primary);
  margin-bottom: 4px;
}
.subtitle { color: var(--text-secondary); font-size: 14px; }

/* Stats Bar */
.stats-bar {
  display: flex;
  align-items: center;
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 16px 24px;
  margin-bottom: 20px;
  flex-shrink: 0;
  box-shadow: var(--shadow-sm);
}
.stat-item { display: flex; flex-direction: column; gap: 4px; }
.stat-label { font-size: 12px; color: var(--text-secondary); text-transform: uppercase; }
.stat-value { font-size: 20px; font-weight: 700; color: var(--text-primary); line-height: 1; }
.stat-value.success { color: #10b981; }
.stat-value.warning { color: #f59e0b; }
.stat-value.primary { color: var(--primary); }
.stat-divider { width: 1px; height: 24px; background: var(--border); margin: 0 24px; }

/* Table */
.table-container {
  flex: 1;
  min-height: 0;
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.req-table { width: 100%; }
.req-table :deep(.el-table__row) { cursor: pointer; }

.req-title-cell { font-weight: 600; color: var(--text-primary); }
.points-badge { 
  display: inline-flex; align-items: center; justify-content: center;
  background: #f1f5f9; color: #475569; border-radius: 12px; padding: 2px 10px; font-size: 12px; font-weight: 600;
}

.status-indicator { display: flex; align-items: center; justify-content: center; gap: 6px; font-size: 13px; }
.status-dot { width: 6px; height: 6px; border-radius: 50%; background: #9ca3af; }
.status-dot.parsed { background: #10b981; }
.status-dot.parsing { background: #f59e0b; }
.status-dot.failed { background: #ef4444; }

.creator-text, .time-text { font-size: 13px; color: var(--text-secondary); }

/* Empty State */
.empty-state {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
}
.empty-icon { font-size: 64px; margin-bottom: 16px; opacity: 0.3; }
.empty-actions { margin-top: 24px; display: flex; gap: 12px; }

/* Drawer & Points */
.drawer-content { padding: 20px; }
.drawer-header-actions { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; border-bottom: 1px solid var(--border); padding-bottom: 16px; }
.meta-label { font-size: 14px; color: var(--text-secondary); font-weight: 500; }

.points-list { display: flex; flex-direction: column; gap: 16px; }
.point-card { background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 8px; padding: 16px; }
.point-head { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
.point-idx { font-family: monospace; font-size: 12px; color: var(--text-secondary); }
.point-mod { font-size: 12px; font-weight: 600; color: var(--text-secondary); }
.point-t { font-weight: 700; color: var(--text-primary); margin-bottom: 4px; font-size: 15px; }
.point-d { font-size: 14px; color: var(--text-secondary); line-height: 1.5; }

.empty-points { text-align: center; padding: 40px; color: var(--text-secondary); font-size: 14px; border: 1px dashed var(--border); border-radius: 8px; }
.form-actions { display: flex; justify-content: flex-end; gap: 12px; margin-top: 20px; }

@media (max-width: 768px) {
  .stats-bar { display: none; }
}
</style>
