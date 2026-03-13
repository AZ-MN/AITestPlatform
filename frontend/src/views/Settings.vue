<template>
  <div class="settings-container">
    <div class="page-header">
      <div class="header-content">
        <h2>模型设置</h2>
        <p class="subtitle">配置 AI 模型连接参数，管理您的生成能力。</p>
      </div>
      <el-button type="primary" :icon="Plus" @click="openAdd">添加模型</el-button>
    </div>

    <div class="settings-content">
      <!-- Top Info Section -->
      <div class="top-section">
        <div class="info-card">
          <div class="info-header">
            <el-icon class="info-icon"><InfoFilled /></el-icon>
            <h4>配置说明</h4>
          </div>
          <p class="info-text">
            配置 API Key 后即可启用 AI 生成功能。建议至少配置一个模型（如 OpenAI、Claude 或 DeepSeek）以保证生成质量。
          </p>
        </div>

        <div class="providers-card">
          <div class="providers-header">
             <h4>支持的供应商</h4>
          </div>
          <div class="providers-row">
             <div v-for="p in providers" :key="p.id" class="provider-badge">
                <span class="p-icon-small">{{ providerIcon(p.id) }}</span>
                <span class="p-name-small">{{ p.name }}</span>
             </div>
          </div>
        </div>
      </div>

      <div class="models-grid">
          <div v-for="cfg in configs" :key="cfg.id" class="model-card">
            <div class="card-header">
              <div class="provider-logo" :class="`provider-${cfg.provider}`">
                {{ providerIcon(cfg.provider) }}
              </div>
              <div class="model-info">
                <div class="model-name-row">
                  <span class="model-name" :title="cfg.model_name">{{ cfg.model_name }}</span>
                  <el-tag v-if="cfg.is_default" size="small" effect="dark" type="success" class="default-tag">默认</el-tag>
                </div>
                <div class="provider-name">{{ providerLabel(cfg.provider) }}</div>
              </div>
              <div class="card-actions">
                <el-dropdown trigger="click" @command="(c) => handleCommand(c, cfg)">
                  <el-button link class="more-btn"><el-icon><MoreFilled /></el-icon></el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item command="test" :icon="Promotion">连通性测试</el-dropdown-item>
                      <el-dropdown-item command="edit" :icon="Edit">编辑配置</el-dropdown-item>
                      <el-dropdown-item command="delete" :icon="Delete" divided class="text-danger">删除配置</el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </div>
            
            <div class="card-body">
              <div class="stat-row">
                <span class="stat-label">Temperature</span>
                <span class="stat-val">{{ cfg.temperature }}</span>
              </div>
              <div class="stat-row">
                <span class="stat-label">Max Tokens</span>
                <span class="stat-val">{{ cfg.max_tokens }}</span>
              </div>
              <div class="stat-row">
                <span class="stat-label">状态</span>
                <span class="stat-val">
                  <span class="status-dot" :class="{ active: cfg.is_active }"></span>
                  {{ cfg.is_active ? '已启用' : '禁用' }}
                </span>
              </div>
            </div>
          </div>

          <!-- Add New Card -->
          <div class="add-card" @click="openAdd">
            <div class="add-icon"><el-icon><Plus /></el-icon></div>
            <span class="add-text">配置新模型</span>
          </div>
        </div>
      </div>

    <!-- Edit Dialog -->
    <el-dialog 
      v-model="showDialog" 
      :title="editId ? '编辑模型' : '添加模型'" 
      width="500px" 
      align-center
      destroy-on-close
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <el-form-item label="供应商" prop="provider">
          <el-select v-model="form.provider" placeholder="选择供应商" style="width:100%" @change="onProviderChange">
            <el-option v-for="p in providers" :key="p.id" :value="p.id" :label="p.name">
              <span style="float: left">{{ p.name }}</span>
              <span style="float: right; color: var(--text-secondary); font-size: 12px">{{ providerIcon(p.id) }}</span>
            </el-option>
          </el-select>
        </el-form-item>
        
        <el-form-item label="模型名称" prop="model_name">
          <el-select 
            v-model="form.model_name" 
            placeholder="选择或输入模型名称" 
            style="width:100%" 
            allow-create 
            filterable 
            default-first-option
          >
            <el-option v-for="m in currentModels" :key="m" :value="m" :label="m" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="API Key" prop="api_key">
          <el-input v-model="form.api_key" type="password" show-password placeholder="输入 API 密钥" />
        </el-form-item>
        
        <el-form-item label="API Base URL (可选)">
          <el-input v-model="form.api_base_url" placeholder="默认使用官方地址，无需修改" />
        </el-form-item>

        <div class="form-row">
          <el-form-item label="默认温度" style="flex: 1">
            <el-input-number v-model="form.temperature_num" :min="0" :max="2" :step="0.1" controls-position="right" style="width: 100%" />
          </el-form-item>
          <el-form-item label="最大 Token" style="flex: 1">
            <el-input-number v-model="form.max_tokens" :min="100" :step="1000" controls-position="right" style="width: 100%" />
          </el-form-item>
        </div>

        <el-form-item>
          <el-checkbox v-model="form.is_default_bool" label="设为默认模型" border />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存配置</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { Plus, Edit, Delete, Promotion, MoreFilled, InfoFilled } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { modelApi } from '@/api/models'
import type { AIModelConfig } from '@/api/types'

const configs = ref<AIModelConfig[]>([])
const providers = ref<any[]>([])
const showDialog = ref(false)
const saving = ref(false)
const editId = ref<number>()
const formRef = ref()

const form = reactive({
  provider: '', model_name: '', api_key: '', api_base_url: '',
  temperature_num: 0.3, max_tokens: 4096, is_default_bool: false
})

const rules = {
  provider: [{ required: true, message: '请选择供应商', trigger: 'change' }],
  model_name: [{ required: true, message: '请输入模型名称', trigger: 'change' }],
}

onMounted(async () => {
  loadData()
})

async function loadData() {
  configs.value = await modelApi.list()
  providers.value = await modelApi.providers()
}

const currentModels = computed(() => {
  const p = providers.value.find(p => p.id === form.provider)
  return p?.models || []
})

// Actions
function openAdd() {
  editId.value = undefined
  Object.assign(form, { 
    provider: '', model_name: '', api_key: '', api_base_url: '',
    temperature_num: 0.7, max_tokens: 4096, is_default_bool: false 
  })
  showDialog.value = true
}

function handleCommand(cmd: string, cfg: AIModelConfig) {
  if (cmd === 'test') testModel(cfg)
  if (cmd === 'edit') editConfig(cfg)
  if (cmd === 'delete') removeConfig(cfg)
}

function editConfig(cfg: AIModelConfig) {
  editId.value = cfg.id
  Object.assign(form, {
    provider: cfg.provider, model_name: cfg.model_name,
    api_key: '', api_base_url: cfg.api_base_url || '',
    temperature_num: parseFloat(cfg.temperature) || 0.7,
    max_tokens: cfg.max_tokens, is_default_bool: !!cfg.is_default
  })
  showDialog.value = true
}

async function handleSave() {
  if (!formRef.value) return
  await formRef.value.validate()
  
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
      ElMessage.success('配置已更新')
    } else {
      await modelApi.add(payload)
      ElMessage.success('配置已添加')
    }
    loadData()
    showDialog.value = false
  } catch (e) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

async function testModel(cfg: AIModelConfig) {
  const load = ElMessage.info({ message: '正在测试连通性...', duration: 0 })
  try {
    const res = await modelApi.test(cfg.id)
    load.close()
    if (res?.ok) ElMessage.success(`测试成功：${cfg.model_name} 可用`)
    else ElMessage.error(`测试失败：${res?.error || '连接超时或配置错误'}`)
  } catch {
    load.close()
    ElMessage.error('网络请求失败')
  }
}

async function removeConfig(cfg: AIModelConfig) {
  try {
    await ElMessageBox.confirm(`确定删除 ${cfg.model_name} 吗？`, '删除确认', { type: 'warning' })
    await modelApi.remove(cfg.id)
    ElMessage.success('已删除')
    loadData()
  } catch {}
}

function onProviderChange() {
  const p = providers.value.find(p => p.id === form.provider)
  if (p?.models?.length) form.model_name = p.models[0]
}

// Helpers
function providerLabel(id: string) { return providers.value.find(p => p.id === id)?.name || id }
function providerIcon(id: string) {
  const map: any = { openai: '🤖', anthropic: '🔮', tongyi: '🌟', zhipu: '🧠', deepseek: '🐋' }
  return map[id] || '🤖'
}
</script>

<style scoped>
.settings-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}
.page-header h2 {
  font-size: 24px;
  font-weight: 800;
  color: var(--text-primary);
  margin-bottom: 4px;
}
.subtitle { color: var(--text-secondary); font-size: 14px; }

/* Layout */
.settings-layout {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* Top Section */
.top-section {
  display: flex;
  gap: 20px;
}

/* Info Card */
.info-card {
  flex: 1;
  background: var(--card-bg);
  border-radius: var(--radius-lg);
  padding: 24px;
  border: 1px solid var(--border);
  box-shadow: var(--shadow-sm);
  display: flex;
  flex-direction: column;
  justify-content: center;
}
.info-header { 
  display: flex; 
  align-items: center; 
  gap: 10px; 
  margin-bottom: 12px; 
  color: var(--primary); 
}
.info-icon { font-size: 20px; }
.info-header h4 { 
  font-size: 16px; 
  font-weight: 700; 
  color: var(--text-primary); 
  margin: 0; 
}
.info-text { 
  font-size: 14px; 
  color: var(--text-secondary); 
  line-height: 1.6; 
  margin: 0;
}

/* Providers Card */
.providers-card {
  width: 420px;
  background: var(--card-bg);
  border-radius: var(--radius-lg);
  padding: 24px;
  border: 1px solid var(--border);
  box-shadow: var(--shadow-sm);
  display: flex;
  flex-direction: column;
  justify-content: center;
}
.providers-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}
.providers-header h3 { 
  font-size: 15px; 
  font-weight: 700; 
  margin: 0; 
  color: var(--text-primary);
}
.provider-tags { 
  display: flex; 
  gap: 12px; 
  flex-wrap: wrap; 
}
.provider-tag {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: var(--bg-secondary);
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  border: 1px solid transparent;
  transition: all 0.2s;
}
.provider-tag:hover {
  border-color: var(--primary);
  background: var(--primary-light);
  color: var(--primary);
  transform: translateY(-1px);
}

/* Grid */
.models-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.model-card {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 20px;
  transition: all 0.3s;
}
.model-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
  border-color: var(--primary-light);
}

.card-header { display: flex; gap: 12px; align-items: flex-start; margin-bottom: 20px; }
.provider-logo {
  width: 44px; height: 44px;
  border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  font-size: 22px;
  background: var(--bg-secondary);
}
.provider-openai { color: #10a37f; background: rgba(16, 163, 127, 0.1); }
.provider-anthropic { color: #cc785c; background: rgba(204, 120, 92, 0.1); }

.model-info { flex: 1; min-width: 0; }
.model-name-row { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.model-name { 
  font-weight: 700; 
  font-size: 16px; 
  color: var(--text-primary); 
  overflow: hidden; 
  text-overflow: ellipsis; 
  white-space: nowrap; 
  max-width: 100%;
}
.provider-name { font-size: 13px; color: var(--text-secondary); }
.default-tag { height: 18px; padding: 0 6px; font-size: 11px; }

.card-body {
  background: var(--bg-secondary);
  border-radius: 8px;
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.stat-row { display: flex; justify-content: space-between; font-size: 13px; }
.stat-label { color: var(--text-secondary); }
.stat-val { font-weight: 600; color: var(--text-primary); display: flex; align-items: center; gap: 6px; }
.status-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--text-placeholder); }
.status-dot.active { background: #10b981; }

.add-card {
  border: 2px dashed var(--border);
  border-radius: var(--radius-lg);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  cursor: pointer;
  min-height: 180px;
  transition: all 0.2s;
  background: rgba(255,255,255,0.5);
  color: var(--text-placeholder);
}
.add-card:hover { border-color: var(--primary); background: var(--primary-light); color: var(--primary); }
.add-icon { 
  width: 40px; height: 40px; border-radius: 50%; background: #fff; 
  display: flex; align-items: center; justify-content: center; 
  font-size: 20px; box-shadow: var(--shadow-sm);
}
.add-text { font-weight: 600; font-size: 14px; }

/* Providers Section */
.providers-section {
  background: var(--card-bg);
  border-radius: var(--radius-lg);
  padding: 20px;
  border: 1px solid var(--border);
}
.providers-section h3 { font-size: 14px; font-weight: 700; margin-bottom: 12px; }
.providers-list { display: flex; flex-direction: column; gap: 10px; }
.provider-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px;
  border-radius: 8px;
  transition: background 0.2s;
  cursor: default;
}
.provider-item:hover { background: var(--bg-secondary); }
.p-icon { font-size: 20px; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; background: #fff; border-radius: 6px; border: 1px solid var(--border); }
.p-details { display: flex; flex-direction: column; }
.p-name { font-size: 13px; font-weight: 600; }
.p-models { font-size: 11px; color: var(--text-secondary); }

.form-row { display: flex; gap: 16px; }
.text-danger { color: var(--danger); }

@media (max-width: 1024px) {
  .top-section { flex-direction: column; }
  .providers-card { width: 100%; }
}
</style>
