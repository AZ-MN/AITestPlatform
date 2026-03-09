<template>
  <div class="req-page">
    <div class="page-header">
      <div>
        <h2>需求管理</h2>
        <p>先检索/过滤需求，再进入解析与生成，减少重复点击。</p>
      </div>
      <div class="header-actions">
        <el-button :icon="Upload" @click="showUpload = true">上传文档</el-button>
        <el-button type="primary" :icon="Plus" @click="showText = true">手动输入</el-button>
      </div>
    </div>

    <div class="req-toolbar page-card">
      <el-input v-model="keyword" clearable placeholder="搜索标题..." style="width:240px" />
      <el-select v-model="statusFilter" clearable placeholder="全部状态" style="width:140px">
        <el-option label="已解析" value="parsed" />
        <el-option label="解析中" value="parsing" />
        <el-option label="失败" value="failed" />
      </el-select>
      <div class="toolbar-summary">共 {{ filteredRequirements.length }} 条</div>
    </div>

    <!-- 需求列表 -->
    <div v-if="!loading && filteredRequirements.length === 0" class="empty-state">
      <div class="empty-icon">📄</div>
      <h3>暂无需求</h3>
      <p>上传需求文档或手动输入需求，平台将自动解析需求点用于生成测试用例</p>
      <div style="display:flex;gap:12px;justify-content:center;margin-top:16px">
        <el-button type="primary" @click="showUpload = true">上传文档</el-button>
        <el-button @click="showText = true">手动输入</el-button>
      </div>
    </div>

    <el-table v-else v-loading="loading" :data="filteredRequirements" row-class-name="req-row">
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
      <el-table-column label="操作" width="280" fixed="right">
        <template #default="{ row }">
          <el-button size="small" type="primary" link @click="viewReq(row)">查看需求点</el-button>
          <el-button size="small" type="warning" link :loading="reparsingId === row.id" @click="openReparse(row)">重新解析</el-button>
          <el-button size="small" type="success" link
            @click="$router.push(`/projects/${projectId}/generate?req_id=${row.id}`)">
            生成用例
          </el-button>
          <el-button size="small" type="danger" link @click="deleteReq(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 上传文档弹窗 -->
    <el-dialog v-model="showUpload" title="上传需求文档" width="500px">
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
        <el-form-item v-if="uploadForm.useAi" label="AI模型">
          <el-select v-model="uploadForm.aiProvider" placeholder="选择模型供应商" style="width:100%">
            <el-option v-for="m in modelConfigs" :key="m.id" :value="m.provider"
              :label="`${m.provider} · ${m.model_name}${m.is_default ? '（默认）' : ''}`" />
          </el-select>
          <div v-if="!modelConfigs.length" class="form-tip">
            未检测到可用模型，请先到「模型设置」添加配置。
          </div>
        </el-form-item>
        <el-form-item label="解析提示词">
          <el-input v-model="uploadForm.parsePrompt" type="textarea" :rows="2" placeholder="可选：例如，按最小可测试步骤拆分，覆盖异常与边界场景" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showUpload = false">取消</el-button>
        <el-button type="primary" :loading="uploading" @click="handleUpload">上传并解析</el-button>
      </template>
    </el-dialog>

    <!-- 手动输入弹窗 -->
    <el-dialog v-model="showText" title="手动输入需求" width="600px">
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
        <el-form-item v-if="textForm.useAi" label="AI模型">
          <el-select v-model="textForm.aiProvider" placeholder="选择模型供应商" style="width:100%">
            <el-option v-for="m in modelConfigs" :key="m.id" :value="m.provider"
              :label="`${m.provider} · ${m.model_name}${m.is_default ? '（默认）' : ''}`" />
          </el-select>
          <div v-if="!modelConfigs.length" class="form-tip">
            未检测到可用模型，请先到「模型设置」添加配置。
          </div>
        </el-form-item>
        <el-form-item label="解析提示词">
          <el-input v-model="textForm.parsePrompt" type="textarea" :rows="2" placeholder="可选：例如，每条需求点仅保留一个可验证行为" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showText = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleTextSave">保存并解析</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showReparse" title="重新解析需求" width="560px">
      <el-form :model="reparseForm" label-width="90px">
        <el-form-item label="AI解析">
          <el-switch v-model="reparseForm.useAi" active-text="AI智能解析需求点" inactive-text="规则解析" />
        </el-form-item>
        <el-form-item v-if="reparseForm.useAi" label="AI模型">
          <el-select v-model="reparseForm.aiProvider" placeholder="选择模型供应商" style="width:100%">
            <el-option v-for="m in modelConfigs" :key="m.id" :value="m.provider"
              :label="`${m.provider} · ${m.model_name}${m.is_default ? '（默认）' : ''}`" />
          </el-select>
        </el-form-item>
        <el-form-item label="解析提示词">
          <el-input v-model="reparseForm.parsePrompt" type="textarea" :rows="3" placeholder="例如：按测试工程师视角拆分到最小可测试行为，优先保留可执行断言" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showReparse = false">取消</el-button>
        <el-button type="primary" :loading="reparsing" @click="handleReparse">开始重新解析</el-button>
      </template>
    </el-dialog>

    <!-- 需求点查看弹窗 -->
    <el-dialog v-model="showPoints" :title="`需求点 - ${currentReq?.title}`" width="760px" top="5vh">
      <div class="points-toolbar">
        <span class="points-count">共 {{ editablePoints.length }} 个需求点</span>
        <div style="display:flex;gap:8px">
          <el-radio-group v-model="pointViewMode" size="small" :disabled="editingPoints">
            <el-radio-button value="xmind">XMind视图</el-radio-button>
            <el-radio-button value="list">列表视图</el-radio-button>
          </el-radio-group>
          <el-button size="small" @click="exportXmind">导出XMind(OPML)</el-button>
          <el-button size="small" @click="toggleEditPoints">{{ editingPoints ? '完成编辑' : '编辑需求点' }}</el-button>
          <el-button v-if="editingPoints" size="small" @click="splitPointsFiner">细粒度拆分</el-button>
          <el-button v-if="editingPoints" size="small" type="primary" :loading="savingPoints" @click="savePoints">保存需求点</el-button>
          <el-button size="small" type="success"
            @click="$router.push(`/projects/${projectId}/generate?req_id=${currentReq?.id}`); showPoints=false">
            生成测试用例 →
          </el-button>
        </div>
      </div>
      <div v-if="pointViewMode === 'xmind' && !editingPoints" class="xmind-wrap">
        <div class="xmind-root">{{ currentReq?.title || '需求梳理' }}</div>
        <div class="xmind-modules">
          <div v-for="m in xmindTree" :key="m.module" class="xmind-module">
            <div class="xmind-module-title">{{ m.module }}（{{ m.points.length }}）</div>
            <div class="xmind-points">
              <div v-for="p in m.points" :key="p.id + p.title" class="xmind-point">
                <div class="xmind-point-title">{{ p.id }} {{ p.title }}</div>
                <div class="xmind-point-desc">{{ p.description }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div v-else class="points-list">
        <div v-for="(p, i) in editablePoints" :key="i" class="point-item">
          <div class="point-header">
            <template v-if="editingPoints">
              <el-input v-model="p.id" size="small" placeholder="需求ID" style="width:140px" />
              <el-select v-model="p.priority" size="small" style="width:110px">
                <el-option label="P0" value="P0" />
                <el-option label="P1" value="P1" />
                <el-option label="P2" value="P2" />
                <el-option label="P3" value="P3" />
              </el-select>
              <el-input v-model="p.module" size="small" placeholder="模块" style="width:160px" />
            </template>
            <template v-else>
              <span class="point-id">{{ p.id || `REQ-${i+1}` }}</span>
              <el-tag :class="`tag-${p.priority?.toLowerCase()}`" size="small">{{ p.priority }}</el-tag>
              <span class="point-module">{{ p.module }}</span>
            </template>
          </div>
          <template v-if="editingPoints">
            <el-input v-model="p.title" placeholder="需求点标题" style="margin-bottom:8px" />
            <el-input v-model="p.description" type="textarea" :rows="2" placeholder="需求点描述" />
            <el-input v-model="p.rulesText" type="textarea" :rows="2" placeholder="规则（每行一条）" style="margin-top:8px" />
          </template>
          <template v-else>
            <div class="point-title">{{ p.title }}</div>
            <div class="point-desc">{{ p.description }}</div>
            <div v-if="p.rules?.length" class="point-rules">
              <span v-for="r in p.rules" :key="r" class="rule-tag">{{ r }}</span>
            </div>
          </template>
          <div v-if="editingPoints" style="margin-top:8px">
            <el-button size="small" type="danger" link @click="removePoint(i)">删除该需求点</el-button>
          </div>
        </div>
      </div>
      <div v-if="editingPoints" style="margin-top:10px">
        <el-button size="small" @click="addPoint">+ 新增需求点</el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Plus, Upload } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { requirementApi } from '@/api/requirements'
import { modelApi } from '@/api/models'
import { taskApi } from '@/api/tasks'
import type { Requirement, RequirementPoint, AIModelConfig } from '@/api/types'

const route = useRoute()
const router = useRouter()
const projectId = computed(() => Number(route.params.id))
const requirements = ref<Requirement[]>([])
const keyword = ref('')
const statusFilter = ref<string>()
const loading = ref(false)
const uploading = ref(false)
const saving = ref(false)
const showUpload = ref(false)
const showText = ref(false)
const showPoints = ref(false)
const currentReq = ref<Requirement | null>(null)
const currentPoints = computed<RequirementPoint[]>(() => (currentReq.value?.parse_result as RequirementPoint[]) || [])
const editablePoints = ref<any[]>([])
const editingPoints = ref(false)
const savingPoints = ref(false)
const pointViewMode = ref<'xmind' | 'list'>('xmind')
const showReparse = ref(false)
const reparsing = ref(false)
const reparsingId = ref<number>()
const reparseTarget = ref<Requirement | null>(null)
const uploadFile = ref<File | null>(null)
const modelConfigs = ref<AIModelConfig[]>([])

const uploadForm = reactive({ title: '', useAi: true, aiProvider: '', parsePrompt: '' })
const textForm = reactive({ title: '', content: '', useAi: true, aiProvider: '', parsePrompt: '' })
const reparseForm = reactive({ useAi: true, aiProvider: '', parsePrompt: '' })
const xmindTree = computed(() => {
  const groups = new Map<string, any[]>()
  editablePoints.value.forEach((p: any) => {
    const moduleName = (p.module || '未分类模块').trim() || '未分类模块'
    if (!groups.has(moduleName)) groups.set(moduleName, [])
    groups.get(moduleName)!.push(p)
  })
  return [...groups.entries()].map(([module, points]) => ({ module, points }))
})
const filteredRequirements = computed(() => {
  const kw = keyword.value.trim().toLowerCase()
  return requirements.value.filter(r => {
    const keywordOk = !kw || r.title.toLowerCase().includes(kw)
    const statusOk = !statusFilter.value || r.status === statusFilter.value
    return keywordOk && statusOk
  })
})

onMounted(async () => {
  await Promise.all([fetchReqs(), fetchModels()])
})

async function fetchModels() {
  modelConfigs.value = await modelApi.list()
  const def = modelConfigs.value.find(m => m.is_default) || modelConfigs.value[0]
  if (def) {
    uploadForm.aiProvider = def.provider
    textForm.aiProvider = def.provider
    reparseForm.aiProvider = def.provider
  }
}

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
  if (uploadForm.useAi) {
    if (!uploadForm.aiProvider) return ElMessage.warning('请先选择AI模型供应商')
  }
  uploading.value = true
  const fd = new FormData()
  fd.append('file', uploadFile.value)
  fd.append('project_id', String(projectId.value))
  fd.append('title', uploadForm.title)
  fd.append('use_ai', String(uploadForm.useAi))
  if (uploadForm.useAi) fd.append('ai_provider', uploadForm.aiProvider)
  if (uploadForm.parsePrompt.trim()) fd.append('parse_prompt', uploadForm.parsePrompt.trim())
  try {
    await requirementApi.upload(fd)
    ElMessage.success('上传解析成功')
    showUpload.value = false
    uploadForm.title = ''
    uploadForm.parsePrompt = ''
    uploadForm.aiProvider = uploadForm.aiProvider || (modelConfigs.value.find(m => m.is_default)?.provider || modelConfigs.value[0]?.provider || '')
    uploadFile.value = null
    fetchReqs()
  } finally { uploading.value = false }
}

async function handleTextSave() {
  if (!textForm.title) return ElMessage.warning('请输入需求标题')
  if (!textForm.content.trim()) return ElMessage.warning('请输入需求内容')
  if (textForm.useAi && !textForm.aiProvider) return ElMessage.warning('请先选择AI模型供应商')
  saving.value = true
  try {
    await requirementApi.createText(
      { project_id: projectId.value, title: textForm.title, content: textForm.content },
      textForm.useAi,
      textForm.useAi ? textForm.aiProvider : undefined,
      textForm.parsePrompt.trim() || undefined
    )
    ElMessage.success('需求解析成功')
    showText.value = false
    Object.assign(textForm, {
      title: '',
      content: '',
      useAi: true,
      aiProvider: textForm.aiProvider || (modelConfigs.value.find(m => m.is_default)?.provider || modelConfigs.value[0]?.provider || ''),
      parsePrompt: ''
    })
    fetchReqs()
  } finally { saving.value = false }
}

function viewReq(req: Requirement) {
  currentReq.value = req
  editablePoints.value = normalizePoints(req.parse_result || [])
  editingPoints.value = false
  pointViewMode.value = 'xmind'
  showPoints.value = true
}

function toggleEditPoints() {
  editingPoints.value = !editingPoints.value
  if (editingPoints.value) pointViewMode.value = 'list'
  if (editingPoints.value && !editablePoints.value.length) {
    editablePoints.value = [newPoint(1)]
  }
}

function newPoint(index: number) {
  return {
    id: `REQ-${index}`,
    title: '',
    description: '',
    priority: 'P1',
    module: '',
    conditions: [] as string[],
    rules: [] as string[],
    rulesText: '',
  }
}

function normalizePoints(points: RequirementPoint[]) {
  return (points || []).map((p, i) => ({
    id: p.id || `REQ-${i + 1}`,
    title: p.title || '',
    description: p.description || '',
    priority: p.priority || 'P1',
    module: p.module || '',
    conditions: Array.isArray(p.conditions) ? p.conditions : [],
    rules: Array.isArray(p.rules) ? p.rules : [],
    rulesText: Array.isArray(p.rules) ? p.rules.join('\n') : '',
  }))
}

function addPoint() {
  editablePoints.value.push(newPoint(editablePoints.value.length + 1))
}

function removePoint(index: number) {
  editablePoints.value.splice(index, 1)
}

function openReparse(req: Requirement) {
  reparseTarget.value = req
  reparseForm.useAi = true
  reparseForm.parsePrompt = ''
  reparseForm.aiProvider = reparseForm.aiProvider || modelConfigs.value.find(m => m.is_default)?.provider || modelConfigs.value[0]?.provider || ''
  showReparse.value = true
}

async function handleReparse() {
  if (!reparseTarget.value) return
  if (reparseForm.useAi && !reparseForm.aiProvider) return ElMessage.warning('请先选择AI模型供应商')
  reparsing.value = true
  reparsingId.value = reparseTarget.value.id
  try {
    await taskApi.createReparse({
      requirement_id: reparseTarget.value.id,
      use_ai: reparseForm.useAi,
      ai_provider: reparseForm.useAi ? reparseForm.aiProvider : undefined,
      parse_prompt: reparseForm.parsePrompt.trim() || undefined,
    })
    showReparse.value = false
    ElMessage.success('重解析任务已入队，请到任务中心查看进度')
  } finally {
    reparsing.value = false
    reparsingId.value = undefined
  }
}

function splitFragments(text: string) {
  const normalized = text.replace(/[；;]/g, '。')
  return normalized
    .split(/。|\n|，|,|、|并且|同时|以及|或者|或|且/)
    .map(x => x.trim())
    .filter(x => x.length >= 8)
}

function splitPointsFiner() {
  const result: any[] = []
  let idx = 1
  editablePoints.value.forEach((p: any) => {
    const source = [p.description, ...(Array.isArray(p.rules) ? p.rules : []), p.rulesText]
      .filter(Boolean)
      .join('\n')
    const fragments = splitFragments(source)
    if (!fragments.length) {
      result.push({ ...p, id: `REQ-${idx++}` })
      return
    }
    fragments.forEach((frag, i) => {
      result.push({
        ...p,
        id: `REQ-${idx++}`,
        title: i === 0 ? p.title : `${p.title} - 子场景${i + 1}`,
        description: frag,
      })
    })
  })
  editablePoints.value = result
  ElMessage.success(`已细粒度拆分为 ${result.length} 个需求点`)
}

function xmlEscape(input: string) {
  return input
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;')
}

function exportXmind() {
  if (!editablePoints.value.length || !currentReq.value) return ElMessage.warning('暂无可导出的需求点')
  const reqTitle = xmlEscape(currentReq.value.title || '需求梳理')
  const items = editablePoints.value.map((p: any) => {
    const title = xmlEscape(`${p.id || ''} ${p.title || ''}`.trim())
    const desc = xmlEscape(p.description || '')
    return `<outline text="${title}"><outline text="${desc}" /></outline>`
  }).join('')
  const opml = `<?xml version="1.0" encoding="UTF-8"?>\n<opml version="2.0"><head><title>${reqTitle}</title></head><body><outline text="${reqTitle}">${items}</outline></body></opml>`
  const blob = new Blob([opml], { type: 'text/xml;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${currentReq.value.title || 'requirement'}.opml`
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('已导出OPML，可直接导入XMind')
}

async function savePoints() {
  if (!currentReq.value) return
  const points = editablePoints.value.map((p, i) => ({
    id: (p.id || `REQ-${i + 1}`).trim(),
    title: (p.title || '').trim(),
    description: (p.description || '').trim(),
    priority: p.priority || 'P1',
    module: (p.module || '').trim(),
    conditions: Array.isArray(p.conditions) ? p.conditions : [],
    rules: String(p.rulesText || '')
      .split('\n')
      .map((x: string) => x.trim())
      .filter(Boolean),
  }))
  if (points.some(p => !p.title || !p.description)) {
    return ElMessage.warning('请为每个需求点填写标题和描述')
  }
  savingPoints.value = true
  try {
    const updated = await requirementApi.update(currentReq.value.id, { parse_result: points })
    currentReq.value = updated
    const idx = requirements.value.findIndex(r => r.id === updated.id)
    if (idx >= 0) requirements.value[idx] = updated
    editablePoints.value = normalizePoints(updated.parse_result || [])
    editingPoints.value = false
    ElMessage.success('需求点已保存')
  } finally {
    savingPoints.value = false
  }
}

async function deleteReq(req: Requirement) {
  await ElMessageBox.confirm(`确认删除需求「${req.title}」？`, '删除确认', { type: 'warning' })
  await requirementApi.remove(req.id)
  ElMessage.success('删除成功')
  fetchReqs()
}

function fmtDate(s: string) {
  return new Date(s).toLocaleString('zh-CN', { dateStyle: 'short', timeStyle: 'short' })
}
</script>

<style scoped>
.req-page { max-width: 1200px; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 14px; }
.page-header h2 { font-size: 24px; font-weight: 700; }
.page-header p { font-size: 13px; color: var(--text-secondary); margin-top: 4px; }
.header-actions { display: flex; gap: 8px; }
.req-toolbar {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-bottom: 12px;
  padding: 14px;
}
.toolbar-summary { margin-left: auto; font-size: 12px; color: var(--text-secondary); }

.empty-state { text-align: center; padding: 60px 20px; background: #fff; border-radius: 12px; border: 1px solid var(--border); }
.empty-icon { font-size: 48px; margin-bottom: 12px; }
.empty-state h3 { font-size: 18px; margin-bottom: 8px; }
.empty-state p { color: var(--text-secondary); font-size: 14px; }

:deep(.req-row) { cursor: default; }

.points-toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.points-count { font-size: 13px; color: var(--text-secondary); }
.points-list { max-height: 65vh; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; }
.xmind-wrap {
  max-height: 65vh;
  overflow-y: auto;
  padding: 14px;
  border: 1px solid #e9edf8;
  border-radius: 10px;
  background: linear-gradient(180deg, #fbfcff 0%, #f7f9ff 100%);
}
.xmind-root {
  display: inline-block;
  padding: 8px 14px;
  border-radius: 999px;
  background: #4f6ef7;
  color: #fff;
  font-weight: 700;
  margin-bottom: 12px;
}
.xmind-modules { display: flex; flex-direction: column; gap: 12px; }
.xmind-module {
  border-left: 2px solid #cdd8ff;
  padding-left: 12px;
}
.xmind-module-title {
  font-size: 13px;
  font-weight: 700;
  color: #3b4fc4;
  margin-bottom: 8px;
}
.xmind-points { display: flex; flex-direction: column; gap: 8px; }
.xmind-point {
  border: 1px solid #dfe6ff;
  border-radius: 8px;
  background: #fff;
  padding: 8px 10px;
}
.xmind-point-title { font-size: 13px; font-weight: 600; color: #1f2937; margin-bottom: 4px; }
.xmind-point-desc { font-size: 12px; color: #6b7280; line-height: 1.5; }
.point-item { border: 1px solid var(--border); border-radius: 8px; padding: 12px 14px; }
.point-header { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.point-id { font-size: 11px; color: #9ca3af; font-family: monospace; }
.point-module { font-size: 11px; color: #9ca3af; }
.point-title { font-weight: 600; font-size: 14px; margin-bottom: 4px; }
.point-desc { font-size: 13px; color: var(--text-secondary); line-height: 1.5; }
.point-rules { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 6px; }
.rule-tag { font-size: 11px; background: #f3f4f6; color: #6b7280; padding: 2px 8px; border-radius: 4px; }
.form-tip { margin-top: 6px; font-size: 12px; color: #9ca3af; }
</style>
