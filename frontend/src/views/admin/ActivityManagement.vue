<template>
  <div class="activity-management">
    <h2 class="page-title">🎯 活动管理</h2>

    <el-card>
      <template #header>
        <div class="card-header">
          <span>活动列表</span>
          <el-button type="primary" @click="showCreateDialog">
            <el-icon><Plus /></el-icon>
            发布活动
          </el-button>
        </div>
      </template>

      <el-table :data="activities" stripe v-loading="loading">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="title" label="活动名称" min-width="150" />
        <el-table-column prop="activity_time" label="活动日期" width="120">
          <template #default="{ row }">
            {{ formatDate(row.activity_time) }}
          </template>
        </el-table-column>
        <el-table-column prop="location" label="地点" width="120" />
        <el-table-column prop="sign_count" label="报名人数" width="100">
          <template #default="{ row }">
            {{ row.sign_count || 0 }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="发布时间" width="120">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="showSigns(row)">报名详情</el-button>
            <el-button type="success" link size="small" @click="exportSigns(row)">导出</el-button>
            <el-button type="danger" link size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建活动对话框 -->
    <el-dialog v-model="createDialogVisible" title="发布活动" width="500px">
      <el-form ref="createFormRef" :model="createForm" :rules="rules" label-width="100px">
        <el-form-item label="活动名称" prop="title">
          <el-input v-model="createForm.title" placeholder="请输入活动名称" />
        </el-form-item>
        <el-form-item label="活动日期" prop="activity_time">
          <el-date-picker
            v-model="createForm.activity_time"
            type="datetime"
            placeholder="选择日期和时间"
            style="width: 100%;"
            format="YYYY-MM-DD HH:mm"
            value-format="YYYY-MM-DD HH:mm:ss"
          />
        </el-form-item>
        <el-form-item label="活动地点" prop="location">
          <el-input v-model="createForm.location" placeholder="请输入活动地点" />
        </el-form-item>
        <el-form-item label="活动内容" prop="content">
          <el-input
            v-model="createForm.content"
            type="textarea"
            :rows="4"
            placeholder="请输入活动具体内容"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="handleCreate">发布</el-button>
      </template>
    </el-dialog>

    <!-- 报名详情对话框 -->
    <el-dialog v-model="signsDialogVisible" :title="`报名详情 - ${currentActivity?.title}`" width="600px">
      <el-table :data="signs" stripe v-loading="signsLoading">
        <el-table-column prop="username" label="姓名" width="120" />
        <el-table-column prop="student_id" label="学号" width="150" />
        <el-table-column prop="signed_at" label="报名时间">
          <template #default="{ row }">
            {{ formatDateTime(row.signed_at) }}
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="signs.length === 0 && !signsLoading" description="暂无报名" />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { activityApi } from '@/api'

const loading = ref(false)
const creating = ref(false)
const activities = ref([])
const createDialogVisible = ref(false)
const signsDialogVisible = ref(false)
const signsLoading = ref(false)
const signs = ref([])
const currentActivity = ref(null)
const createFormRef = ref(null)

const createForm = reactive({
  title: '',
  activity_time: '',
  location: '',
  content: ''
})

const rules = {
  title: [{ required: true, message: '请输入活动名称', trigger: 'blur' }],
  activity_time: [{ required: true, message: '请选择活动日期', trigger: 'change' }]
}

const formatDate = (time) => {
  if (!time) return '-'
  const date = new Date(time)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

const formatDateTime = (time) => {
  if (!time) return '-'
  const date = new Date(time)
  return `${formatDate(date)} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}:${String(date.getSeconds()).padStart(2, '0')}`
}

const loadActivities = async () => {
  loading.value = true
  try {
    activities.value = await activityApi.getList({ limit: 100 })
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const showCreateDialog = () => {
  createForm.title = ''
  createForm.activity_time = ''
  createForm.location = ''
  createForm.content = ''
  createDialogVisible.value = true
}

const handleCreate = async () => {
  const valid = await createFormRef.value.validate().catch(() => false)
  if (!valid) return

  creating.value = true
  try {
    await activityApi.create(createForm)
    ElMessage.success('发布成功')
    createDialogVisible.value = false
    loadActivities()
  } catch (e) {
    if (e.response?.data?.detail) {
      ElMessage.error(e.response.data.detail)
    }
  } finally {
    creating.value = false
  }
}

const showSigns = async (row) => {
  currentActivity.value = row
  signsDialogVisible.value = true
  signsLoading.value = true
  try {
    signs.value = await activityApi.getSigns(row.id)
  } catch (e) {
    console.error(e)
  } finally {
    signsLoading.value = false
  }
}

const exportSigns = async (row) => {
  try {
    const response = await activityApi.exportSigns(row.id)
    // 创建下载链接
    const blob = new Blob([response.data], { type: 'text/csv;charset=utf-8;' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `activity_${row.id}_signs_${new Date().getTime()}.csv`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (e) {
    ElMessage.error('导出失败')
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要删除活动 "${row.title}" 吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await activityApi.delete(row.id)
    ElMessage.success('删除成功')
    loadActivities()
  } catch (e) {
    if (e !== 'cancel') {
      console.error(e)
    }
  }
}

onMounted(() => {
  loadActivities()
})
</script>

<style scoped>
.activity-management {
  max-width: 1200px;
  margin: 0 auto;
}

.page-title {
  font-size: 24px;
  color: #333;
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
