<template>
  <div class="case-library">
    <div class="page-header">
      <div>
        <h2>用例库</h2>
        <div class="sub-title">支持批量评审、最小回归集筛选与多格式导出</div>
      </div>
      <div class="header-actions">
        <el-button :icon="Download" @click="showExport = true">导出</el-button>
        <el-button type="primary" :icon="Plus" @click="showCreate = true">新建用例</el-button>
      </div>
    </div>

    <div class="overview page-card">
      <span class="ov-pill">当前页 {{ cases.length }} 条</span>
      <span class="ov-pill">总量 {{ total }} 条</span>
      <span class="ov-pill">待评审 {{ pendingCount }} 条</span>
      <span class="ov-pill" v-if="selectedIds.length">已选 {{ selectedIds.length }} 条</span>
      <span class="ov-pill ov-warn" v-if="regressionMode">最小回归集模式</span>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar page-card">
      <el-input v-model="filters.keyword" placeholder="搜索用例标题..." clearable
        :prefix-icon="Search" style="width:220px" @change="fetchCases" />
      <el-select v-model="filters.test_type" placeholder="测试类型" clearable style="width:130px" @change="fetchCases">
        <el-option label="功能测试" value="functional" />
        <el-option label="接口测试" value="api" />
        <el-option label="单元测试" value="unit" />
        <el-option label="回归测试" value="regression" />
      </el-select>
      <el-select v-model="filters.case_level" placeholder="优先级" clearable style="width:110px" @change="fetchCases">
        <el-option label="P0 核心" value="P0" />
        <el-option label="P1 高优" value="P1" />
        <el-option label="P2 中优" value="P2" />
        <el-option label="P3 低优" value="P3" />
      </el-select>
      <el-select v-model="filters.status" placeholder="状态" clearable style="width:120px" @change="fetchCases">
        <el-option label="草稿" value="draft" />
        <el-option label="待评审" value="pending_review" />
        <el-option label="已评审" value="reviewed" />
        <el-option label="已作废" value="deprecated" />
      </el-select>
      <el-button @click="resetFilters">重置</el-button>
      <el-button type="warning" plain @click="loadMinimalRegression">最小回归集</el-button>
      <el-button v-if="regressionMode" @click="exitRegressionMode">恢复列表</el-button>
      <div class="filter-stats">
        共 <strong>{{ total }}</strong> 条
        <template v-if="selectedIds.length">
          ，已选 <strong>{{ selectedIds.length }}</strong> 条
          <el-button size="small" type="warning" link @click="batchSubmitReview">批量提审</el-button>
          <el-button size="small" type="success" link @click="batchApprove">批量通过</el-button>
          <el-button size="small" type="info" link @click="batchResetDraft">重置草稿</el-button>
          <el-button size="small" type="danger" link @click="batchDelete">批量删除</el-button>
        </template>
      </div>
    </div>

    <!-- 用例表格 -->
    <div class="page-card table-wrap">
      <el-table
        v-loading="loading"
        :data="cases"
        @selection-change="handleSelect"
        @row-click="handleCaseRowClick"
        row-key="id"
      >
        <el-table-column type="selection" width="44" />
        <el-table-column label="用例ID" prop="case_id" width="130" fixed>
          <template #default="{ row }">
            <span class="case-id">{{ row.case_id }}</span>
          </template>
        </el-table-column>
        <el-table-column label="标题" prop="title" min-width="260" show-overflow-tooltip />
        <el-table-column label="模块" prop="module" width="120" show-overflow-tooltip />
        <el-table-column label="优先级" width="80" align="center">
          <template #default="{ row }">
            <el-tag :class="`tag-${row.case_level?.toLowerCase()}`" size="small">{{ row.case_level }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="类型" width="90" align="center">
          <template #default="{ row }">
            <el-tag type="info" size="small">{{ typeLabel(row.test_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="来源" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.ai_generated ? 'primary' : 'warning'" size="small">
              {{ row.ai_generated ? 'AI' : '手动' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination">
        <el-pagination background layout="total, sizes, prev, pager, next"
          :total="total" v-model:current-page="page" v-model:page-size="pageSize"
          :page-sizes="[20, 50, 100]" @change="fetchCases" />
      </div>
    </div>

    <!-- 用例详情弹窗 -->
    <el-drawer v-model="showDetail" title="用例详情" size="600px" :close-on-click-modal="true">
      <div v-if="detailCase" class="case-detail">
        <div class="detail-top-actions">
          <el-tooltip :content="editingCase ? '取消编辑' : '编辑用例'" placement="top">
            <el-button text circle @click="toggleCaseEdit">
              <el-icon><Edit /></el-icon>
            </el-button>
          </el-tooltip>
          <el-tooltip content="删除用例" placement="top">
            <el-button text circle type="danger" @click="deleteCase(detailCase)">
              <el-icon><Delete /></el-icon>
            </el-button>
          </el-tooltip>
        </div>
        <div v-if="editingCase" class="case-edit-form">
          <el-form label-width="90px">
            <el-form-item label="标题"><el-input v-model="caseForm.title" /></el-form-item>
            <el-form-item label="模块"><el-input v-model="caseForm.module" /></el-form-item>
            <el-form-item label="优先级">
              <el-select v-model="caseForm.case_level" style="width:100%">
                <el-option label="P0" value="P0" /><el-option label="P1" value="P1" /><el-option label="P2" value="P2" /><el-option label="P3" value="P3" />
              </el-select>
            </el-form-item>
            <el-form-item label="状态">
              <el-select v-model="caseForm.status" style="width:100%">
                <el-option label="草稿" value="draft" /><el-option label="待评审" value="pending_review" /><el-option label="已评审" value="reviewed" />
              </el-select>
            </el-form-item>
            <el-form-item label="前置条件"><el-input v-model="caseForm.preconditions" type="textarea" :rows="2" /></el-form-item>
            <el-form-item label="备注"><el-input v-model="caseForm.remarks" type="textarea" :rows="2" /></el-form-item>
          </el-form>
        </div>
        <template v-else>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="用例ID">{{ detailCase.case_id }}</el-descriptions-item>
          <el-descriptions-item label="优先级">
            <el-tag :class="`tag-${detailCase.case_level?.toLowerCase()}`" size="small">{{ detailCase.case_level }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="所属模块">{{ detailCase.module }}</el-descriptions-item>
          <el-descriptions-item label="测试类型">{{ typeLabel(detailCase.test_type) }}</el-descriptions-item>
          <el-descriptions-item label="适用阶段">{{ stageLabel(detailCase.stage) }}</el-descriptions-item>
          <el-descriptions-item label="状态">{{ statusLabel(detailCase.status) }}</el-descriptions-item>
          <el-descriptions-item label="用例标题" :span="2">{{ detailCase.title }}</el-descriptions-item>
          <el-descriptions-item label="前置条件" :span="2">{{ detailCase.preconditions || '无' }}</el-descriptions-item>
        </el-descriptions>

        <div class="steps-section">
          <h4>操作步骤 & 预期结果</h4>
          <div v-for="(s, i) in (detailCase.steps || [])" :key="i" class="step-item">
            <div class="step-num">{{ s.step || i+1 }}</div>
            <div class="step-content">
              <div class="step-action">{{ s.action }}</div>
              <div class="step-expected">预期：{{ s.expected }}</div>
            </div>
          </div>
        </div>

        <div v-if="detailCase.remarks" class="remarks">
          <strong>备注：</strong>{{ detailCase.remarks }}
        </div>

        <!-- 评分 -->
        <div class="rating-section">
          <span>用例质量评分：</span>
          <el-rate v-model="ratingVal" @change="submitRating" />
        </div>
        <div class="detail-actions">
          <el-button v-if="detailCase.status === 'draft'" size="small" type="warning" @click="submitReview(detailCase)">提交评审</el-button>
          <el-button v-else-if="detailCase.status === 'pending_review'" size="small" type="success" @click="approveCase(detailCase)">评审通过</el-button>
          <el-button v-if="detailCase.status === 'pending_review'" size="small" @click="rejectCase(detailCase)">驳回</el-button>
        </div>
        <div class="review-log" v-if="reviewLogs.length">
          <h4>评审记录</h4>
          <div class="review-item" v-for="log in reviewLogs" :key="log.id">
            <div class="review-meta">{{ fmtDate(log.created_at) }} · {{ log.created_by_name || '用户' }} · {{ actionLabel(log.action) }}</div>
            <div class="review-desc" v-if="log.comment">{{ log.comment }}</div>
            <div class="review-desc" v-else-if="log.from_status || log.to_status">{{ statusLabel(log.from_status || '') }} → {{ statusLabel(log.to_status || '') }}</div>
          </div>
        </div>
        </template>
        <div v-if="editingCase" class="detail-actions">
          <el-button @click="toggleCaseEdit">取消</el-button>
          <el-button type="primary" :loading="savingCase" @click="saveCaseEdit">保存用例</el-button>
        </div>
      </div>
    </el-drawer>

    <!-- 导出弹窗 -->
    <el-dialog v-model="showExport" title="导出用例" width="400px" :close-on-click-modal="false">
      <el-form label-width="80px">
        <el-form-item label="导出格式">
          <el-radio-group v-model="exportFmt">
            <el-radio value="excel">Excel (.xlsx)</el-radio>
            <el-radio value="markdown">Markdown (.md)</el-radio>
            <el-radio value="csv">CSV (.csv)</el-radio>
            <el-radio value="postman">Postman (.json)</el-radio>
            <el-radio value="jmeter">JMeter (.jmx)</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="导出范围">
          <el-radio-group v-model="exportScope">
            <el-radio value="all">全部用例（{{ total }} 条）</el-radio>
            <el-radio v-if="selectedIds.length" value="selected">
              已选用例（{{ selectedIds.length }} 条）
            </el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showExport = false">取消</el-button>
        <el-button type="primary" :loading="exporting" @click="handleExport">导出</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { Plus, Download, Search, Delete, Edit } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { caseApi } from '@/api/cases'
import type { TestCase, CaseReviewLog } from '@/api/types'

const route = useRoute()
const projectId = computed(() => Number(route.params.id))
const cases = ref<TestCase[]>([])
const total = ref(0)
const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const selectedIds = ref<number[]>([])
const showDetail = ref(false)
const showCreate = ref(false)
const showExport = ref(false)
const detailCase = ref<TestCase | null>(null)
const reviewLogs = ref<CaseReviewLog[]>([])
const editingCase = ref(false)
const savingCase = ref(false)
const caseForm = reactive({
  title: '',
  module: '',
  case_level: 'P1',
  status: 'draft',
  preconditions: '',
  remarks: '',
})
const ratingVal = ref(0)
const exporting = ref(false)
const exportFmt = ref('excel')
const exportScope = ref('all')
const regressionMode = ref(false)
const pendingCount = computed(() => cases.value.filter(c => c.status === 'pending_review').length)

const filters = reactive({
  keyword: '', test_type: '', case_level: '', status: ''
})

onMounted(fetchCases)

async function fetchCases() {
  loading.value = true
  try {
    const res = await caseApi.list({
      project_id: projectId.value,
      page: page.value,
      page_size: pageSize.value,
      ...filters,
    })
    cases.value = res.items
    total.value = res.total
    regressionMode.value = false
  } finally { loading.value = false }
}

function handleSelect(rows: TestCase[]) {
  selectedIds.value = rows.map(r => r.id)
}

function resetFilters() {
  Object.assign(filters, { keyword: '', test_type: '', case_level: '', status: '' })
  page.value = 1
  fetchCases()
}

async function loadMinimalRegression() {
  const prompt = await ElMessageBox.prompt('可选：输入变更模块（逗号分隔）', '生成最小回归集', {
    confirmButtonText: '生成',
    cancelButtonText: '取消',
    inputPlaceholder: '如：登录,支付',
    closeOnClickModal: false,
    closeOnPressEscape: false,
  }).catch(() => null)
  if (!prompt) return
  loading.value = true
  try {
    const res = await caseApi.minimalRegression({
      project_id: projectId.value,
      changed_modules: prompt.value || undefined,
      limit: 50,
    })
    cases.value = res.items
    total.value = res.total
    regressionMode.value = true
    ElMessage.success(`已生成最小回归集，共 ${res.total} 条`)
  } finally { loading.value = false }
}

function exitRegressionMode() {
  fetchCases()
}

function viewCase(c: TestCase) {
  detailCase.value = c
  editingCase.value = false
  fillCaseForm(c)
  ratingVal.value = c.rating || 0
  showDetail.value = true
  loadReviews(c.id)
}

async function loadReviews(caseId: number) {
  reviewLogs.value = await caseApi.reviews(caseId)
}

function fillCaseForm(c: TestCase) {
  caseForm.title = c.title || ''
  caseForm.module = c.module || ''
  caseForm.case_level = c.case_level || 'P1'
  caseForm.status = c.status || 'draft'
  caseForm.preconditions = c.preconditions || ''
  caseForm.remarks = c.remarks || ''
}

function toggleCaseEdit() {
  if (!detailCase.value) return
  editingCase.value = !editingCase.value
  if (editingCase.value) fillCaseForm(detailCase.value)
}

function handleCaseRowClick(row: TestCase, column: any) {
  if (column?.type === 'selection') return
  viewCase(row)
}

async function deleteCase(c: TestCase) {
  await ElMessageBox.confirm(`确认删除「${c.title}」？`, '删除确认', {
    type: 'warning',
    closeOnClickModal: false,
    closeOnPressEscape: false,
  })
  await caseApi.remove(c.id)
  ElMessage.success('删除成功')
  if (detailCase.value?.id === c.id) showDetail.value = false
  fetchCases()
}

async function updateStatus(c: TestCase, status: 'draft' | 'pending_review' | 'reviewed' | 'deprecated', msg: string) {
  try {
    await caseApi.setStatus(c.id, status)
  } catch (e: any) {
    if (e?.response?.status === 404) {
      await caseApi.update(c.id, { status })
    } else {
      throw e
    }
  }
  ElMessage.success(msg)
  await fetchCases()
  if (detailCase.value?.id === c.id) {
    const latest = cases.value.find(item => item.id === c.id)
    if (latest) {
      detailCase.value = latest
      await loadReviews(c.id)
    }
  }
}

async function saveCaseEdit() {
  if (!detailCase.value) return
  savingCase.value = true
  try {
    const updated = await caseApi.update(detailCase.value.id, {
      title: caseForm.title,
      module: caseForm.module,
      case_level: caseForm.case_level,
      status: caseForm.status,
      preconditions: caseForm.preconditions,
      remarks: caseForm.remarks,
    })
    detailCase.value = updated
    await fetchCases()
    editingCase.value = false
    await loadReviews(updated.id)
    ElMessage.success('用例已更新')
  } finally {
    savingCase.value = false
  }
}

async function submitReview(c: TestCase) {
  await updateStatus(c, 'pending_review', '已提交评审')
}

async function approveCase(c: TestCase) {
  await updateStatus(c, 'reviewed', '评审通过')
}

async function rejectCase(c: TestCase) {
  await updateStatus(c, 'draft', '已驳回并退回草稿')
}

async function batchDelete() {
  await ElMessageBox.confirm(`确认删除选中的 ${selectedIds.value.length} 条用例？`, '批量删除', {
    type: 'warning',
    closeOnClickModal: false,
    closeOnPressEscape: false,
  })
  await caseApi.batchDelete(selectedIds.value)
  ElMessage.success('批量删除成功')
  selectedIds.value = []
  fetchCases()
}

async function batchSubmitReview() {
  try {
    await caseApi.batchSetStatus(selectedIds.value, 'pending_review')
  } catch (e: any) {
    if (e?.response?.status === 404) {
      await Promise.all(selectedIds.value.map(id => caseApi.update(id, { status: 'pending_review' })))
    } else {
      throw e
    }
  }
  ElMessage.success('已批量提交评审')
  selectedIds.value = []
  await fetchCases()
}

async function batchApprove() {
  try {
    await caseApi.batchSetStatus(selectedIds.value, 'reviewed')
  } catch (e: any) {
    if (e?.response?.status === 404) {
      await Promise.all(selectedIds.value.map(id => caseApi.update(id, { status: 'reviewed' })))
    } else {
      throw e
    }
  }
  ElMessage.success('已批量评审通过')
  selectedIds.value = []
  await fetchCases()
}

async function batchResetDraft() {
  try {
    await caseApi.batchSetStatus(selectedIds.value, 'draft')
  } catch (e: any) {
    if (e?.response?.status === 404) {
      await Promise.all(selectedIds.value.map(id => caseApi.update(id, { status: 'draft' })))
    } else {
      throw e
    }
  }
  ElMessage.success('已批量重置为草稿')
  selectedIds.value = []
  await fetchCases()
}

async function submitRating() {
  if (!detailCase.value) return
  await caseApi.rate(detailCase.value.id, { rating: ratingVal.value })
  ElMessage.success('评分已提交，感谢反馈')
}

async function handleExport() {
  exporting.value = true
  try {
    const payload = {
      project_id: projectId.value,
      format: exportFmt.value,
      case_ids: exportScope.value === 'selected' ? selectedIds.value : undefined,
    }
    const blob = await caseApi.export(payload)
    const ext = { excel: 'xlsx', markdown: 'md', csv: 'csv', postman: 'json', jmeter: 'jmx' }[exportFmt.value] || 'xlsx'
    const url = URL.createObjectURL(blob as unknown as Blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `test_cases.${ext}`
    a.click()
    URL.revokeObjectURL(url)
    showExport.value = false
    ElMessage.success('导出成功')
  } finally { exporting.value = false }
}

const typeLabel = (t: string) =>
  ({ functional: '功能', api: '接口', unit: '单元', regression: '回归' })[t] || t
const stageLabel = (s: string) =>
  ({ smoke: '冒烟', integration: '集成', system: '系统', regression: '回归' })[s] || s
const statusLabel = (s: string) =>
  ({ draft: '草稿', pending_review: '待评审', reviewed: '已评审', deprecated: '已作废' })[s] || s
const statusType = (s: string): 'success' | 'primary' | 'warning' | 'info' | 'danger' =>
  (({ draft: 'info', pending_review: 'warning', reviewed: 'success', deprecated: 'danger' } as const)[
    s as 'draft' | 'pending_review' | 'reviewed' | 'deprecated'
  ] || 'info')
const actionLabel = (a: string) =>
  ({ update: '编辑', status_change: '状态变更', rating: '评分反馈' } as Record<string, string>)[a] || a
const fmtDate = (s: string) => new Date(s).toLocaleString('zh-CN', { dateStyle: 'short', timeStyle: 'short' })
</script>

<style scoped>
.case-library { width: 100%; max-width: none; height: 100%; min-height: 0; display: flex; flex-direction: column; overflow: hidden; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { font-size: 22px; font-weight: 700; }
.sub-title { margin-top: 4px; color: var(--text-secondary); font-size: 13px; }
.header-actions { display: flex; gap: 8px; }
.overview {
  margin-bottom: 12px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  padding: 10px 12px;
}
.ov-pill {
  border: 1px solid #e5e7eb;
  background: #f8fafc;
  border-radius: 999px;
  padding: 2px 10px;
  font-size: 12px;
  color: #4b5563;
}
.ov-warn { color: #b45309; border-color: #fcd34d; background: #fffbeb; }

.filter-bar {
  display: flex; flex-wrap: wrap; gap: 10px; align-items: center;
  margin-bottom: 12px; padding: 14px 16px;
}
.filter-stats { margin-left: auto; font-size: 13px; color: var(--text-secondary); display: flex; align-items: center; gap: 6px; }

.table-wrap { padding: 0; overflow: hidden; flex: 1; min-height: 0; display: flex; flex-direction: column; }
.table-wrap :deep(.el-table) { flex: 1; }
.pagination { padding: 12px 16px; display: flex; justify-content: flex-end; }

.case-id { font-family: monospace; font-size: 12px; color: #6b7280; }

.case-detail { padding: 4px; }
.detail-top-actions {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 8px;
  gap: 6px;
}
.case-edit-form { padding-top: 4px; }
.detail-actions {
  display: flex;
  gap: 8px;
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid var(--border);
  justify-content: flex-end;
}
.steps-section { margin-top: 20px; }
.steps-section h4 { font-size: 14px; font-weight: 600; margin-bottom: 10px; }
.step-item { display: flex; gap: 10px; margin-bottom: 10px; }
.step-num {
  width: 24px; height: 24px; border-radius: 50%;
  background: #4f6ef7; color: #fff;
  font-size: 12px; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0; margin-top: 2px;
}
.step-action { font-size: 13px; margin-bottom: 3px; }
.step-expected { font-size: 12px; color: #059669; background: #f0fdf4; border-radius: 4px; padding: 3px 8px; }
.remarks { margin-top: 12px; font-size: 13px; color: var(--text-secondary); background: #f9fafb; border-radius: 6px; padding: 8px; }
.rating-section { margin-top: 16px; display: flex; align-items: center; gap: 10px; font-size: 13px; border-top: 1px solid var(--border); padding-top: 12px; }
.review-log { margin-top: 16px; border-top: 1px solid var(--border); padding-top: 12px; }
.review-log h4 { font-size: 14px; margin-bottom: 8px; }
.review-item { padding: 8px 0; border-bottom: 1px dashed var(--border); }
.review-meta { font-size: 12px; color: #6b7280; margin-bottom: 4px; }
.review-desc { font-size: 13px; }
</style>
