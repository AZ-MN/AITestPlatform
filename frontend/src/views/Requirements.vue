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
            <span class="req-title-cell">{{ truncate(row.title) }}</span>
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

    <!-- Detail Dialog -->
    <el-dialog 
      v-model="showPoints" 
      :title="currentReq?.title || '需求详情'" 
      width="75%" 
      top="8vh"
      class="req-detail-dialog"
      destroy-on-close
    >
      <div class="dialog-body">
        <div class="dialog-toolbar">
           <div class="left-info">
             <el-tag effect="plain" round class="count-tag">共 {{ currentPoints.length }} 个需求点</el-tag>
             
             <transition name="el-fade-in">
               <div v-if="selectedPoints.length" class="batch-actions">
                 <span class="sel-count">已选 {{ selectedPoints.length }} 项</span>
                 <el-button type="primary" size="small" @click="openBatchEdit">批量修改</el-button>
                 <el-button type="danger" size="small" plain @click="batchDeletePoints">批量删除</el-button>
               </div>
             </transition>
           </div>
           
           <div class="right-actions">
             <el-tooltip v-if="!editingReq" content="编辑" placement="top">
                <el-button :icon="Edit" circle class="icon-btn" @click="toggleEditReq" />
             </el-tooltip>
             <el-tooltip content="删除" placement="top">
                <el-button :icon="Delete" circle type="danger" plain class="icon-btn" @click="deleteCurrentReq" />
             </el-tooltip>
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

        <div v-else class="table-view">
           <el-table 
             :data="paginatedPoints" 
             stripe 
             border 
             style="width: 100%" 
             height="100%" 
             class="points-table"
             @selection-change="handleSelectionChange"
           >
              <el-table-column type="selection" width="45" align="center" />
              <el-table-column prop="id" label="编码" width="100" show-overflow-tooltip sortable>
                 <template #default="{ row, $index }">
                    <span class="code-text">{{ row.id || `REQ-${String($index+1).padStart(3, '0')}` }}</span>
                 </template>
              </el-table-column>
              <el-table-column prop="priority" label="优先级" width="100" sortable show-overflow-tooltip>
                <template #default="{ row }">
                  <el-tag :type="priorityType(row.priority)" size="small" effect="dark" class="prio-tag">{{ row.priority || 'P1' }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="module" label="所属模块" width="160" show-overflow-tooltip sortable>
                 <template #default="{ row }">
                    <span class="module-text">{{ row.module }}</span>
                 </template>
              </el-table-column>
              <el-table-column prop="title" label="需求标题" width="300" show-overflow-tooltip>
                 <template #default="{ row }">
                    <span class="title-text">{{ row.title }}</span>
                 </template>
              </el-table-column>
              <el-table-column prop="description" label="详细内容" min-width="300" show-overflow-tooltip>
                 <template #default="{ row }">
                   <div class="desc-text">{{ row.description }}</div>
                 </template>
              </el-table-column>
           </el-table>
           <div class="pagination-bar">
              <el-pagination
                v-model:current-page="currentPage"
                v-model:page-size="pageSize"
                :page-sizes="[10, 20, 50, 100]"
                layout="total, sizes, prev, pager, next, jumper"
                :total="currentPoints.length"
                size="small"
                @size-change="handleSizeChange"
                @current-change="handlePageChange"
              />
           </div>
        </div>
      </div>
    </el-dialog>

    <!-- Batch Edit Dialog -->
    <el-dialog v-model="showBatchEdit" title="批量修改" width="400px" append-to-body>
      <el-form :model="batchForm" label-position="top">
        <el-form-item label="优先级">
          <el-select v-model="batchForm.priority" placeholder="不修改" clearable>
            <el-option label="P0 (最高)" value="P0" />
            <el-option label="P1 (高)" value="P1" />
            <el-option label="P2 (中)" value="P2" />
            <el-option label="P3 (低)" value="P3" />
          </el-select>
        </el-form-item>
        <el-form-item label="所属模块">
           <el-input v-model="batchForm.module" placeholder="输入模块名 (留空则不修改)" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showBatchEdit = false">取消</el-button>
        <el-button type="primary" :loading="savingReqEdit" @click="handleBatchEditSave">确定修改</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { Plus, Upload, Delete, Edit, Document, UploadFilled, Refresh } from '@element-plus/icons-vue'
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
const showBatchEdit = ref(false)
const currentReq = ref<Requirement | null>(null)
const editingReq = ref(false)
const savingReqEdit = ref(false)
const editingTitle = ref('')
const editingPointsJson = ref('')
const uploadFile = ref<File | null>(null)
const selectedPoints = ref<RequirementPoint[]>([])
const currentPage = ref(1)
const pageSize = ref(10)

const uploadForm = reactive({ title: '', useAi: true })
const textForm = reactive({ title: '', content: '', useAi: true })
const batchForm = reactive({ priority: '', module: '' })

// Computed
const currentPoints = computed<RequirementPoint[]>(() => (currentReq.value?.parse_result as RequirementPoint[]) || [])
const paginatedPoints = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return currentPoints.value.slice(start, end)
})
const parsedCount = computed(() => requirements.value.filter(r => r.status === 'parsed').length)
const pendingCount = computed(() => requirements.value.filter(r => r.status === 'parsing').length)
const failedCount = computed(() => requirements.value.filter(r => r.status === 'failed').length)
const pointsTotal = computed(() => requirements.value.reduce((s, r) => s + (r.req_points_count || 0), 0))

// Lifecycle
onMounted(fetchReqs)

// Actions
function handlePageChange(val: number) { currentPage.value = val }
function handleSizeChange(val: number) { pageSize.value = val }

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
  selectedPoints.value = []
  currentPage.value = 1
}

function handleSelectionChange(val: RequirementPoint[]) {
  selectedPoints.value = val
}

async function batchDeletePoints() {
  if (!selectedPoints.value.length || !currentReq.value) return
  try {
    await ElMessageBox.confirm(`确定删除选中的 ${selectedPoints.value.length} 个需求点吗？`, '批量删除', { type: 'warning' })
    
    // Filter out selected points
    const selectedIds = new Set(selectedPoints.value.map(p => p.id))
    const newPoints = (currentReq.value.parse_result as RequirementPoint[]).filter(p => !selectedIds.has(p.id))
    
    await updateReqPoints(newPoints)
  } catch(e) {}
}

function openBatchEdit() {
  batchForm.priority = ''
  batchForm.module = ''
  showBatchEdit.value = true
}

async function handleBatchEditSave() {
  if (!selectedPoints.value.length || !currentReq.value) return
  
  const points = [...(currentReq.value.parse_result as RequirementPoint[])]
  const selectedIds = new Set(selectedPoints.value.map(p => p.id))
  
  points.forEach(p => {
    if (selectedIds.has(p.id)) {
      if (batchForm.priority) p.priority = batchForm.priority
      if (batchForm.module) p.module = batchForm.module
    }
  })
  
  await updateReqPoints(points)
  showBatchEdit.value = false
}

async function updateReqPoints(points: RequirementPoint[]) {
  if (!currentReq.value) return
  savingReqEdit.value = true
  try {
    const updated = await requirementApi.update(currentReq.value.id, {
      ...currentReq.value,
      parse_result: points,
    })
    currentReq.value = updated
    selectedPoints.value = []
    fetchReqs()
    ElMessage.success('更新成功')
  } catch(e) {
    ElMessage.error('更新失败')
  } finally {
    savingReqEdit.value = false
  }
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
const truncate = (s: string, n=20) => s?.length > n ? s.slice(0, n) + '...' : s
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

/* Dialog Styles */
.req-detail-dialog :deep(.el-dialog__header) {
  padding: 20px 24px;
  border-bottom: 1px solid var(--border);
  margin: 0;
}
.req-detail-dialog :deep(.el-dialog__title) { font-weight: 700; color: var(--text-primary); }
.req-detail-dialog :deep(.el-dialog__body) {
  padding: 0;
}
.dialog-body { padding: 24px; height: 100%; display: flex; flex-direction: column; }

.dialog-toolbar { 
  display: flex; 
  justify-content: space-between; 
  align-items: center; 
  margin-bottom: 20px; 
}
.left-info { display: flex; align-items: center; gap: 16px; height: 32px; }
.count-tag { font-weight: 600; border: none; background: #f3f4f6; color: #4b5563; }
.doc-meta { color: var(--text-secondary); font-size: 13px; }

.batch-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  border: 1px solid var(--border);
  padding: 4px 12px;
  border-radius: 4px;
}
.sel-count { font-size: 13px; color: var(--text-secondary); margin-right: 8px; }

.table-view { 
  border: 1px solid var(--border); 
  border-radius: 8px; 
  overflow: hidden; 
  box-shadow: 0 1px 2px rgba(0,0,0,0.05);
  display: flex;
  flex-direction: column;
}
.table-view :deep(.el-table .cell) {
  display: flex;
  align-items: center;
  height: 100%;
}
.table-view :deep(.el-table__row) { height: 52px; }

/* Table Height Adjustment */
.table-view { 
  border: 1px solid var(--border); 
  border-radius: 8px; 
  overflow: hidden; 
  box-shadow: 0 1px 2px rgba(0,0,0,0.05);
  display: flex;
  flex-direction: column;
  height: 550px; /* Fixed height for dialog content */
}

/* Ensure no gap between table and pagination */
.table-view :deep(.el-table) {
  flex: 1; 
  border-bottom: none;
}
.table-view :deep(.el-table__inner-wrapper::before) {
  display: none; 
}

.pagination-bar {
  padding: 8px 16px;
  border-top: 1px solid var(--border);
  background: var(--bg-secondary);
  display: flex;
  justify-content: flex-end;
  flex-shrink: 0;
}

.code-text { font-family: 'JetBrains Mono', monospace; color: var(--text-secondary); font-size: 13px; }
.prio-tag { font-weight: 700; border: none; width: 32px; justify-content: center; }

/* Unified Font Styles */
.module-text {
  white-space: nowrap; 
  overflow: hidden;
  text-overflow: ellipsis;
  display: block;
  width: 100%;
  color: var(--text-primary);
  font-size: 13px;
}

.title-text { 
  font-weight: 400; /* Removed bold */
  color: var(--text-primary); 
  font-size: 13px; 
  
  white-space: nowrap; 
  overflow: hidden;
  text-overflow: ellipsis;
  display: block;
  width: 100%;
}

.desc-text { 
  white-space: nowrap; 
  overflow: hidden;
  text-overflow: ellipsis;
  color: #555; 
  font-size: 13px; 
  width: 100%;
  display: block;
}

.right-actions { display: flex; gap: 8px; }
.icon-btn { padding: 6px; font-size: 14px; width: 28px; height: 28px; }

.form-actions { display: flex; justify-content: flex-end; gap: 12px; margin-top: 20px; }

@media (max-width: 768px) {
  .stats-bar { display: none; }
}
</style>
