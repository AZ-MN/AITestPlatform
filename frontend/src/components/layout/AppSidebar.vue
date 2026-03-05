<template>
  <div class="sidebar">
    <div class="logo" :class="{ collapsed }">
      <el-icon size="24" color="#1890ff"><cpu /></el-icon>
      <span v-if="!collapsed" class="logo-text">AI测试平台</span>
    </div>
    <el-menu
      :default-active="route.path"
      :collapse="collapsed"
      router
      background-color="#001529"
      text-color="#ffffffa6"
      active-text-color="#1890ff"
      :collapse-transition="false"
    >
      <el-menu-item index="/dashboard">
        <el-icon><DataBoard /></el-icon><template #title>质量看板</template>
      </el-menu-item>

      <el-sub-menu index="admin">
        <template #title><el-icon><Setting /></el-icon><span>平台管理</span></template>
        <el-menu-item index="/admin/projects"><el-icon><FolderOpened /></el-icon>项目管理</el-menu-item>
        <el-menu-item index="/admin/iterations"><el-icon><Calendar /></el-icon>迭代管理</el-menu-item>
        <el-menu-item index="/admin/users"><el-icon><User /></el-icon>用户管理</el-menu-item>
        <el-menu-item index="/admin/roles"><el-icon><Lock /></el-icon>角色权限</el-menu-item>
        <el-menu-item index="/admin/llm"><el-icon><MagicStick /></el-icon>AI模型配置</el-menu-item>
      </el-sub-menu>

      <el-sub-menu index="requirements">
        <template #title><el-icon><Document /></el-icon><span>需求&用例</span></template>
        <el-menu-item index="/requirements"><el-icon><Files /></el-icon>需求管理</el-menu-item>
        <el-menu-item index="/testcases"><el-icon><List /></el-icon>用例库</el-menu-item>
      </el-sub-menu>

      <el-sub-menu index="apitest">
        <template #title><el-icon><Connection /></el-icon><span>接口测试</span></template>
        <el-menu-item index="/apitest/apis"><el-icon><Share /></el-icon>接口管理</el-menu-item>
        <el-menu-item index="/apitest/debug"><el-icon><Promotion /></el-icon>接口调试</el-menu-item>
        <el-menu-item index="/apitest/cases"><el-icon><Tickets /></el-icon>接口用例</el-menu-item>
      </el-sub-menu>

      <el-sub-menu index="automation">
        <template #title><el-icon><VideoPlay /></el-icon><span>自动化测试</span></template>
        <el-menu-item index="/automation/scripts"><el-icon><Edit /></el-icon>脚本管理</el-menu-item>
        <el-menu-item index="/automation/tasks"><el-icon><Timer /></el-icon>任务调度</el-menu-item>
      </el-sub-menu>

      <el-menu-item index="/defects">
        <el-icon><Warning /></el-icon><template #title>缺陷管理</template>
      </el-menu-item>

      <el-menu-item index="/testdata">
        <el-icon><Grid /></el-icon><template #title>测试数据</template>
      </el-menu-item>

      <el-menu-item index="/reports">
        <el-icon><TrendCharts /></el-icon><template #title>质量报告</template>
      </el-menu-item>
    </el-menu>
  </div>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'
defineProps<{ collapsed: boolean }>()
const route = useRoute()
</script>

<style scoped>
.sidebar { height: 100%; display: flex; flex-direction: column; }
.logo {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  border-bottom: 1px solid #ffffff1a;
  padding: 0 16px;
  overflow: hidden;
  white-space: nowrap;
}
.logo.collapsed { padding: 0; }
.logo-text { color: #fff; font-size: 16px; font-weight: 700; letter-spacing: 1px; }
.el-menu { border-right: none; flex: 1; overflow-y: auto; }
</style>
