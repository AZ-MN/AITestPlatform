<template>
  <div class="generate-container">
    <div class="page-desc">
       <p class="subtitle">配置 AI 模型参数，自动基于需求生成高质量测试用例。</p>
    </div>

    <div class="workspace">
      <!-- Left Panel: Configuration -->
      <div class="config-panel">
        <div class="panel-header">
          <h3>生成配置</h3>
          <el-button link class="reset-icon-btn" @click="resetConfig">
             <el-icon><RefreshRight /></el-icon>
             <span>重置</span>
          </el-button>
        </div>
        
        <div class="config-scroll">
          <el-form :model="config" label-position="top" class="config-form">
            <!-- 1. Model & Source -->
            <div class="form-section">
              <el-form-item label="AI 模型">
                <el-select v-model="config.ai_provider" placeholder="选择模型" style="width: 100%">
                  <el-option 
                    v-for="m in modelConfigs" 
                    :key="m.id" 
                    :value="m.provider"
                    :label="`${providerName(m.provider)} - ${m.model_name}`" 
                  />
                  <el-option v-if="!modelConfigs.length" value="" label="请先配置模型" disabled />
                </el-select>
              </el-form-item>

              <el-form-item label="需求来源">
                <el-select v-model="config.requirement_id" placeholder="选择需求文档" style="width: 100%" @change="onReqChange">
                  <el-option v-for="r in requirements" :key="r.id" :label="r.title" :value="r.id" />
                </el-select>
              </el-form-item>
              
              <el-form-item label="模块筛选" v-if="modules.length">
                <el-select v-model="config.module_filter" placeholder="全选" clearable style="width: 100%">
                  <el-option v-for="m in modules" :key="m" :label="m" :value="m" />
                </el-select>
              </el-form-item>
            </div>

            <div class="divider"></div>

            <!-- 2. Test Strategy -->
            <div class="form-section">
              <el-form-item label="测试类型">
                <div class="radio-cards">
                  <div 
                    v-for="type in ['functional', 'api', 'unit']" 
                    :key="type"
                    :class="['radio-card', { active: config.test_type === type }]"
                    @click="config.test_type = type"
                  >
                    <span class="card-label">{{ typeLabel(type) }}</span>
                  </div>
                </div>
              </el-form-item>

              <el-form-item label="用例颗粒度">
                <el-radio-group v-model="config.granularity" size="default">
                  <el-radio-button label="coarse">粗略</el-radio-button>
                  <el-radio-button label="medium">适中</el-radio-button>
                  <el-radio-button label="fine">详细</el-radio-button>
                </el-radio-group>
              </el-form-item>

              <el-form-item label="覆盖场景">
                <el-checkbox-group v-model="config.cover_scenarios" class="scenario-grid">
                  <el-checkbox label="normal">正常流程</el-checkbox>
                  <el-checkbox label="exception">异常场景</el-checkbox>
                  <el-checkbox label="boundary">边界值</el-checkbox>
                  <el-checkbox label="permission">权限控制</el-checkbox>
                  <el-checkbox label="compatibility">兼容性</el-checkbox>
                  <el-checkbox label="security">安全性</el-checkbox>
                </el-checkbox-group>
              </el-form-item>
            </div>

            <div class="divider"></div>

            <!-- 3. Prompt & Advanced -->
            <div class="form-section">
              <el-form-item label="生成提示词">
                <el-input 
                  v-model="config.case_prompt" 
                  type="textarea" 
                  :rows="4" 
                  placeholder="例如：请按测试步骤、预期结果的格式输出，重点覆盖异常输入情况。" 
                />
              </el-form-item>

              <el-collapse v-model="activeCollapse" class="advanced-collapse">
                <el-collapse-item title="高级设置 (温度/创造性)" name="1">
                  <div class="slider-row">
                    <span class="slider-label">温度: {{ config.temperature }}</span>
                    <el-slider v-model="config.temperature" :min="0" :max="1" :step="0.1" size="small" />
                  </div>
                  <p class="hint-text">值越高越发散，值越低越稳定。</p>
                </el-collapse-item>
              </el-collapse>
            </div>
          </el-form>
        </div>

        <div class="panel-footer">
          <el-button type="primary" size="large" class="generate-btn" :loading="generating" :disabled="!canGenerate" @click="handleGenerate">
            {{ generating ? '正在生成...' : '开始生成' }}
            <el-icon class="el-icon--right"><MagicStick /></el-icon>
          </el-button>
        </div>
      </div>

      <!-- Right Panel: Results & Preview -->
      <div class="result-panel">
        <el-tabs v-model="activeTab" class="result-tabs">
          <el-tab-pane label="需求预览" name="preview">
            <div class="tab-content scrollable">
              <div v-if="!filteredPoints.length" class="empty-state">
                <el-icon class="empty-icon"><Document /></el-icon>
                <p>请在左侧选择需求来源</p>
              </div>
              <div v-else class="req-preview">
                <div v-for="(group, idx) in reqGroups" :key="idx" class="req-group">
                  <div class="group-title">{{ group.module || '通用模块' }} <el-tag size="small" round>{{ group.points.length }}</el-tag></div>
                  <div class="req-list">
                    <div v-for="p in group.points" :key="p.id" class="req-card">
                      <div class="req-header">
                        <span class="req-title">{{ p.title }}</span>
                        <el-tag size="small" :type="priorityType(p.priority)">{{ p.priority || 'P1' }}</el-tag>
                      </div>
                      <div class="req-desc">{{ p.description }}</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </el-tab-pane>
          
          <el-tab-pane label="生成结果" name="result">
             <div class="tab-content scrollable">
                <div v-if="!lastResult && !generating" class="empty-state">
                  <el-icon class="empty-icon"><Cpu /></el-icon>
                  <p>点击左侧“开始生成”按钮启动 AI</p>
                </div>
                
                <div v-else class="result-content">
                  <div v-if="lastResult" class="result-meta">
                     <el-alert 
                       :title="`生成成功！共 ${lastResult.total} 条用例，耗时 ${lastResult.elapsed_seconds}s`" 
                       type="success" 
                       show-icon 
                       :closable="false"
                     />
                     <div class="result-actions">
                        <el-button type="primary" plain size="small" @click="$router.push(`/projects/${projectId}/cases`)">前往用例库查看</el-button>
                     </div>
                  </div>

                  <div class="cases-preview-list">
                    <div v-for="(c, i) in previewCases" :key="i" class="case-item-preview">
                      <div class="case-head">
                        <span class="case-seq">#{{ i+1 }}</span>
                        <span class="case-t">{{ c.title }}</span>
                        <el-tag size="small">{{ c.case_level }}</el-tag>
                      </div>
                      <div class="case-steps">
                         <div v-for="(s, si) in (c.steps || [])" :key="si" class="step-line">
                           <span class="step-idx">{{ si+1 }}.</span>
                           <span class="step-act">{{ s.action }}</span>
                           <span class="step-exp">预期: {{ s.expected }}</span>
                         </div>
                      </div>
                    </div>
                  </div>
                </div>
             </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { MagicStick, Document, Cpu, Setting, RefreshRight } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { requirementApi } from '@/api/requirements'
import { caseApi } from '@/api/cases'
import { modelApi } from '@/api/models'
import type { Requirement, RequirementPoint, AIModelConfig } from '@/api/types'

const route = useRoute()
const router = useRouter()
const projectId = computed(() => Number(route.params.id))

const DEFAULT_PROMPT = `作为资深测试工程师，请基于需求文档生成全面的测试用例。
重点关注：
1. [此处填写重点模块，如：登录流程]
2. 异常场景和边界值处理
3. 数据一致性和安全性

输出要求：
- 步骤清晰，预期结果明确
- 覆盖正向和逆向场景`

// State
const requirements = ref<Requirement[]>([])
const modelConfigs = ref<AIModelConfig[]>([])
const reqPoints = ref<RequirementPoint[]>([])
const generating = ref(false)
const lastResult = ref<any>(null)
const activeTab = ref('preview')
const activeCollapse = ref([''])
const previewCases = ref<any[]>([])

const config = reactive({
  requirement_id: undefined as number | undefined,
  test_type: 'functional',
  granularity: 'medium',
  cover_scenarios: ['normal', 'exception', 'boundary'],
  ai_provider: undefined as string | undefined,
  temperature: 0.3,
  case_prompt: DEFAULT_PROMPT,
  module_filter: undefined as string | undefined,
})

// Computed
const canGenerate = computed(() => 
  !!config.ai_provider && reqPoints.value.length > 0 && !!config.case_prompt
)

const modules = computed(() => {
  const s = new Set(reqPoints.value.map(p => p.module).filter(Boolean))
  return [...s]
})

const filteredPoints = computed(() => {
  if (!config.module_filter) return reqPoints.value
  return reqPoints.value.filter(p => p.module === config.module_filter)
})

const reqGroups = computed(() => {
  const groups: Record<string, RequirementPoint[]> = {}
  filteredPoints.value.forEach(p => {
    const m = p.module || '通用模块'
    if (!groups[m]) groups[m] = []
    groups[m].push(p)
  })
  return Object.entries(groups).map(([k, v]) => ({ module: k, points: v }))
})

// Lifecycle
onMounted(async () => {
  requirements.value = await requirementApi.list(projectId.value)
  modelConfigs.value = await modelApi.list()
  
  if (modelConfigs.value.length) {
    const def = modelConfigs.value.find(m => m.is_default) || modelConfigs.value[0]
    config.ai_provider = def.provider
  }

  if (route.query.req_id) {
    config.requirement_id = Number(route.query.req_id)
    await onReqChange(config.requirement_id)
  } else if (requirements.value.length > 0) {
    config.requirement_id = requirements.value[0].id
    await onReqChange(config.requirement_id)
  }
})

// Actions
async function onReqChange(id?: number) {
  if (!id) { reqPoints.value = []; return }
  const req = await requirementApi.get(id)
  reqPoints.value = (req.parse_result as RequirementPoint[]) || []
}

function resetConfig() {
  config.test_type = 'functional'
  config.granularity = 'medium'
  config.cover_scenarios = ['normal', 'exception', 'boundary']
  config.case_prompt = DEFAULT_PROMPT
  config.module_filter = undefined
  config.temperature = 0.3
  lastResult.value = null
  previewCases.value = []
}

async function handleGenerate() {
  if (!reqPoints.value.length) return ElMessage.warning('请选择需求')
  
  generating.value = true
  activeTab.value = 'result'
  previewCases.value = []
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
      case_prompt: config.case_prompt,
      module_filter: config.module_filter,
    }
    
    // Simulate streaming effect or just wait
    const res: any = await caseApi.generate(payload)
    lastResult.value = res
    
    // If cases are returned, show them
    if (res.cases && res.cases.length) {
       previewCases.value = res.cases
    } else if (res.generation_mode === 'rule') {
       // Mock fetch if the API doesn't return cases directly in some modes
       previewCases.value = res.cases || []
    } else {
      // Fetch latest generated cases for this req to preview
      const list = await caseApi.list({ project_id: projectId.value, page: 1, page_size: 20 })
      previewCases.value = list.items
    }
    
    ElMessage.success('生成完成')
  } catch (e) {
    ElMessage.error('生成失败，请检查模型配置')
  } finally {
    generating.value = false
  }
}

// Helpers
function providerName(p: string) {
  const map: any = { openai: 'OpenAI', anthropic: 'Claude', tongyi: '通义千问', zhipu: '智谱GLM', deepseek: 'DeepSeek' }
  return map[p] || p
}
function typeLabel(t: string) {
  const map: any = { functional: '功能测试', api: '接口测试', unit: '单元测试' }
  return map[t] || t
}
function priorityType(p: string) {
  const map: any = { P0: 'danger', P1: 'warning', P2: 'primary', P3: 'info' }
  return map[p] || 'info'
}
</script>

<style scoped>
.generate-container {
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

.workspace {
  flex: 1;
  min-height: 0;
  display: flex;
  gap: 24px;
  align-items: stretch;
}

/* Config Panel */
.config-panel {
  width: 320px;
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  box-shadow: var(--shadow-sm);
}
.panel-header {
  padding: 12px 16px;
  border-bottom: 1px solid var(--border);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--bg-secondary);
  border-radius: var(--radius-lg) var(--radius-lg) 0 0;
}
.panel-header h3 { font-size: 15px; font-weight: 700; margin: 0; color: var(--text-primary); }
.reset-icon-btn { 
  font-size: 13px; 
  padding: 4px 8px; 
  height: auto; 
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  gap: 4px;
}
.reset-icon-btn:hover {
  color: var(--primary);
}

.config-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}
.panel-footer {
  padding: 12px 16px;
  border-top: 1px solid var(--border);
  background: var(--bg-secondary);
  border-radius: 0 0 var(--radius-lg) var(--radius-lg);
}

.divider { height: 1px; background: var(--border); margin: 20px 0; }
.form-section { display: flex; flex-direction: column; gap: 0; }

/* Radio Cards */
.radio-cards { display: flex; gap: 8px; }
.radio-card {
  flex: 1;
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 8px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 13px;
}
.radio-card:hover { border-color: var(--primary); background: var(--bg-secondary); }
.radio-card.active { border-color: var(--primary); background: var(--primary-light); color: var(--primary); font-weight: 600; }

.scenario-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.generate-btn { width: 100%; font-weight: 700; }
.slider-row { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; font-size: 12px; }
.hint-text { font-size: 12px; color: var(--text-secondary); margin: 0; }

/* Result Panel */
.result-panel {
  flex: 1;
  min-width: 0;
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.result-tabs { flex: 1; display: flex; flex-direction: column; min-height: 0; }
.result-tabs :deep(.el-tabs__header) { margin: 0; padding: 0 20px; border-bottom: 1px solid var(--border); background: var(--bg-secondary); }
.result-tabs :deep(.el-tabs__content) { flex: 1; min-height: 0; display: flex; flex-direction: column; }
.result-tabs :deep(.el-tab-pane) { flex: 1; height: 100%; min-height: 0; }

.tab-content { height: 100%; overflow-y: auto; padding: 24px; }
.empty-state {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
}
.empty-icon { font-size: 48px; margin-bottom: 16px; opacity: 0.3; }

/* Preview Styles */
.req-group { margin-bottom: 24px; }
.group-title { font-size: 14px; font-weight: 700; margin-bottom: 12px; display: flex; align-items: center; gap: 8px; }
.req-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 12px; }
.req-card { border: 1px solid var(--border); border-radius: 8px; padding: 12px; background: #fff; }
.req-header { display: flex; justify-content: space-between; margin-bottom: 8px; align-items: flex-start; gap: 8px; }
.req-title { font-size: 13px; font-weight: 600; line-height: 1.4; }
.req-desc { font-size: 12px; color: var(--text-secondary); line-height: 1.5; }

/* Result Styles */
.result-meta { margin-bottom: 24px; }
.result-actions { margin-top: 12px; text-align: right; }
.cases-preview-list { display: flex; flex-direction: column; gap: 16px; }
.case-item-preview { border: 1px solid var(--border); border-radius: 8px; padding: 16px; background: #fff; }
.case-head { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; border-bottom: 1px dashed var(--border); padding-bottom: 8px; }
.case-seq { font-family: monospace; color: var(--text-secondary); font-size: 12px; }
.case-t { font-weight: 600; font-size: 14px; flex: 1; }
.case-steps { font-size: 13px; color: var(--text-primary); display: flex; flex-direction: column; gap: 6px; }
.step-line { display: flex; gap: 8px; }
.step-idx { color: var(--text-secondary); min-width: 16px; }
.step-act { flex: 1; }
.step-exp { color: #059669; background: #ecfdf5; padding: 0 4px; border-radius: 4px; }

@media (max-width: 900px) {
  .workspace { flex-direction: column; }
  .config-panel { width: 100%; height: auto; max-height: 500px; }
  .result-panel { height: 500px; }
}
</style>
