<template>
  <div>
    <div class="page-header"><h2>质量报告中心</h2></div>
    <el-card>
      <template #header>AI自动生成测试报告</template>
      <el-form :model="form" label-width="120px" style="max-width:600px">
        <el-form-item label="项目名称"><el-input v-model="form.project_name" /></el-form-item>
        <el-form-item label="迭代名称"><el-input v-model="form.iteration_name" /></el-form-item>
        <el-form-item label="执行总数"><el-input-number v-model="form.total_executions" :min="0" /></el-form-item>
        <el-form-item label="通过数"><el-input-number v-model="form.passed" :min="0" /></el-form-item>
        <el-form-item label="缺陷总数"><el-input-number v-model="form.defect_total" :min="0" /></el-form-item>
        <el-form-item label="未关闭缺陷"><el-input-number v-model="form.defect_open" :min="0" /></el-form-item>
        <el-form-item>
          <el-button type="primary" icon="MagicStick" :loading="generating" @click="generateReport">AI生成报告</el-button>
        </el-form-item>
      </el-form>
    </el-card>
    <el-card v-if="report" style="margin-top:16px">
      <template #header>AI测试报告</template>
      <el-descriptions :column="1" border>
        <el-descriptions-item label="执行摘要">{{ report.summary }}</el-descriptions-item>
        <el-descriptions-item label="测试范围">{{ report.test_scope }}</el-descriptions-item>
        <el-descriptions-item label="执行结果">{{ report.execution_result }}</el-descriptions-item>
        <el-descriptions-item label="质量结论">
          <el-tag :type="report.quality_conclusion?.includes('通过')?'success':'danger'" size="large">{{ report.quality_conclusion }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="风险点">
          <ul><li v-for="r in report.risk_points" :key="r">{{ r }}</li></ul>
        </el-descriptions-item>
        <el-descriptions-item label="后续建议">
          <ul><li v-for="s in report.suggestions" :key="s">{{ s }}</li></ul>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>
<script setup lang="ts">
import { ref, reactive } from 'vue'
import { reportApi } from '@/api/modules'
import { useProjectStore } from '@/stores/project'
const projectStore = useProjectStore()
const generating = ref(false)
const report = ref<any>(null)
const form = reactive({ project_name:'', iteration_name:'Sprint 1', total_executions:0, passed:0, failed:0, defect_total:0, defect_open:0 })
const generateReport = async () => {
  form.project_name = projectStore.currentProject?.name || '当前项目'
  generating.value=true; try {
    const res:any = await reportApi.generateAiReport(form)
    report.value = res.report
  } finally { generating.value=false }
}
</script>
