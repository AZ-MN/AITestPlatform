<template>
  <div class="generate-page">
    <div class="page-header">
      <div>
        <h2>智能生成测试用例</h2>
        <div class="sub-title">在当前页面完成配置、生成与结果查看，减少跨模块跳转</div>
      </div>
    </div>

    <div class="generate-layout">
      <div class="left-column">
      <!-- 左：主流程配置 -->
      <div class="config-panel page-card">
        <div class="panel-title-row">
          <h3>生成流程配置</h3>
          <el-tooltip content="高级参数配置" placement="top">
            <el-button class="advanced-icon-btn" circle @click="advancedDialogVisible = true">
              <el-icon><Setting /></el-icon>
            </el-button>
          </el-tooltip>
        </div>
        <div class="config-body">
          <el-alert
            v-if="!modelConfigs.length"
            title="当前未配置 AI 模型，将使用规则引擎生成可用用例"
            type="warning"
            show-icon
            :closable="false"
            style="margin-bottom:12px"
          />

          <div class="section-label"><span class="sec-index">1</span>选择模型<span class="required-mark">*</span></div>
          <el-select v-model="config.ai_provider" placeholder="请选择用于生成的AI模型" style="width:100%">
            <el-option v-for="m in modelConfigs" :key="m.id" :value="m.provider"
              :label="`${providerName(m.provider)} · ${m.model_name}`" />
            <el-option v-if="!modelConfigs.length" value="" label="（请先在设置中添加AI模型）" disabled />
          </el-select>

          <div class="section-label"><span class="sec-index">2</span>选择需求来源<span class="required-mark">*</span></div>
          <el-select v-model="config.requirement_id" placeholder="选择已解析的需求" clearable style="width:100%"
            @change="onReqChange">
            <el-option v-for="r in requirements" :key="r.id" :label="r.title" :value="r.id" />
          </el-select>

          <div class="section-label"><span class="sec-index">3</span>选择覆盖模块</div>
          <el-select v-model="config.module_filter" placeholder="全部模块" clearable style="width:100%">
            <el-option v-for="m in modules" :key="m" :label="m" :value="m" />
          </el-select>

          <div class="section-label"><span class="sec-index">4</span>选择测试类型</div>
          <el-radio-group v-model="config.test_type" class="type-group">
            <el-radio-button value="functional">功能测试</el-radio-button>
            <el-radio-button value="api">接口测试</el-radio-button>
            <el-radio-button value="unit">单元测试</el-radio-button>
          </el-radio-group>

          <div class="section-label"><span class="sec-index">5</span>选择用例颗粒度</div>
          <el-radio-group v-model="config.granularity">
            <el-radio value="coarse">粗（按流程）</el-radio>
            <el-radio value="medium">中（按功能点）</el-radio>
            <el-radio value="fine">细（按单一场景）</el-radio>
          </el-radio-group>

          <div class="section-label"><span class="sec-index">6</span>用例提示词<span class="required-mark">*</span></div>
          <el-input
            v-model="config.case_prompt"
            type="textarea"
            :rows="4"
            placeholder="请描述你期望的用例风格与重点，例如：按资深测试工程师思路，优先覆盖核心链路、异常流程和边界条件，步骤简洁明确。"
          />

          <div class="section-label"><span class="sec-index">7</span>选择覆盖场景</div>
          <el-checkbox-group v-model="config.cover_scenarios" class="scenario-group">
            <el-checkbox value="normal">正常流程</el-checkbox>
            <el-checkbox value="exception">异常场景</el-checkbox>
            <el-checkbox value="boundary">边界值</el-checkbox>
            <el-checkbox value="permission">权限控制</el-checkbox>
            <el-checkbox value="compatibility">兼容性</el-checkbox>
            <el-checkbox value="security">数据安全</el-checkbox>
          </el-checkbox-group>
        </div>

        <div class="config-footer">
          <div class="footer-actions">
            <el-button size="default" @click="resetConfig">重置</el-button>
            <el-button type="primary" size="default" :loading="generating" :disabled="!canGenerate"
              @click="handleGenerate">
              <el-icon v-if="!generating"><MagicStick /></el-icon>
              {{ generating ? 'AI 生成中...' : '开始生成' }}
            </el-button>
          </div>
          <div class="footer-hint">模型与需求选择完成后即可生成</div>
          <div v-if="lastResult" class="result-summary">
            <div class="result-line">生成完成：{{ lastResult.total }} 条 · {{ lastResult.elapsed_seconds }}s</div>
          </div>
        </div>
      </div>

      <el-dialog v-model="advancedDialogVisible" title="高级参数配置" width="620px" class="advanced-dialog" :close-on-click-modal="false">
        <div class="advanced-dialog-body">
          <div class="advanced-summary">
            <div>
              <div class="advanced-title">生成风格微调</div>
              <div class="advanced-sub">选择预设风格或手动拖动滑杆，立即应用到本次生成。</div>
            </div>
            <el-tag type="primary" effect="light">{{ temperatureLabel }}</el-tag>
          </div>
          <div class="preset-grid">
            <button type="button" class="preset-card" :class="{ active: config.temperature === 0.2 }" @click="applyTemperature(0.2)">
              <span class="preset-name">稳健</span>
              <span class="preset-desc">结构清晰、保守严谨</span>
            </button>
            <button type="button" class="preset-card" :class="{ active: config.temperature === 0.5 }" @click="applyTemperature(0.5)">
              <span class="preset-name">均衡</span>
              <span class="preset-desc">覆盖与创造性平衡</span>
            </button>
            <button type="button" class="preset-card" :class="{ active: config.temperature === 0.8 }" @click="applyTemperature(0.8)">
              <span class="preset-name">探索</span>
              <span class="preset-desc">更多发散场景探索</span>
            </button>
          </div>
          <div class="advanced-item">
            <div class="temp-row">
              <span>创造性（Temperature）</span>
              <span class="temp-val">{{ config.temperature.toFixed(1) }}</span>
            </div>
            <el-slider v-model="config.temperature" :min="0" :max="1" :step="0.1" :marks="tempMarks" />
            <div class="advanced-tip">低温度更稳定，高温度更发散；建议先用预设再微调。</div>
          </div>
        </div>
        <template #footer>
          <div class="advanced-footer">
            <el-button @click="resetAdvanced">恢复默认</el-button>
            <el-button type="primary" @click="advancedDialogVisible = false">完成</el-button>
          </div>
        </template>
      </el-dialog>
      </div>

      <!-- 右：需求点预览 -->
      <div class="preview-panel page-card">
        <div class="preview-header">
          <h3>需求点预览</h3>
          <span class="preview-count">{{ filteredPoints.length }} 个</span>
        </div>
        <div class="preview-body">
          <div v-if="!filteredPoints.length" class="preview-empty">
            <p>{{ requirements.length ? '请先在左侧选择需求来源' : '当前项目还没有需求，请先在需求管理中录入需求' }}</p>
          </div>
          <el-tree
            v-else
            :data="mindmapData"
            node-key="id"
            default-expand-all
            :expand-on-click-node="false"
            class="mindmap-tree"
          >
            <template #default="{ data }">
              <div :class="['mind-node', `kind-${data.kind}`]">
                <div class="mind-line">
                  <span class="node-label">{{ data.label }}</span>
                  <el-tag v-if="data.priority" :class="`tag-${String(data.priority).toLowerCase()}`" size="small">{{ data.priority }}</el-tag>
                  <span v-if="data.kind === 'module'" class="node-count">{{ data.count }}项</span>
                </div>
                <div v-if="data.description" class="node-desc">{{ data.description }}</div>
              </div>
            </template>
          </el-tree>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { requirementApi } from '@/api/requirements'
import { caseApi } from '@/api/cases'
import { modelApi } from '@/api/models'
import type { Requirement, RequirementPoint, AIModelConfig } from '@/api/types'

const route = useRoute()
const projectId = computed(() => Number(route.params.id))
const requirements = ref<Requirement[]>([])
const modelConfigs = ref<AIModelConfig[]>([])
const generating = ref(false)
const lastResult = ref<any>(null)
const reqPoints = ref<RequirementPoint[]>([])
const advancedDialogVisible = ref(false)

const config = reactive({
  requirement_id: undefined as number | undefined,
  test_type: 'functional',
  granularity: 'medium',
  cover_scenarios: ['normal', 'exception', 'boundary'],
  ai_provider: undefined as string | undefined,
  temperature: 0.3,
  case_prompt: '',
  module_filter: undefined as string | undefined,
})

const canGenerate = computed(() =>
  !!config.ai_provider && reqPoints.value.length > 0 && modelConfigs.value.length > 0 && !!config.case_prompt.trim()
)

const modules = computed(() => {
  const mods = new Set(reqPoints.value.map(p => p.module).filter(Boolean))
  return [...mods]
})

const filteredPoints = computed(() => {
  if (!config.module_filter) return reqPoints.value
  return reqPoints.value.filter(p => p.module === config.module_filter)
})
const mindmapData = computed(() => {
  const moduleMap = new Map<string, RequirementPoint[]>()
  for (const p of filteredPoints.value) {
    const key = p.module || '通用模块'
    if (!moduleMap.has(key)) moduleMap.set(key, [])
    moduleMap.get(key)!.push(p)
  }
  return [{
    id: `root-${config.requirement_id || 'none'}`,
    kind: 'root',
    label: selectedReqTitle.value || '需求点总览',
    children: [...moduleMap.entries()].map(([module, points], idx) => ({
      id: `module-${idx}-${module}`,
      kind: 'module',
      label: module,
      count: points.length,
      children: points.map((point, pIdx) => ({
        id: `point-${idx}-${pIdx}-${point.id || pIdx}`,
        kind: 'point',
        label: point.title || point.id || `需求点${pIdx + 1}`,
        priority: point.priority,
        description: point.description || '',
      })),
    })),
  }]
})

const tempMarks = { 0: '严谨', 0.5: '均衡', 1: '发散' }
const selectedReqTitle = computed(() => requirements.value.find(r => r.id === config.requirement_id)?.title || '')
const temperatureLabel = computed(() => {
  if (config.temperature <= 0.3) return '稳健生成'
  if (config.temperature <= 0.6) return '均衡生成'
  return '探索生成'
})

onMounted(async () => {
  requirements.value = await requirementApi.list(projectId.value)
  modelConfigs.value = await modelApi.list()
  if (modelConfigs.value.length) {
    const def = modelConfigs.value.find(m => m.is_default) || modelConfigs.value[0]
    config.ai_provider = def.provider
  }
  // 支持从需求页面跳转带参数
  const reqId = route.query.req_id
  if (reqId) {
    config.requirement_id = Number(reqId)
    await onReqChange(Number(reqId))
  } else if (requirements.value.length === 1) {
    config.requirement_id = requirements.value[0].id
    await onReqChange(requirements.value[0].id)
  }
})

async function onReqChange(id?: number) {
  if (!id) { reqPoints.value = []; return }
  const req = await requirementApi.get(id)
  reqPoints.value = (req.parse_result as RequirementPoint[]) || []
}

function resetConfig() {
  Object.assign(config, {
    requirement_id: undefined,
    test_type: 'functional',
    granularity: 'medium',
    cover_scenarios: ['normal', 'exception', 'boundary'],
    ai_provider: modelConfigs.value[0]?.provider,
    temperature: 0.3,
    case_prompt: '',
    module_filter: undefined,
  })
  reqPoints.value = []
  lastResult.value = null
}

function applyTemperature(value: number) {
  config.temperature = value
}

function resetAdvanced() {
  config.temperature = 0.3
}

async function handleGenerate() {
  if (!reqPoints.value.length) return ElMessage.warning('请先选择需求来源')
  if (!config.ai_provider || !modelConfigs.value.length) return ElMessage.warning('请先选择可用模型')
  if (!config.case_prompt.trim()) return ElMessage.warning('请填写用例提示词')
  generating.value = true
  lastResult.value = null
  const startAt = Date.now()
  try {
    const payload = {
      project_id: projectId.value,
      requirement_id: config.requirement_id,
      req_points: filteredPoints.value,
      test_type: config.test_type,
      granularity: config.granularity,
      cover_scenarios: config.cover_scenarios,
      ai_provider: config.ai_provider,
      temperature: config.temperature,
      case_prompt: config.case_prompt,
      module_filter: config.module_filter,
    }
    const result: any = await caseApi.generate(payload)
    lastResult.value = result
    if (result.generation_mode === 'rule') {
      ElMessage.success(`已生成 ${result.total} 条用例（规则引擎模式）`)
    } else {
      ElMessage.success(`生成完成，共 ${result.total} 条用例`)
    }
  } catch (e: any) {
    const detail = e?.response?.data?.detail || ''
    const shouldFallback =
      e?.response?.status === 502 ||
      (typeof detail === 'string' && (detail.includes('API Key') || detail.includes('未配置')))
    if (shouldFallback) {
      const fallbackResult = await generateByRules(startAt)
      lastResult.value = fallbackResult
      ElMessage.success(`已生成 ${fallbackResult.total} 条用例（本地规则模式）`)
    }
  } finally {
    generating.value = false
  }
}

async function generateByRules(startAt: number) {
  const scenarioLabelMap: Record<string, string> = {
    normal: '正常流程',
    exception: '异常场景',
    boundary: '边界场景',
    permission: '权限控制',
    compatibility: '兼容性',
    security: '安全性',
  }
  const selected = (config.cover_scenarios || []).filter(s => scenarioLabelMap[s])
  const picked = selected.slice(0, ({ coarse: 1, medium: 2, fine: selected.length } as any)[config.granularity] || 2)
  const stage = config.test_type === 'api' ? 'integration' : (config.test_type === 'unit' ? 'unit' : 'system')
  const createdCases: any[] = []
  for (const p of filteredPoints.value) {
    for (const s of picked.length ? picked : ['normal']) {
      const scenarioName = scenarioLabelMap[s] || s
      const payload = {
        project_id: projectId.value,
        requirement_id: config.requirement_id,
        module: p.module || '通用模块',
        title: `${p.title} - ${scenarioName}`,
        case_level: p.priority || 'P1',
        test_type: config.test_type,
        stage,
        preconditions: `已具备执行「${p.title}」的测试环境`,
        steps: [
          { step: 1, action: `输入${scenarioName}测试数据并执行`, expected: '系统成功接收请求' },
          { step: 2, action: '检查页面/接口返回与状态变化', expected: `结果符合${scenarioName}预期` },
        ],
        expected_results: [`结果符合${scenarioName}预期`],
        remarks: '前端规则引擎生成',
      }
      const created = await caseApi.create(payload)
      createdCases.push(created)
    }
  }
  return {
    batch_id: `local-${Date.now()}`,
    total: createdCases.length,
    cases: createdCases,
    elapsed_seconds: Number(((Date.now() - startAt) / 1000).toFixed(2)),
    generation_mode: 'rule',
  }
}

function providerName(p: string): string {
  const map: Record<string, string> = {
    openai: 'OpenAI', anthropic: 'Claude', tongyi: '通义千问',
    zhipu: '智谱GLM', deepseek: 'DeepSeek'
  }
  return map[p] || p
}
</script>

<style scoped>
.generate-page { width: 100%; max-width: none; height: 100%; min-height: 0; display: flex; flex-direction: column; overflow-y: auto; overflow-x: hidden; }
.page-header { margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center; gap: 10px; flex-shrink: 0; }
.page-header h2 { font-size: 22px; font-weight: 700; }
.sub-title { margin-top: 4px; color: var(--text-secondary); font-size: 13px; }

.generate-layout { display: grid; grid-template-columns: minmax(340px, 420px) minmax(0, 1fr); gap: 20px; align-items: stretch; flex: 1; min-height: 0; }
.left-column { min-height: 0; min-width: 0; overflow: hidden; display: flex; }
.config-panel, .preview-panel { min-height: 0; min-width: 0; overflow: hidden; display: flex; flex-direction: column; }
.config-panel { flex: 1; height: 100%; }
.config-body, .preview-body { flex: 1; min-height: 0; overflow: auto; overflow-x: hidden; padding-right: 2px; }
.config-footer {
  position: sticky;
  bottom: 0;
  z-index: 2;
  background: #fff;
  border-top: 1px solid var(--border);
  padding-top: 12px;
  margin-top: 12px;
  flex-shrink: 0;
}

.panel-title-row { display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-bottom: 16px; }
.config-panel h3, .preview-panel h3 { font-size: 15px; font-weight: 600; margin-bottom: 0; }
.advanced-icon-btn { width: 32px; height: 32px; border-color: #dbe3ff; background: #f5f7ff; color: #4f6ef7; }
.section-label {
  font-size: 13px; font-weight: 500; color: var(--text-secondary);
  margin: 20px 0 10px;
  display: flex; align-items: center; gap: 8px;
}
.section-label.small { margin-top: 12px; }
.required-mark { color: #ef4444; font-size: 14px; font-weight: 700; line-height: 1; }
.sec-index {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  color: #fff;
  background: #4f6ef7;
}
.temp-val { color: #4f6ef7; font-weight: 700; }
.config-body :deep(.el-select),
.config-body :deep(.el-radio-group),
.config-body :deep(.el-checkbox-group),
.config-body :deep(.el-textarea) { margin-bottom: 8px; }

.type-group { width: 100%; display: flex; }
.type-group :deep(.el-radio-button) { flex: 1; }
.type-group :deep(.el-radio-button__inner) { width: 100%; }

.scenario-group { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; }

.result-summary { margin-top: 10px; border: 1px solid #dbeafe; background: #f8fbff; border-radius: 8px; padding: 8px 10px; }
.result-line { font-size: 13px; font-weight: 600; color: #1f2937; }
.footer-actions { display: flex; gap: 8px; }
.footer-actions .el-button { flex: 1; }
.footer-hint { margin-top: 8px; font-size: 12px; color: #6b7280; }
.advanced-dialog-body { display: grid; gap: 14px; }
.advanced-summary { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; padding: 12px; border-radius: 10px; background: linear-gradient(135deg, #f4f7ff 0%, #eef2ff 100%); }
.advanced-title { font-size: 14px; font-weight: 600; color: #1f2937; }
.advanced-sub { margin-top: 4px; font-size: 12px; color: #64748b; line-height: 1.5; }
.preset-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; }
.preset-card { border: 1px solid #dbe3ff; background: #fff; border-radius: 10px; padding: 10px; text-align: left; cursor: pointer; transition: all .2s ease; }
.preset-card:hover { border-color: #9ab0ff; box-shadow: 0 4px 12px rgba(79, 110, 247, 0.12); }
.preset-card.active { border-color: #4f6ef7; background: #f4f7ff; box-shadow: inset 0 0 0 1px #4f6ef7; }
.preset-name { display: block; font-size: 13px; font-weight: 600; color: #111827; }
.preset-desc { display: block; margin-top: 4px; font-size: 12px; color: #64748b; line-height: 1.4; }
.advanced-item { border: 1px solid #e6eaf5; border-radius: 10px; padding: 14px; background: #fafbff; }
.temp-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; font-size: 13px; color: #4b5563; }
.advanced-tip { margin-top: 8px; font-size: 12px; color: #64748b; }
.advanced-footer { display: flex; justify-content: flex-end; gap: 8px; }
:deep(.advanced-dialog .el-dialog) { border-radius: 12px; overflow: hidden; }
:deep(.advanced-dialog .el-dialog__header) { border-bottom: 1px solid #edf0f7; margin-right: 0; padding: 16px 20px 14px; }
:deep(.advanced-dialog .el-dialog__body) { padding: 14px 20px 8px; }
:deep(.advanced-dialog .el-dialog__footer) { border-top: 1px solid #edf0f7; padding: 12px 20px 14px; }

.preview-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.preview-count { font-size: 13px; color: var(--text-secondary); }
.preview-empty { text-align: center; padding: 40px; color: #9ca3af; font-size: 14px; }
.mindmap-tree { background: transparent; }
.mind-node { min-width: 0; width: 100%; border: 1px solid #e5e7eb; border-radius: 8px; padding: 6px 10px; background: #fff; }
.mind-node.kind-root { background: #eef2ff; border-color: #c7d2fe; }
.mind-node.kind-module { background: #f8fafc; }
.mind-line { display: flex; align-items: center; gap: 8px; min-width: 0; }
.node-label { font-size: 13px; font-weight: 500; color: #111827; line-height: 1.4; white-space: normal; word-break: break-word; }
.node-count { margin-left: auto; font-size: 11px; color: #6b7280; }
.node-desc { margin-top: 4px; font-size: 12px; color: #6b7280; line-height: 1.4; white-space: normal; word-break: break-word; }
:deep(.mindmap-tree .el-tree-node__content) { height: auto; align-items: flex-start; padding: 4px 0; }
:deep(.mindmap-tree .el-tree-node) { min-width: 0; }
:deep(.mindmap-tree .el-tree-node__children) { padding-left: 18px; }
@media (max-width: 1024px) {
  .generate-layout { grid-template-columns: 1fr; gap: 12px; }
  .config-panel, .preview-panel { min-height: 300px; }
}
@media (max-width: 768px) {
  .page-header { align-items: flex-start; }
  .scenario-group { grid-template-columns: 1fr; }
  .preset-grid { grid-template-columns: 1fr; }
}
</style>
