<template>
  <div class="projects-page">
    <div class="page-header">
      <div>
        <h2>项目管理</h2>
        <div class="sub-title">统一管理项目资产与协作成员，点击卡片可直接进入项目</div>
      </div>
      <el-button type="primary" :icon="Plus" @click="showCreate = true">新建项目</el-button>
    </div>

    <div class="toolbar page-card">
      <el-input
        v-model="keyword"
        placeholder="搜索项目名称..."
        clearable
        style="width:260px"
      />
      <el-segmented v-model="statusFilter" :options="statusOptions" />
      <span class="toolbar-stat">共 {{ filteredProjects.length }} / {{ projectStore.projects.length }} 个项目</span>
    </div>

    <div class="project-grid">
      <div
        v-for="p in filteredProjects"
        :key="p.id"
        class="project-card"
        tabindex="0"
        @click="openProject(p)"
        @keydown.enter.prevent="openProject(p)"
        @keydown.space.prevent="openProject(p)"
      >
        <div class="card-top">
          <div class="main-info">
            <span class="p-icon">{{ p.icon }}</span>
            <el-tooltip :content="p.name" placement="top">
              <span class="p-name">{{ p.name }}</span>
            </el-tooltip>
          </div>
          <div class="top-right">
            <el-tag :type="p.status === 'active' ? 'success' : 'info'" size="small" :class="['status-tag', p.status === 'active' ? 'is-active' : 'is-archived']">
              {{ p.status === 'active' ? '进行中' : '已归档' }}
            </el-tag>
            <div class="card-icons" @click.stop>
              <el-tooltip content="编辑项目" placement="top">
                <el-button text circle @click.stop="editProject(p)">
                  <el-icon><Edit /></el-icon>
                </el-button>
              </el-tooltip>
              <el-tooltip :content="p.status === 'archived' ? '取消归档' : '归档项目'" placement="top">
                <el-button text circle type="warning" @click.stop="p.status === 'archived' ? unarchiveProject(p) : archiveProject(p)">
                  <el-icon><RefreshLeft v-if="p.status === 'archived'" /><FolderRemove v-else /></el-icon>
                </el-button>
              </el-tooltip>
              <el-tooltip content="删除项目" placement="top">
                <el-button text circle type="danger" :disabled="p.status === 'archived'" @click.stop="deleteProject(p)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </el-tooltip>
            </div>
          </div>
        </div>
        <div class="p-desc">{{ p.description || '暂无项目描述，点击进入后可补充。' }}</div>
        <div class="p-stats">
          <span class="stat-pill"><em>📄</em>{{ p.req_count }} 需求</span>
          <span class="stat-pill"><em>📋</em>{{ p.case_count }} 用例</span>
          <span class="stat-pill"><em>👥</em>{{ p.member_count }} 成员</span>
        </div>
        <div class="card-hint">点击任意区域进入项目</div>
      </div>

      <div class="add-card" @click="showCreate = true">
        <el-icon :size="36"><Plus /></el-icon>
        <span>新建项目</span>
      </div>
    </div>

    <!-- 新建项目弹窗 -->
    <el-dialog v-model="showCreate" :title="editMode ? '编辑项目' : '新建项目'" width="480px" :close-on-click-modal="false">
      <el-form ref="formRef" :model="form" label-width="80px">
        <el-form-item label="项目图标">
          <div class="icon-picker">
            <span v-for="ico in icons" :key="ico"
              :class="['icon-opt', { active: form.icon === ico }]"
              @click="form.icon = ico">{{ ico }}</span>
          </div>
        </el-form-item>
        <el-form-item label="项目名称" prop="name" :rules="[{ required: true }]">
          <el-input v-model="form.name" placeholder="请输入项目名称" />
        </el-form-item>
        <el-form-item label="项目描述">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="项目描述（可选）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreate = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">{{ editMode ? '保存' : '创建' }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, Edit, Delete, FolderRemove, RefreshLeft } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useProjectStore } from '@/stores/project'
import { projectApi } from '@/api/projects'
import type { Project } from '@/api/types'

const projectStore = useProjectStore()
const router = useRouter()
const showCreate = ref(false)
const editMode = ref(false)
const saving = ref(false)
const editId = ref<number>()
const formRef = ref()
const icons = ['📋', '🛒', '🏦', '🏥', '🎮', '📱', '💼', '🚀', '🔧', '🌐', '📊', '🤖']
const keyword = ref('')
const statusFilter = ref<'all' | 'active' | 'archived'>('all')
const statusOptions = [
  { label: '全部', value: 'all' },
  { label: '进行中', value: 'active' },
  { label: '已归档', value: 'archived' },
]

const form = reactive({ name: '', description: '', icon: '📋' })
const filteredProjects = computed(() => {
  const key = keyword.value.trim().toLowerCase()
  return projectStore.projects.filter(p => {
    const statusOk = statusFilter.value === 'all' || p.status === statusFilter.value
    const keyOk = !key || p.name.toLowerCase().includes(key)
    return statusOk && keyOk
  })
})

onMounted(() => projectStore.fetchProjects())

function openProject(p: Project) {
  projectStore.setCurrent(p)
  router.push(`/projects/${p.id}/requirements`)
}

function editProject(p: Project) {
  editMode.value = true
  editId.value = p.id
  form.name = p.name
  form.description = p.description || ''
  form.icon = p.icon
  showCreate.value = true
}

async function handleSave() {
  await formRef.value?.validate()
  saving.value = true
  try {
    if (editMode.value && editId.value) {
      await projectApi.update(editId.value, form)
      ElMessage.success('更新成功')
    } else {
      await projectApi.create(form)
      ElMessage.success('项目创建成功')
    }
    await projectStore.fetchProjects()
    showCreate.value = false
    editMode.value = false
    Object.assign(form, { name: '', description: '', icon: '📋' })
  } finally {
    saving.value = false
  }
}

async function archiveProject(p: Project) {
  await ElMessageBox.confirm(`确认归档项目「${p.name}」？`, '归档确认', {
    type: 'warning',
    closeOnClickModal: false,
    closeOnPressEscape: false,
  })
  try {
    await projectApi.archive(p.id)
  } catch (e: any) {
    if (e?.response?.status === 404) {
      await projectApi.setStatus(p.id, 'archived')
    } else {
      throw e
    }
  }
  ElMessage.success('已归档')
  await projectStore.fetchProjects()
}

async function unarchiveProject(p: Project) {
  await ElMessageBox.confirm(`确认将项目「${p.name}」取消归档？`, '取消归档确认', {
    type: 'info',
    closeOnClickModal: false,
    closeOnPressEscape: false,
  })
  try {
    await projectApi.unarchive(p.id)
  } catch (e: any) {
    if (e?.response?.status === 404) {
      await projectApi.setStatus(p.id, 'active')
    } else {
      throw e
    }
  }
  ElMessage.success('已取消归档')
  await projectStore.fetchProjects()
}

async function deleteProject(p: Project) {
  if (p.status === 'archived') {
    ElMessage.warning('已归档项目不可删除，请先取消归档')
    return
  }
  await ElMessageBox.confirm(
    `确认永久删除项目「${p.name}」？该操作将同时删除其需求和测试用例，且不可恢复。`,
    '删除确认',
    {
      type: 'error',
      confirmButtonText: '确认删除',
      cancelButtonText: '取消',
      closeOnClickModal: false,
      closeOnPressEscape: false,
    }
  )
  try {
    await projectApi.purge(p.id)
  } catch (e: any) {
    if (e?.response?.status === 404) {
      await projectApi.remove(p.id)
    } else {
      throw e
    }
  }
  const latest = await projectApi.list()
  if (latest.some(item => item.id === p.id)) {
    ElMessage.error('删除未生效，请稍后重试（建议重启后端）')
    await projectStore.fetchProjects()
    return
  }
  if (projectStore.current?.id === p.id) projectStore.current = null
  ElMessage.success('项目已删除')
  await projectStore.fetchProjects()
}
</script>

<style scoped>
.projects-page { width: 100%; max-width: none; height: 100%; min-height: 0; display: flex; flex-direction: column; overflow: hidden; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.page-header h2 { font-size: 22px; font-weight: 700; }
.sub-title { margin-top: 4px; font-size: 13px; color: var(--text-secondary); }
.toolbar {
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
}
.toolbar-stat { margin-left: auto; font-size: 13px; color: var(--text-secondary); }

.project-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
  flex: 1;
  min-height: 0;
  overflow: auto;
  padding-right: 2px;
}
.project-card {
  background: linear-gradient(180deg, #ffffff 0%, #fcfdff 100%);
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  padding: 20px;
  transition: all .2s;
  cursor: pointer;
  position: relative;
  overflow: hidden;
}
.project-card::before {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
  height: 3px;
  background: linear-gradient(90deg, #4f6ef7 0%, #7c92ff 100%);
  opacity: 0;
  transition: opacity .2s;
}
.project-card:hover::before { opacity: 1; }
.project-card:hover { border-color: #c7d2fe; box-shadow: 0 8px 20px rgba(79,110,247,.12); transform: translateY(-2px); }
.project-card:focus-visible { outline: 2px solid #4f6ef7; outline-offset: 2px; }
.card-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.main-info { display: flex; align-items: center; gap: 8px; min-width: 0; flex: 1; }
.top-right { display: flex; align-items: center; gap: 8px; }
.card-icons { display: flex; align-items: center; opacity: .55; transition: opacity .2s; }
.project-card:hover .card-icons, .project-card:focus-within .card-icons { opacity: 1; }
.p-icon {
  font-size: 24px;
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #f1f5ff;
}
.p-name {
  font-size: 16px;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.p-desc { font-size: 13px; color: var(--text-secondary); margin-bottom: 12px; min-height: 38px; line-height: 1.45; }
.p-stats { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 8px; }
.stat-pill {
  font-size: 12px;
  color: #4b5563;
  background: #f8fafc;
  border: 1px solid #e5e7eb;
  border-radius: 999px;
  padding: 2px 8px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.stat-pill em { font-style: normal; opacity: .9; }
.card-hint { font-size: 12px; color: #9ca3af; }
.status-tag { border-radius: 999px; font-weight: 600; }
:deep(.card-icons .el-button + .el-button) { margin-left: 0; }
:deep(.card-icons .el-button.is-text) { width: 26px; height: 26px; }

.add-card {
  background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
  border: 2px dashed var(--border);
  border-radius: 14px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  cursor: pointer;
  color: #9ca3af;
  min-height: 200px;
  transition: all .2s;
  font-size: 14px;
}
.add-card:hover { border-color: #4f6ef7; color: #4f6ef7; }

.icon-picker { display: flex; flex-wrap: wrap; gap: 8px; }
.icon-opt {
  width: 36px; height: 36px;
  display: flex; align-items: center; justify-content: center;
  font-size: 20px;
  border: 2px solid var(--border);
  border-radius: 8px;
  cursor: pointer;
  transition: all .15s;
}
.icon-opt.active { border-color: #4f6ef7; background: var(--primary-light); }
.icon-opt:hover { border-color: #4f6ef7; }

@media (max-width: 768px) {
  .toolbar { flex-wrap: wrap; }
  .toolbar-stat { margin-left: 0; }
  .top-right { gap: 4px; }
}
</style>
