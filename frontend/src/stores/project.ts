import { defineStore } from 'pinia'
import { ref } from 'vue'
import { projectApi } from '@/api/projects'
import type { Project } from '@/api/types'

export const useProjectStore = defineStore('project', () => {
  const projects = ref<Project[]>([])
  const current = ref<Project | null>(null)

  async function fetchProjects() {
    projects.value = await projectApi.list()
  }

  async function fetchProject(id: number) {
    current.value = await projectApi.get(id)
  }

  function setCurrent(p: Project) {
    current.value = p
  }

  return { projects, current, fetchProjects, fetchProject, setCurrent }
})
