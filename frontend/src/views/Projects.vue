<template>
  <div class="projects-page">
    <div class="page-header">
      <h2>项目管理</h2>
      <el-button type="primary" :icon="Plus" @click="showCreate = true">新建项目</el-button>
    </div>

    <div class="project-grid">
      <div
        v-for="p in projectStore.projects"
        :key="p.id"
        class="project-card"
        tabindex="0"
        @click="openProject(p)"
        @keydown.enter.prevent="openProject(p)"
        @keydown.space.prevent="openProject(p)"
      >
        <div class="card-top">
          <span class="p-icon">{{ p.icon }}</span>
          <div class="top-right">
            <el-tag :type="p.status === 'active' ? 'success' : 'info'" size="small">
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
        <div class="p-name">{{ p.name }}</div>
        <div class="p-desc">{{ p.description || '暂无描述' }}</div>
        <div class="p-stats">
          <span>📋 {{ p.case_count }} 用例</span>
          <span>📄 {{ p.req_count }} 需求</span>
          <span>👥 {{ p.member_count }} 成员</span>
        </div>
        <div class="card-hint">点击卡片进入项目</div>
      </div>

      <div class="add-card" @click="showCreate = true">
        <el-icon :size="36"><Plus /></el-icon>
        <span>新建项目</span>
      </div>
    </div>

    <!-- 新建项目弹窗 -->
    <el-dialog v-model="showCreate" :title="editMode ? '编辑项目' : '新建项目'" width="480px">
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
import { ref, reactive, onMounted } from 'vue'
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

const form = reactive({ name: '', description: '', icon: '📋' })

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
  await ElMessageBox.confirm(`确认归档项目「${p.name}」？`, '归档确认', { type: 'warning' })
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
  await ElMessageBox.confirm(`确认将项目「${p.name}」取消归档？`, '取消归档确认', { type: 'info' })
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
    { type: 'error', confirmButtonText: '确认删除', cancelButtonText: '取消' }
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
.projects-page { width: 100%; max-width: none; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.page-header h2 { font-size: 22px; font-weight: 700; }

.project-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 16px; }
.project-card {
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px;
  transition: all .2s;
  cursor: pointer;
}
.project-card:hover { border-color: #4f6ef7; box-shadow: 0 4px 16px rgba(79,110,247,.1); transform: translateY(-1px); }
.project-card:focus-visible { outline: 2px solid #4f6ef7; outline-offset: 2px; }
.card-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.top-right { display: flex; align-items: center; gap: 8px; }
.card-icons { display: flex; align-items: center; }
.p-icon { font-size: 32px; }
.p-name { font-size: 16px; font-weight: 600; margin-bottom: 6px; }
.p-desc { font-size: 13px; color: var(--text-secondary); margin-bottom: 12px; min-height: 36px; }
.p-stats { display: flex; gap: 12px; font-size: 12px; color: #9ca3af; margin-bottom: 8px; }
.card-hint { font-size: 12px; color: #9ca3af; }
:deep(.card-icons .el-button + .el-button) { margin-left: 0; }

.add-card {
  background: #fff;
  border: 2px dashed var(--border);
  border-radius: 12px;
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
  .top-right { gap: 4px; }
}
</style>
