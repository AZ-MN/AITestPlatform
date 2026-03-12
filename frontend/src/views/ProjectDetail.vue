<template>
  <div class="project-detail">
    <div class="project-nav page-card" v-if="projectStore.current">
      <div class="project-title">
        <span class="icon">{{ projectStore.current.icon }}</span>
        <span class="name">{{ projectStore.current.name }}</span>
      </div>
      <div class="tabs">
        <router-link :to="`/projects/${projectStore.current.id}/requirements`" class="tab" :class="{ active: route.path.includes('/requirements') }">需求管理</router-link>
        <router-link :to="`/projects/${projectStore.current.id}/generate`" class="tab" :class="{ active: route.path.includes('/generate') }">智能生成</router-link>
        <router-link :to="`/projects/${projectStore.current.id}/cases`" class="tab" :class="{ active: route.path.includes('/cases') }">用例库</router-link>
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
  padding: 12px 16px;
}
.project-title { display: flex; align-items: center; gap: 8px; }
.icon { font-size: 20px; }
.name { font-size: 15px; font-weight: 600; }
.tabs { display: flex; gap: 8px; }
.tab {
  height: 32px;
  padding: 0 12px;
  border-radius: 8px;
  display: inline-flex;
  align-items: center;
  color: #4b5563;
  text-decoration: none;
  font-size: 13px;
}
.tab:hover { background: #f3f4f6; }
.tab.active { background: #eef2ff; color: #4f46e5; }

@media (max-width: 768px) {
  .project-nav { flex-direction: column; align-items: flex-start; gap: 10px; }
}
</style>
