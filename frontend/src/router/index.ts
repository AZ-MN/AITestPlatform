import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/',
    component: () => import('@/components/layout/AppLayout.vue'),
    meta: { requiresAuth: true },
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/Dashboard.vue'),
        meta: { title: '质量看板', icon: 'DataBoard' },
      },
      // 平台管理
      { path: 'admin/users', name: 'UserManagement', component: () => import('@/views/admin/UserManagement.vue'), meta: { title: '用户管理' } },
      { path: 'admin/roles', name: 'RoleManagement', component: () => import('@/views/admin/RoleManagement.vue'), meta: { title: '角色权限' } },
      { path: 'admin/projects', name: 'ProjectManagement', component: () => import('@/views/admin/ProjectManagement.vue'), meta: { title: '项目管理' } },
      { path: 'admin/iterations', name: 'IterationManagement', component: () => import('@/views/admin/IterationManagement.vue'), meta: { title: '迭代管理' } },
      { path: 'admin/llm', name: 'LLMConfig', component: () => import('@/views/admin/LLMConfig.vue'), meta: { title: 'AI模型配置' } },
      // 需求用例
      { path: 'requirements', name: 'RequirementList', component: () => import('@/views/requirements/RequirementList.vue'), meta: { title: '需求管理' } },
      { path: 'requirements/:id', name: 'RequirementDetail', component: () => import('@/views/requirements/RequirementDetail.vue'), meta: { title: '需求详情' } },
      { path: 'testcases', name: 'TestCaseList', component: () => import('@/views/requirements/TestCaseList.vue'), meta: { title: '用例库' } },
      // 接口测试
      { path: 'apitest/apis', name: 'ApiList', component: () => import('@/views/apitest/ApiList.vue'), meta: { title: '接口管理' } },
      { path: 'apitest/debug', name: 'ApiDebug', component: () => import('@/views/apitest/ApiDebug.vue'), meta: { title: '接口调试' } },
      { path: 'apitest/cases', name: 'ApiCaseList', component: () => import('@/views/apitest/ApiCaseList.vue'), meta: { title: '接口用例' } },
      // 自动化
      { path: 'automation/scripts', name: 'ScriptList', component: () => import('@/views/automation/ScriptList.vue'), meta: { title: '脚本管理' } },
      { path: 'automation/scripts/:id', name: 'ScriptEditor', component: () => import('@/views/automation/ScriptEditor.vue'), meta: { title: '脚本编辑器' } },
      { path: 'automation/tasks', name: 'TaskSchedule', component: () => import('@/views/automation/TaskSchedule.vue'), meta: { title: '任务调度' } },
      // 缺陷
      { path: 'defects', name: 'DefectList', component: () => import('@/views/defects/DefectList.vue'), meta: { title: '缺陷管理' } },
      { path: 'defects/:id', name: 'DefectDetail', component: () => import('@/views/defects/DefectDetail.vue'), meta: { title: '缺陷详情' } },
      // 测试数据
      { path: 'testdata', name: 'TestDataGenerator', component: () => import('@/views/testdata/TestDataGenerator.vue'), meta: { title: '测试数据' } },
      // 报告
      { path: 'reports', name: 'ReportCenter', component: () => import('@/views/reports/ReportCenter.vue'), meta: { title: '质量报告' } },
    ],
  },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// Auth guard
router.beforeEach((to) => {
  const token = localStorage.getItem('access_token')
  if (to.meta.requiresAuth !== false && !token) {
    return '/login'
  }
  if (to.path === '/login' && token) {
    return '/'
  }
})

export default router
