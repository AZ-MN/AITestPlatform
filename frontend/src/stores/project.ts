import { defineStore } from 'pinia'
import { ref } from 'vue'
import { projectApi } from '@/api/projects'
import type { Project } from '@/api/types'

export const useProjectStore = defineStore('project', () => {
  const projects = ref<Project[]>([])
  const current = ref<Project | null>(null)
  const savedProjectId = Number(localStorage.getItem('current_project_id') || 0)

  async function fetchProjects() {
    projects.value = await projectApi.list()
    if (!current.value && savedProjectId) {
      const matched = projects.value.find(p => p.id === savedProjectId)
      if (matched) current.value = matched
    }
  }

  async function fetchProject(id: number) {
    current.value = await projectApi.get(id)
    localStorage.setItem('current_project_id', String(id))
  }

  function setCurrent(p: Project) {
    current.value = p
    localStorage.setItem('current_project_id', String(p.id))
  }

  return { projects, current, fetchProjects, fetchProject, setCurrent }
})
