<template>
  <div class="dashboard">
    <div class="page-title">
      <div>
        <h2>仪表盘</h2>
        <span class="subtitle">欢迎回来，{{ auth.user?.full_name }} 👋</span>
      </div>
      <div class="title-actions">
        <el-button @click="$router.push('/projects')">项目管理</el-button>
        <el-button type="primary" @click="goGenerate">开始生成</el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stat-cards">
      <div v-for="stat in stats" :key="stat.label" class="stat-card">
        <div class="stat-icon" :style="{ background: stat.bg }">{{ stat.icon }}</div>
        <div>
          <div class="stat-value">{{ stat.value }}</div>
          <div class="stat-label">{{ stat.label }}</div>
          <div class="stat-sub">{{ stat.hint }}</div>
        </div>
      </div>
    </div>

    <div class="status-board section">
      <div class="status-item">
        <div class="status-title">项目活跃率</div>
        <div class="status-value">{{ activeRate }}%</div>
        <el-progress :percentage="activeRate" :stroke-width="8" :show-text="false" />
      </div>
      <div class="status-item">
        <div class="status-title">平均用例密度</div>
        <div class="status-value">{{ avgCasesPerProject }}</div>
        <div class="status-desc">每个项目平均用例数</div>
      </div>
      <div class="status-item">
        <div class="status-title">生成能力状态</div>
        <div class="status-value">{{ modelCount > 0 ? 'AI + 规则' : '规则引擎' }}</div>
        <div class="status-desc">{{ modelCount > 0 ? `默认模型：${defaultModelName}` : '建议在模型设置中补充 AI 配置' }}</div>
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
              <span class="meta-pill">📄 {{ p.req_count }} 需求</span>
              <span class="meta-pill">📋 {{ p.case_count }} 用例</span>
              <span class="meta-pill">👥 {{ p.member_count }} 成员</span>
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

    <div class="section quick-start">
      <div class="section-header">
        <h3>快速开始</h3>
      </div>
      <el-alert
        v-if="modelCount === 0"
        title="未配置 AI 模型，系统将自动使用规则引擎兜底生成"
        type="warning"
        show-icon
        :closable="false"
      />
      <div v-else class="model-tip">默认模型：{{ defaultModelName }}</div>
      <div class="quick-grid">
        <div class="quick-item" @click="$router.push('/projects')">
          <div class="q-title">1. 创建或进入项目</div>
          <div class="q-desc">先准备项目空间和成员，统一需求与用例资产。</div>
          <el-button type="primary" link>打开项目管理</el-button>
        </div>
        <div class="quick-item" @click="goRequirements">
          <div class="q-title">2. 上传或录入需求</div>
          <div class="q-desc">支持文档上传与手动输入，自动解析需求点。</div>
          <el-button type="primary" link>进入需求管理</el-button>
        </div>
        <div class="quick-item" @click="goGenerate">
          <div class="q-title">3. 一键生成测试用例</div>
          <div class="q-desc">按测试类型与场景生成草稿，并可直接发起评审。</div>
          <el-button type="primary" link>进入智能生成</el-button>
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
import { modelApi } from '@/api/models'
import type { Project } from '@/api/types'

const auth = useAuthStore()
const projectStore = useProjectStore()
const router = useRouter()

const totalCases = ref(0)
const totalReqs = ref(0)
const modelCount = ref(0)
const defaultModelName = ref('未设置')

onMounted(async () => {
  await Promise.all([projectStore.fetchProjects(), loadModels()])
  totalCases.value = projectStore.projects.reduce((s, p) => s + (p.case_count || 0), 0)
  totalReqs.value = projectStore.projects.reduce((s, p) => s + (p.req_count || 0), 0)
})

const recentProjects = computed(() =>
  projectStore.projects.filter(p => p.status === 'active').slice(0, 6)
)

const stats = computed(() => [
  { label: '项目总数', value: projectStore.projects.length, icon: '📁', bg: '#eef0fe', hint: `含归档 ${archivedCount.value}` },
  { label: '需求总数', value: totalReqs.value, icon: '📄', bg: '#fef3e2', hint: `平均每项目 ${avgReqsPerProject.value}` },
  { label: '用例总数', value: totalCases.value, icon: '📋', bg: '#e8f5e9', hint: `平均每项目 ${avgCasesPerProject.value}` },
  { label: '活跃项目', value: recentProjects.value.length, icon: '🚀', bg: '#fce4ec', hint: `活跃率 ${activeRate.value}%` },
])
const archivedCount = computed(() => projectStore.projects.filter(p => p.status === 'archived').length)
const activeRate = computed(() => {
  const total = projectStore.projects.length
  if (!total) return 0
  return Math.round((recentProjects.value.length / total) * 100)
})
const avgCasesPerProject = computed(() => {
  const total = projectStore.projects.length
  if (!total) return 0
  return Math.round(totalCases.value / total)
})
const avgReqsPerProject = computed(() => {
  const total = projectStore.projects.length
  if (!total) return 0
  return Math.round(totalReqs.value / total)
})

function openProject(p: Project) {
  projectStore.setCurrent(p)
  router.push(`/projects/${p.id}/requirements`)
}

async function loadModels() {
  try {
    const models = await modelApi.list()
    modelCount.value = models.length
    if (models.length) {
      const def = models.find(m => m.is_default) || models[0]
      defaultModelName.value = `${providerName(def.provider)} · ${def.model_name}`
    }
  } catch {
    modelCount.value = 0
  }
}

function goRequirements() {
  const p = recentProjects.value[0]
  router.push(p ? `/projects/${p.id}/requirements` : '/projects')
}

function goGenerate() {
  const p = recentProjects.value[0]
  router.push(p ? `/projects/${p.id}/generate` : '/projects')
}

function providerName(p: string) {
  return ({ openai: 'OpenAI', anthropic: 'Claude', tongyi: '通义千问', zhipu: '智谱GLM', deepseek: 'DeepSeek' } as Record<string, string>)[p] || p
}
</script>

<style scoped>
.dashboard { width: 100%; max-width: none; }
.page-title { margin-bottom: 24px; display: flex; justify-content: space-between; align-items: center; gap: 12px; }
.page-title h2 { font-size: 22px; font-weight: 700; }
.subtitle { color: var(--text-secondary); font-size: 14px; }
.title-actions { display: flex; gap: 8px; }

.stat-cards { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 28px; }
.stat-card {
  background: linear-gradient(180deg, #ffffff 0%, #fbfdff 100%);
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
.stat-sub { font-size: 12px; color: #9ca3af; margin-top: 4px; }

.section { background: #fff; border-radius: 12px; border: 1px solid var(--border); padding: 20px 24px; }
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.section-header h3 { font-size: 16px; font-weight: 600; }
.status-board { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 16px; }
.status-item { border: 1px solid #e5e7eb; border-radius: 10px; padding: 14px; background: #f9fafb; }
.status-title { font-size: 12px; color: #6b7280; }
.status-value { font-size: 20px; font-weight: 700; margin: 6px 0; color: #111827; }
.status-desc { font-size: 12px; color: #6b7280; }

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
.meta-pill { border: 1px solid #e5e7eb; border-radius: 999px; padding: 1px 8px; color: #6b7280; background: #f8fafc; }
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
.quick-start { margin-top: 16px; }
.model-tip { font-size: 13px; color: var(--text-secondary); margin-bottom: 12px; }
.quick-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-top: 12px; }
.quick-item { border: 1px solid var(--border); border-radius: 10px; padding: 14px; cursor: pointer; }
.quick-item:hover { border-color: #4f6ef7; background: #fafbff; }
.q-title { font-size: 14px; font-weight: 600; margin-bottom: 6px; }
.q-desc { font-size: 12px; color: var(--text-secondary); line-height: 1.5; min-height: 36px; }

@media (max-width: 900px) {
  .page-title { flex-direction: column; align-items: flex-start; }
  .stat-cards { grid-template-columns: repeat(2, 1fr); }
  .status-board { grid-template-columns: 1fr; }
  .project-grid { grid-template-columns: repeat(2, 1fr); }
  .quick-grid { grid-template-columns: 1fr; }
}
</style>
