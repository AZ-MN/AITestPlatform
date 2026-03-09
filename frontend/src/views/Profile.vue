<template>
  <div class="profile-page">
    <div class="page-header"><h2>个人设置</h2></div>

    <div class="profile-layout">
      <div class="profile-card page-card">
        <div class="avatar-section">
          <el-avatar :size="80" :style="{ background: '#4f6ef7', fontSize: '32px' }">
            {{ auth.user?.full_name?.charAt(0) || 'U' }}
          </el-avatar>
          <div>
            <div class="user-name">{{ auth.user?.full_name }}</div>
            <div class="user-role">{{ roleLabel(auth.user?.role) }}</div>
            <div class="user-email">{{ auth.user?.email }}</div>
          </div>
        </div>

        <el-divider />

        <el-form ref="formRef" :model="form" label-width="90px">
          <el-form-item label="姓名">
            <el-input v-model="form.full_name" />
          </el-form-item>
          <el-form-item label="旧密码">
            <el-input v-model="form.old_password" type="password" show-password placeholder="不修改密码则留空" />
          </el-form-item>
          <el-form-item label="新密码">
            <el-input v-model="form.new_password" type="password" show-password placeholder="不修改密码则留空" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="saving" @click="handleSave">保存修改</el-button>
          </el-form-item>
        </el-form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { authApi } from '@/api/auth'

const auth = useAuthStore()
const saving = ref(false)
const formRef = ref()

const form = reactive({
  full_name: auth.user?.full_name || '',
  old_password: '',
  new_password: '',
})

function roleLabel(role?: string) {
  return { super_admin: '超级管理员', project_admin: '项目管理员', test_lead: '测试负责人',
    test_engineer: '测试工程师', developer: '研发工程师', pm: '产品经理' }[role || ''] || role || ''
}

async function handleSave() {
  saving.value = true
  try {
    const payload: any = { full_name: form.full_name }
    if (form.new_password) {
      payload.old_password = form.old_password
      payload.new_password = form.new_password
    }
    await authApi.updateMe(payload)
    await auth.fetchMe()
    ElMessage.success('保存成功')
    form.old_password = ''
    form.new_password = ''
  } finally { saving.value = false }
}
</script>

<style scoped>
.profile-page { max-width: 600px; }
.page-header { margin-bottom: 20px; }
.page-header h2 { font-size: 22px; font-weight: 700; }
.avatar-section { display: flex; align-items: center; gap: 20px; margin-bottom: 20px; }
.user-name { font-size: 18px; font-weight: 600; }
.user-role { font-size: 13px; color: #4f6ef7; margin: 4px 0; }
.user-email { font-size: 13px; color: var(--text-secondary); }
</style>
