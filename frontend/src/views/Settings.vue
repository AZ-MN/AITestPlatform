<template>
  <div class="settings-container">
    <div class="page-desc">
       <p class="subtitle">配置 AI 模型连接参数，管理您的生成能力。</p>
    </div>

    <!-- Stats Bar -->
    <div class="stats-bar">
      <div class="stat-item">
        <span class="stat-label">已配置模型</span>
        <span class="stat-value">{{ configs.length }}</span>
      </div>
      <div class="stat-divider"></div>
      <div class="stat-item">
        <span class="stat-label">默认模型</span>
        <span class="stat-value primary">{{ configs.find(c => c.is_default)?.model_name || '未设置' }}</span>
      </div>
      <div class="stat-divider"></div>
      
      <div class="provider-chips">
        <div v-for="p in providers" :key="p.id" class="provider-chip">
          <span class="chip-icon">{{ providerIcon(p.id) }}</span>
          <span class="chip-name">{{ p.name }}</span>
        </div>
      </div>

      <div class="header-actions">
        <el-button type="primary" :icon="Plus" @click="openAdd">添加模型</el-button>
      </div>
    </div>

    <!-- Models Area -->
    <div class="models-area" v-loading="loading">
      <!-- Empty State -->
      <div v-if="!loading && configs.length === 0" class="empty-state">
        <div class="empty-illustration">
          <div class="orbit-system">
             <div class="planet planet-1"></div>
             <div class="planet planet-2"></div>
             <div class="sun">🤖</div>
          </div>
        </div>
        <h3 class="empty-title">暂无模型配置</h3>
        <p class="empty-desc">您可以添加多个模型配置，并设置一个默认模型用于自动生成。</p>
        <div class="empty-actions">
           <el-button type="primary" size="large" :icon="Plus" @click="openAdd">立即添加模型</el-button>
        </div>
        <div class="quick-providers">
           <span class="quick-label">快速添加：</span>
           <div v-for="p in providers" :key="p.id" class="quick-provider" @click="openAddWithProvider(p.id)">
             {{ providerIcon(p.id) }} {{ p.name }}
           </div>
        </div>
      </div>

      <!-- Models Grid -->
      <div v-else class="models-grid">
        <div v-for="cfg in configs" :key="cfg.id" class="model-card">
          <div class="card-main">
            <div class="card-header">
              <div class="provider-logo" :class="`provider-${cfg.provider}`">
                {{ providerIcon(cfg.provider) }}
              </div>
              <div class="model-meta">
                <div class="model-name-row">
                  <span class="model-name" :title="cfg.model_name">{{ cfg.model_name }}</span>
                  <el-tag v-if="cfg.is_default" size="small" type="success" effect="dark" class="default-tag">默认</el-tag>
                </div>
                <div class="provider-name">{{ providerLabel(cfg.provider) }}</div>
              </div>
              <div class="card-menu">
                 <el-dropdown trigger="click" @command="(c) => handleCommand(c, cfg)">
                  <el-button link class="more-btn"><el-icon><MoreFilled /></el-icon></el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item command="test" :icon="Promotion">连通性测试</el-dropdown-item>
                      <el-dropdown-item command="edit" :icon="Edit">编辑配置</el-dropdown-item>
                      <el-dropdown-item command="delete" :icon="Delete" divided class="text-danger">删除</el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </div>
            
            <div class="card-params">
               <div class="param-item">
                 <span class="param-label">Temperature</span>
                 <span class="param-val">{{ cfg.temperature }}</span>
               </div>
               <div class="param-item">
                 <span class="param-label">Max Tokens</span>
                 <span class="param-val">{{ cfg.max_tokens }}</span>
               </div>
               <div class="param-item">
                 <span class="param-label">状态</span>
                 <span class="param-val">
                    <span class="status-indicator" :class="{active: cfg.is_active}"></span>
                    {{ cfg.is_active ? '已启用' : '禁用' }}
                 </span>
               </div>
            </div>
          </div>
        </div>

        <!-- Add Card -->
        <div class="add-card" @click="openAdd">
           <div class="add-inner">
             <div class="add-icon"><el-icon><Plus /></el-icon></div>
             <span class="add-text">添加模型配置</span>
           </div>
        </div>
      </div>
    </div>

    <!-- Edit Dialog -->
    <el-dialog 
      v-model="showDialog" 
      :title="editId ? '编辑模型配置' : '添加新模型'" 
      width="520px" 
      align-center
      destroy-on-close
      class="settings-dialog"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top" class="settings-form">
        <el-form-item label="供应商" prop="provider">
          <el-select v-model="form.provider" placeholder="选择供应商" style="width:100%" @change="onProviderChange">
            <el-option v-for="p in providers" :key="p.id" :value="p.id" :label="p.name">
              <span class="option-label">{{ p.name }}</span>
              <span class="option-icon">{{ providerIcon(p.id) }}</span>
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

        <div class="form-row two-cols">
          <el-form-item label="Temperature" prop="temperature_num" style="flex: 1">
            <el-input-number v-model="form.temperature_num" :min="0" :max="2" :step="0.1" controls-position="right" style="width: 100%" />
          </el-form-item>
          <el-form-item label="Max Tokens" prop="max_tokens" style="flex: 1">
            <el-input-number v-model="form.max_tokens" :min="100" :step="1000" controls-position="right" style="width: 100%" />
          </el-form-item>
        </div>

        <el-form-item>
          <el-checkbox v-model="form.is_default_bool" label="设为默认模型" border />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showDialog = false" plain>取消</el-button>
          <el-button type="primary" :loading="saving" @click="handleSave">保存配置</el-button>
        </div>
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
const loading = ref(false)
const showDialog = ref(false)
const saving = ref(false)
const editId = ref<number>()
const formRef = ref()

const form = reactive({
  provider: '', model_name: '', api_key: '', api_base_url: '',
  temperature_num: 0.7, max_tokens: 4096, is_default_bool: false
})

const rules = {
  provider: [{ required: true, message: '请选择供应商', trigger: 'change' }],
  model_name: [{ required: true, message: '请输入模型名称', trigger: 'change' }],
}

onMounted(async () => {
  loadData()
})

async function loadData() {
  loading.value = true
  try {
    configs.value = await modelApi.list()
    providers.value = await modelApi.providers()
  } finally {
    loading.value = false
  }
}

const currentModels = computed(() => {
  const p = providers.value.find(p => p.id === form.provider)
  return p?.models || []
})

// Actions
function openAdd() {
  editId.value = undefined
  resetForm()
  showDialog.value = true
}

function openAddWithProvider(providerId: string) {
  editId.value = undefined
  resetForm()
  form.provider = providerId
  onProviderChange()
  showDialog.value = true
}

function resetForm() {
  Object.assign(form, { 
    provider: '', model_name: '', api_key: '', api_base_url: '',
    temperature_num: 0.7, max_tokens: 4096, is_default_bool: false 
  })
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
  background: var(--bg);
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
.stat-value.primary { color: var(--primary); }
.stat-divider { width: 1px; height: 24px; background: var(--border); margin: 0 24px; }

.provider-chips { display: flex; gap: 8px; flex: 1; margin-left: 24px; overflow-x: auto; }
.provider-chip {
  display: flex; align-items: center; gap: 6px; padding: 6px 10px;
  background: var(--bg-secondary); border-radius: 6px;
  font-size: 12px; font-weight: 600; color: var(--text-primary);
  border: 1px solid transparent;
  flex-shrink: 0;
}

.header-actions { margin-left: auto; }

/* Models Area */
.models-area { flex: 1; overflow-y: auto; padding-bottom: 20px; min-height: 0; }

/* Empty State */
.empty-state {
  height: 400px;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  background: var(--card-bg); border-radius: var(--radius-lg); border: 1px dashed var(--border);
}
.empty-illustration { margin-bottom: 24px; font-size: 48px; opacity: 0.8; }
.orbit-system { position: relative; width: 100px; height: 100px; display: flex; align-items: center; justify-content: center; }
.sun { z-index: 2; font-size: 40px; }
.planet { position: absolute; border-radius: 50%; border: 1px solid var(--border); }
.planet-1 { width: 100%; height: 100%; animation: orbit 10s linear infinite; }
.planet-2 { width: 70%; height: 70%; animation: orbit 7s linear infinite reverse; }
@keyframes orbit { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

.empty-title { font-size: 18px; font-weight: 700; color: var(--text-primary); margin-bottom: 8px; }
.empty-desc { font-size: 14px; color: var(--text-secondary); margin-bottom: 24px; max-width: 400px; text-align: center; }
.quick-providers { margin-top: 32px; display: flex; align-items: center; gap: 12px; }
.quick-label { font-size: 13px; color: var(--text-secondary); }
.quick-provider {
  padding: 6px 12px; background: var(--bg-secondary); border-radius: 20px;
  font-size: 13px; cursor: pointer; transition: all 0.2s;
  display: flex; align-items: center; gap: 6px;
  border: 1px solid transparent;
}
.quick-provider:hover { background: var(--primary-light); color: var(--primary); border-color: var(--primary); }

/* Models Grid */
.models-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 24px;
}

.model-card {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 16px;
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex; flex-direction: column;
}
.model-card:hover { transform: translateY(-4px); box-shadow: var(--shadow-md); border-color: var(--primary-light); }

.card-main { padding: 20px; flex: 1; display: flex; flex-direction: column; gap: 16px; }

.card-header { display: flex; gap: 12px; align-items: flex-start; }
.provider-logo {
  width: 48px; height: 48px; border-radius: 12px;
  background: var(--bg-secondary);
  display: flex; align-items: center; justify-content: center; font-size: 24px;
}
.provider-openai .provider-logo { background: rgba(16, 163, 127, 0.1); color: #10a37f; }
.provider-anthropic .provider-logo { background: rgba(204, 120, 92, 0.1); color: #cc785c; }
.provider-deepseek .provider-logo { background: rgba(59, 130, 246, 0.1); color: #3b82f6; }

.model-meta { flex: 1; min-width: 0; }
.model-name-row { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.model-name { font-weight: 700; font-size: 16px; color: var(--text-primary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 100%; }
.provider-name { font-size: 13px; color: var(--text-secondary); }

.card-params {
  display: flex; justify-content: space-between;
  background: var(--bg-secondary); border-radius: 8px; padding: 12px;
}
.param-item { display: flex; flex-direction: column; gap: 2px; }
.param-label { font-size: 11px; color: var(--text-secondary); text-transform: uppercase; }
.param-val { font-size: 13px; font-weight: 600; color: var(--text-primary); display: flex; align-items: center; gap: 6px; }

.status-indicator { width: 6px; height: 6px; border-radius: 50%; background: var(--text-placeholder); }
.status-indicator.active { background: #10b981; box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.2); }

/* Add Card */
.add-card {
  border: 2px dashed var(--border); border-radius: 16px;
  min-height: 200px;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; transition: all 0.2s;
  background: rgba(255,255,255,0.4);
}
.add-card:hover { border-color: var(--primary); background: var(--primary-light); }
.add-inner { display: flex; flex-direction: column; align-items: center; gap: 12px; color: var(--text-secondary); }
.add-icon { width: 48px; height: 48px; border-radius: 50%; background: #fff; display: flex; align-items: center; justify-content: center; font-size: 24px; box-shadow: var(--shadow-sm); transition: transform 0.2s; }
.add-card:hover .add-icon { transform: scale(1.1); color: var(--primary); }
.add-text { font-weight: 600; font-size: 14px; }

.form-row.two-cols { display: flex; gap: 20px; }
.option-label { float: left; }
.option-icon { float: right; color: var(--text-secondary); font-size: 14px; }
.dialog-footer { display: flex; justify-content: flex-end; gap: 12px; margin-top: 8px; }

@media (max-width: 1024px) {
  .info-banner { flex-direction: column; align-items: flex-start; gap: 16px; }
  .banner-right { border-left: none; padding-left: 0; border-top: 1px solid var(--border); padding-top: 16px; width: 100%; }
}
</style>