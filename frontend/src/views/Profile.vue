<template>
  <div class="profile-page">
    <div class="page-desc">
       <p class="subtitle">管理您的个人信息和安全设置</p>
    </div>

    <div class="profile-card page-card">
      <div class="card-content">
        <!-- Sidebar Info -->
        <div class="profile-sidebar">
          <div class="avatar-wrapper">
            <el-avatar :size="100" class="profile-avatar">
              {{ auth.user?.full_name?.charAt(0) || 'U' }}
            </el-avatar>
            <div class="role-badge">{{ roleLabel(auth.user?.role) }}</div>
          </div>
          <div class="user-info-text">
            <h3 class="user-name">{{ auth.user?.full_name }}</h3>
            <p class="user-email">{{ auth.user?.email }}</p>
          </div>
        </div>

        <div class="divider-vertical"></div>

        <!-- Form Section -->
        <div class="form-section">
          <h3 class="section-title">基本信息</h3>
          <el-form ref="formRef" :model="form" label-position="top" class="profile-form">
            <el-form-item label="姓名">
              <el-input v-model="form.full_name" size="large" />
            </el-form-item>
            
            <div class="password-section">
              <h3 class="section-title">安全设置</h3>
              <el-form-item label="当前密码">
                <el-input 
                  v-model="form.old_password" 
                  type="password" 
                  show-password 
                  placeholder="如需修改密码，请先输入当前密码" 
                  size="large"
                />
              </el-form-item>
              <el-form-item label="新密码">
                <el-input 
                  v-model="form.new_password" 
                  type="password" 
                  show-password 
                  placeholder="输入新密码" 
                  size="large"
                />
              </el-form-item>
            </div>

            <div class="form-actions">
              <el-button type="primary" size="large" :loading="saving" @click="handleSave">保存更改</el-button>
            </div>
          </el-form>
        </div>
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
      if (!form.old_password) {
        ElMessage.warning('请输入当前密码以修改新密码')
        return
      }
      payload.old_password = form.old_password
      payload.new_password = form.new_password
    }
    await authApi.updateMe(payload)
    await auth.fetchMe()
    ElMessage.success('个人信息已更新')
    form.old_password = ''
    form.new_password = ''
  } catch (e) {
    // API handles errors usually
  } finally { saving.value = false }
}
</script>

<style scoped>
.profile-page { 
  width: 100%; 
  /* max-width removed for full width tiling */
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

.profile-card {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.card-content {
  display: flex;
  min-height: 400px;
}

.profile-sidebar {
  width: 280px;
  background: var(--bg-secondary);
  padding: 40px 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  border-right: 1px solid var(--border);
  flex-shrink: 0;
}

.avatar-wrapper {
  position: relative;
  margin-bottom: 20px;
}
.profile-avatar {
  background: linear-gradient(135deg, #4f46e5, #818cf8);
  font-size: 36px;
  font-weight: 600;
  border: 4px solid #fff;
  box-shadow: var(--shadow-md);
}
.role-badge {
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%) translateY(50%);
  background: #fff;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  color: var(--primary);
  border: 1px solid var(--border);
  box-shadow: var(--shadow-sm);
  white-space: nowrap;
}

.user-info-text { margin-top: 16px; overflow: hidden; width: 100%; }
.user-name { font-size: 20px; font-weight: 700; color: var(--text-primary); margin-bottom: 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.user-email { font-size: 14px; color: var(--text-secondary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.form-section {
  flex: 1;
  padding: 40px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 24px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border);
}

.profile-form {
  max-width: 400px;
}

.password-section { margin-top: 40px; }

.form-actions {
  margin-top: 40px;
}

@media (max-width: 768px) {
  .card-content { flex-direction: column; }
  .profile-sidebar { width: 100%; border-right: none; border-bottom: 1px solid var(--border); }
  .form-section { padding: 24px; }
  .profile-form { max-width: 100%; }
}
</style>
