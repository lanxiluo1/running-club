<template>
  <div class="data-export">
    <h2 class="page-title">📊 数据导出</h2>

    <el-card>
      <template #header>
        <span>导出设置</span>
      </template>

      <el-form :model="form" label-width="100px">
        <el-form-item label="日期范围">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleExport" :loading="loading">
            <el-icon><Download /></el-icon>
            导出CSV文件
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card style="margin-top: 20px;">
      <template #header>
        <span>导出说明</span>
      </template>
      <div class="export-tips">
        <p>• 导出的CSV文件可使用Excel打开</p>
        <p>• 包含字段：姓名、学号、日期（横向）、每个日期的总跑量、累计跑量</p>
        <p>• 默认导出所有记录，可通过日期范围筛选</p>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { Download } from '@element-plus/icons-vue'
import request from '@/utils/request'

const dateRange = ref([])
const form = reactive({})
const loading = ref(false)

const handleExport = async () => {
  loading.value = true
  try {
    const params = {}
    if (dateRange.value && dateRange.value.length === 2) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }

    // 构建URL和参数 (通过代理 /api/admin -> localhost:8000/api/admin)
    const url = new URL('/api/admin/export/run-records', window.location.origin)
    if (params.start_date) url.searchParams.set('start_date', params.start_date)
    if (params.end_date) url.searchParams.set('end_date', params.end_date)

    const token = localStorage.getItem('token')
    const response = await fetch(url.toString(), {
      headers: { Authorization: `Bearer ${token}` }
    })

    if (!response.ok) {
      throw new Error('导出失败')
    }

    const blob = await response.blob()
    const downloadUrl = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = `run_records_${new Date().toISOString().slice(0, 10)}.csv`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(downloadUrl)

    ElMessage.success('导出成功')
  } catch (e) {
    ElMessage.error('导出失败，请重试')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.data-export {
  max-width: 800px;
  margin: 0 auto;
}

.page-title {
  font-size: 24px;
  color: #333;
  margin-bottom: 24px;
}

.export-tips {
  color: #666;
  font-size: 14px;
  line-height: 2;
}

.export-tips p {
  margin: 0;
}
</style>
