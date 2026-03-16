<template>
  <div class="members-container">
    <div class="page-desc">
      <p class="subtitle">管理项目成员及其权限角色。</p>
    </div>

    <!-- Stats Overview -->
    <div class="stats-overview">
      <div class="stat-card">
        <div class="stat-icon bg-blue"><el-icon><UserFilled /></el-icon></div>
        <div class="stat-info">
          <div class="stat-value">{{ members.length }}</div>
          <div class="stat-label">成员总数</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon bg-purple"><el-icon><Management /></el-icon></div>
        <div class="stat-info">
          <div class="stat-value">{{ adminCount }}</div>
          <div class="stat-label">管理员</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon bg-green"><el-icon><Tools /></el-icon></div>
        <div class="stat-info">
          <div class="stat-value">{{ testerCount }}</div>
          <div class="stat-label">测试工程师</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon bg-orange"><el-icon><View /></el-icon></div>
        <div class="stat-info">
          <div class="stat-value">{{ viewerCount }}</div>
          <div class="stat-label">访客</div>
        </div>
      </div>
      
      <div class="action-card">
         <el-button type="primary" :icon="Plus" size="large" class="add-member-btn" @click="openAddDialog">添加成员</el-button>
      </div>
    </div>

    <!-- Members Table -->
    <div class="content-card">
      <div class="table-toolbar">
        <el-input
          v-model="searchQuery"
          placeholder="搜索成员姓名或邮箱..."
          prefix-icon="Search"
          style="width: 240px"
          clearable
        />
      </div>
      
      <el-table :data="filteredMembers" style="width: 100%" height="100%" v-loading="loading">
        <el-table-column label="成员" min-width="200">
          <template #default="{ row }">
            <div class="user-cell">
              <el-avatar :size="32" :style="{ backgroundColor: stringToColor(row.username) }">
                {{ row.full_name?.charAt(0)?.toUpperCase() || row.username?.charAt(0)?.toUpperCase() }}
              </el-avatar>
              <div class="user-info">
                <div class="user-name">{{ row.full_name }}</div>
                <div class="user-email">{{ row.username }}</div>
              </div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="角色" width="150">
          <template #default="{ row }">
            <el-tag :type="roleType(row.role)" effect="light" round>
              {{ roleLabel(row.role) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="加入时间" width="180">
          <template #default="{ row }">
            <span class="text-secondary">{{ formatDate(row.joined_at) }}</span>
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="100" align="right">
          <template #default="{ row }">
            <el-tooltip content="移除成员" placement="top">
              <el-button 
                type="danger" 
                link 
                :icon="Delete" 
                :disabled="isCreator(row)"
                @click="confirmRemove(row)"
              />
            </el-tooltip>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- Add Member Dialog -->
    <el-dialog
      v-model="showAddDialog"
      title="添加成员"
      width="480px"
      align-center
      destroy-on-close
    >
      <el-form :model="addForm" label-position="top">
        <el-form-item label="选择用户">
          <el-select 
            v-model="addForm.userId" 
            placeholder="搜索并选择用户" 
            filterable 
            style="width: 100%"
          >
            <el-option
              v-for="user in availableUsers"
              :key="user.id"
              :label="user.full_name ? `${user.full_name} (${user.username})` : user.username"
              :value="user.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="分配角色">
          <el-radio-group v-model="addForm.role" class="role-selector">
            <el-radio-button label="tester">测试工程师</el-radio-button>
            <el-radio-button label="project_admin">管理员</el-radio-button>
            <el-radio-button label="viewer">访客</el-radio-button>
          </el-radio-group>
          <div class="role-desc">
            {{ roleDescription(addForm.role) }}
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showAddDialog = false">取消</el-button>
          <el-button type="primary" :loading="submitting" @click="handleAddMember">
            添加成员
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Delete, UserFilled, Tools, View, Management } from '@element-plus/icons-vue'
import { useProjectStore } from '@/stores/project'
import { projectApi } from '@/api/projects'
import { authApi } from '@/api/auth'
import type { ProjectMember, User } from '@/api/types'

const route = useRoute()
const projectStore = useProjectStore()
const projectId = Number(route.params.id)

// State
const loading = ref(false)
const submitting = ref(false)
const showAddDialog = ref(false)
const searchQuery = ref('')
const members = ref<ProjectMember[]>([])
const allUsers = ref<User[]>([])

const addForm = reactive({
  userId: undefined as number | undefined,
  role: 'tester'
})

// Computed
const filteredMembers = computed(() => {
  if (!searchQuery.value) return members.value
  const q = searchQuery.value.toLowerCase()
  return members.value.filter(m => 
    m.full_name?.toLowerCase().includes(q) || 
    m.username.toLowerCase().includes(q)
  )
})

const adminCount = computed(() => members.value.filter(m => m.role === 'project_admin').length)
const testerCount = computed(() => members.value.filter(m => m.role === 'tester').length)
const viewerCount = computed(() => members.value.filter(m => m.role === 'viewer').length)

const availableUsers = computed(() => {
  const currentMemberIds = new Set(members.value.map(m => m.user_id))
  return allUsers.value.filter(u => !currentMemberIds.has(u.id))
})

// Lifecycle
onMounted(async () => {
  await loadData()
})

// Methods
async function loadData() {
  loading.value = true
  try {
    const [membersData, usersData] = await Promise.all([
      projectApi.members(projectId),
      authApi.listUsers()
    ])
    members.value = membersData
    allUsers.value = usersData
  } catch (e) {
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

function openAddDialog() {
  addForm.userId = undefined
  addForm.role = 'tester'
  showAddDialog.value = true
}

async function handleAddMember() {
  if (!addForm.userId) {
    ElMessage.warning('请选择一个用户')
    return
  }
  
  submitting.value = true
  try {
    await projectApi.addMember(projectId, {
      user_id: addForm.userId,
      role: addForm.role
    })
    ElMessage.success('成员添加成功')
    showAddDialog.value = false
    loadData()
  } catch (e) {
    ElMessage.error('添加失败')
  } finally {
    submitting.value = false
  }
}

async function confirmRemove(member: ProjectMember) {
  try {
    await ElMessageBox.confirm(
      `确定要移除成员 "${member.full_name || member.username}" 吗？`,
      '移除成员',
      {
        type: 'warning',
        confirmButtonText: '移除',
        cancelButtonText: '取消',
        confirmButtonClass: 'el-button--danger'
      }
    )
    
    await projectApi.removeMember(projectId, member.id)
    ElMessage.success('成员已移除')
    loadData()
  } catch (e) {
    // Cancelled
  }
}

// Helpers
function isCreator(member: ProjectMember) {
  // Assuming current project creator cannot be removed (logic from original file)
  return member.user_id === projectStore.current?.created_by
}

function roleLabel(role: string) {
  const map: Record<string, string> = {
    project_admin: '管理员',
    tester: '测试工程师',
    viewer: '访客'
  }
  return map[role] || role
}

function roleType(role: string): any {
  const map: Record<string, string> = {
    project_admin: 'danger',
    tester: 'primary',
    viewer: 'info'
  }
  return map[role] || 'info'
}

function roleDescription(role: string) {
  const map: Record<string, string> = {
    project_admin: '拥有项目的所有权限，包括成员管理、项目设置等。',
    tester: '可以管理需求、生成和执行测试用例。',
    viewer: '仅拥有查看权限，无法修改任何数据。'
  }
  return map[role] || ''
}

function formatDate(iso: string) {
  if (!iso) return '-'
  return new Date(iso).toLocaleDateString()
}

function stringToColor(str: string) {
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash)
  }
  const c = (hash & 0x00ffffff).toString(16).toUpperCase()
  return '#' + '00000'.substring(0, 6 - c.length) + c
}
</script>

<style scoped>
.members-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.page-desc {
  height: 28px;
  display: flex;
  align-items: center;
  margin-bottom: 12px;
  flex-shrink: 0;
  padding: 0;
}
.subtitle { color: var(--text-secondary); font-size: 14px; margin: 0; }

/* Stats Overview */
.stats-overview {
  display: grid;
  grid-template-columns: repeat(4, 1fr) auto;
  gap: 24px;
  margin-bottom: 24px;
}
.action-card {
  display: flex;
  align-items: center;
  justify-content: center;
}
.add-member-btn {
  height: 100%;
  width: 100%;
  min-height: 80px;
  font-size: 16px;
}

.stat-card {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: var(--shadow-sm);
}
.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: #fff;
}
.bg-blue { background: linear-gradient(135deg, #60a5fa, #3b82f6); }
.bg-purple { background: linear-gradient(135deg, #a78bfa, #8b5cf6); }
.bg-green { background: linear-gradient(135deg, #34d399, #10b981); }
.bg-orange { background: linear-gradient(135deg, #fbbf24, #f59e0b); }

.stat-info {
  display: flex;
  flex-direction: column;
}
.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.2;
}
.stat-label {
  font-size: 13px;
  color: var(--text-secondary);
}

/* Content Card */
.content-card {
  flex: 1;
  min-height: 0;
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 24px;
  box-shadow: var(--shadow-sm);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.el-table {
  flex: 1;
  height: 100%;
}
.table-toolbar {
  margin-bottom: 20px;
  display: flex;
  justify-content: space-between;
}

.user-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}
.user-info {
  display: flex;
  flex-direction: column;
  line-height: 1.3;
}
.user-name {
  font-weight: 600;
  color: var(--text-primary);
}
.user-email {
  font-size: 12px;
  color: var(--text-secondary);
}
.text-secondary {
  color: var(--text-secondary);
}

.role-selector {
  width: 100%;
  margin-bottom: 12px;
}
.role-desc {
  font-size: 12px;
  color: var(--text-secondary);
  background: var(--bg-secondary);
  padding: 8px 12px;
  border-radius: 6px;
}

@media (max-width: 992px) {
  .stats-overview {
    grid-template-columns: repeat(2, 1fr);
  }
}
@media (max-width: 576px) {
  .stats-overview {
    grid-template-columns: 1fr;
  }
}
</style>
