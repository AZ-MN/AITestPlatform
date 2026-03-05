<template>
  <div class="header">
    <div class="header-left">
      <el-button :icon="collapsed ? 'Expand' : 'Fold'" text @click="$emit('toggle-sidebar')" />
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
        <el-breadcrumb-item v-if="route.meta.title">{{ route.meta.title }}</el-breadcrumb-item>
      </el-breadcrumb>
    </div>
    <div class="header-right">
      <el-select
        v-if="projectStore.projects.length"
        v-model="selectedProjectId"
        placeholder="选择项目"
        size="small"
        style="width: 160px; margin-right: 16px"
        @change="onProjectChange"
      >
        <el-option v-for="p in projectStore.projects" :key="p.id" :label="p.name" :value="p.id" />
      </el-select>
      <el-dropdown>
        <div class="user-info">
          <el-avatar :size="32" style="background: #1890ff">
            {{ authStore.user?.full_name?.charAt(0) || authStore.user?.username?.charAt(0) }}
          </el-avatar>
          <span class="username">{{ authStore.user?.full_name || authStore.user?.username }}</span>
          <el-icon><ArrowDown /></el-icon>
        </div>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item @click="handleLogout">
              <el-icon><SwitchButton /></el-icon>退出登录
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useProjectStore } from '@/stores/project'

defineProps<{ collapsed: boolean }>()
defineEmits(['toggle-sidebar'])

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const projectStore = useProjectStore()
const selectedProjectId = ref<number | null>(null)

onMounted(async () => {
  authStore.loadUserFromStorage()
  await projectStore.fetchProjects()
  if (projectStore.currentProject) {
    selectedProjectId.value = projectStore.currentProject.id
  }
})

const onProjectChange = (id: number) => {
  const project = projectStore.projects.find(p => p.id === id)
  if (project) projectStore.setCurrentProject(project)
}

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.header { height: 100%; display: flex; align-items: center; justify-content: space-between; padding: 0 20px; }
.header-left, .header-right { display: flex; align-items: center; gap: 8px; }
.user-info { display: flex; align-items: center; gap: 8px; cursor: pointer; }
.username { font-size: 14px; color: #303133; }
</style>
