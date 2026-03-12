<template>
  <div class="generate-page">
    <div class="page-header">
      <h2>智能生成测试用例</h2>
    </div>

    <div class="generate-layout">
      <!-- 左：生成配置 -->
      <div class="config-panel page-card">
        <h3>生成配置</h3>

        <!-- 需求来源 -->
        <div class="section-label">需求来源</div>
        <el-select v-model="config.requirement_id" placeholder="选择已解析的需求" clearable style="width:100%"
          @change="onReqChange">
          <el-option v-for="r in requirements" :key="r.id" :label="`${r.title} (${r.req_points_count}点)`" :value="r.id" />
        </el-select>

        <div v-if="reqPoints.length" class="req-summary">
          <el-tag type="success" size="small">{{ reqPoints.length }} 个需求点已加载</el-tag>
          <div class="module-filter-row">
            <span>模块筛选：</span>
            <el-select v-model="config.module_filter" placeholder="全部模块" clearable size="small" style="flex:1">
              <el-option v-for="m in modules" :key="m" :label="m" :value="m" />
            </el-select>
          </div>
        </div>

        <!-- 生成类型 -->
        <div class="section-label">测试类型</div>
        <el-radio-group v-model="config.test_type" class="type-group">
          <el-radio-button value="functional">功能测试</el-radio-button>
          <el-radio-button value="api">接口测试</el-radio-button>
          <el-radio-button value="unit">单元测试</el-radio-button>
        </el-radio-group>

        <!-- 颗粒度 -->
        <div class="section-label">用例颗粒度</div>
        <el-radio-group v-model="config.granularity">
          <el-radio value="coarse">粗（按流程）</el-radio>
          <el-radio value="medium">中（按功能点）</el-radio>
          <el-radio value="fine">细（按单一场景）</el-radio>
        </el-radio-group>

        <!-- 覆盖场景 -->
        <div class="section-label">覆盖场景</div>
        <el-checkbox-group v-model="config.cover_scenarios" class="scenario-group">
          <el-checkbox value="normal">正常流程</el-checkbox>
          <el-checkbox value="exception">异常场景</el-checkbox>
          <el-checkbox value="boundary">边界值</el-checkbox>
          <el-checkbox value="permission">权限控制</el-checkbox>
          <el-checkbox value="compatibility">兼容性</el-checkbox>
          <el-checkbox value="security">数据安全</el-checkbox>
        </el-checkbox-group>

        <!-- AI 模型 -->
        <div class="section-label">AI 模型</div>
        <el-select v-model="config.ai_provider" placeholder="选择AI供应商" style="width:100%">
          <el-option v-for="m in modelConfigs" :key="m.id" :value="m.provider"
            :label="`${providerName(m.provider)} · ${m.model_name}`" />
          <el-option v-if="!modelConfigs.length" value="" label="（请先在设置中添加AI模型）" disabled />
        </el-select>

        <!-- Temperature -->
        <div class="section-label">创造性（Temperature）<span class="temp-val">{{ config.temperature }}</span></div>
        <el-slider v-model="config.temperature" :min="0" :max="1" :step="0.1" :marks="tempMarks" />

        <!-- 补充说明 -->
        <div class="section-label">补充说明（可选）</div>
        <el-input v-model="config.custom_instructions" type="textarea" :rows="2"
          placeholder="如：重点关注支付流程、用例需包含并发场景..." />

        <el-button type="primary" size="large" :loading="generating" :disabled="!canGenerate"
          style="width:100%;margin-top:20px" @click="handleGenerate">
          <el-icon v-if="!generating"><MagicStick /></el-icon>
          {{ generating ? 'AI 生成中...' : '开始生成' }}
        </el-button>

        <div v-if="lastResult" class="result-summary">
          <el-result icon="success" :title="`生成完成`"
            :sub-title="`共 ${lastResult.total} 条用例，耗时 ${lastResult.elapsed_seconds}s`">
            <template #extra>
              <el-button type="primary" @click="$router.push(`/projects/${projectId}/cases?batch=${lastResult.batch_id}`)">
                查看生成结果
              </el-button>
            </template>
          </el-result>
        </div>
      </div>

      <!-- 右：需求点预览 -->
      <div class="preview-panel page-card">
        <div class="preview-header">
          <h3>需求点预览</h3>
          <span class="preview-count">{{ filteredPoints.length }} 个</span>
        </div>
        <div v-if="!filteredPoints.length" class="preview-empty">
          <p>请先在左侧选择需求来源</p>
        </div>
        <div v-else class="preview-list">
          <div v-for="(p, i) in filteredPoints" :key="i" class="req-point">
            <div class="rp-header">
              <span class="rp-id">{{ p.id }}</span>
              <el-tag :class="`tag-${p.priority?.toLowerCase()}`" size="small">{{ p.priority }}</el-tag>
              <span class="rp-module">{{ p.module }}</span>
            </div>
            <div class="rp-title">{{ p.title }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { requirementApi } from '@/api/requirements'
import { caseApi } from '@/api/cases'
import { modelApi } from '@/api/models'
import type { Requirement, RequirementPoint, AIModelConfig } from '@/api/types'

const route = useRoute()
const router = useRouter()
const projectId = computed(() => Number(route.params.id))
const requirements = ref<Requirement[]>([])
const modelConfigs = ref<AIModelConfig[]>([])
const generating = ref(false)
const lastResult = ref<any>(null)
const reqPoints = ref<RequirementPoint[]>([])

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
  reqPoints.value.length > 0
)

const modules = computed(() => {
  const mods = new Set(reqPoints.value.map(p => p.module).filter(Boolean))
  return [...mods]
})

const filteredPoints = computed(() => {
  if (!config.module_filter) return reqPoints.value
  return reqPoints.value.filter(p => p.module === config.module_filter)
})

const tempMarks = { 0: '严谨', 0.5: '均衡', 1: '发散' }

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
  }
})

async function onReqChange(id?: number) {
  if (!id) { reqPoints.value = []; return }
  const req = await requirementApi.get(id)
  reqPoints.value = (req.parse_result as RequirementPoint[]) || []
}

async function handleGenerate() {
  if (!reqPoints.value.length) return ElMessage.warning('请先选择需求来源')
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
.generate-page { max-width: 1300px; }
.page-header { margin-bottom: 20px; }
.page-header h2 { font-size: 22px; font-weight: 700; }

.generate-layout { display: grid; grid-template-columns: 380px 1fr; gap: 20px; align-items: start; }

.config-panel h3, .preview-panel h3 { font-size: 15px; font-weight: 600; margin-bottom: 16px; }
.section-label {
  font-size: 13px; font-weight: 500; color: var(--text-secondary);
  margin: 16px 0 8px;
  display: flex; align-items: center; gap: 8px;
}
.temp-val { color: #4f6ef7; font-weight: 700; }

.type-group { width: 100%; display: flex; }
.type-group :deep(.el-radio-button) { flex: 1; }
.type-group :deep(.el-radio-button__inner) { width: 100%; }

.scenario-group { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; }

.req-summary { background: #f9fafb; border-radius: 8px; padding: 10px; margin-top: 8px; }
.module-filter-row { display: flex; align-items: center; gap: 8px; margin-top: 8px; font-size: 13px; }

.result-summary { margin-top: 16px; border-top: 1px solid var(--border); padding-top: 16px; }

.preview-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.preview-count { font-size: 13px; color: var(--text-secondary); }
.preview-empty { text-align: center; padding: 40px; color: #9ca3af; font-size: 14px; }
.preview-list { max-height: calc(100vh - 200px); overflow-y: auto; display: flex; flex-direction: column; gap: 8px; }

.req-point { border: 1px solid var(--border); border-radius: 8px; padding: 10px 12px; }
.rp-header { display: flex; align-items: center; gap: 6px; margin-bottom: 4px; }
.rp-id { font-size: 11px; font-family: monospace; color: #9ca3af; }
.rp-module { font-size: 11px; color: #9ca3af; }
.rp-title { font-size: 13px; font-weight: 500; line-height: 1.4; }
</style>
