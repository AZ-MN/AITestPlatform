<template>
  <div>
    <div class="page-header"><h2>用户管理</h2><el-button type="primary" icon="Plus" @click="showDialog=true">新增用户</el-button></div>
    <el-table :data="list" border stripe v-loading="loading">
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="username" label="账号" />
      <el-table-column prop="full_name" label="姓名" />
      <el-table-column prop="email" label="邮箱" />
      <el-table-column prop="phone" label="手机号" />
      <el-table-column label="状态" width="90"><template #default="{row}"><el-tag :type="row.is_active?'success':'danger'" size="small">{{row.is_active?'正常':'禁用'}}</el-tag></template></el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="160"><template #default="{row}">{{row.created_at?.substring(0,16)}}</template></el-table-column>
      <el-table-column label="操作" width="180">
        <template #default="{row}">
          <el-button link type="primary" @click="toggleActive(row)">{{row.is_active?'禁用':'启用'}}</el-button>
          <el-button link type="warning" @click="resetPwd(row)">重置密码</el-button>
          <el-button link type="danger" @click="deleteUser(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-dialog v-model="showDialog" title="新增用户" width="480px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="账号" required><el-input v-model="form.username" /></el-form-item>
        <el-form-item label="姓名"><el-input v-model="form.full_name" /></el-form-item>
        <el-form-item label="邮箱"><el-input v-model="form.email" /></el-form-item>
        <el-form-item label="手机号"><el-input v-model="form.phone" /></el-form-item>
        <el-form-item label="密码" required><el-input v-model="form.password" type="password" show-password /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog=false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveUser">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { userApi } from '@/api/modules'
const list = ref<any[]>([])
const loading = ref(false)
const saving = ref(false)
const showDialog = ref(false)
const form = reactive({ username: '', full_name: '', email: '', phone: '', password: '' })
const fetchList = async () => { loading.value=true; try { list.value=(await userApi.list()) as any[] } finally { loading.value=false } }
const saveUser = async () => { saving.value=true; try { await userApi.create(form); ElMessage.success('创建成功'); showDialog.value=false; fetchList() } finally { saving.value=false } }
const toggleActive = async (row: any) => { await userApi.update(row.id, {is_active: !row.is_active}); fetchList() }
const resetPwd = async (row: any) => { const {value} = await ElMessageBox.prompt('请输入新密码','重置密码',{inputType:'password'}); await userApi.resetPassword(row.id, value); ElMessage.success('密码已重置') }
const deleteUser = async (id: number) => { await ElMessageBox.confirm('确认删除？','提示',{type:'warning'}); await userApi.delete(id); fetchList() }
onMounted(fetchList)
</script>
