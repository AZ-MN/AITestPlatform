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
        <div class="stat-icon" :style="{ background: stat.bg }">
          <el-icon><component :is="stat.icon" /></el-icon>
        </div>
        <div>
          <div class="stat-value">{{ stat.value }}</div>
          <div class="stat-label">{{ stat.label }}</div>
          <div class="stat-sub">{{ stat.hint }}</div>
        </div>
      </div>
    </div>

    <!-- 中间引导区：快速开始 + 运行状态 -->
    <div class="guide-row">
      <!-- Quick Start Guide -->
      <div class="section guide-section">
        <div class="section-header">
          <h3><el-icon><Guide /></el-icon> 快速开始指引</h3>
        </div>
        <div class="guide-steps">
          <div class="step-card" @click="$router.push('/projects')">
            <div class="step-num">01</div>
            <div class="step-content">
              <div class="step-title">创建项目</div>
              <div class="step-desc">新建或管理测试项目</div>
            </div>
            <div class="step-icon"><el-icon><Folder /></el-icon></div>
          </div>
          <div class="step-arrow"><el-icon><Right /></el-icon></div>
          <div class="step-card" @click="goRequirements">
            <div class="step-num">02</div>
            <div class="step-content">
              <div class="step-title">录入需求</div>
              <div class="step-desc">上传文档/智能解析</div>
            </div>
            <div class="step-icon"><el-icon><Document /></el-icon></div>
          </div>
          <div class="step-arrow"><el-icon><Right /></el-icon></div>
          <div class="step-card" @click="goGenerate">
            <div class="step-num">03</div>
            <div class="step-content">
              <div class="step-title">生成用例</div>
              <div class="step-desc">AI 一键生成测试用例</div>
            </div>
            <div class="step-icon"><el-icon><MagicStick /></el-icon></div>
          </div>
        </div>
      </div>

      <!-- Status Board (Mini) -->
      <div class="section status-mini">
        <div class="section-header"><h3>运行状态</h3></div>
        <div class="status-content">
          <div class="status-row-item">
            <span class="label">活跃率</span>
            <div class="value-group">
              <span class="value">{{ activeRate }}%</span>
              <el-progress type="circle" :percentage="activeRate" :width="20" :stroke-width="3" :show-text="false" color="#10b981" />
            </div>
          </div>
          <div class="status-divider"></div>
          <div class="status-row-item">
            <span class="label">AI 就绪</span>
            <div class="value-group">
              <span class="value">{{ modelCount > 0 ? 'Yes' : 'No' }}</span>
              <el-icon class="status-icon-check" :class="{ ready: modelCount > 0 }"><CircleCheckFilled /></el-icon>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Recently Active Projects (Full Width) -->
    <div class="section project-section">
      <div class="section-header">
        <h3>最近项目</h3>
        <el-button link type="primary" @click="$router.push('/projects')">全部项目 <el-icon><ArrowRight /></el-icon></el-button>
      </div>
      <div class="project-list-horizontal">
        <div v-for="p in recentProjects" :key="p.id" class="project-card-h" @click="openProject(p)">
          <div class="ph-icon">{{ p.icon }}</div>
          <div class="ph-info">
            <div class="ph-name">{{ p.name }}</div>
            <div class="ph-desc">{{ p.description || '暂无描述' }}</div>
          </div>
          <div class="ph-stats">
            <span class="ph-tag"><el-icon><Document /></el-icon> {{ p.req_count }}</span>
            <span class="ph-tag"><el-icon><List /></el-icon> {{ p.case_count }}</span>
          </div>
          <el-icon class="ph-arrow"><ArrowRight /></el-icon>
        </div>
        <div v-if="recentProjects.length === 0" class="empty-placeholder">
          暂无最近项目，去创建吧！
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
import { Folder, Document, MagicStick, Cpu, DataLine, List, Guide, Right, CircleCheckFilled, ArrowRight } from '@element-plus/icons-vue'

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
  { label: '项目总数', value: projectStore.projects.length, icon: Folder, bg: '#eef0fe', hint: `含归档 ${archivedCount.value}` },
  { label: '需求总数', value: totalReqs.value, icon: Document, bg: '#fef3e2', hint: `平均每项目 ${avgReqsPerProject.value}` },
  { label: '用例总数', value: totalCases.value, icon: List, bg: '#e8f5e9', hint: `平均每项目 ${avgCasesPerProject.value}` },
  { label: '活跃项目', value: recentProjects.value.length, icon: DataLine, bg: '#fce4ec', hint: `活跃率 ${activeRate.value}%` },
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
.dashboard { width: 100%; display: flex; flex-direction: column; gap: 32px; }

/* 头部欢迎区 - 更加紧凑 */
.page-title { 
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 24px;
  display: flex; 
  justify-content: space-between; 
  align-items: center; 
  gap: 24px; 
  box-shadow: var(--shadow-sm);
  background-image: radial-gradient(circle at right top, var(--primary-light), transparent 40%);
}
.page-title h2 { 
  font-size: 24px; 
  font-weight: 700; 
  color: var(--text-primary);
  margin-bottom: 4px;
  letter-spacing: -0.5px;
}
.subtitle { 
  color: var(--text-secondary); 
  font-size: 14px; 
}

/* 统计卡片 - 卡片化设计 */
.stat-cards { 
  display: grid; 
  grid-template-columns: repeat(4, 1fr); 
  gap: 20px; 
}
.stat-card {
  background: #fff;
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  box-shadow: var(--shadow-sm);
  transition: var(--transition);
  position: relative;
  overflow: hidden;
}
.stat-card:hover { transform: translateY(-2px); box-shadow: var(--shadow-md); border-color: var(--primary-light); }
.stat-icon {
  width: 40px; height: 40px;
  border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  font-size: 20px;
}
.stat-value { 
  font-size: 28px; 
  font-weight: 700; 
  color: var(--text-primary); 
  line-height: 1;
}
.stat-label { 
  font-size: 13px; 
  color: var(--text-secondary); 
  font-weight: 500;
}
.stat-sub { font-size: 12px; color: var(--text-placeholder); display: flex; align-items: center; gap: 4px; margin-top: auto; }

/* 主体内容区 */
.dashboard-grid {
  display: grid;
  grid-template-columns: 3fr 1fr;
  gap: 24px;
  align-items: start; /* Prevent columns from stretching to full height unnecessarily */
}

/* 状态看板 & 最近项目 */
.section { 
  background: #fff; 
  border-radius: var(--radius-xl); 
  border: 1px solid var(--border); 
  padding: 24px; 
  box-shadow: var(--shadow-md);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.section-header { 
  display: flex; 
  justify-content: space-between; 
  align-items: center; 
  margin-bottom: 16px; 
  flex-shrink: 0;
}
.section-header h3 { 
  font-size: 16px; 
  font-weight: 700; 
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 8px;
}

/* Guide Row */
.guide-row {
  display: grid;
  grid-template-columns: 3fr 1fr;
  gap: 24px;
}
.guide-section {
  background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
  border-color: #bbf7d0;
}
.guide-steps {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 8px 0;
}
.step-card {
  flex: 1;
  background: rgba(255,255,255,0.6);
  border: 1px solid rgba(255,255,255,0.8);
  border-radius: var(--radius-lg);
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
  overflow: hidden;
}
.step-card:hover {
  background: #fff;
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}
.step-num {
  font-size: 24px;
  font-weight: 800;
  color: #10b981;
  opacity: 0.2;
  position: absolute;
  right: -4px;
  top: -8px;
  font-family: 'Arial', sans-serif;
}
.step-content { flex: 1; z-index: 1; }
.step-title { font-weight: 700; color: var(--text-primary); margin-bottom: 2px; }
.step-desc { font-size: 12px; color: var(--text-secondary); }
.step-icon { 
  width: 36px; height: 36px; 
  background: #10b981; 
  color: #fff; 
  border-radius: 8px; 
  display: flex; align-items: center; justify-content: center;
  font-size: 18px;
  z-index: 1;
}
.step-arrow { color: #10b981; opacity: 0.5; font-size: 20px; }

/* Status Mini */
.status-mini {
  background: #fff;
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
}
.status-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: space-around;
}
.status-row-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.status-divider { height: 1px; background: var(--border); margin: 8px 0; }
.value-group { display: flex; align-items: center; gap: 8px; }
.value-group .value { font-weight: 700; font-size: 16px; color: var(--text-primary); }
.status-icon-check { color: var(--border); font-size: 18px; }
.status-icon-check.ready { color: #10b981; }

/* Horizontal Project List */
.project-list-horizontal {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 16px;
}
.project-card-h {
  background: #fff;
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 16px;
  cursor: pointer;
  transition: all 0.2s;
}
.project-card-h:hover {
  border-color: var(--primary);
  background: var(--bg-secondary);
  transform: translateX(4px);
}
.ph-icon {
  width: 44px; height: 44px;
  font-size: 22px;
  background: var(--bg);
  border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
}
.ph-info { flex: 1; min-width: 0; }
.ph-name { font-weight: 600; font-size: 15px; color: var(--text-primary); margin-bottom: 2px; }
.ph-desc { font-size: 12px; color: var(--text-secondary); text-overflow: ellipsis; white-space: nowrap; overflow: hidden; }
.ph-stats { display: flex; gap: 12px; }
.ph-tag { 
  font-size: 12px; color: var(--text-secondary); 
  display: flex; align-items: center; gap: 4px; 
  background: var(--bg); padding: 2px 8px; border-radius: 4px;
}
.ph-arrow { color: var(--text-placeholder); font-size: 16px; }

.empty-placeholder { padding: 40px; text-align: center; color: var(--text-secondary); }

/* 响应式调整 */
@media (max-width: 1200px) {
  .stat-cards { grid-template-columns: repeat(2, 1fr); }
  .guide-row { grid-template-columns: 1fr; }
  .status-mini { display: none; }
  .project-list-horizontal { grid-template-columns: 1fr; }
}

@media (max-width: 768px) {
  .page-title { flex-direction: column; align-items: flex-start; padding: 20px; }
  .stat-cards { grid-template-columns: 1fr; gap: 16px; }
  .guide-steps { flex-direction: column; gap: 12px; }
  .step-arrow { transform: rotate(90deg); }
}

@media (max-width: 768px) {
  .page-title { flex-direction: column; align-items: flex-start; padding: 20px; }
  .stat-cards { grid-template-columns: 1fr; gap: 16px; }
  .project-list { gap: 12px; }
  .project-card { flex-direction: column; align-items: flex-start; gap: 12px; }
  .p-meta { margin-left: 0; width: 100%; justify-content: space-between; }
  .side-column { flex-direction: column; }
}
</style>
