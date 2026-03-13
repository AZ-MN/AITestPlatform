<template>
  <el-container class="app-layout">
    <!-- 侧边栏 -->
    <el-aside :width="collapsed ? '64px' : '220px'" class="sidebar">
      <div class="sidebar-header">
        <span class="logo-icon">✨</span>
        <transition name="fade">
          <span v-if="!collapsed" class="logo-text">AI测试平台</span>
        </transition>
      </div>

      <el-menu
        :default-active="activeMenu"
        :collapse="collapsed"
        :collapse-transition="false"
        class="sidebar-menu"
      >
        <el-menu-item index="/dashboard" @click="router.push('/dashboard')">
          <el-icon><DataAnalysis /></el-icon>
          <template #title>仪表盘</template>
        </el-menu-item>

        <el-menu-item index="/projects" @click="router.push('/projects')">
          <el-icon><Folder /></el-icon>
          <template #title>项目管理</template>
        </el-menu-item>

        <el-menu-item index="/settings" @click="router.push('/settings')">
          <el-icon><Setting /></el-icon>
          <template #title>模型设置</template>
        </el-menu-item>
      </el-menu>

      <div class="sidebar-footer">
        <el-tooltip 
          :content="collapsed ? '展开导航' : '收起导航'" 
          placement="right" 
          :show-after="500"
        >
          <div class="collapse-trigger" @click="collapsed = !collapsed">
            <el-icon class="collapse-icon">
              <Fold v-if="!collapsed" /><Expand v-else />
            </el-icon>
          </div>
        </el-tooltip>
      </div>
    </el-aside>

    <!-- 主内容区 -->
    <el-container class="main-container">
      <el-header class="app-header">
        <div class="header-left">
          <el-breadcrumb>
            <el-breadcrumb-item v-for="b in breadcrumbs" :key="b.path" :to="b.path">
              <span class="crumb-text" :title="b.title">{{ b.title }}</span>
            </el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-right">
          <el-dropdown @command="handleCommand">
            <div class="user-info">
              <el-avatar :size="32" :style="{ background: '#4f6ef7' }">
                {{ auth.user?.full_name?.charAt(0) || 'U' }}
              </el-avatar>
              <span class="username">{{ auth.user?.full_name }}</span>
              <el-icon><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">个人设置</el-dropdown-item>
                <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-main class="app-main">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useProjectStore } from '@/stores/project'
import { ElMessageBox } from 'element-plus'

const auth = useAuthStore()
const projectStore = useProjectStore()
const route = useRoute()
const router = useRouter()
const collapsed = ref(false)

const activeMenu = computed(() => {
  if (route.path.startsWith('/projects/')) return '/projects'
  return route.path
})

const breadcrumbs = computed(() => {
  const crumbs = [{ path: '/dashboard', title: '首页' }]
  if (route.path.includes('/projects/') && projectStore.current) {
    crumbs.push({ path: '/projects', title: '项目' })
    crumbs.push({ path: '', title: projectStore.current.name })
    if (route.path.includes('/requirements')) crumbs.push({ path: '', title: '需求管理' })
    if (route.path.includes('/generate')) crumbs.push({ path: '', title: '智能生成' })
    if (route.path.includes('/cases')) crumbs.push({ path: '', title: '用例库' })
    if (route.path.includes('/members')) crumbs.push({ path: '', title: '项目成员' })
  } else if (route.path === '/projects') {
    crumbs.push({ path: '', title: '项目管理' })
  } else if (route.path === '/settings') {
    crumbs.push({ path: '', title: '模型设置' })
  }
  return crumbs
})

async function handleCommand(cmd: string) {
  if (cmd === 'logout') {
    await ElMessageBox.confirm('确认退出登录？', '提示', {
      type: 'warning',
      closeOnClickModal: false,
      closeOnPressEscape: false,
    })
    auth.logout()
    router.push('/login')
  } else if (cmd === 'profile') {
    router.push('/profile')
  }
}
</script>

<style scoped>
.app-layout { 
  height: 100vh; 
  overflow: hidden; 
  background: var(--bg);
  display: flex;
}

/* Sidebar Styles */
.sidebar {
  background: linear-gradient(180deg, #1e1b4b 0%, #0f172a 100%);
  display: flex;
  flex-direction: column;
  transition: width 0.4s cubic-bezier(0.2, 0, 0, 1);
  overflow: hidden;
  z-index: 20;
  box-shadow: 4px 0 24px rgba(0,0,0,0.1);
}

.sidebar-header {
  height: 64px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 20px;
  flex-shrink: 0;
  border-bottom: 1px solid rgba(255,255,255,0.05);
}
.logo-icon { 
  font-size: 24px; 
  flex-shrink: 0; 
  filter: drop-shadow(0 2px 4px rgba(0,0,0,0.2));
}
.logo-text { 
  color: #fff; 
  font-size: 16px; 
  font-weight: 700; 
  letter-spacing: -0.01em;
  white-space: nowrap; 
}

.sidebar-menu { 
  border: none; 
  background: transparent; 
  flex: 1; 
  overflow-y: auto; 
  padding: 16px 8px;
}
:deep(.el-menu-item) {
  color: #94a3b8 !important;
  border-radius: 8px;
  margin-bottom: 4px;
  height: 44px;
  line-height: 44px;
  font-weight: 500;
  border: 1px solid transparent;
}
:deep(.el-menu-item:hover) {
  background: rgba(255,255,255,0.08) !important;
  color: #f8fafc !important;
}
:deep(.el-menu-item.is-active) {
  background: rgba(79, 70, 229, 0.9) !important;
  color: #fff !important;
  font-weight: 600;
  box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3);
}
:deep(.el-menu-item .el-icon) { font-size: 18px; margin-right: 10px; }

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid rgba(255,255,255,0.05);
  display: flex;
  justify-content: center;
}

.collapse-trigger {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: rgba(255,255,255,0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  color: #fff;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}
.collapse-trigger:hover {
  background: rgba(79, 70, 229, 0.8);
  transform: scale(1.1);
  box-shadow: 0 8px 16px rgba(79, 70, 229, 0.3);
}
.collapse-icon { font-size: 20px; transition: transform 0.3s; }
.collapse-trigger:hover .collapse-icon { transform: rotate(180deg); }

/* Main Container */
.main-container { 
  flex: 1;
  display: flex; 
  flex-direction: column; 
  min-width: 0;
  background: var(--bg);
  position: relative;
}

/* Floating Header */
.crumb-text {
  display: inline-block;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  vertical-align: bottom;
}
.app-header {
  height: 64px;
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  z-index: 100;
  background: rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(0,0,0,0.05);
  transition: all 0.3s ease;
}
.header-left { display: flex; align-items: center; gap: 16px; }

.header-right .user-info {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  padding: 4px 12px 4px 4px;
  border-radius: 20px;
  background: transparent;
  border: 1px solid transparent;
  transition: var(--transition);
}
.header-right .user-info:hover { 
  background: rgba(255,255,255,0.8);
  border-color: var(--border);
  box-shadow: var(--shadow-sm); 
}

.username { font-size: 14px; font-weight: 600; color: var(--text-primary); }

/* Content Area */
.app-main {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 80px 24px 24px 24px; /* Header height + spacing */
  background: var(--bg);
}

/* Page Transition */
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s ease, transform 0.3s ease; }
.fade-enter-from { opacity: 0; transform: translateY(10px); }
.fade-leave-to { opacity: 0; transform: translateY(-10px); }

/* Remove centralized constraints - let views control their own layout */
.app-main :deep(> div) {
  width: 100%;
  height: 100%;
}

@media (max-width: 1200px) {
  .app-header, .app-main { padding-left: 24px; padding-right: 24px; }
}
</style>
