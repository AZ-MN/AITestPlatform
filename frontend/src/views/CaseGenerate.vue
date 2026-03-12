<template>
  <div class="generate-page">
    <div class="page-header">
      <div>
        <h2>智能生成测试用例</h2>
        <div class="sub-title">在当前页面完成配置、生成与结果查看，减少跨模块跳转</div>
      </div>
    </div>

    <div class="generate-layout">
      <!-- 左：生成配置 -->
      <div class="config-panel page-card">
        <h3>生成配置</h3>
        <div class="config-body">
          <el-alert
            v-if="!modelConfigs.length"
            title="当前未配置 AI 模型，将使用规则引擎生成可用用例"
            type="warning"
            show-icon
            :closable="false"
            style="margin-bottom:12px"
          />

          <div class="section-label"><span class="sec-index">1</span>选择模型（必选）</div>
          <el-select v-model="config.ai_provider" placeholder="请选择用于生成的AI模型" style="width:100%">
            <el-option v-for="m in modelConfigs" :key="m.id" :value="m.provider"
              :label="`${providerName(m.provider)} · ${m.model_name}`" />
            <el-option v-if="!modelConfigs.length" value="" label="（请先在设置中添加AI模型）" disabled />
          </el-select>

          <div class="section-label"><span class="sec-index">2</span>选择需求来源</div>
          <el-select v-model="config.requirement_id" placeholder="选择已解析的需求" clearable style="width:100%"
            @change="onReqChange">
            <el-option v-for="r in requirements" :key="r.id" :label="`${r.title} (${r.req_points_count}点)`" :value="r.id" />
          </el-select>

          <div v-if="reqPoints.length" class="req-summary">
            <el-tag type="success" size="small">{{ reqPoints.length }} 个需求点已加载</el-tag>
            <div class="summary-title">{{ selectedReqTitle }}</div>
          </div>

          <div class="section-label"><span class="sec-index">3</span>确定本次生成目标</div>
          <el-radio-group v-model="config.test_type" class="type-group">
            <el-radio-button value="functional">功能测试</el-radio-button>
            <el-radio-button value="api">接口测试</el-radio-button>
            <el-radio-button value="unit">单元测试</el-radio-button>
          </el-radio-group>

          <div class="section-label small">用例颗粒度</div>
          <el-radio-group v-model="config.granularity">
            <el-radio value="coarse">粗（按流程）</el-radio>
            <el-radio value="medium">中（按功能点）</el-radio>
            <el-radio value="fine">细（按单一场景）</el-radio>
          </el-radio-group>

          <div class="section-label small">覆盖模块（可选）</div>
          <el-select v-model="config.module_filter" placeholder="全部模块" clearable style="width:100%">
            <el-option v-for="m in modules" :key="m" :label="m" :value="m" />
          </el-select>

          <div class="section-label"><span class="sec-index">4</span>选择覆盖场景</div>
          <el-checkbox-group v-model="config.cover_scenarios" class="scenario-group">
            <el-checkbox value="normal">正常流程</el-checkbox>
            <el-checkbox value="exception">异常场景</el-checkbox>
            <el-checkbox value="boundary">边界值</el-checkbox>
            <el-checkbox value="permission">权限控制</el-checkbox>
            <el-checkbox value="compatibility">兼容性</el-checkbox>
            <el-checkbox value="security">数据安全</el-checkbox>
          </el-checkbox-group>

          <el-collapse class="advanced-collapse" v-model="advancedPanels">
            <el-collapse-item title="高级参数（可选）" name="advanced">
              <div class="section-label small">创造性（Temperature）<span class="temp-val">{{ config.temperature }}</span></div>
              <el-slider v-model="config.temperature" :min="0" :max="1" :step="0.1" :marks="tempMarks" />

              <div class="section-label small">补充说明（可选）</div>
              <el-input v-model="config.custom_instructions" type="textarea" :rows="2"
                placeholder="如：重点关注支付流程、用例需包含并发场景..." />
            </el-collapse-item>
          </el-collapse>
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
const advancedPanels = ref<string[]>([])

const config = reactive({
  requirement_id: undefined as number | undefined,
  test_type: 'functional',
  granularity: 'medium',
  cover_scenarios: ['normal', 'exception', 'boundary'],
  ai_provider: undefined as string | undefined,
  temperature: 0.3,
  custom_instructions: '',
  module_filter: undefined as string | undefined,
})

const canGenerate = computed(() =>
  !!config.ai_provider && reqPoints.value.length > 0 && modelConfigs.value.length > 0
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
    custom_instructions: '',
    module_filter: undefined,
  })
  reqPoints.value = []
  lastResult.value = null
}

async function handleGenerate() {
  if (!reqPoints.value.length) return ElMessage.warning('请先选择需求来源')
  if (!config.ai_provider || !modelConfigs.value.length) return ElMessage.warning('请先选择可用模型')
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
      custom_instructions: config.custom_instructions,
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
.config-panel, .preview-panel { min-height: 0; min-width: 0; overflow: hidden; display: flex; flex-direction: column; }
.config-body, .preview-body { flex: 1; min-height: 0; overflow: auto; overflow-x: hidden; padding-right: 2px; }
.config-footer {
  border-top: 1px solid var(--border);
  padding-top: 12px;
  margin-top: 12px;
  flex-shrink: 0;
}

.config-panel h3, .preview-panel h3 { font-size: 15px; font-weight: 600; margin-bottom: 16px; }
.section-label {
  font-size: 13px; font-weight: 500; color: var(--text-secondary);
  margin: 16px 0 8px;
  display: flex; align-items: center; gap: 8px;
}
.section-label.small { margin-top: 12px; }
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

.type-group { width: 100%; display: flex; }
.type-group :deep(.el-radio-button) { flex: 1; }
.type-group :deep(.el-radio-button__inner) { width: 100%; }

.scenario-group { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; }

.req-summary { background: #f9fafb; border-radius: 8px; padding: 10px; margin-top: 8px; }
.summary-title { margin-top: 6px; font-size: 12px; color: #6b7280; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.advanced-collapse { margin-top: 14px; }

.result-summary { margin-top: 10px; border: 1px solid #dbeafe; background: #f8fbff; border-radius: 8px; padding: 8px 10px; }
.result-line { font-size: 13px; font-weight: 600; color: #1f2937; }
.footer-actions { display: flex; gap: 8px; }
.footer-actions .el-button { flex: 1; }
.footer-hint { margin-top: 8px; font-size: 12px; color: #6b7280; }

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
}
</style>
