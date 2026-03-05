<template>
  <div>
    <div class="page-header">
      <h2>质量看板</h2>
      <el-select v-model="selectedProjectId" placeholder="选择项目" style="width: 200px" @change="fetchData">
        <el-option v-for="p in projectStore.projects" :key="p.id" :label="p.name" :value="p.id" />
      </el-select>
    </div>

    <!-- 统计卡片 -->
    <div class="card-stats">
      <div class="stat-card">
        <div class="label">用例总数</div>
        <div class="value primary">{{ stats.cases.total }}</div>
      </div>
      <div class="stat-card">
        <div class="label">缺陷总数</div>
        <div class="value danger">{{ stats.defects.total }}</div>
      </div>
      <div class="stat-card">
        <div class="label">未解决缺陷</div>
        <div class="value warning">{{ stats.defects.open }}</div>
      </div>
      <div class="stat-card">
        <div class="label">自动化通过率</div>
        <div class="value success">{{ stats.executions.pass_rate }}%</div>
      </div>
    </div>

    <el-row :gutter="16">
      <!-- 用例优先级分布 -->
      <el-col :span="12">
        <el-card header="用例优先级分布">
          <v-chart :option="caseChartOption" style="height: 280px" autoresize />
        </el-card>
      </el-col>
      <!-- 缺陷严重程度分布 -->
      <el-col :span="12">
        <el-card header="缺陷严重程度分布">
          <v-chart :option="defectChartOption" style="height: 280px" autoresize />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { PieChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { reportApi } from '@/api/modules'
import { useProjectStore } from '@/stores/project'

use([PieChart, TitleComponent, TooltipComponent, LegendComponent, CanvasRenderer])

const projectStore = useProjectStore()
const selectedProjectId = ref<number | null>(null)
const stats = ref({
  cases: { total: 0, by_priority: { P0: 0, P1: 0, P2: 0, P3: 0 } },
  defects: { total: 0, open: 0, by_severity: {} as Record<string, number> },
  executions: { total: 0, passed: 0, pass_rate: 0 },
})

const fetchData = async () => {
  if (!selectedProjectId.value) return
  const res: any = await reportApi.getDashboard(selectedProjectId.value)
  stats.value = res
}

const caseChartOption = computed(() => ({
  tooltip: { trigger: 'item' },
  legend: { bottom: 0 },
  series: [{
    type: 'pie', radius: ['40%', '70%'],
    data: Object.entries(stats.value.cases.by_priority).map(([name, value]) => ({ name, value })),
    label: { formatter: '{b}: {c}' },
  }],
}))

const defectChartOption = computed(() => ({
  tooltip: { trigger: 'item' },
  legend: { bottom: 0 },
  color: ['#f5222d', '#fa8c16', '#fadb14', '#52c41a', '#1890ff'],
  series: [{
    type: 'pie', radius: ['40%', '70%'],
    data: Object.entries(stats.value.defects.by_severity).map(([name, value]) => ({
      name: { blocker: '致命', critical: '严重', normal: '一般', minor: '轻微', trivial: '建议' }[name] || name,
      value
    })),
  }],
}))

onMounted(async () => {
  await projectStore.fetchProjects()
  if (projectStore.currentProject) {
    selectedProjectId.value = projectStore.currentProject.id
    await fetchData()
  }
})
</script>
