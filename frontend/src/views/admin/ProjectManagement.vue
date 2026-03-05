<template>
  <div>
    <div class="page-header"><h2>项目管理</h2><el-button type="primary" icon="Plus" @click="showDialog=true">新建项目</el-button></div>
    <el-table :data="list" border stripe v-loading="loading">
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="name" label="项目名称" />
      <el-table-column prop="description" label="描述" show-overflow-tooltip />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{row}"><el-tag :type="row.status==='active'?'success':'info'" size="small">{{row.status==='active'?'进行中':'已归档'}}</el-tag></template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="160"><template #default="{row}">{{row.created_at?.substring(0,16)}}</template></el-table-column>
      <el-table-column label="操作" width="150">
        <template #default="{row}">
          <el-button link type="primary" @click="setCurrentProject(row)">切换</el-button>
          <el-button link type="danger" @click="deleteProject(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-dialog v-model="showDialog" title="新建项目" width="500px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="项目名称" required><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="项目描述"><el-input v-model="form.description" type="textarea" :rows="3" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog=false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveProject">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { projectApi } from '@/api/modules'
import { useProjectStore } from '@/stores/project'
const projectStore = useProjectStore()
const list = ref<any[]>([])
const loading = ref(false)
const saving = ref(false)
const showDialog = ref(false)
const form = reactive({ name: '', description: '' })
const fetchList = async () => { loading.value=true; try { list.value=(await projectApi.list()) as any[] } finally { loading.value=false } }
const saveProject = async () => { saving.value=true; try { await projectApi.create(form); ElMessage.success('创建成功'); showDialog.value=false; fetchList() } finally { saving.value=false } }
const setCurrentProject = (row: any) => { projectStore.setCurrentProject(row); ElMessage.success(`已切换到项目: ${row.name}`) }
const deleteProject = async (id: number) => { await ElMessageBox.confirm('确认删除？','提示',{type:'warning'}); await projectApi.delete(id); fetchList() }
onMounted(fetchList)
</script>
