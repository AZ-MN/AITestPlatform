<template>
  <div class="login-page">
    <div class="login-box">
      <div class="login-header">
        <div class="logo">🧪</div>
        <h1>AI 测试用例智能生成平台</h1>
        <p>智能生成 · 全流程管理 · 协同提效</p>
      </div>

      <el-form ref="formRef" :model="form" :rules="rules" size="large" @submit.prevent="handleLogin">
        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="用户名" :prefix-icon="User" clearable />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="form.password" type="password" placeholder="密码"
            :prefix-icon="Lock" show-password @keyup.enter="handleLogin" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" class="login-btn" @click="handleLogin">
            登 录
          </el-button>
        </el-form-item>
      </el-form>

      <div class="login-footer">
        <span>默认账号：admin / Admin@123</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { User, Lock } from '@element-plus/icons-vue'
import { ElMessage, type FormInstance } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()
const formRef = ref<FormInstance>()
const loading = ref(false)

const form = reactive({ username: 'admin', password: 'Admin@123' })
const rules = {
  username: [{ required: true, message: '请输入用户名' }],
  password: [{ required: true, message: '请输入密码' }],
}

async function handleLogin() {
  await formRef.value?.validate()
  loading.value = true
  try {
    await auth.login(form.username, form.password)
    ElMessage.success('登录成功')
    router.push('/')
  } catch {
    // error handled by http interceptor
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f1f5f9;
  background-image: 
    radial-gradient(at 0% 0%, rgba(79, 70, 229, 0.1) 0px, transparent 50%),
    radial-gradient(at 100% 100%, rgba(59, 130, 246, 0.1) 0px, transparent 50%);
  position: relative;
  overflow: hidden;
}

.login-box {
  width: 400px;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(12px);
  border-radius: 20px;
  padding: 48px 40px;
  box-shadow: 
    0 4px 6px -1px rgba(0, 0, 0, 0.05),
    0 10px 15px -3px rgba(0, 0, 0, 0.05),
    0 0 0 1px rgba(255, 255, 255, 0.5) inset;
  z-index: 1;
}

.login-header { text-align: center; margin-bottom: 40px; }
.logo { font-size: 48px; margin-bottom: 16px; display: inline-block; filter: drop-shadow(0 4px 6px rgba(0,0,0,0.1)); }
.login-header h1 { 
  font-size: 24px; 
  font-weight: 700; 
  color: #1e293b; 
  margin-bottom: 8px;
  letter-spacing: -0.5px;
}
.login-header p { 
  color: #64748b; 
  font-size: 14px; 
  font-weight: 400;
}

:deep(.el-input__wrapper) {
  background: #f8fafc;
  box-shadow: none !important;
  border: 1px solid #e2e8f0;
  padding: 12px 16px !important;
  transition: all 0.2s;
}
:deep(.el-input__wrapper:hover) {
  border-color: #cbd5e1;
}
:deep(.el-input__wrapper.is-focus) {
  background: #fff;
  border-color: #4f46e5;
  box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1) !important;
}

.login-btn { 
  width: 100%; 
  height: 48px; 
  font-size: 16px; 
  border-radius: 10px; 
  margin-top: 8px;
  font-weight: 600;
  letter-spacing: 0.5px;
  background: linear-gradient(to right, #4f46e5, #4338ca);
  border: none;
}
.login-btn:hover {
  opacity: 0.9;
  transform: translateY(-1px);
}

.login-footer { 
  text-align: center; 
  font-size: 13px; 
  color: #94a3b8; 
  margin-top: 24px; 
  padding-top: 20px;
  border-top: 1px solid #f1f5f9;
}
</style>
