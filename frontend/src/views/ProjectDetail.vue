<template>
  <div>
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
