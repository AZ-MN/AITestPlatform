<template>
  <div>
    <div class="page-header">
      <h2>接口管理</h2>
      <div>
        <el-button icon="Upload" @click="showImport=true">导入Swagger</el-button>
        <el-button type="primary" icon="Plus" @click="showDialog=true">手动录入</el-button>
      </div>
    </div>
    <el-table :data="list" border stripe v-loading="loading">
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="module" label="模块" width="120" />
      <el-table-column prop="method" label="Method" width="100">
        <template #default="{row}">
          <el-tag :type="{GET:'success',POST:'',PUT:'warning',DELETE:'danger',PATCH:'warning'}[row.method]||''" size="small">{{row.method}}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="path" label="路径" show-overflow-tooltip />
      <el-table-column prop="name" label="接口名称" show-overflow-tooltip />
      <el-table-column prop="source" label="来源" width="100"><template #default="{row}"><el-tag size="small" type="info">{{row.source}}</el-tag></template></el-table-column>
      <el-table-column label="操作" width="200">
        <template #default="{row}">
          <el-button link type="primary" @click="goDebug(row)">调试</el-button>
          <el-button link type="success" @click="aiGenerateCases(row)">AI生成用例</el-button>
          <el-button link type="danger" @click="deleteApi(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-dialog v-model="showImport" title="导入Swagger/OpenAPI" width="600px">
      <el-input v-model="swaggerText" type="textarea" :rows="12" placeholder="粘贴Swagger/OpenAPI JSON内容..." style="font-family:monospace;font-size:12px" />
      <template #footer>
        <el-button @click="showImport=false">取消</el-button>
        <el-button type="primary" :loading="importing" @click="importSwagger">导入</el-button>
      </template>
    </el-dialog>
  </div>
</template>
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { apitestApi } from '@/api/modules'
import { useProjectStore } from '@/stores/project'
const router = useRouter()
const projectStore = useProjectStore()
const list = ref<any[]>([])
const loading = ref(false)
const importing = ref(false)
const showDialog = ref(false)
const showImport = ref(false)
const swaggerText = ref('')
const fetchList = async () => {
  if (!projectStore.currentProject) return
  loading.value=true; try { list.value=(await apitestApi.listDefinitions({project_id:projectStore.currentProject.id})) as any[] } finally { loading.value=false }
}
const importSwagger = async () => {
  importing.value=true; try {
    const swagger = JSON.parse(swaggerText.value)
    const res:any = await apitestApi.importSwagger({project_id:projectStore.currentProject!.id, swagger_content:swagger})
    ElMessage.success(res.message); showImport.value=false; fetchList()
  } catch(e:any) { ElMessage.error('JSON格式错误: '+e.message) } finally { importing.value=false }
}
const goDebug = (row:any) => router.push({path:'/apitest/debug',query:{url:`http://localhost:8080${row.path}`,method:row.method}})
const aiGenerateCases = async (row:any) => {
  const res:any = await apitestApi.aiGenerateCases({project_id:projectStore.currentProject!.id, api_definition_id:row.id, save_to_db:true})
  ElMessage.success(`AI生成 ${res.length} 条用例`)
}
const deleteApi = async (id:number) => { await ElMessageBox.confirm('确认删除？','提示',{type:'warning'}); await apitestApi.deleteDefinition(id); fetchList() }
onMounted(fetchList)
</script>
