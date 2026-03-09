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
        :default-openeds="defaultOpeneds"
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

        <template v-if="projectStore.projects.length">
          <div v-if="!collapsed" class="menu-section-title">项目导航</div>
          <el-sub-menu index="project-list" class="project-list-sub-menu">
            <template #title>
              <el-icon><Collection /></el-icon>
              <span>所有项目</span>
            </template>
            <el-menu-item
              v-for="p in projectStore.projects"
              :key="p.id"
              :index="`/projects/${p.id}/requirements`"
              @click="selectProject(p)"
            >
              <span class="project-item-label">{{ p.icon }} {{ p.name }}</span>
            </el-menu-item>
          </el-sub-menu>
        </template>

        <template v-if="projectStore.current">
          <div v-if="!collapsed" class="menu-section-title">当前项目</div>
          <el-sub-menu index="project" class="project-sub-menu">
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
        </template>

        <div v-if="!collapsed" class="menu-section-title">系统设置</div>
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
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useProjectStore } from '@/stores/project'
import { ElMessageBox } from 'element-plus'
import type { Project } from '@/api/types'

const auth = useAuthStore()
const projectStore = useProjectStore()
const route = useRoute()
const router = useRouter()
const collapsed = ref(false)

const activeMenu = computed(() => route.path)
const currentProjectId = computed(() => Number(route.params.id || 0))
const defaultOpeneds = computed(() => currentProjectId.value ? ['project-list', 'project'] : ['project-list'])

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

function selectProject(p: Project) {
  projectStore.setCurrent(p)
}

async function hydrateSidebarProjects() {
  if (!projectStore.projects.length) await projectStore.fetchProjects()
}

function syncCurrentProject() {
  const id = currentProjectId.value
  if (!id) return
  const matched = projectStore.projects.find(p => p.id === id)
  if (matched) projectStore.setCurrent(matched)
}

onMounted(async () => {
  await hydrateSidebarProjects()
  syncCurrentProject()
})

watch(() => route.params.id, syncCurrentProject)
</script>

<style scoped>
.app-layout { height: 100vh; overflow: hidden; }

.sidebar {
  background: linear-gradient(180deg, #13182b 0%, #171d35 42%, #111629 100%);
  display: flex;
  flex-direction: column;
  transition: width .24s ease;
  overflow: hidden;
  box-shadow: 8px 0 24px rgba(10, 16, 38, .18);
}
.sidebar-header {
  height: 62px;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 14px;
  border-bottom: 1px solid rgba(255,255,255,.08);
  flex-shrink: 0;
}
.logo-icon {
  width: 30px;
  height: 30px;
  border-radius: 8px;
  background: linear-gradient(135deg, #58c1ff 0%, #5c7cfa 100%);
  font-size: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 6px 14px rgba(92,124,250,.35);
  flex-shrink: 0;
}
.logo-text { color: #fff; font-size: 15px; font-weight: 700; white-space: nowrap; letter-spacing: .2px; }

.sidebar-menu { border: none; background: transparent; flex: 1; overflow-y: auto; padding: 10px 8px; }
.menu-section-title {
  font-size: 11px;
  color: rgba(255,255,255,.45);
  margin: 10px 12px 6px;
  letter-spacing: .6px;
}
:deep(.sidebar-menu.el-menu) {
  --el-menu-bg-color: transparent;
  --el-menu-hover-bg-color: rgba(108, 127, 255, .16);
  --el-menu-text-color: rgba(255,255,255,.72);
  --el-menu-active-color: #fff;
  border-right: none;
  background: transparent !important;
}
:deep(.sidebar-menu .el-menu),
:deep(.sidebar-menu .el-sub-menu__title),
:deep(.sidebar-menu .el-menu--inline) {
  background: transparent !important;
}
:deep(.el-menu-item), :deep(.el-sub-menu__title) {
  color: rgba(255,255,255,.7) !important;
  border-radius: 10px;
  margin: 4px 2px;
  height: 42px;
  line-height: 42px;
  transition: all .18s ease;
  font-weight: 500;
}
:deep(.el-menu-item:hover), :deep(.el-sub-menu__title:hover) {
  background: rgba(108, 127, 255, .16) !important;
  color: #fff !important;
  transform: translateX(2px);
}
:deep(.el-menu-item.is-active) {
  background: linear-gradient(90deg, #4f6ef7 0%, #6384ff 100%) !important;
  color: #fff !important;
  box-shadow: 0 8px 18px rgba(79, 110, 247, .35);
}
:deep(.el-sub-menu.is-active > .el-sub-menu__title) {
  color: #fff !important;
}
:deep(.el-sub-menu .el-menu-item) { padding-left: 44px !important; }
:deep(.project-sub-menu .el-menu--inline) {
  margin: 2px 0 6px;
  padding: 4px;
  border-radius: 10px;
  background: rgba(255,255,255,.04) !important;
}
:deep(.project-list-sub-menu .el-menu--inline) {
  margin: 2px 0 6px;
  padding: 4px;
  border-radius: 10px;
  background: rgba(255,255,255,.03) !important;
}
.project-item-label {
  max-width: 140px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
:deep(.sidebar-menu .el-icon) { font-size: 15px; }

.sidebar-footer {
  padding: 12px;
  border-top: 1px solid rgba(255,255,255,.08);
  display: flex;
  justify-content: flex-end;
}
.collapse-btn {
  color: rgba(255,255,255,.7);
  cursor: pointer;
  font-size: 18px;
  padding: 7px;
  border-radius: 8px;
  background: rgba(255,255,255,.06);
  transition: all .18s ease;
}
.collapse-btn:hover {
  color: #fff;
  background: rgba(108, 127, 255, .3);
}

.main-container { overflow: hidden; }

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
</style>
