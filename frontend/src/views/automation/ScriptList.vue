<template>
  <div>
    <div class="page-header">
      <h2>脚本管理</h2>
      <div>
        <el-button icon="MagicStick" type="success" @click="showAiDialog=true">AI生成脚本</el-button>
        <el-button type="primary" icon="Plus" @click="createScript">新建脚本</el-button>
      </div>
    </div>
    <el-table :data="list" border stripe v-loading="loading">
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="name" label="脚本名称" />
      <el-table-column prop="script_type" label="类型" width="90"><template #default="{row}"><el-tag size="small">{{row.script_type==='api'?'API自动化':'UI自动化'}}</el-tag></template></el-table-column>
      <el-table-column prop="language" label="语言" width="90" />
      <el-table-column prop="version" label="版本" width="70" />
      <el-table-column label="AI生成" width="90"><template #default="{row}"><el-tag v-if="row.is_ai_generated" size="small" color="#722ed1" style="color:#fff">AI</el-tag></template></el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="160"><template #default="{row}">{{row.created_at?.substring(0,16)}}</template></el-table-column>
      <el-table-column label="操作" width="140">
        <template #default="{row}">
          <el-button link type="primary" @click="goEdit(row)">编辑</el-button>
          <el-button link type="danger">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-dialog v-model="showAiDialog" title="AI生成自动化脚本" width="560px">
      <el-form label-width="100px">
        <el-form-item label="脚本类型">
          <el-radio-group v-model="aiForm.script_type">
            <el-radio value="api">API自动化 (Pytest)</el-radio>
            <el-radio value="ui">UI自动化 (Playwright)</el-radio>
          </el-radio-group>
        </el-form-item>
        <template v-if="aiForm.script_type==='ui'">
          <el-form-item label="页面URL"><el-input v-model="aiForm.url" placeholder="https://..." /></el-form-item>
          <el-form-item label="操作步骤"><el-input v-model="aiForm.steps" type="textarea" :rows="5" placeholder="描述用户操作步骤..." /></el-form-item>
        </template>
        <el-form-item label="基础URL" v-if="aiForm.script_type==='api'"><el-input v-model="aiForm.base_url" placeholder="http://localhost:8080" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAiDialog=false">取消</el-button>
        <el-button type="primary" :loading="aiGenerating" @click="aiGenerate">生成</el-button>
      </template>
    </el-dialog>
  </div>
</template>
<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { automationApi } from '@/api/modules'
import { useProjectStore } from '@/stores/project'
const router = useRouter()
const projectStore = useProjectStore()
const list = ref<any[]>([])
const loading = ref(false)
const showAiDialog = ref(false)
const aiGenerating = ref(false)
const aiForm = reactive({ script_type:'api', url:'', steps:'', base_url:'http://localhost:8080' })
const fetchList = async () => {
  if (!projectStore.currentProject) return
  loading.value=true; try { list.value=(await automationApi.listScripts({project_id:projectStore.currentProject.id})) as any[] } finally { loading.value=false }
}
const createScript = async () => {
  const res:any = await automationApi.createScript({project_id:projectStore.currentProject!.id, name:'新脚本', content:'# 脚本内容', script_type:'api', language:'python'})
  router.push(`/automation/scripts/${res.id}`)
}
const goEdit = (row:any) => router.push(`/automation/scripts/${row.id}`)
const aiGenerate = async () => {
  aiGenerating.value=true; try {
    const res:any = await automationApi.aiGenerateScript({project_id:projectStore.currentProject!.id, ...aiForm})
    ElMessage.success('脚本生成成功'); showAiDialog.value=false; fetchList()
  } finally { aiGenerating.value=false }
}
onMounted(fetchList)
</script>
