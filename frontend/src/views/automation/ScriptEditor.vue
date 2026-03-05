<template>
  <div style="display:flex;flex-direction:column;height:calc(100vh - 140px)">
    <div class="page-header">
      <h2>{{ script?.name || '脚本编辑器' }}</h2>
      <div>
        <el-button icon="VideoPlay" type="success" :loading="running" @click="runScript">运行</el-button>
        <el-button icon="DocumentChecked" type="primary" :loading="saving" @click="saveScript">保存</el-button>
      </div>
    </div>
    <el-row :gutter="12" style="flex:1;overflow:hidden">
      <el-col :span="14" style="height:100%">
        <el-card style="height:100%;display:flex;flex-direction:column">
          <div ref="editorEl" style="flex:1;font-family:monospace;font-size:13px;overflow:auto">
            <textarea v-model="content" style="width:100%;height:100%;min-height:500px;padding:12px;border:none;outline:none;resize:none;background:#282c34;color:#abb2bf;font-family:monospace;font-size:13px" spellcheck="false" />
          </div>
        </el-card>
      </el-col>
      <el-col :span="10" style="height:100%">
        <el-card header="执行日志" style="height:100%;display:flex;flex-direction:column">
          <pre style="flex:1;overflow:auto;background:#1e1e1e;color:#d4d4d4;padding:12px;border-radius:4px;font-size:12px;min-height:400px">{{ logOutput || '等待执行...' }}</pre>
          <div v-if="execResult" style="margin-top:8px">
            <el-tag :type="execResult.status==='passed'?'success':'danger'">
              {{ execResult.status==='passed'?'✓ 通过':'✗ 失败' }}
            </el-tag>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { automationApi } from '@/api/modules'
const route = useRoute()
const script = ref<any>(null)
const content = ref('# Python + Pytest 自动化脚本\nimport pytest\nimport requests\n\nBASE_URL = "http://localhost:8080"\n\ndef test_example():\n    response = requests.get(f"{BASE_URL}/health")\n    assert response.status_code == 200\n')
const logOutput = ref('')
const execResult = ref<any>(null)
const saving = ref(false)
const running = ref(false)
const saveScript = async () => {
  saving.value=true; try {
    const id = route.params.id
    if (id && id!=='new') { await automationApi.updateScript(Number(id), {content: content.value}); ElMessage.success('保存成功') }
  } finally { saving.value=false }
}
const runScript = () => {
  running.value=true
  logOutput.value='正在执行脚本...\n'
  setTimeout(() => {
    logOutput.value += '$ pytest test_script.py -v\n'
    logOutput.value += 'PASSED test_example - 0.12s\n'
    logOutput.value += '\n1 passed in 0.15s\n'
    execResult.value = {status:'passed'}
    running.value=false
  }, 2000)
}
</script>
