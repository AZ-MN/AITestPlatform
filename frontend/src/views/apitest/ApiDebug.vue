<template>
  <div>
    <div class="page-header">
      <h2>接口调试</h2>
    </div>
    <el-row :gutter="16" style="height: calc(100vh - 140px)">
      <!-- 左：请求配置 -->
      <el-col :span="12">
        <el-card style="height: 100%">
          <div style="display:flex;gap:8px;margin-bottom:12px">
            <el-select v-model="req.method" style="width:110px">
              <el-option v-for="m in ['GET','POST','PUT','DELETE','PATCH']" :key="m" :label="m" :value="m" />
            </el-select>
            <el-input v-model="req.url" placeholder="https://api.example.com/endpoint" style="flex:1" />
            <el-button type="primary" :loading="sending" @click="sendRequest">发送</el-button>
          </div>
          <el-tabs v-model="activeTab">
            <el-tab-pane label="Headers" name="headers">
              <div v-for="(h, i) in headerList" :key="i" style="display:flex;gap:8px;margin-bottom:6px">
                <el-input v-model="h.key" placeholder="Header名" size="small" />
                <el-input v-model="h.value" placeholder="值" size="small" />
                <el-button size="small" icon="Delete" @click="headerList.splice(i,1)" />
              </div>
              <el-button size="small" icon="Plus" @click="headerList.push({key:'',value:''})">添加</el-button>
            </el-tab-pane>
            <el-tab-pane label="Params" name="params">
              <div v-for="(p, i) in paramList" :key="i" style="display:flex;gap:8px;margin-bottom:6px">
                <el-input v-model="p.key" placeholder="参数名" size="small" />
                <el-input v-model="p.value" placeholder="值" size="small" />
                <el-button size="small" icon="Delete" @click="paramList.splice(i,1)" />
              </div>
              <el-button size="small" icon="Plus" @click="paramList.push({key:'',value:''})">添加</el-button>
            </el-tab-pane>
            <el-tab-pane label="Body" name="body">
              <el-input v-model="bodyText" type="textarea" :rows="14" placeholder='{"key": "value"}' style="font-family: monospace; font-size:13px" />
            </el-tab-pane>
          </el-tabs>
        </el-card>
      </el-col>
      <!-- 右：响应结果 -->
      <el-col :span="12">
        <el-card style="height: 100%">
          <div v-if="response" style="font-size:13px">
            <div style="display:flex;gap:16px;margin-bottom:12px;align-items:center">
              <el-tag :type="response.status_code < 300 ? 'success' : 'danger'" size="large">
                {{ response.status_code }}
              </el-tag>
              <span style="color:#909399">{{ response.response_time_ms }} ms</span>
              <span style="color:#909399">{{ (response.size_bytes / 1024).toFixed(2) }} KB</span>
            </div>
            <el-tabs>
              <el-tab-pane label="响应体">
                <pre style="background:#f5f5f5;padding:12px;border-radius:4px;overflow:auto;max-height:400px;font-size:12px">{{ formattedBody }}</pre>
              </el-tab-pane>
              <el-tab-pane label="响应头">
                <el-table :data="responseHeaders" size="small">
                  <el-table-column prop="key" label="Header" />
                  <el-table-column prop="value" label="值" show-overflow-tooltip />
                </el-table>
              </el-tab-pane>
            </el-tabs>
          </div>
          <el-empty v-else description="发送请求后查看响应" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { apitestApi } from '@/api/modules'

const req = reactive({ method: 'GET', url: '', timeout: 30 })
const activeTab = ref('headers')
const sending = ref(false)
const response = ref<any>(null)
const headerList = ref<{ key: string; value: string }[]>([{ key: 'Content-Type', value: 'application/json' }])
const paramList = ref<{ key: string; value: string }[]>([])
const bodyText = ref('')

const sendRequest = async () => {
  if (!req.url) { ElMessage.warning('请输入请求URL'); return }
  sending.value = true
  try {
    const headers: Record<string, string> = {}
    headerList.value.filter(h => h.key).forEach(h => (headers[h.key] = h.value))
    const params: Record<string, string> = {}
    paramList.value.filter(p => p.key).forEach(p => (params[p.key] = p.value))
    let body = null
    if (bodyText.value.trim()) {
      try { body = JSON.parse(bodyText.value) } catch { body = bodyText.value }
    }
    response.value = await apitestApi.debug({ method: req.method, url: req.url, headers, params, body })
  } finally { sending.value = false }
}

const formattedBody = computed(() => {
  if (!response.value?.body) return ''
  if (typeof response.value.body === 'object') {
    return JSON.stringify(response.value.body, null, 2)
  }
  return String(response.value.body)
})

const responseHeaders = computed(() => {
  if (!response.value?.headers) return []
  return Object.entries(response.value.headers).map(([key, value]) => ({ key, value }))
})
</script>
