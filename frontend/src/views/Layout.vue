<template>
  <el-container class="app-layout">
    <!-- 侧边栏 -->
    <el-aside :width="collapsed ? '64px' : '220px'" class="sidebar">
      <div class="sidebar-header">
        <span class="logo-icon">🧪</span>
        <transition name="fade">
          <span v-if="!collapsed" class="logo-text">AI测试平台</span>
        </transition>
      </div>

      <el-menu
        :default-active="activeMenu"
        :collapse="collapsed"
        :collapse-transition="false"
        router
        class="sidebar-menu"
      >
        <el-menu-item index="/dashboard">
          <el-icon><DataAnalysis /></el-icon>
          <template #title>仪表盘</template>
        </el-menu-item>

        <el-menu-item index="/projects">
          <el-icon><Folder /></el-icon>
          <template #title>项目管理</template>
        </el-menu-item>

        <el-sub-menu v-if="projectStore.current" index="project">
          <template #title>
            <el-icon><Files /></el-icon>
            <span>{{ projectStore.current.icon }} {{ projectStore.current.name }}</span>
          </template>
          <el-menu-item :index="`/projects/${projectStore.current.id}/requirements`">
            <el-icon><Document /></el-icon>
            <template #title>需求管理</template>
          </el-menu-item>
          <el-menu-item :index="`/projects/${projectStore.current.id}/generate`">
            <el-icon><MagicStick /></el-icon>
            <template #title>智能生成</template>
          </el-menu-item>
          <el-menu-item :index="`/projects/${projectStore.current.id}/cases`">
            <el-icon><List /></el-icon>
            <template #title>用例库</template>
          </el-menu-item>
        </el-sub-menu>

        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon>
          <template #title>模型设置</template>
        </el-menu-item>
      </el-menu>

      <div class="sidebar-footer">
        <el-icon class="collapse-btn" @click="collapsed = !collapsed">
          <Fold v-if="!collapsed" /><Expand v-else />
        </el-icon>
      </div>
    </el-aside>

    <!-- 主内容区 -->
    <el-container class="main-container">
      <el-header class="app-header">
        <div class="header-left">
          <el-breadcrumb>
            <el-breadcrumb-item v-for="b in breadcrumbs" :key="b.path" :to="b.path">
              {{ b.title }}
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

const activeMenu = computed(() => route.path)

const breadcrumbs = computed(() => {
  const crumbs = [{ path: '/dashboard', title: '首页' }]
  if (route.path.includes('/projects/') && projectStore.current) {
    crumbs.push({ path: '/projects', title: '项目' })
    crumbs.push({ path: '', title: projectStore.current.name })
    if (route.path.includes('/requirements')) crumbs.push({ path: '', title: '需求管理' })
    if (route.path.includes('/generate')) crumbs.push({ path: '', title: '智能生成' })
    if (route.path.includes('/cases')) crumbs.push({ path: '', title: '用例库' })
  } else if (route.path === '/projects') {
    crumbs.push({ path: '', title: '项目管理' })
  } else if (route.path === '/settings') {
    crumbs.push({ path: '', title: '模型设置' })
  }
  return crumbs
})

async function handleCommand(cmd: string) {
  if (cmd === 'logout') {
    await ElMessageBox.confirm('确认退出登录？', '提示', { type: 'warning' })
    auth.logout()
    router.push('/login')
  } else if (cmd === 'profile') {
    router.push('/profile')
  }
}
</script>

<style scoped>
.app-layout { height: 100vh; overflow: hidden; }

.sidebar {
  background: #1a1c2e;
  display: flex;
  flex-direction: column;
  transition: width .2s;
  overflow: hidden;
}
.sidebar-header {
  height: 56px;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 16px;
  border-bottom: 1px solid rgba(255,255,255,.08);
  flex-shrink: 0;
}
.logo-icon { font-size: 24px; flex-shrink: 0; }
.logo-text { color: #fff; font-size: 15px; font-weight: 700; white-space: nowrap; }

.sidebar-menu { border: none; background: transparent; flex: 1; overflow-y: auto; }
:deep(.el-menu-item), :deep(.el-sub-menu__title) {
  color: rgba(255,255,255,.7) !important;
  border-radius: 8px;
  margin: 2px 8px;
}
:deep(.el-menu-item:hover), :deep(.el-sub-menu__title:hover) {
  background: rgba(255,255,255,.08) !important;
  color: #fff !important;
}
:deep(.el-menu-item.is-active) {
  background: #4f6ef7 !important;
  color: #fff !important;
}
:deep(.el-sub-menu .el-menu-item) { padding-left: 44px !important; }

.sidebar-footer {
  padding: 12px;
  border-top: 1px solid rgba(255,255,255,.08);
  display: flex;
  justify-content: flex-end;
}
.collapse-btn {
  color: rgba(255,255,255,.5);
  cursor: pointer;
  font-size: 18px;
  padding: 4px;
}
.collapse-btn:hover { color: #fff; }

.main-container { overflow: hidden; min-width: 0; }

.app-header {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-bottom: 1px solid var(--border);
  padding: 0 24px;
}
.header-right .user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}
.username { font-size: 14px; color: #374151; }

.app-main {
  background: var(--bg);
  overflow-y: auto;
  padding: 20px 24px;
}

.app-main :deep(.dashboard),
.app-main :deep(.projects-page),
.app-main :deep(.req-page),
.app-main :deep(.generate-page),
.app-main :deep(.case-library),
.app-main :deep(.settings-page),
.app-main :deep(.profile-page) {
  width: 100%;
  max-width: none !important;
}

@media (max-width: 1200px) {
  .app-header { padding: 0 16px; }
  .app-main { padding: 16px; }
}

@media (max-width: 768px) {
  .app-header { padding: 0 12px; }
  .app-main { padding: 12px; }
  .username { display: none; }
}
</style>
