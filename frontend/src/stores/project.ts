import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Project, Iteration } from '@/types'
import { projectApi } from '@/api/modules'

export const useProjectStore = defineStore('project', () => {
  const projects = ref<Project[]>([])
  const currentProject = ref<Project | null>(null)
  const currentIteration = ref<Iteration | null>(null)

  const fetchProjects = async () => {
    const res: any = await projectApi.list()
    projects.value = res
  }

  const setCurrentProject = (project: Project) => {
    currentProject.value = project
    localStorage.setItem('current_project', JSON.stringify(project))
  }

  const loadFromStorage = () => {
    const stored = localStorage.getItem('current_project')
    if (stored) {
      try { currentProject.value = JSON.parse(stored) } catch {}
    }
  }

  return { projects, currentProject, currentIteration, fetchProjects, setCurrentProject, loadFromStorage }
})
