<template>
  <div class="case-library">
    <div class="page-desc">
       <p class="subtitle">集中管理测试用例，支持多维度筛选、评审与导出。</p>
    </div>

    <!-- Stats / Overview -->
    <div class="stats-bar">
      <div class="stat-item">
        <span class="stat-label">总用例数</span>
        <span class="stat-value">{{ total }}</span>
      </div>
      <div class="stat-divider"></div>
      <div class="stat-item">
        <span class="stat-label">待评审</span>
        <span class="stat-value warning">{{ pendingCount }}</span>
      </div>
      <div class="stat-divider"></div>
      <div class="stat-item" v-if="selectedIds.length">
        <span class="stat-label">已选择</span>
        <span class="stat-value primary">{{ selectedIds.length }}</span>
      </div>
      
      <div style="margin-left: auto; display: flex; gap: 12px;">
         <el-button :icon="Download" @click="showExport = true">导出数据</el-button>
         <el-button type="primary" :icon="Plus" @click="showCreate = true">新建用例</el-button>
      </div>
    </div>

    <!-- Filters & Toolbar -->
    <div class="toolbar-card">
      <div class="filter-group">
        <el-input 
          v-model="filters.keyword" 
          placeholder="搜索用例标题/ID..." 
          :prefix-icon="Search" 
          clearable 
          class="filter-input"
          @change="fetchCases" 
        />
        <el-select v-model="filters.test_type" placeholder="测试类型" clearable class="filter-select" @change="fetchCases">
          <el-option label="功能测试" value="functional" />
          <el-option label="接口测试" value="api" />
          <el-option label="单元测试" value="unit" />
        </el-select>
        <el-select v-model="filters.case_level" placeholder="优先级" clearable class="filter-select" @change="fetchCases">
          <el-option label="P0 核心" value="P0" />
          <el-option label="P1 高优" value="P1" />
          <el-option label="P2 中优" value="P2" />
          <el-option label="P3 低优" value="P3" />
        </el-select>
        <el-select v-model="filters.status" placeholder="状态" clearable class="filter-select" @change="fetchCases">
          <el-option label="草稿" value="draft" />
          <el-option label="待评审" value="pending_review" />
          <el-option label="已评审" value="reviewed" />
        </el-select>
        <el-button @click="resetFilters" :icon="Refresh" circle />
      </div>
      
      <div class="action-group">
        <transition name="el-fade-in">
          <div v-if="selectedIds.length" class="batch-actions">
            <span class="sel-count">已选 {{ selectedIds.length }} 项</span>
            <el-button type="primary" size="small" @click="handleBatchReview">提交评审</el-button>
            <el-button type="danger" size="small" plain @click="handleBatchDelete">批量删除</el-button>
          </div>
        </transition>
      </div>
    </div>

    <!-- Data Table -->
    <div class="table-container">
      <el-table
        v-loading="loading"
        :data="cases"
        @selection-change="handleSelect"
        @row-click="handleCaseRowClick"
        row-key="id"
        height="100%"
        stripe
        border
        class="cases-table"
      >
        <el-table-column type="selection" width="48" align="center" />
        <el-table-column label="ID" prop="case_id" width="140" fixed show-overflow-tooltip>
          <template #default="{ row }">
            <span class="mono-text">{{ row.case_id }}</span>
          </template>
        </el-table-column>
        <el-table-column label="标题" prop="title" min-width="300" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="case-title">{{ row.title }}</span>
          </template>
        </el-table-column>
        <el-table-column label="模块" prop="module" min-width="120" show-overflow-tooltip>
           <template #default="{ row }">
             <span class="module-text">{{ row.module || '-' }}</span>
           </template>
        </el-table-column>
        <el-table-column label="优先级" width="100" align="center" show-overflow-tooltip>
          <template #default="{ row }">
            <el-tag :type="priorityType(row.case_level)" size="small" effect="dark" class="prio-tag">{{ row.case_level }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="类型" width="100" align="center" show-overflow-tooltip>
          <template #default="{ row }">
            <el-tag type="info" size="small" effect="plain">{{ typeLabel(row.test_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="来源" width="90" align="center" show-overflow-tooltip>
          <template #default="{ row }">
            <el-tag :type="row.ai_generated ? 'primary' : 'warning'" size="small" effect="light" round>
              {{ row.ai_generated ? 'AI' : '人工' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100" align="center" show-overflow-tooltip>
          <template #default="{ row }">
             <div class="status-indicator">
                <span :class="['status-dot', row.status]"></span>
                {{ statusLabel(row.status) }}
             </div>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" align="center" fixed="right">
           <template #default="{ row }">
              <el-button :icon="Edit" circle size="small" @click.stop="editCase(row)" />
              <el-button :icon="Delete" circle size="small" type="danger" plain @click.stop="deleteCase(row)" />
           </template>
        </el-table-column>
      </el-table>
    </div>
    
    <div class="pagination-bar">
      <el-pagination 
        background 
        layout="total, sizes, prev, pager, next, jumper"
        :total="total" 
        v-model:current-page="page" 
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]" 
        @change="fetchCases" 
      />
    </div>

    <!-- Case Detail Drawer -->
    <el-drawer v-model="showDetail" title="用例详情" size="640px" destroy-on-close class="detail-drawer">
      <div v-if="detailCase" class="detail-content">
        <div class="detail-header-actions">
           <div class="detail-title-row">
             <span class="detail-id">{{ detailCase.case_id }}</span>
             <el-tag :type="statusType(detailCase.status)" size="small">{{ statusLabel(detailCase.status) }}</el-tag>
           </div>
           <div class="actions">
            <el-button-group v-if="!editingCase">
              <el-button :icon="Edit" @click="toggleCaseEdit">编辑</el-button>
              <el-button :icon="Delete" type="danger" plain @click="deleteCase(detailCase)">删除</el-button>
            </el-button-group>
           </div>
        </div>

        <div v-if="editingCase" class="edit-form-container">
          <el-form label-position="top" :model="caseForm">
            <el-form-item label="标题"><el-input v-model="caseForm.title" /></el-form-item>
            <el-row :gutter="16">
               <el-col :span="12"><el-form-item label="模块"><el-input v-model="caseForm.module" /></el-form-item></el-col>
               <el-col :span="12">
                  <el-form-item label="优先级">
                    <el-select v-model="caseForm.case_level" style="width:100%">
                      <el-option v-for="l in ['P0','P1','P2','P3']" :key="l" :label="l" :value="l"/>
                    </el-select>
                  </el-form-item>
               </el-col>
            </el-row>
            <el-form-item label="前置条件"><el-input v-model="caseForm.preconditions" type="textarea" :rows="3" /></el-form-item>
            <el-form-item label="备注"><el-input v-model="caseForm.remarks" type="textarea" :rows="2" /></el-form-item>
            <div class="form-actions">
              <el-button @click="toggleCaseEdit">取消</el-button>
              <el-button type="primary" :loading="savingCase" @click="saveCaseEdit">保存</el-button>
            </div>
          </el-form>
        </div>

        <template v-else>
          <div class="detail-section">
            <h3 class="detail-title">{{ detailCase.title }}</h3>
            <div class="meta-grid">
               <div class="meta-item"><label>模块</label><span>{{ detailCase.module }}</span></div>
               <div class="meta-item"><label>类型</label><span>{{ typeLabel(detailCase.test_type) }}</span></div>
               <div class="meta-item"><label>阶段</label><span>{{ stageLabel(detailCase.stage) }}</span></div>
               <div class="meta-item"><label>优先级</label><span :class="['priority-badge', `p-${detailCase.case_level?.toLowerCase()}`]">{{ detailCase.case_level }}</span></div>
            </div>
            
            <div class="info-block" v-if="detailCase.preconditions">
              <h4>前置条件</h4>
              <p>{{ detailCase.preconditions }}</p>
            </div>

            <div class="steps-block">
              <h4>执行步骤 & 预期结果</h4>
              <div v-for="(s, i) in (detailCase.steps || [])" :key="i" class="step-row">
                <div class="step-index">{{ s.step || i+1 }}</div>
                <div class="step-body">
                  <div class="step-desc">{{ s.action }}</div>
                  <div class="step-expect">
                    <el-icon><CircleCheck /></el-icon>
                    预期：{{ s.expected }}
                  </div>
                </div>
              </div>
            </div>
            
            <div class="info-block" v-if="detailCase.remarks">
               <h4>备注</h4>
               <p>{{ detailCase.remarks }}</p>
            </div>
          </div>

          <div class="review-actions-bar">
             <div class="rating-box">
                <span>质量评分：</span>
                <el-rate v-model="ratingVal" @change="submitRating" />
             </div>
             <div class="btn-group">
                <el-button v-if="detailCase.status === 'draft'" type="primary" plain @click="submitReview(detailCase)">提交评审</el-button>
                <el-button v-else-if="detailCase.status === 'pending_review'" type="success" @click="approveCase(detailCase)">通过</el-button>
                <el-button v-if="detailCase.status === 'pending_review'" type="danger" plain @click="rejectCase(detailCase)">驳回</el-button>
             </div>
          </div>

          <div class="history-block" v-if="reviewLogs.length">
            <h4>变更记录</h4>
            <div class="timeline">
               <div v-for="log in reviewLogs" :key="log.id" class="timeline-item">
                  <div class="timeline-dot"></div>
                  <div class="timeline-content">
                     <div class="log-header">
                       <span class="log-user">{{ log.created_by_name || '用户' }}</span>
                       <span class="log-action">{{ actionLabel(log.action) }}</span>
                       <span class="log-time">{{ fmtDate(log.created_at) }}</span>
                     </div>
                     <div class="log-detail" v-if="log.comment">{{ log.comment }}</div>
                     <div class="log-detail" v-else-if="log.from_status || log.to_status">
                        {{ statusLabel(log.from_status || '') }} ➝ {{ statusLabel(log.to_status || '') }}
                     </div>
                  </div>
               </div>
            </div>
          </div>
        </template>
      </div>
    </el-drawer>

    <!-- Export Dialog -->
    <el-dialog v-model="showExport" title="导出用例" width="480px" align-center>
      <el-form label-position="top">
        <el-form-item label="导出格式">
          <div class="format-grid">
             <div 
               v-for="fmt in ['excel', 'markdown', 'csv', 'postman', 'jmeter']" 
               :key="fmt"
               :class="['format-card', { active: exportFmt === fmt }]"
               @click="exportFmt = fmt"
             >
                <span class="fmt-name">{{ fmt.toUpperCase() }}</span>
             </div>
          </div>
        </el-form-item>
        <el-form-item label="导出范围">
          <el-radio-group v-model="exportScope">
            <el-radio value="all" border>全部 ({{ total }})</el-radio>
            <el-radio value="selected" border :disabled="!selectedIds.length">选中 ({{ selectedIds.length }})</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showExport = false">取消</el-button>
        <el-button type="primary" :loading="exporting" @click="handleExport">开始导出</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { Plus, Download, Search, Delete, Edit, Refresh, ArrowDown, CircleCheck } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { caseApi } from '@/api/cases'
import type { TestCase, CaseReviewLog } from '@/api/types'

const route = useRoute()
const projectId = computed(() => {
  const n = Number(route.params.id)
  return isNaN(n) ? 0 : n
})

// State
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
const exporting = ref(false)
const exportFmt = ref('excel')
const exportScope = ref('all')
const ratingVal = ref(0)

const filters = reactive({
  keyword: '', test_type: '', case_level: '', status: ''
})

const caseForm = reactive({
  title: '', module: '', case_level: 'P1', status: 'draft', preconditions: '', remarks: ''
})

// Computed
const pendingCount = computed(() => cases.value.filter(c => c.status === 'pending_review').length)

// Lifecycle
onMounted(() => {
  if (projectId.value) fetchCases()
})

// Actions
async function fetchCases() {
  if (!projectId.value) return
  loading.value = true
  try {
    const res = await caseApi.list({
      project_id: projectId.value,
      page: page.value,
      page_size: pageSize.value,
      ...filters,
    })
    cases.value = res.items || []
    total.value = res.total || 0
  } catch (err) {
    console.error('Fetch cases failed:', err)
    ElMessage.error('获取用例列表失败')
  } finally { 
    loading.value = false 
  }
}

function handleSelect(rows: TestCase[]) {
  selectedIds.value = rows.map(r => r.id)
}

function resetFilters() {
  Object.assign(filters, { keyword: '', test_type: '', case_level: '', status: '' })
  page.value = 1
  fetchCases()
}

// Bulk Actions
function handleBatchCommand(cmd: string) {
  if (cmd === 'review') handleBatchReview()
  if (cmd === 'approve') batchApprove()
  if (cmd === 'reset') batchResetDraft()
  if (cmd === 'delete') handleBatchDelete()
}

async function handleBatchDelete() {
  try {
    await ElMessageBox.confirm(`确定删除选中的 ${selectedIds.value.length} 条用例吗？`, '批量删除', { type: 'warning' })
    await caseApi.batchDelete(selectedIds.value)
    ElMessage.success('删除成功')
    selectedIds.value = []
    fetchCases()
  } catch(e) {}
}

async function handleBatchReview() {
  await batchUpdateStatus('pending_review', '已批量提交评审')
}
async function batchApprove() {
  await batchUpdateStatus('reviewed', '已批量通过')
}
async function batchResetDraft() {
  await batchUpdateStatus('draft', '已批量重置为草稿')
}

async function batchUpdateStatus(status: string, msg: string) {
  try {
     // Try batch API if available, else sequential (mocking batch behavior)
    try {
      await caseApi.batchSetStatus(selectedIds.value, status)
    } catch {
       await Promise.all(selectedIds.value.map(id => caseApi.update(id, { status })))
    }
    ElMessage.success(msg)
    selectedIds.value = []
    fetchCases()
  } catch (e) { ElMessage.error('操作失败') }
}

// Detail & Edit
function handleCaseRowClick(row: TestCase, column: any) {
  if (column?.type === 'selection') return
  viewCase(row)
}

function viewCase(c: TestCase) {
  detailCase.value = c
  editingCase.value = false
  fillCaseForm(c)
  ratingVal.value = c.rating || 0
  showDetail.value = true
  loadReviews(c.id)
}


function fillCaseForm(c: TestCase) {
  caseForm.title = c.title || ''
  caseForm.module = c.module || ''
  caseForm.case_level = c.case_level || 'P1'
  caseForm.status = c.status || 'draft'
  caseForm.preconditions = c.preconditions || ''
  caseForm.remarks = c.remarks || ''
}

function editCase(row: TestCase) {
  detailCase.value = row
  showDetail.value = true
  editingCase.value = true
  fillCaseForm(row)
  loadReviews(row.id)
}

function toggleCaseEdit() {
  if (!detailCase.value) return
  editingCase.value = !editingCase.value
  if (editingCase.value) {
    if (detailCase.value) {
      Object.assign(caseForm, {
        title: detailCase.value.title,
        module: detailCase.value.module,
        case_level: detailCase.value.case_level,
        status: detailCase.value.status,
        preconditions: detailCase.value.preconditions,
        remarks: detailCase.value.remarks
      })
    }
  }
}

async function saveCaseEdit() {
  if (!detailCase.value) return
  savingCase.value = true
  try {
    await caseApi.update(detailCase.value.id, caseForm)
    ElMessage.success('保存成功')
    editingCase.value = false
    fetchCases()
    // Refresh detail
    const res = await caseApi.get(detailCase.value.id)
    detailCase.value = res
  } catch (e) {
    ElMessage.error('保存失败')
  } finally {
    savingCase.value = false
  }
}

function deleteCase(row: TestCase) {
  ElMessageBox.confirm('确定删除该用例吗？', '提示', { type: 'warning' })
    .then(async () => {
      await caseApi.remove(row.id)
      ElMessage.success('删除成功')
      fetchCases()
      if (detailCase.value?.id === row.id) showDetail.value = false
    })
    .catch(() => {})
}


// Single Status Update
async function updateStatus(c: TestCase, status: string, msg: string) {
   try {
     await caseApi.setStatus(c.id, status)
     ElMessage.success(msg)
     fetchCases()
     if (detailCase.value?.id === c.id) {
        // Refresh
        const res = await caseApi.get(c.id)
        detailCase.value = res
        loadReviews(c.id)
     }
   } catch { ElMessage.error('操作失败') }
}

async function submitReview(c: TestCase) { updateStatus(c, 'pending_review', '已提交评审') }
async function approveCase(c: TestCase) { updateStatus(c, 'reviewed', '评审通过') }
async function rejectCase(c: TestCase) { updateStatus(c, 'draft', '已驳回') }

async function submitRating() {
  if (!detailCase.value) return
  await caseApi.rate(detailCase.value.id, { rating: ratingVal.value })
  ElMessage.success('已评分')
}

async function loadReviews(id: number) {
  try {
    reviewLogs.value = await caseApi.reviews(id)
  } catch(e) { reviewLogs.value = [] }
}

// Export
async function handleExport() {
  exporting.value = true
  try {
    const blob = await caseApi.export({ 
      project_id: projectId.value, 
      format: exportFmt.value, 
      case_ids: exportScope.value === 'selected' ? selectedIds.value : undefined 
    })
    // Mock download
    const url = URL.createObjectURL(blob as any)
    const a = document.createElement('a')
    a.href = url
    a.download = `cases_${projectId.value}.${exportFmt.value === 'excel' ? 'xlsx' : 'txt'}`
    a.click()
    showExport.value = false
    ElMessage.success('导出成功')
  } catch(e) { ElMessage.error('导出失败') }
  finally { exporting.value = false }
}

// Utils
const typeLabel = (t: string) => ({ functional: '功能', api: '接口', unit: '单元', regression: '回归' })[t] || t
const priorityType = (l: string) => {
  if (!l) return 'info'
  const map: any = { P0: 'danger', P1: 'warning', P2: 'warning', P3: 'info' }
  return map[l.toUpperCase()] || 'info'
}
const stageLabel = (s: string) => ({ smoke: '冒烟', integration: '集成', system: '系统' })[s] || s
const statusLabel = (s: string) => ({ draft: '草稿', pending_review: '待评审', reviewed: '已评审', deprecated: '已作废' })[s] || s
const statusType = (s: string): any => ({ draft: 'info', pending_review: 'warning', reviewed: 'success', deprecated: 'danger' })[s] || 'info'
const actionLabel = (a: string) => ({ update: '编辑', status_change: '状态变更', rating: '评分' })[a] || a
const fmtDate = (s: string) => new Date(s).toLocaleString('zh-CN', { dateStyle: 'short', timeStyle: 'short' })
</script>

<style scoped>
.case-library {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  max-width: 100%;
}

.page-desc {
  height: 28px;
  display: flex;
  align-items: center;
  margin-bottom: 12px;
  flex-shrink: 0;
  padding: 0;
}
.subtitle { color: var(--text-secondary); font-size: 14px; margin: 0; }

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
.stat-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.stat-label { font-size: 12px; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.05em; }
.stat-value { font-size: 20px; font-weight: 700; color: var(--text-primary); line-height: 1; }
.stat-value.warning { color: #f59e0b; }
.stat-value.primary { color: var(--primary); }
.stat-divider { width: 1px; height: 24px; background: var(--border); margin: 0 24px; }

/* Toolbar */
.toolbar-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  flex-shrink: 0;
  flex-wrap: wrap;
  gap: 16px;
}
.filter-group { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
.filter-input { width: 220px; }
.filter-select { width: 140px; }

/* Batch Actions */
.batch-actions {
  display: flex;
  align-items: center; /* Ensure vertical centering */
  justify-content: center; /* Add if needed, but flex-start is usually default */
  height: 32px; /* Set fixed height for better alignment */
  gap: 12px;
  background: var(--bg-secondary);
  padding: 0 12px;
  border-radius: 4px;
  border: 1px solid var(--border);
}
.sel-count { 
  font-size: 13px; 
  color: var(--text-secondary); 
  margin-right: 16px; 
  line-height: 1; /* Remove line-height offset */
  display: flex;
  align-items: center;
}

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
.mono-text { font-family: 'JetBrains Mono', Consolas, monospace; font-size: 13px; }
.case-title { font-weight: 500; color: var(--text-primary); }
.priority-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 700;
}
.priority-badge.p-p0 { background: #fee2e2; color: #ef4444; }
.priority-badge.p-p1 { background: #ffedd5; color: #f97316; }
.priority-badge.p-p2 { background: #fef3c7; color: #d97706; }
.priority-badge.p-p3 { background: #f3f4f6; color: #6b7280; }

.status-indicator { display: flex; align-items: center; justify-content: center; gap: 6px; font-size: 13px; }
.status-dot { width: 6px; height: 6px; border-radius: 50%; background: #9ca3af; }
.status-dot.reviewed { background: #10b981; }
.status-dot.pending_review { background: #f59e0b; }
.status-dot.deprecated { background: #ef4444; }

.pagination-bar {
  padding: 16px 0;
  display: flex;
  justify-content: flex-end;
  flex-shrink: 0;
}

/* Drawer Styles */
.detail-content { padding: 20px; }
.detail-header-actions { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.detail-title-row { display: flex; gap: 12px; align-items: center; }
.detail-id { font-family: monospace; font-size: 18px; font-weight: 700; color: var(--text-primary); }

.detail-title { font-size: 20px; margin-bottom: 20px; line-height: 1.4; }
.meta-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; margin-bottom: 24px; background: var(--bg-secondary); padding: 16px; border-radius: 8px; }
.meta-item { display: flex; flex-direction: column; gap: 4px; }
.meta-item label { font-size: 12px; color: var(--text-secondary); }
.meta-item span { font-weight: 500; }

.info-block { margin-bottom: 24px; }
.info-block h4 { font-size: 14px; font-weight: 700; margin-bottom: 8px; color: var(--text-primary); }
.info-block p { font-size: 14px; line-height: 1.6; color: var(--text-primary); }

.steps-block { margin-bottom: 24px; }
.step-row { display: flex; gap: 16px; margin-bottom: 16px; }
.step-index { width: 24px; height: 24px; background: var(--primary); color: #fff; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700; flex-shrink: 0; margin-top: 2px; }
.step-body { flex: 1; background: var(--bg-secondary); padding: 12px; border-radius: 8px; }
.step-desc { font-size: 14px; margin-bottom: 8px; font-weight: 500; }
.step-expect { font-size: 13px; color: #059669; display: flex; align-items: center; gap: 6px; }

.review-actions-bar { border-top: 1px solid var(--border); padding-top: 20px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.rating-box { display: flex; align-items: center; gap: 12px; font-size: 14px; }

.history-block h4 { margin-bottom: 16px; font-size: 14px; font-weight: 700; }
.timeline-item { position: relative; padding-left: 20px; margin-bottom: 16px; border-left: 2px solid var(--border); }
.timeline-dot { position: absolute; left: -5px; top: 6px; width: 8px; height: 8px; border-radius: 50%; background: var(--text-secondary); }
.log-header { font-size: 12px; color: var(--text-secondary); margin-bottom: 4px; display: flex; gap: 8px; }
.log-user { font-weight: 600; color: var(--text-primary); }
.log-detail { font-size: 13px; }

/* Export Dialog */
.format-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.format-card { border: 1px solid var(--border); padding: 12px; border-radius: 8px; text-align: center; cursor: pointer; transition: all 0.2s; }
.format-card:hover { border-color: var(--primary); background: var(--bg-secondary); }
.format-card.active { border-color: var(--primary); background: var(--primary-light); color: var(--primary); font-weight: 700; }
.fmt-name { font-size: 13px; }
.text-danger { color: var(--danger); }

@media (max-width: 768px) {
  .toolbar-card { flex-direction: column; align-items: stretch; }
  .filter-group { flex-direction: column; align-items: stretch; }
  .filter-input, .filter-select { width: 100%; }
  .stats-bar { display: none; }
}
</style>
