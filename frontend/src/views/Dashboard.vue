<template>
  <div class="dashboard">
    <div class="page-title">
      <h2>仪表盘</h2>
      <span class="subtitle">欢迎回来，{{ auth.user?.full_name }} 👋</span>
    </div>

    <!-- 统计卡片 -->
    <div class="stat-cards">
      <div v-for="stat in stats" :key="stat.label" class="stat-card">
        <div class="stat-icon" :style="{ background: stat.bg }">{{ stat.icon }}</div>
        <div>
          <div class="stat-value">{{ stat.value }}</div>
          <div class="stat-label">{{ stat.label }}</div>
        </div>
      </div>
    </div>

    <!-- 最近项目 -->
    <div class="section">
      <div class="section-header">
        <h3>最近项目</h3>
        <el-button link type="primary" @click="$router.push('/projects')">全部项目 →</el-button>
      </div>
      <div class="project-grid">
        <div v-for="p in recentProjects" :key="p.id"
          class="project-card" @click="openProject(p)">
          <div class="p-icon">{{ p.icon }}</div>
          <div class="p-info">
            <div class="p-name">{{ p.name }}</div>
            <div class="p-desc">{{ p.description || '暂无描述' }}</div>
            <div class="p-meta">
              <span>📋 {{ p.case_count }} 用例</span>
              <span>📄 {{ p.req_count }} 需求</span>
              <span>👥 {{ p.member_count }} 成员</span>
            </div>
          </div>
          <el-tag :type="p.status === 'active' ? 'success' : 'info'" size="small">
            {{ p.status === 'active' ? '进行中' : '已归档' }}
          </el-tag>
        </div>
        <div class="project-card new-project" @click="$router.push('/projects')">
          <el-icon :size="32"><Plus /></el-icon>
          <span>创建新项目</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useProjectStore } from '@/stores/project'
import type { Project } from '@/api/types'

const auth = useAuthStore()
const projectStore = useProjectStore()
const router = useRouter()

const totalCases = ref(0)
const totalReqs = ref(0)

onMounted(async () => {
  await projectStore.fetchProjects()
  totalCases.value = projectStore.projects.reduce((s, p) => s + (p.case_count || 0), 0)
  totalReqs.value = projectStore.projects.reduce((s, p) => s + (p.req_count || 0), 0)
})

const recentProjects = computed(() =>
  projectStore.projects.filter(p => p.status === 'active').slice(0, 6)
)

const stats = computed(() => [
  { label: '项目总数', value: projectStore.projects.length, icon: '📁', bg: '#eef0fe' },
  { label: '需求总数', value: totalReqs.value, icon: '📄', bg: '#fef3e2' },
  { label: '用例总数', value: totalCases.value, icon: '📋', bg: '#e8f5e9' },
  { label: '活跃项目', value: recentProjects.value.length, icon: '🚀', bg: '#fce4ec' },
])

function openProject(p: Project) {
  projectStore.setCurrent(p)
  router.push(`/projects/${p.id}/requirements`)
}
</script>

<style scoped>
.dashboard { max-width: 1200px; }
.page-title { margin-bottom: 24px; }
.page-title h2 { font-size: 22px; font-weight: 700; }
.subtitle { color: var(--text-secondary); font-size: 14px; }

.stat-cards { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 28px; }
.stat-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  border: 1px solid var(--border);
}
.stat-icon { width: 48px; height: 48px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 22px; flex-shrink: 0; }
.stat-value { font-size: 26px; font-weight: 700; line-height: 1; }
.stat-label { font-size: 13px; color: var(--text-secondary); margin-top: 4px; }

.section { background: #fff; border-radius: 12px; border: 1px solid var(--border); padding: 20px 24px; }
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.section-header h3 { font-size: 16px; font-weight: 600; }

.project-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }
.project-card {
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 16px;
  cursor: pointer;
  transition: all .2s;
  display: flex;
  align-items: flex-start;
  gap: 12px;
}
.project-card:hover { border-color: #4f6ef7; box-shadow: 0 4px 12px rgba(79,110,247,.1); transform: translateY(-1px); }
.p-icon { font-size: 28px; flex-shrink: 0; }
.p-info { flex: 1; min-width: 0; }
.p-name { font-weight: 600; font-size: 14px; margin-bottom: 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.p-desc { font-size: 12px; color: var(--text-secondary); margin-bottom: 8px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.p-meta { display: flex; gap: 8px; font-size: 11px; color: #9ca3af; }
.new-project {
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #9ca3af;
  border-style: dashed;
  gap: 8px;
  font-size: 13px;
}
.new-project:hover { color: #4f6ef7; border-color: #4f6ef7; }

@media (max-width: 900px) {
  .stat-cards { grid-template-columns: repeat(2, 1fr); }
  .project-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
