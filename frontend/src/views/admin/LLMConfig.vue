<template>
  <div>
    <div class="page-header">
      <h2>AI模型配置</h2>
      <el-button type="primary" icon="Plus" @click="showDialog = true">新增配置</el-button>
    </div>

    <el-table :data="configs" border stripe v-loading="loading">
      <el-table-column prop="name" label="配置名称" />
      <el-table-column prop="provider" label="提供商">
        <template #default="{ row }">
          <el-tag>{{ providerLabels[row.provider] || row.provider }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="model_name" label="模型版本" />
      <el-table-column prop="endpoint" label="API端点" show-overflow-tooltip />
      <el-table-column prop="max_tokens" label="最大Token" width="110" />
      <el-table-column prop="timeout" label="超时(s)" width="90" />
      <el-table-column label="默认">
        <template #default="{ row }">
          <el-tag v-if="row.is_default" type="success">默认</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160">
        <template #default="{ row }">
          <el-button link type="primary" @click="testConnection(row)">测试连接</el-button>
          <el-button link type="danger" @click="deleteConfig(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="showDialog" title="新增LLM配置" width="520px">
      <el-form :model="form" label-width="110px">
        <el-form-item label="配置名称" required>
          <el-input v-model="form.name" placeholder="如: GPT-4生产配置" />
        </el-form-item>
        <el-form-item label="提供商" required>
          <el-select v-model="form.provider" @change="onProviderChange">
            <el-option v-for="(label, val) in providerLabels" :key="val" :label="label" :value="val" />
          </el-select>
        </el-form-item>
        <el-form-item label="API Key" required>
          <el-input v-model="form.api_key" type="password" show-password placeholder="sk-..." />
        </el-form-item>
        <el-form-item label="API端点">
          <el-input v-model="form.endpoint" placeholder="https://api.openai.com/v1" />
        </el-form-item>
        <el-form-item label="模型版本">
          <el-input v-model="form.model_name" placeholder="gpt-4o" />
        </el-form-item>
        <el-form-item label="最大Token">
          <el-input-number v-model="form.max_tokens" :min="512" :max="128000" />
        </el-form-item>
        <el-form-item label="超时时间(s)">
          <el-input-number v-model="form.timeout" :min="10" :max="300" />
        </el-form-item>
        <el-form-item label="设为默认">
          <el-switch v-model="form.is_default" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveConfig">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { llmConfigApi } from '@/api/modules'

const configs = ref<any[]>([])
const loading = ref(false)
const saving = ref(false)
const showDialog = ref(false)
const form = reactive({
  name: '', provider: 'openai', api_key: '', endpoint: '', model_name: 'gpt-4o',
  max_tokens: 4096, timeout: 60, temperature: 0.7, is_default: false,
})
const providerLabels: Record<string, string> = {
  openai: 'OpenAI', qianwen: '通义千问', wenxin: '文心一言', xunfei: '讯飞星火', custom: '自定义'
}
const providerDefaults: Record<string, Partial<typeof form>> = {
  openai: { endpoint: 'https://api.openai.com/v1', model_name: 'gpt-4o' },
  qianwen: { endpoint: 'https://dashscope.aliyuncs.com/compatible-mode/v1', model_name: 'qwen-turbo' },
  wenxin: { endpoint: 'https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat', model_name: 'ernie-4.0' },
}

const onProviderChange = (val: string) => {
  const defaults = providerDefaults[val] || {}
  Object.assign(form, defaults)
}

const fetchConfigs = async () => {
  loading.value = true
  try { configs.value = (await llmConfigApi.list()) as any[] } finally { loading.value = false }
}

const saveConfig = async () => {
  saving.value = true
  try {
    await llmConfigApi.create(form)
    ElMessage.success('保存成功')
    showDialog.value = false
    fetchConfigs()
  } finally { saving.value = false }
}

const testConnection = async (row: any) => {
  const res: any = await llmConfigApi.test(row.id)
  if (res.status === 'success') {
    ElMessage.success(`连接成功: ${res.response}`)
  } else {
    ElMessage.error(`连接失败: ${res.error}`)
  }
}

const deleteConfig = async (id: number) => {
  await ElMessageBox.confirm('确认删除此配置？', '警告', { type: 'warning' })
  await llmConfigApi.delete(id)
  ElMessage.success('删除成功')
  fetchConfigs()
}

onMounted(fetchConfigs)
</script>
