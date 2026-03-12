<template>
  <div class="project-detail">
    <div class="project-nav page-card" v-if="projectStore.current">
      <div class="project-info">
        <div class="project-title">
          <span class="icon">{{ projectStore.current.icon }}</span>
          <span class="name" :title="projectStore.current.name">{{ projectStore.current.name }}</span>
        </div>
        <div class="project-metrics">
          <span class="metric-item">需求 {{ projectStore.current.req_count || 0 }}</span>
          <span class="metric-item">用例 {{ projectStore.current.case_count || 0 }}</span>
          <span class="metric-item">成员 {{ projectStore.current.member_count || 0 }}</span>
        </div>
      </div>
      <div class="tabs">
        <router-link :to="`/projects/${projectStore.current.id}/requirements`" class="tab" :class="{ active: route.path.includes('/requirements') }">需求管理</router-link>
        <router-link :to="`/projects/${projectStore.current.id}/generate`" class="tab" :class="{ active: route.path.includes('/generate') }">智能生成</router-link>
        <router-link :to="`/projects/${projectStore.current.id}/cases`" class="tab" :class="{ active: route.path.includes('/cases') }">用例库</router-link>
        <router-link :to="`/projects/${projectStore.current.id}/members`" class="tab" :class="{ active: route.path.includes('/members') }">项目成员</router-link>
      </div>
    </div>
    <router-view />
  </div>
</template>

<script setup lang="ts">
import { onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useProjectStore } from '@/stores/project'

const route = useRoute()
const projectStore = useProjectStore()

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
.project-detail { display: flex; flex-direction: column; gap: 12px; }
.project-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 10px 14px;
}
.project-info { display: flex; align-items: center; gap: 12px; min-width: 0; }
.project-title { display: flex; align-items: center; gap: 8px; }
.icon { font-size: 20px; }
.name {
  font-size: 15px;
  font-weight: 600;
  max-width: 220px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.project-metrics { display: flex; align-items: center; gap: 8px; }
.metric-item {
  font-size: 12px;
  color: #6b7280;
  background: #f8fafc;
  border: 1px solid #e5e7eb;
  border-radius: 999px;
  padding: 2px 8px;
}
.tabs {
  display: flex;
  gap: 6px;
  background: #f8fafc;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 4px;
}
.tab {
  height: 30px;
  padding: 0 10px;
  border-radius: 8px;
  display: inline-flex;
  align-items: center;
  color: #4b5563;
  text-decoration: none;
  font-size: 13px;
  white-space: nowrap;
}
.tab:hover { background: #f3f4f6; }
.tab.active { background: #eef2ff; color: #4f46e5; font-weight: 600; }

@media (max-width: 768px) {
  .project-nav { flex-direction: column; align-items: stretch; gap: 10px; }
  .project-info { justify-content: space-between; }
  .project-metrics { display: none; }
  .tabs { overflow-x: auto; }
}
</style>
