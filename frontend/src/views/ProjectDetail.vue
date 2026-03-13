<template>
  <div class="project-detail">
    <div class="project-header" v-if="projectStore.current">
      <div class="header-main">
        <div class="project-brand">
          <div class="project-icon">{{ projectStore.current.icon }}</div>
          <div class="project-meta">
            <h1 class="project-name" :title="projectStore.current.name">{{ truncatedName }}</h1>
            <div class="project-stats">
              <span class="stat"><el-icon><Document /></el-icon> {{ projectStore.current.req_count || 0 }} 需求</span>
              <span class="divider">/</span>
              <span class="stat"><el-icon><List /></el-icon> {{ projectStore.current.case_count || 0 }} 用例</span>
              <span class="divider">/</span>
              <span class="stat"><el-icon><User /></el-icon> {{ projectStore.current.member_count || 0 }} 成员</span>
            </div>
          </div>
        </div>
      </div>
      
      <div class="header-nav">
        <router-link :to="`/projects/${projectStore.current.id}/requirements`" class="nav-item" active-class="active">
          <el-icon><Document /></el-icon>需求管理
        </router-link>
        <router-link :to="`/projects/${projectStore.current.id}/generate`" class="nav-item" active-class="active">
          <el-icon><MagicStick /></el-icon>智能生成
        </router-link>
        <router-link :to="`/projects/${projectStore.current.id}/cases`" class="nav-item" active-class="active">
          <el-icon><Collection /></el-icon>用例库
        </router-link>
        <router-link :to="`/projects/${projectStore.current.id}/members`" class="nav-item" active-class="active">
          <el-icon><User /></el-icon>项目成员
        </router-link>
      </div>
    </div>

    <div class="detail-content">
      <router-view />
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, watch, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useProjectStore } from '@/stores/project'
import { Document, List, User, MagicStick, Collection } from '@element-plus/icons-vue'

const route = useRoute()
const projectStore = useProjectStore()

const truncatedName = computed(() => {
  const name = projectStore.current?.name || ''
  return name.length > 20 ? name.slice(0, 20) + '...' : name
})

async function loadProject() {
  const id = Number(route.params.id)
  if (id && projectStore.current?.id !== id) {
    await projectStore.fetchProject(id)
  }
}

onMounted(loadProject)
watch(() => route.params.id, loadProject)
</script>

<style scoped>
.project-detail { 
  display: flex; 
  flex-direction: column; 
  height: 100%; 
  min-height: 0;
  gap: 24px;
}

.project-header {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding-bottom: 0;
  border-bottom: 1px solid var(--border);
  background: transparent;
}

.header-main {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.project-brand {
  display: flex;
  align-items: center;
  gap: 16px;
}
.project-icon {
  width: 56px;
  height: 56px;
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  box-shadow: var(--shadow-sm);
}
.project-meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.project-name {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.2;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
  max-width: 100%;
}
.project-stats {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--text-secondary);
}
.stat { display: flex; align-items: center; gap: 4px; }
.divider { color: var(--border); }

.header-nav {
  display: flex;
  gap: 32px;
  margin-bottom: -1px; /* Overlap border */
}
.nav-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 4px;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
  text-decoration: none;
  border-bottom: 2px solid transparent;
  transition: all 0.2s;
}
.nav-item:hover {
  color: var(--primary);
}
.nav-item.active {
  color: var(--primary);
  border-bottom-color: var(--primary);
  font-weight: 600;
}
.nav-item .el-icon { font-size: 16px; }

.detail-content { 
  flex: 1; 
  min-height: 0; 
  overflow: hidden;
  /* Adjust for nested views to fill space */
  display: flex;
  flex-direction: column;
}
/* Ensure nested views take full height */
.detail-content :deep(> div) {
  flex: 1;
  height: 100%;
}

@media (max-width: 768px) {
  .header-nav { overflow-x: auto; gap: 20px; padding-bottom: 4px; }
  .project-name { font-size: 20px; }
  .project-icon { width: 48px; height: 48px; font-size: 24px; }
}
</style>
