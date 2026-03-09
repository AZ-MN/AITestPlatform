<template>
  <div class="projects-page">
    <div class="page-header">
      <div>
        <h2>项目管理</h2>
        <p>按测试团队使用习惯优化：先筛选，再操作，最后进入项目。</p>
      </div>
      <el-button type="primary" :icon="Plus" @click="showCreate = true">新建项目</el-button>
    </div>

    <div class="toolbar page-card">
      <el-input v-model="keyword" placeholder="搜索项目名称..." clearable style="width:260px" />
      <el-select v-model="statusFilter" placeholder="全部状态" clearable style="width:140px">
        <el-option label="进行中" value="active" />
        <el-option label="已归档" value="archived" />
      </el-select>
      <el-select v-model="sortBy" style="width:170px">
        <el-option label="最近更新" value="updated" />
        <el-option label="用例最多" value="cases" />
        <el-option label="需求最多" value="requirements" />
      </el-select>
      <div class="toolbar-summary">共 {{ filteredProjects.length }} 个项目</div>
    </div>

    <div class="project-grid">
      <div v-for="p in filteredProjects" :key="p.id" class="project-card">
        <div class="card-top">
          <span class="p-icon">{{ p.icon }}</span>
          <div style="display:flex;gap:6px">
            <el-tag v-if="projectStore.current?.id === p.id" type="primary" size="small">当前</el-tag>
            <el-tag :type="p.status === 'active' ? 'success' : 'info'" size="small">
              {{ p.status === 'active' ? '进行中' : '已归档' }}
            </el-tag>
          </div>
        </div>
        <div class="p-name">{{ p.name }}</div>
        <div class="p-desc">{{ p.description || '暂无描述' }}</div>
        <div class="p-stats">
          <span>📋 {{ p.case_count }} 用例</span>
          <span>📄 {{ p.req_count }} 需求</span>
          <span>👥 {{ p.member_count }} 成员</span>
        </div>
        <div class="card-actions">
          <el-button size="small" @click="setCurrentOnly(p)">设为当前</el-button>
          <el-button size="small" type="primary" @click="openProject(p)">进入项目</el-button>
          <el-button size="small" @click="editProject(p)">编辑</el-button>
          <el-button size="small" type="danger" plain @click="deleteProject(p)">删除</el-button>
        </div>
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
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { Plus } from '@element-plus/icons-vue'
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
const keyword = ref('')
const statusFilter = ref('')
const sortBy = ref<'updated' | 'cases' | 'requirements'>('updated')
const icons = ['📋', '🛒', '🏦', '🏥', '🎮', '📱', '💼', '🚀', '🔧', '🌐', '📊', '🤖']

const form = reactive({ name: '', description: '', icon: '📋' })

onMounted(() => projectStore.fetchProjects())
const filteredProjects = computed(() => {
  const kw = keyword.value.trim().toLowerCase()
  const list = projectStore.projects.filter(p => {
    const keywordOk = !kw || p.name.toLowerCase().includes(kw)
    const statusOk = !statusFilter.value || p.status === statusFilter.value
    return keywordOk && statusOk
  })
  return list.sort((a, b) => {
    if (sortBy.value === 'cases') return (b.case_count || 0) - (a.case_count || 0)
    if (sortBy.value === 'requirements') return (b.req_count || 0) - (a.req_count || 0)
    return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
  })
})

function openProject(p: Project) {
  projectStore.setCurrent(p)
  router.push(`/projects/${p.id}/requirements`)
}

function setCurrentOnly(p: Project) {
  projectStore.setCurrent(p)
  ElMessage.success(`已切换当前项目：${p.name}`)
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

async function deleteProject(p: Project) {
  await ElMessageBox.confirm(`确认删除项目「${p.name}」？删除后不可恢复。`, '删除确认', { type: 'warning' })
  await projectApi.remove(p.id)
  if (projectStore.current?.id === p.id) {
    projectStore.clearCurrent()
  }
  ElMessage.success('项目已删除')
  await projectStore.fetchProjects()
}
</script>

<style scoped>
.projects-page { max-width: 1200px; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px; }
.page-header h2 { font-size: 24px; font-weight: 700; }
.page-header p { margin-top: 4px; font-size: 13px; color: var(--text-secondary); }
.toolbar {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-bottom: 14px;
  padding: 14px;
}
.toolbar-summary {
  margin-left: auto;
  font-size: 12px;
  color: var(--text-secondary);
}

.project-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
.project-card {
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 20px;
  transition: all .2s;
}
.project-card:hover { border-color: #4f6ef7; box-shadow: 0 10px 22px rgba(79,110,247,.12); transform: translateY(-2px); }
.card-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.p-icon { font-size: 32px; }
.p-name { font-size: 16px; font-weight: 600; margin-bottom: 6px; }
.p-desc { font-size: 13px; color: var(--text-secondary); margin-bottom: 12px; min-height: 36px; }
.p-stats { display: flex; gap: 12px; font-size: 12px; color: #9ca3af; margin-bottom: 16px; }
.card-actions { display: flex; gap: 8px; }

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
</style>
