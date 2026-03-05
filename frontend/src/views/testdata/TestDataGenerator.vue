<template>
  <div>
    <div class="page-header">
      <h2>测试数据生成</h2>
    </div>
    <el-row :gutter="16">
      <el-col :span="8">
        <el-card header="选择数据类型">
          <div class="type-grid">
            <div
              v-for="t in dataTypes" :key="t.code"
              class="type-item"
              :class="{ active: selectedType === t.code }"
              @click="selectedType = t.code"
            >
              <div class="type-label">{{ t.label }}</div>
              <div class="type-cat">{{ t.category }}</div>
            </div>
          </div>
          <el-divider />
          <el-form label-width="80px" size="small">
            <el-form-item label="生成数量">
              <el-input-number v-model="count" :min="1" :max="1000" />
            </el-form-item>
          </el-form>
          <el-button type="primary" style="width:100%" :loading="generating" @click="generateData">
            生成数据
          </el-button>
        </el-card>

        <el-card header="数据脱敏" style="margin-top: 16px">
          <el-form label-width="80px" size="small">
            <el-form-item label="原始数据"><el-input v-model="maskInput" /></el-form-item>
            <el-form-item label="数据类型">
              <el-select v-model="maskType">
                <el-option label="手机号" value="phone" />
                <el-option label="身份证" value="id_card" />
                <el-option label="银行卡" value="bank_card" />
                <el-option label="邮箱" value="email" />
                <el-option label="姓名" value="name" />
              </el-select>
            </el-form-item>
            <el-form-item label="脱敏结果">
              <el-input :value="maskResult" readonly />
            </el-form-item>
          </el-form>
          <el-button @click="maskData" style="width:100%">脱敏处理</el-button>
        </el-card>
      </el-col>

      <el-col :span="16">
        <el-card>
          <template #header>
            <div style="display:flex;justify-content:space-between;align-items:center">
              <span>生成结果 <el-tag v-if="generatedData.length">{{ generatedData.length }} 条</el-tag></span>
              <el-button v-if="generatedData.length" size="small" icon="CopyDocument" @click="copyAll">复制全部</el-button>
            </div>
          </template>
          <el-table :data="tableData" border stripe max-height="600">
            <el-table-column prop="index" label="#" width="60" />
            <el-table-column prop="value" label="数据值" />
          </el-table>
          <el-empty v-if="!generatedData.length" description="点击左侧生成按钮" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { testdataApi } from '@/api/modules'

const dataTypes = ref<any[]>([])
const selectedType = ref('name')
const count = ref(10)
const generating = ref(false)
const generatedData = ref<any[]>([])
const maskInput = ref('')
const maskType = ref('phone')
const maskResult = ref('')

const tableData = computed(() =>
  generatedData.value.map((v, i) => ({ index: i + 1, value: String(v) }))
)

const generateData = async () => {
  generating.value = true
  try {
    const res: any = await testdataApi.generate({ data_type: selectedType.value, count: count.value })
    generatedData.value = res.data
  } finally { generating.value = false }
}

const maskData = async () => {
  if (!maskInput.value) return
  const res: any = await testdataApi.mask({ value: maskInput.value, data_type: maskType.value })
  maskResult.value = res.masked
}

const copyAll = () => {
  const text = generatedData.value.join('\n')
  navigator.clipboard.writeText(text)
  ElMessage.success('已复制到剪贴板')
}

onMounted(async () => {
  const res: any = await testdataApi.getTypes()
  dataTypes.value = res.types
})
</script>

<style scoped>
.type-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-bottom: 12px; }
.type-item {
  padding: 10px 8px; border: 1px solid #e8e8e8; border-radius: 6px;
  cursor: pointer; text-align: center; transition: all 0.2s;
}
.type-item:hover { border-color: #1890ff; color: #1890ff; }
.type-item.active { background: #e6f7ff; border-color: #1890ff; color: #1890ff; }
.type-label { font-size: 13px; font-weight: 500; }
.type-cat { font-size: 11px; color: #909399; }
</style>
