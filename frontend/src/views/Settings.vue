<template>
  <div class="settings-page">
    <div class="page-header">
      <h2>AI 模型设置</h2>
      <el-button type="primary" :icon="Plus" @click="openAdd">添加模型配置</el-button>
    </div>

    <!-- 供应商说明 -->
    <el-alert type="info" :closable="false" style="margin-bottom:16px">
      <template #title>
        配置 AI 模型 API Key 后，即可在「智能生成」页面使用对应模型生成测试用例。
        至少配置一个模型方可使用生成功能。
      </template>
    </el-alert>

    <!-- 已配置的模型 -->
    <div class="model-grid">
      <div v-for="cfg in configs" :key="cfg.id" class="model-card page-card">
        <div class="model-card-header">
          <div class="provider-badge" :style="{ background: providerColor(cfg.provider) }">
            {{ providerIcon(cfg.provider) }}
          </div>
          <div class="model-main">
            <el-tooltip :content="cfg.model_name" placement="top">
              <div class="model-name">{{ cfg.model_name }}</div>
            </el-tooltip>
            <div class="provider-name">{{ providerLabel(cfg.provider) }}</div>
          </div>
          <div class="model-header-right" @click.stop>
            <el-tag v-if="cfg.is_default" type="success" size="small">默认</el-tag>
            <div class="model-actions">
              <el-tooltip content="连通性测试" placement="top">
                <el-button circle text :loading="testingId === cfg.id" @click="testModel(cfg)">
                  <el-icon v-if="testingId !== cfg.id"><Promotion /></el-icon>
                </el-button>
              </el-tooltip>
              <el-tooltip content="编辑模型" placement="top">
                <el-button circle text @click="editConfig(cfg)">
                  <el-icon><Edit /></el-icon>
                </el-button>
              </el-tooltip>
              <el-tooltip content="删除模型" placement="top">
                <el-button circle text type="danger" @click="removeConfig(cfg)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </el-tooltip>
            </div>
          </div>
        </div>
        <div class="model-meta">
          <div class="meta-item"><span>温度</span><strong>{{ cfg.temperature }}</strong></div>
          <div class="meta-item"><span>最大令牌</span><strong>{{ cfg.max_tokens }}</strong></div>
          <div class="meta-item"><span>状态</span><strong>{{ cfg.is_active ? '启用' : '禁用' }}</strong></div>
        </div>
        <div v-if="testResults[cfg.id]" :class="['test-result', testResults[cfg.id].ok ? 'ok' : 'fail']">
          <span v-if="testResults[cfg.id].ok">✅ 连通成功：{{ testResults[cfg.id].reply }}</span>
          <span v-else>❌ 连通失败：{{ testResults[cfg.id].error }}</span>
        </div>
      </div>

      <div class="add-model-card" @click="openAdd">
        <el-icon :size="32"><Plus /></el-icon>
        <span>添加新模型</span>
      </div>
    </div>

    <!-- 支持的供应商 -->
    <div class="providers-section page-card" style="margin-top:20px">
      <h3>支持的 AI 供应商</h3>
      <div class="providers-grid">
        <div v-for="p in providers" :key="p.id" class="provider-item">
          <div class="provider-icon-lg" :style="{ background: providerColor(p.id) }">
            {{ providerIcon(p.id) }}
          </div>
          <div>
            <div class="provider-item-name">{{ p.name }}</div>
            <div class="provider-models">{{ p.models.join(' / ') }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 添加/编辑弹窗 -->
    <el-dialog v-model="showDialog" :title="editId ? '编辑模型配置' : '添加模型配置'" width="520px" :close-on-click-modal="false">
      <el-form ref="formRef" :model="form" label-width="110px">
        <el-form-item label="供应商" prop="provider" :rules="[{ required: true, message: '请选择供应商', trigger: 'change' }]">
          <el-select v-model="form.provider" placeholder="选择供应商" style="width:100%" @change="onProviderChange">
            <el-option v-for="p in providers" :key="p.id" :value="p.id" :label="p.name" />
          </el-select>
        </el-form-item>
        <el-form-item label="模型" prop="model_name" :rules="[{ required: true, message: '请选择或输入模型名称', trigger: 'change' }]">
          <el-select v-model="form.model_name" placeholder="选择模型" style="width:100%" allow-create filterable>
            <el-option v-for="m in currentModels" :key="m" :value="m" :label="m" />
          </el-select>
        </el-form-item>
        <el-form-item label="API 密钥">
          <el-input v-model="form.api_key" type="password" show-password placeholder="请输入模型密钥（可选）" />
        </el-form-item>
        <el-form-item label="接口地址">
          <el-input v-model="form.api_base_url" placeholder="可选，留空则使用默认地址" />
        </el-form-item>
        <el-form-item label="温度参数">
          <el-input-number v-model.number="form.temperature_num" :min="0" :max="1" :step="0.1" :precision="1" />
          <span style="margin-left:8px;color:#9ca3af;font-size:12px">越低越严谨，越高越发散</span>
        </el-form-item>
        <el-form-item label="最大令牌数">
          <el-input-number v-model="form.max_tokens" :min="512" :max="128000" :step="512" />
        </el-form-item>
        <el-form-item label="设为默认">
          <el-switch v-model="form.is_default_bool" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { Plus, Edit, Delete, Promotion } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { modelApi } from '@/api/models'
import type { AIModelConfig } from '@/api/types'

const configs = ref<AIModelConfig[]>([])
const providers = ref<any[]>([])
const showDialog = ref(false)
const saving = ref(false)
const editId = ref<number>()
const testingId = ref<number>()
const testResults = ref<Record<number, any>>({})
const formRef = ref()

const form = reactive({
  provider: '', model_name: '', api_key: '', api_base_url: '',
  temperature_num: 0.3, max_tokens: 4096, is_default_bool: false
})

onMounted(async () => {
  configs.value = await modelApi.list()
  providers.value = await modelApi.providers()
})

const currentModels = computed(() => {
  const p = providers.value.find(p => p.id === form.provider)
  return p?.models || []
})

function providerLabel(id: string) {
  return providers.value.find(p => p.id === id)?.name || id
}
function providerIcon(id: string) {
  return { openai: '🤖', anthropic: '🔮', tongyi: '🌟', zhipu: '🧠', deepseek: '🔵' }[id] || '🤖'
}
function providerColor(id: string) {
  return { openai: '#10a37f22', anthropic: '#cc785c22', tongyi: '#ff6a0022', zhipu: '#3b82f622', deepseek: '#6366f122' }[id] || '#f3f4f6'
}

function onProviderChange() {
  const p = providers.value.find(p => p.id === form.provider)
  if (p?.models?.length) form.model_name = p.models[0]
}

function openAdd() {
  editId.value = undefined
  Object.assign(form, { provider: '', model_name: '', api_key: '', api_base_url: '',
    temperature_num: 0.3, max_tokens: 4096, is_default_bool: false })
  showDialog.value = true
}

function editConfig(cfg: AIModelConfig) {
  editId.value = cfg.id
  Object.assign(form, {
    provider: cfg.provider, model_name: cfg.model_name,
    api_key: '', api_base_url: cfg.api_base_url || '',
    temperature_num: parseFloat(cfg.temperature) || 0.3,
    max_tokens: cfg.max_tokens, is_default_bool: !!cfg.is_default
  })
  showDialog.value = true
}

async function handleSave() {
  await formRef.value?.validate()
  saving.value = true
  const payload = {
    provider: form.provider, model_name: form.model_name,
    api_key: form.api_key || undefined,
    api_base_url: form.api_base_url || undefined,
    temperature: String(form.temperature_num),
    max_tokens: form.max_tokens,
    is_default: form.is_default_bool ? 1 : 0,
  }
  try {
    if (editId.value) {
      await modelApi.update(editId.value, payload)
      ElMessage.success('更新成功')
    } else {
      await modelApi.add(payload)
      ElMessage.success('添加成功')
    }
    configs.value = await modelApi.list()
    showDialog.value = false
  } finally { saving.value = false }
}

async function testModel(cfg: AIModelConfig) {
  testingId.value = cfg.id
  testResults.value[cfg.id] = null
  const res = await modelApi.test(cfg.id)
  testResults.value[cfg.id] = res
  testingId.value = undefined
}

async function removeConfig(cfg: AIModelConfig) {
  await ElMessageBox.confirm(`确认删除「${cfg.model_name}」配置？`, '删除确认', {
    type: 'warning',
    closeOnClickModal: false,
    closeOnPressEscape: false,
  })
  await modelApi.remove(cfg.id)
  ElMessage.success('已删除')
  configs.value = await modelApi.list()
}
</script>

<style scoped>
.settings-page { width: 100%; max-width: none; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { font-size: 22px; font-weight: 700; }

.model-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(296px, 296px));
  justify-content: flex-start;
  align-items: start;
  gap: 18px;
}
.model-card { display: flex; flex-direction: column; gap: 12px; min-height: 184px; border-radius: 14px; position: relative; overflow: hidden; }
.model-card { background: linear-gradient(180deg, #ffffff 0%, #fcfdff 100%); border: 1px solid #e5e7eb; box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04); }
.model-card::before {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
  height: 3px;
  background: linear-gradient(90deg, #4f6ef7 0%, #7c92ff 100%);
  opacity: .55;
}
.model-card-header { display: flex; align-items: center; gap: 10px; }
.provider-badge {
  width: 40px; height: 40px; border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  font-size: 20px; flex-shrink: 0;
}
.model-main { min-width: 0; flex: 1; padding-right: 8px; }
.model-name { font-size: 14px; font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 150px; }
.provider-name { font-size: 12px; color: var(--text-secondary); }
.model-header-right { margin-left: auto; display: flex; flex-direction: column; align-items: flex-end; gap: 4px; }
.model-meta { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; }
.meta-item { background: #f8fafc; border: 1px solid #e5e7eb; border-radius: 10px; padding: 8px 10px; display: flex; flex-direction: column; gap: 2px; }
.meta-item span { font-size: 11px; color: #6b7280; }
.meta-item strong { font-size: 13px; color: #111827; font-weight: 600; }
.model-actions { display: flex; flex-direction: column; gap: 2px; }
.model-actions :deep(.el-button) { width: 28px; height: 28px; }
.model-actions :deep(.el-button:hover) { background: #eef2ff; color: #4f6ef7; }
.test-result { font-size: 12px; padding: 6px 8px; border-radius: 6px; }
.test-result.ok { background: #ecfdf5; color: #059669; }
.test-result.fail { background: #fef2f2; color: #dc2626; }

.add-model-card {
  border: 2px dashed var(--border); border-radius: 14px; padding: 14px;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 8px; cursor: pointer; color: #9ca3af; min-height: 184px;
  transition: all .2s; font-size: 14px;
  background: linear-gradient(180deg, #ffffff 0%, #fcfdff 100%);
}
.add-model-card:hover { border-color: #4f6ef7; color: #4f6ef7; }

.providers-section h3 { font-size: 15px; font-weight: 600; margin-bottom: 14px; }
.providers-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; }
.provider-item { display: flex; align-items: center; gap: 10px; padding: 10px; border: 1px solid var(--border); border-radius: 8px; }
.provider-icon-lg { width: 36px; height: 36px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 18px; flex-shrink: 0; }
.provider-item-name { font-size: 13px; font-weight: 600; }
.provider-models { font-size: 11px; color: #9ca3af; margin-top: 2px; }
</style>
