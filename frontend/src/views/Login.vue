<template>
  <div class="login-page">
    <div class="login-box">
      <div class="login-header">
        <el-icon size="48" color="#1890ff" style="margin-bottom: 12px"><cpu /></el-icon>
        <h1>AI智能测试平台</h1>
        <p class="subtitle">一站式 AI 驱动全链路测试效能平台</p>
      </div>
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top" @submit.prevent="handleLogin">
        <el-form-item prop="username" label="账号">
          <el-input v-model="form.username" placeholder="请输入账号" size="large" prefix-icon="User" />
        </el-form-item>
        <el-form-item prop="password" label="密码">
          <el-input v-model="form.password" type="password" placeholder="请输入密码" size="large" prefix-icon="Lock" show-password @keyup.enter="handleLogin" />
        </el-form-item>
        <el-button type="primary" size="large" :loading="loading" style="width: 100%; margin-top: 8px" @click="handleLogin">
          登 录
        </el-button>
      </el-form>
      <div class="login-tip">默认账号: admin / admin123</div>
    </div>
    <div class="login-bg">
      <div class="feature-list">
        <div class="feature-item" v-for="f in features" :key="f.title">
          <el-icon size="24" :color="f.color"><component :is="f.icon" /></el-icon>
          <div>
            <div class="feature-title">{{ f.title }}</div>
            <div class="feature-desc">{{ f.desc }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()
const formRef = ref()
const loading = ref(false)
const form = reactive({ username: '', password: '' })
const rules = {
  username: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}
const features = [
  { icon: 'Document', color: '#1890ff', title: 'AI需求解析', desc: '智能解析需求文档，自动生成测试点' },
  { icon: 'Tickets', color: '#52c41a', title: 'AI用例生成', desc: '一键生成全覆盖测试用例，效率提升60%' },
  { icon: 'Connection', color: '#722ed1', title: 'AI接口测试', desc: '自动生成API用例，支持Swagger导入' },
  { icon: 'VideoPlay', color: '#fa8c16', title: 'AI自动化', desc: '生成Pytest/Playwright脚本，开箱即用' },
  { icon: 'Warning', color: '#f5222d', title: 'AI缺陷分析', desc: '智能分类、根因分析、修复建议' },
  { icon: 'TrendCharts', color: '#13c2c2', title: '质量看板', desc: 'AI生成测试报告，质量一目了然' },
]

const handleLogin = async () => {
  await formRef.value?.validate()
  loading.value = true
  try {
    await authStore.login(form.username, form.password)
    ElMessage.success('登录成功')
    router.push('/')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  background: linear-gradient(135deg, #001529 0%, #003a8c 100%);
}
.login-box {
  width: 420px;
  background: #fff;
  padding: 48px 40px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-height: 100vh;
}
.login-header { text-align: center; margin-bottom: 36px; }
.login-header h1 { font-size: 24px; font-weight: 700; color: #303133; margin-bottom: 8px; }
.subtitle { color: #909399; font-size: 13px; }
.login-tip { text-align: center; color: #c0c4cc; font-size: 12px; margin-top: 16px; }
.login-bg { flex: 1; display: flex; align-items: center; justify-content: center; padding: 40px; }
.feature-list { display: grid; grid-template-columns: repeat(2, 1fr); gap: 24px; max-width: 600px; }
.feature-item {
  display: flex; gap: 16px; align-items: flex-start;
  background: rgba(255,255,255,0.05);
  border-radius: 12px;
  padding: 20px;
  border: 1px solid rgba(255,255,255,0.1);
}
.feature-title { color: #fff; font-size: 15px; font-weight: 600; margin-bottom: 4px; }
.feature-desc { color: rgba(255,255,255,0.6); font-size: 13px; }
</style>
