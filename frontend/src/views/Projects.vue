<template>
  <div class="projects-container">
    <!-- Page Header -->
    <div class="page-header">
      <div class="header-content">
        <h2>项目列表</h2>
        <p class="subtitle">管理您的所有测试项目，包括需求分析与用例生成。</p>
      </div>
      <el-button type="primary" size="large" :icon="Plus" @click="openCreate">新建项目</el-button>
    </div>

    <!-- Toolbar -->
    <div class="toolbar">
      <div class="left-tools">
        <el-input
          v-model="keyword"
          placeholder="搜索项目..."
          prefix-icon="Search"
          clearable
          class="search-input"
        />
        <el-radio-group v-model="statusFilter" class="status-filter">
          <el-radio-button label="all">全部项目</el-radio-button>
          <el-radio-button label="active">进行中</el-radio-button>
          <el-radio-button label="archived">已归档</el-radio-button>
        </el-radio-group>
        
        <el-button @click="resetFilters" class="reset-btn">重置</el-button>
      </div>
      <div class="right-tools">
        <span class="count-badge">共 {{ filteredProjects.length }} 个项目</span>
      </div>
    </div>

    <!-- Project Grid -->
    <div v-if="filteredProjects.length > 0" class="project-grid">
      <div
        v-for="p in filteredProjects"
        :key="p.id"
        class="project-card"
        @click="openProject(p)"
      >
        <div class="card-main">
          <div class="icon-wrapper">{{ p.icon }}</div>
          <div class="card-content">
            <div class="card-top-row">
              <h3 class="project-name">{{ p.name }}</h3>
              <div class="card-actions" @click.stop>
                <el-dropdown trigger="click" @command="(cmd) => handleCommand(cmd, p)">
                  <el-button link class="more-btn"><el-icon><MoreFilled /></el-icon></el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item command="edit" :icon="Edit">编辑项目</el-dropdown-item>
                      <el-dropdown-item command="archive" :icon="p.status === 'archived' ? 'RefreshLeft' : 'FolderRemove'">
                        {{ p.status === 'archived' ? '恢复项目' : '归档项目' }}
                      </el-dropdown-item>
                      <el-dropdown-item command="delete" :icon="Delete" divided class="text-danger">删除项目</el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </div>
            <p class="project-desc">{{ p.description || '暂无描述' }}</p>
          </div>
        </div>

        <div class="card-footer">
          <div class="stats">
            <div class="stat-item" title="需求数量">
              <el-icon><Document /></el-icon>
              <span>{{ p.req_count || 0 }}</span>
            </div>
            <div class="stat-item" title="用例数量">
              <el-icon><List /></el-icon>
              <span>{{ p.case_count || 0 }}</span>
            </div>
            <div class="stat-item" title="成员数量">
              <el-icon><User /></el-icon>
              <span>{{ p.member_count || 0 }}</span>
            </div>
          </div>
          <el-tag :type="p.status === 'active' ? 'success' : 'info'" size="small" effect="plain" class="status-tag">
            {{ p.status === 'active' ? '进行中' : '已归档' }}
          </el-tag>
        </div>
      </div>
      
      <!-- Add Card -->
      <div class="add-card" @click="openCreate">
        <el-icon class="add-icon"><Plus /></el-icon>
        <span class="add-text">新建项目</span>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else class="empty-state">
      <div class="empty-icon">📂</div>
      <h3>没有找到项目</h3>
      <p>试着调整搜索条件，或者创建一个新项目。</p>
      <el-button v-if="keyword || statusFilter !== 'all'" @click="resetFilters">清除筛选</el-button>
      <el-button v-else type="primary" @click="openCreate">新建第一个项目</el-button>
    </div>

    <!-- Create/Edit Dialog -->
    <el-dialog
      v-model="showDialog"
      :title="isEdit ? '编辑项目' : '新建项目'"
      width="500px"
      align-center
      destroy-on-close
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <el-form-item label="项目图标">
          <div class="icon-selector">
            <div 
              v-for="icon in iconList" 
              :key="icon" 
              class="icon-option"
              :class="{ active: form.icon === icon }"
              @click="form.icon = icon"
            >
              {{ icon }}
            </div>
          </div>
        </el-form-item>
        <el-form-item label="项目名称" prop="name">
          <el-input v-model="form.name" placeholder="例如：电商后台管理系统" size="large" />
        </el-form-item>
        <el-form-item label="项目描述" prop="description">
          <el-input 
            v-model="form.description" 
            type="textarea" 
            :rows="3" 
            placeholder="简要描述项目的目标和范围..." 
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showDialog = false">取消</el-button>
          <el-button type="primary" :loading="submitting" @click="handleSubmit">
            {{ isEdit ? '保存修改' : '立即创建' }}
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useProjectStore } from '@/stores/project'
import { projectApi } from '@/api/projects'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, MoreFilled, Edit, Delete, FolderRemove, RefreshLeft, Document, List, User } from '@element-plus/icons-vue'
import type { Project } from '@/api/types'

const router = useRouter()
const projectStore = useProjectStore()

// State
const keyword = ref('')
const statusFilter = ref('all')
const showDialog = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const formRef = ref()
const currentEditId = ref<number | null>(null)

const iconList = ['🚀', '💻', '📱', '🌐', '🛒', '🎮', '📊', '🔒', '☁️', '🎨']

const form = reactive({
  name: '',
  description: '',
  icon: '🚀'
})

const rules = {
  name: [{ required: true, message: '请输入项目名称', trigger: 'blur' }]
}

// Computed
const filteredProjects = computed(() => {
  return projectStore.projects.filter(p => {
    const matchStatus = statusFilter.value === 'all' || p.status === statusFilter.value
    const matchKey = p.name.toLowerCase().includes(keyword.value.toLowerCase())
    return matchStatus && matchKey
  })
})

// Lifecycle
onMounted(() => {
  projectStore.fetchProjects()
})

// Actions
function resetFilters() {
  keyword.value = ''
  statusFilter.value = 'all'
}

function openProject(p: Project) {
  projectStore.setCurrent(p)
  router.push(`/projects/${p.id}/requirements`)
}

function openCreate() {
  isEdit.value = false
  currentEditId.value = null
  form.name = ''
  form.description = ''
  form.icon = iconList[0]
  showDialog.value = true
}

function handleCommand(cmd: string, p: Project) {
  if (cmd === 'edit') {
    isEdit.value = true
    currentEditId.value = p.id
    form.name = p.name
    form.description = p.description || ''
    form.icon = p.icon
    showDialog.value = true
  } else if (cmd === 'archive') {
    toggleArchive(p)
  } else if (cmd === 'delete') {
    confirmDelete(p)
  }
}

async function handleSubmit() {
  if (!formRef.value) return
  await formRef.value.validate()
  
  submitting.value = true
  try {
    if (isEdit.value && currentEditId.value) {
      await projectApi.update(currentEditId.value, form)
      ElMessage.success('项目已更新')
    } else {
      await projectApi.create(form)
      ElMessage.success('项目已创建')
    }
    await projectStore.fetchProjects()
    showDialog.value = false
  } finally {
    submitting.value = false
  }
}

async function toggleArchive(p: Project) {
  const isArchived = p.status === 'archived'
  const action = isArchived ? '恢复' : '归档'
  
  try {
    await ElMessageBox.confirm(`确定要${action}项目 "${p.name}" 吗？`, '提示', {
      type: 'warning',
      confirmButtonText: '确定',
      cancelButtonText: '取消'
    })
    
    if (isArchived) {
      await projectApi.unarchive(p.id)
    } else {
      await projectApi.archive(p.id)
    }
    ElMessage.success(`项目已${action}`)
    projectStore.fetchProjects()
  } catch (e) {
    // Cancelled
  }
}

async function confirmDelete(p: Project) {
  try {
    await ElMessageBox.confirm(
      `确定要永久删除项目 "${p.name}" 吗？此操作不可恢复！`,
      '危险操作',
      {
        type: 'error',
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        confirmButtonClass: 'el-button--danger'
      }
    )
    
    await projectApi.purge(p.id).catch(() => projectApi.remove(p.id))
    ElMessage.success('项目已删除')
    if (projectStore.current?.id === p.id) projectStore.current = null
    projectStore.fetchProjects()
  } catch (e) {
    // Cancelled or error
  }
}
</script>

<style scoped>
.projects-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}
.page-header h2 {
  font-size: 24px;
  font-weight: 800;
  color: var(--text-primary);
  margin-bottom: 4px;
}
.subtitle {
  color: var(--text-secondary);
  font-size: 14px;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 16px;
  background: var(--card-bg);
  padding: 16px;
  border-radius: var(--radius-lg);
  border: 1px solid var(--border);
}
.left-tools {
  display: flex;
  gap: 16px;
  align-items: center;
}
.search-input {
  width: 280px;
}
.count-badge {
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 500;
}

/* Grid Layout */
.project-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
  padding-bottom: 20px;
}

.project-card {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 16px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.25, 0.8, 0.25, 1);
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
}
.project-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
  border-color: var(--primary);
}

.card-main {
  display: flex;
  gap: 16px;
  margin-bottom: 12px;
  flex: 1;
}
.icon-wrapper {
  width: 44px;
  height: 44px;
  background: var(--bg-secondary);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  transition: background 0.2s;
  flex-shrink: 0;
}
.project-card:hover .icon-wrapper {
  background: var(--primary-light);
}

.card-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.card-top-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 2px;
}
.project-name {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 4px;
  line-height: 1.3;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.project-desc {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top: 1px solid var(--border);
  padding-top: 12px;
}
.stats {
  display: flex;
  gap: 12px;
}
.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
  color: var(--text-secondary);
  font-size: 12px;
}
.stat-item .el-icon { font-size: 13px; }

/* Add Card Style */
.add-card {
  background: transparent;
  border: 2px dashed var(--border);
  border-radius: var(--radius-lg);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
  min-height: 140px; /* Match typical card height */
  color: var(--text-placeholder);
  gap: 8px;
}
.add-card:hover {
  border-color: var(--primary);
  color: var(--primary);
  background: var(--primary-light);
}
.add-icon { font-size: 28px; }
.add-text { font-weight: 600; font-size: 14px; }

/* Empty State */
.empty-state {
  text-align: center;
  padding: 60px 0;
  color: var(--text-secondary);
}
.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.5;
}

/* Filter Button Overrides */
.status-filter .el-radio-button__inner {
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  color: var(--text-secondary);
  box-shadow: none !important;
}
.status-filter .el-radio-button__original-radio:checked + .el-radio-button__inner {
  background: var(--primary) !important;
  border-color: var(--primary) !important;
  color: #fff !important;
  box-shadow: -1px 0 0 0 var(--primary) !important;
}
/* Reset Button Override */
.reset-btn {
  margin-left: 12px;
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  color: var(--text-primary);
}
.reset-btn:hover, .reset-btn:focus {
  background: var(--primary) !important;
  border-color: var(--primary) !important;
  color: #fff !important;
}

/* Dialog Styles */
.icon-selector {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}
.icon-option {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--border);
  border-radius: 8px;
  cursor: pointer;
  font-size: 20px;
  transition: all 0.2s;
}
.icon-option:hover {
  background: var(--bg-secondary);
}
.icon-option.active {
  border-color: var(--primary);
  background: var(--primary-light);
}
.text-danger {
  color: var(--danger);
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
  .toolbar {
    flex-direction: column;
    align-items: stretch;
  }
  .left-tools {
    flex-direction: column;
    align-items: stretch;
  }
  .search-input {
    width: 100%;
  }
}
</style>
