<template>
  <div class="case-library">
    <div class="page-header">
      <h2>用例库</h2>
      <div class="header-actions">
        <el-button :icon="Download" @click="showExport = true">导出</el-button>
        <el-button type="primary" :icon="Plus" @click="openCreate">新建用例</el-button>
      </div>
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
      </el-select>
      <el-button @click="resetFilters">重置</el-button>
      <el-tag v-if="generationBatch" type="success" effect="plain">
        批次：{{ generationBatch }}
      </el-tag>
      <el-button v-if="generationBatch" link type="primary" @click="clearBatchFilter">清空批次筛选</el-button>
      <div class="filter-stats">
        共 <strong>{{ total }}</strong> 条
        <template v-if="selectedIds.length">
          ，已选 <strong>{{ selectedIds.length }}</strong> 条
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
        row-key="id"
        max-height="calc(100vh - 320px)"
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
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="viewCase(row)">查看</el-button>
            <el-button link type="success" size="small" @click="editCase(row)">编辑</el-button>
            <el-button link type="danger" size="small" @click="deleteCase(row)">删除</el-button>
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
    <el-drawer v-model="showDetail" title="用例详情" size="600px">
      <div v-if="detailCase" class="case-detail">
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
      </div>
    </el-drawer>

    <!-- 新建/编辑弹窗 -->
    <el-dialog v-model="showCreate" :title="editing ? '编辑用例' : '新建用例'" width="680px">
      <el-form :model="caseForm" label-width="90px">
        <el-form-item label="用例标题" required>
          <el-input v-model="caseForm.title" placeholder="请输入用例标题" />
        </el-form-item>
        <el-form-item label="所属模块">
          <el-input v-model="caseForm.module" placeholder="如：登录、支付、订单" />
        </el-form-item>
        <el-form-item label="优先级">
          <el-select v-model="caseForm.case_level" style="width: 160px">
            <el-option label="P0 核心" value="P0" />
            <el-option label="P1 高优" value="P1" />
            <el-option label="P2 中优" value="P2" />
            <el-option label="P3 低优" value="P3" />
          </el-select>
        </el-form-item>
        <el-form-item label="测试类型">
          <el-select v-model="caseForm.test_type" style="width: 160px">
            <el-option label="功能测试" value="functional" />
            <el-option label="接口测试" value="api" />
            <el-option label="单元测试" value="unit" />
            <el-option label="回归测试" value="regression" />
          </el-select>
        </el-form-item>
        <el-form-item label="适用阶段">
          <el-select v-model="caseForm.stage" style="width: 160px">
            <el-option label="系统测试" value="system" />
            <el-option label="集成测试" value="integration" />
            <el-option label="回归测试" value="regression" />
            <el-option label="冒烟测试" value="smoke" />
          </el-select>
        </el-form-item>
        <el-form-item label="前置条件">
          <el-input v-model="caseForm.preconditions" type="textarea" :rows="2" placeholder="可选" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="caseForm.remarks" type="textarea" :rows="2" placeholder="可选" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreate = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveCase">{{ editing ? '保存修改' : '创建用例' }}</el-button>
      </template>
    </el-dialog>

    <!-- 导出弹窗 -->
    <el-dialog v-model="showExport" title="导出用例" width="400px">
      <el-form label-width="80px">
        <el-form-item label="导出格式">
          <el-radio-group v-model="exportFmt">
            <el-radio value="excel">Excel (.xlsx)</el-radio>
            <el-radio value="markdown">Markdown (.md)</el-radio>
            <el-radio value="csv">CSV (.csv)</el-radio>
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
import { useRoute, useRouter } from 'vue-router'
import { Plus, Download, Search } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { caseApi } from '@/api/cases'
import type { TestCase } from '@/api/types'
import type { TagProps } from 'element-plus'

const route = useRoute()
const router = useRouter()
const projectId = computed(() => Number(route.params.id))
const generationBatch = computed(() => route.query.batch ? String(route.query.batch) : '')
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
const ratingVal = ref(0)
const exporting = ref(false)
const saving = ref(false)
const exportFmt = ref('excel')
const exportScope = ref('all')
const caseForm = reactive({
  id: undefined as number | undefined,
  title: '',
  module: '',
  case_level: 'P1',
  test_type: 'functional',
  stage: 'system',
  preconditions: '',
  remarks: '',
})
const editing = computed(() => typeof caseForm.id === 'number')

const filters = reactive({
  keyword: '', test_type: '', case_level: '', status: ''
})

onMounted(fetchCases)
watch(() => route.query.batch, () => {
  page.value = 1
  fetchCases()
})

async function fetchCases() {
  loading.value = true
  try {
    const res = await caseApi.list({
      project_id: projectId.value,
      page: page.value,
      page_size: pageSize.value,
      generation_batch: generationBatch.value || undefined,
      ...filters,
    })
    cases.value = res.items
    total.value = res.total
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

function viewCase(c: TestCase) {
  detailCase.value = c
  ratingVal.value = c.rating || 0
  showDetail.value = true
}

function editCase(c: TestCase) {
  caseForm.id = c.id
  caseForm.title = c.title
  caseForm.module = c.module || ''
  caseForm.case_level = c.case_level
  caseForm.test_type = c.test_type
  caseForm.stage = c.stage
  caseForm.preconditions = c.preconditions || ''
  caseForm.remarks = c.remarks || ''
  showCreate.value = true
}

async function saveCase() {
  if (!caseForm.title.trim()) return ElMessage.warning('请输入用例标题')
  saving.value = true
  const payload = {
    title: caseForm.title.trim(),
    module: caseForm.module.trim() || undefined,
    case_level: caseForm.case_level,
    test_type: caseForm.test_type,
    stage: caseForm.stage,
    preconditions: caseForm.preconditions.trim() || undefined,
    remarks: caseForm.remarks.trim() || undefined,
  }
  try {
    if (editing.value) {
      await caseApi.update(caseForm.id as number, payload)
      ElMessage.success('用例更新成功')
    } else {
      await caseApi.create({ project_id: projectId.value, ...payload })
      ElMessage.success('用例创建成功')
    }
    showCreate.value = false
    resetCaseForm()
    fetchCases()
  } finally {
    saving.value = false
  }
}

function resetCaseForm() {
  caseForm.id = undefined
  caseForm.title = ''
  caseForm.module = ''
  caseForm.case_level = 'P1'
  caseForm.test_type = 'functional'
  caseForm.stage = 'system'
  caseForm.preconditions = ''
  caseForm.remarks = ''
}

function openCreate() {
  resetCaseForm()
  showCreate.value = true
}

async function deleteCase(c: TestCase) {
  await ElMessageBox.confirm(`确认删除「${c.title}」？`, '删除确认', { type: 'warning' })
  await caseApi.remove(c.id)
  ElMessage.success('删除成功')
  fetchCases()
}

async function batchDelete() {
  await ElMessageBox.confirm(`确认删除选中的 ${selectedIds.value.length} 条用例？`, '批量删除', { type: 'warning' })
  await caseApi.batchDelete(selectedIds.value)
  ElMessage.success('批量删除成功')
  selectedIds.value = []
  fetchCases()
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
    const ext = { excel: 'xlsx', markdown: 'md', csv: 'csv' }[exportFmt.value] || 'xlsx'
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
const statusType = (s: string): TagProps['type'] => {
  const map: Record<string, TagProps['type']> = {
    draft: 'info',
    pending_review: 'warning',
    reviewed: 'success',
    deprecated: 'danger',
  }
  return map[s] || 'info'
}

function clearBatchFilter() {
  const query = { ...route.query }
  delete query.batch
  router.replace({ query })
}
</script>

<style scoped>
.case-library { max-width: 1400px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { font-size: 22px; font-weight: 700; }
.header-actions { display: flex; gap: 8px; }

.filter-bar {
  display: flex; flex-wrap: wrap; gap: 10px; align-items: center;
  margin-bottom: 12px; padding: 14px 16px;
}
.filter-stats { margin-left: auto; font-size: 13px; color: var(--text-secondary); display: flex; align-items: center; gap: 6px; }

.table-wrap { padding: 0; overflow: hidden; }
.pagination { padding: 12px 16px; display: flex; justify-content: flex-end; }

.case-id { font-family: monospace; font-size: 12px; color: #6b7280; }

.case-detail { padding: 4px; }
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
</style>
