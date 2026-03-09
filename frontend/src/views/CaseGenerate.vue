<template>
  <div class="generate-page">
    <div class="page-header">
      <h2>智能生成测试用例</h2>
      <p>从已解析需求中快速生成高质量测试用例，支持按模块与场景精细控制。</p>
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

        <el-button type="primary" size="large" class="generate-btn" :loading="generating" :disabled="!canGenerate"
          @click="handleGenerate">
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
          <div class="preview-empty-icon">🧩</div>
          <p>请先在左侧选择需求来源</p>
          <span>加载后可按模块筛选并实时预览生成范围</span>
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
  reqPoints.value.length > 0 && !!config.ai_provider
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
  config.module_filter = undefined
  if (!id) { reqPoints.value = []; return }
  const req = await requirementApi.get(id)
  reqPoints.value = (req.parse_result as RequirementPoint[]) || []
}

async function handleGenerate() {
  if (!reqPoints.value.length) return ElMessage.warning('请先选择需求来源')
  if (!config.ai_provider) return ElMessage.warning('请先在模型设置中配置并选择AI模型')
  generating.value = true
  lastResult.value = null
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
    ElMessage.success(`生成完成，共 ${result.total} 条用例`)
  } catch (e: any) {
    // error handled by interceptor
  } finally {
    generating.value = false
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
.generate-page {
  max-width: 1320px;
  padding: 6px;
}
.page-header {
  margin-bottom: 16px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.page-header h2 { font-size: 26px; font-weight: 700; letter-spacing: .3px; }
.page-header p { font-size: 13px; color: var(--text-secondary); }

.generate-layout { display: grid; grid-template-columns: 400px 1fr; gap: 16px; align-items: start; }

.config-panel,
.preview-panel {
  border-radius: 14px;
  border-color: #e8ebf5;
  box-shadow: 0 10px 30px rgba(31, 41, 55, .06);
}

.config-panel {
  position: sticky;
  top: 8px;
}

.config-panel h3, .preview-panel h3 { font-size: 16px; font-weight: 700; margin-bottom: 14px; }
.section-label {
  font-size: 13px; font-weight: 500; color: var(--text-secondary);
  margin: 14px 0 8px;
  display: flex; align-items: center; gap: 8px;
}
.temp-val { color: #4f6ef7; font-weight: 700; }

.type-group { width: 100%; display: flex; }
.type-group :deep(.el-radio-button) { flex: 1; }
.type-group :deep(.el-radio-button__inner) { width: 100%; }

.scenario-group { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }

.req-summary {
  background: linear-gradient(180deg, #f7f9ff 0%, #f4f7ff 100%);
  border: 1px solid #e6ebff;
  border-radius: 10px;
  padding: 10px;
  margin-top: 8px;
}
.module-filter-row { display: flex; align-items: center; gap: 8px; margin-top: 8px; font-size: 13px; }

.result-summary { margin-top: 16px; border-top: 1px solid var(--border); padding-top: 16px; }
.generate-btn { width: 100%; margin-top: 18px; height: 44px; font-weight: 600; }

.preview-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.preview-count {
  font-size: 12px;
  color: #4f6ef7;
  background: #eef2ff;
  padding: 4px 10px;
  border-radius: 999px;
}
.preview-empty {
  text-align: center;
  padding: 52px 24px;
  color: #9ca3af;
  font-size: 14px;
  border: 1px dashed #d8dcef;
  border-radius: 12px;
  background: #fbfcff;
}
.preview-empty-icon { font-size: 28px; margin-bottom: 10px; }
.preview-empty span { font-size: 12px; margin-top: 6px; display: inline-block; color: #a1a8bd; }
.preview-list { max-height: calc(100vh - 210px); overflow-y: auto; display: flex; flex-direction: column; gap: 10px; padding-right: 2px; }

.req-point {
  border: 1px solid #e8ebf5;
  border-radius: 10px;
  padding: 12px;
  background: linear-gradient(180deg, #ffffff 0%, #fbfcff 100%);
}
.rp-header { display: flex; align-items: center; gap: 6px; margin-bottom: 4px; }
.rp-id { font-size: 11px; font-family: monospace; color: #6b7280; font-weight: 600; }
.rp-module { font-size: 11px; color: #9ca3af; }
.rp-title { font-size: 13px; font-weight: 600; line-height: 1.4; color: #1f2937; }

@media (max-width: 1200px) {
  .generate-layout { grid-template-columns: 1fr; }
  .config-panel { position: static; }
  .preview-list { max-height: 520px; }
}
</style>
