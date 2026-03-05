<template>
  <el-container class="app-layout">
    <el-aside :width="isCollapsed ? '64px' : '220px'" class="app-aside">
      <app-sidebar :collapsed="isCollapsed" />
    </el-aside>
    <el-container>
      <el-header class="app-header">
        <app-header @toggle-sidebar="isCollapsed = !isCollapsed" :collapsed="isCollapsed" />
      </el-header>
      <el-main class="app-main">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import AppSidebar from './AppSidebar.vue'
import AppHeader from './AppHeader.vue'

const isCollapsed = ref(false)
</script>

<style scoped>
.app-layout { height: 100vh; overflow: hidden; }
.app-aside {
  background: #001529;
  transition: width 0.3s;
  overflow: hidden;
}
.app-header {
  height: 56px;
  padding: 0;
  background: #fff;
  border-bottom: 1px solid #e8e8e8;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
}
.app-main {
  background: #f0f2f5;
  overflow-y: auto;
  padding: 20px;
}
.fade-enter-active, .fade-leave-active { transition: opacity 0.15s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
