<template>
  <div class="members-page">
    <div class="page-header">
      <h2>项目成员</h2>
      <el-button type="primary" @click="openAdd">添加成员</el-button>
    </div>

    <div class="page-card">
      <el-table :data="members" v-loading="loading">
        <el-table-column prop="full_name" label="姓名" min-width="140" />
        <el-table-column prop="username" label="用户名" width="140" />
        <el-table-column prop="role" label="角色" width="140">
          <template #default="{ row }">
            <el-tag size="small">{{ row.role }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="加入时间" width="180">
          <template #default="{ row }">{{ fmtDate(row.joined_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="120" align="right">
          <template #default="{ row }">
            <el-button
              link
              type="danger"
              :disabled="row.user_id === projectStore.current?.created_by"
              @click="remove(row)"
            >
              移除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog v-model="showAdd" title="添加项目成员" width="420px" :close-on-click-modal="false">
      <el-form :model="form" label-width="90px">
        <el-form-item label="用户">
          <el-select v-model="form.user_id" placeholder="选择用户" style="width:100%" filterable>
            <el-option v-for="u in candidateUsers" :key="u.id" :label="`${u.full_name} (${u.username})`" :value="u.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="form.role" style="width:100%">
            <el-option label="项目管理员" value="project_admin" />
            <el-option label="测试工程师" value="tester" />
            <el-option label="访客" value="viewer" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAdd=false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="add">添加</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { projectApi } from '@/api/projects'
import { authApi } from '@/api/auth'
import { useProjectStore } from '@/stores/project'
import type { ProjectMember, User } from '@/api/types'

const route = useRoute()
const projectStore = useProjectStore()
const projectId = computed(() => Number(route.params.id))
const loading = ref(false)
const saving = ref(false)
const showAdd = ref(false)
const members = ref<ProjectMember[]>([])
const users = ref<User[]>([])
const form = reactive({ user_id: undefined as number | undefined, role: 'tester' })

const candidateUsers = computed(() => {
  const joined = new Set(members.value.map(m => m.user_id))
  return users.value.filter(u => !joined.has(u.id))
})

onMounted(async () => {
  await projectStore.fetchProject(projectId.value)
  await load()
})

async function load() {
  loading.value = true
  try {
    members.value = await projectApi.members(projectId.value)
    users.value = await authApi.listUsers()
  } finally { loading.value = false }
}

function openAdd() {
  form.user_id = undefined
  form.role = 'tester'
  showAdd.value = true
}

async function add() {
  if (!form.user_id) return ElMessage.warning('请选择用户')
  saving.value = true
  try {
    await projectApi.addMember(projectId.value, { user_id: form.user_id, role: form.role })
    ElMessage.success('成员添加成功')
    showAdd.value = false
    await load()
  } finally { saving.value = false }
}

async function remove(member: ProjectMember) {
  await ElMessageBox.confirm(`确认移除成员「${member.full_name}」？`, '移除确认', {
    type: 'warning',
    closeOnClickModal: false,
    closeOnPressEscape: false,
  })
  await projectApi.removeMember(projectId.value, member.id)
  ElMessage.success('成员已移除')
  await load()
}

function fmtDate(s: string) {
  return new Date(s).toLocaleString('zh-CN', { dateStyle: 'short', timeStyle: 'short' })
}
</script>
