import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/Login.vue'),
      meta: { guest: true }
    },
    {
      path: '/',
      component: () => import('@/views/Layout.vue'),
      meta: { requiresAuth: true },
      children: [
        { path: '',        redirect: '/dashboard' },
        { path: 'dashboard', name: 'Dashboard',    component: () => import('@/views/Dashboard.vue') },
        { path: 'projects',  name: 'Projects',     component: () => import('@/views/Projects.vue') },
        {
          path: 'projects/:id',
          component: () => import('@/views/ProjectDetail.vue'),
          children: [
            { path: '',           redirect: 'requirements' },
            { path: 'requirements', name: 'Requirements', component: () => import('@/views/Requirements.vue') },
            { path: 'generate',    name: 'Generate',      component: () => import('@/views/CaseGenerate.vue') },
            { path: 'cases',       name: 'CaseLibrary',   component: () => import('@/views/CaseLibrary.vue') },
          ]
        },
        { path: 'settings',  name: 'Settings',     component: () => import('@/views/Settings.vue') },
        { path: 'tasks',     name: 'TaskCenter',   component: () => import('@/views/TaskCenter.vue') },
        { path: 'profile',   name: 'Profile',      component: () => import('@/views/Profile.vue') },
      ]
    },
    { path: '/:pathMatch(.*)*', redirect: '/' }
  ]
})

router.beforeEach((to, _from, next) => {
  const auth = useAuthStore()
  if (to.meta.requiresAuth && !auth.token) {
    next('/login')
  } else if (to.meta.guest && auth.token) {
    next('/')
  } else {
    next()
  }
})

export default router
