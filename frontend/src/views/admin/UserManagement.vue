<template>
  <div class="user-management">
    <h2 class="page-title">👥 成员管理</h2>

    <el-card>
      <template #header>
        <div class="card-header">
          <span>成员列表</span>
          <el-radio-group v-model="groupType" size="small">
            <el-radio-button label="">全部</el-radio-button>
            <el-radio-button label="beginner">新手组</el-radio-button>
            <el-radio-button label="advanced">进阶组</el-radio-button>
          </el-radio-group>
        </div>
      </template>

      <el-table :data="paginatedUsers" stripe v-loading="loading">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="student_id" label="学号" width="120" />
        <el-table-column prop="username" label="姓名" width="100" />
        <el-table-column prop="academy" label="学院" min-width="120" />
        <el-table-column prop="grade" label="年级" width="100" />
        <el-table-column prop="group_type" label="组别" width="100">
          <template #default="{ row }">
            <el-tag :type="row.group_type === 'advanced' ? 'success' : 'primary'" size="small">
              {{ row.group_type === 'advanced' ? '进阶组' : '新手组' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="role" label="角色" width="80">
          <template #default="{ row }">
            <el-tag v-if="row.role === 'admin'" type="danger" size="small">管理员</el-tag>
            <el-tag v-else type="info" size="small">成员</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="注册时间" width="120">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button type="danger" link size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 50]"
          :total="total"
          layout="total, sizes, prev, pager, next"
        />
      </div>
    </el-card>

    <!-- 编辑对话框 -->
    <el-dialog v-model="editDialogVisible" title="编辑成员" width="500px">
      <el-form ref="editFormRef" :model="editForm" label-width="80px">
        <el-form-item label="姓名">
          <el-input v-model="editForm.username" />
        </el-form-item>
        <el-form-item label="学院">
          <el-input v-model="editForm.academy" />
        </el-form-item>
        <el-form-item label="年级">
          <el-input v-model="editForm.grade" />
        </el-form-item>
        <el-form-item label="组别">
          <el-select v-model="editForm.group_type" style="width: 100%;">
            <el-option label="新手组" value="beginner" />
            <el-option label="进阶组" value="advanced" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="warning" @click="handleResetPassword">
            重置密码为123456
          </el-button>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { adminApi } from '@/api'

const loading = ref(false)
const saving = ref(false)
const users = ref([])
const groupType = ref('')
const editDialogVisible = ref(false)
const editFormRef = ref(null)
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)

// 分页后的数据
const paginatedUsers = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return users.value.slice(start, end)
})

const editForm = reactive({
  id: null,
  username: '',
  academy: '',
  grade: '',
  group_type: 'beginner'
})

const loadUsers = async () => {
  loading.value = true
  try {
    const allUsers = await adminApi.getUsers({ group_type: groupType.value })
    users.value = allUsers
    total.value = allUsers.length
    currentPage.value = 1
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const handleEdit = (row) => {
  editForm.id = row.id
  editForm.username = row.username
  editForm.academy = row.academy || ''
  editForm.grade = row.grade || ''
  editForm.group_type = row.group_type
  editDialogVisible.value = true
}

const handleSave = async () => {
  saving.value = true
  try {
    await adminApi.updateUser(editForm.id, {
      username: editForm.username,
      academy: editForm.academy,
      grade: editForm.grade,
      group_type: editForm.group_type
    })
    ElMessage.success('保存成功')
    editDialogVisible.value = false
    loadUsers()
  } catch (e) {
    // 错误已处理
  } finally {
    saving.value = false
  }
}

const handleResetPassword = async () => {
  try {
    await ElMessageBox.confirm(`确定要重置 "${editForm.username}" 的密码为 123456 吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await adminApi.resetUserPassword(editForm.id)
    ElMessage.success('密码已重置为123456')
    editDialogVisible.value = false
    loadUsers()
  } catch (e) {
    if (e !== 'cancel') {
      console.error(e)
    }
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要删除成员 "${row.username}" 吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await adminApi.deleteUser(row.id)
    ElMessage.success('删除成功')
    loadUsers()
  } catch (e) {
    if (e !== 'cancel') {
      console.error(e)
    }
  }
}

const formatTime = (time) => {
  const date = new Date(time)
  return `${date.getMonth() + 1}-${date.getDate()}`
}

watch(groupType, () => {
  loadUsers()
})

onMounted(() => {
  loadUsers()
})
</script>

<style scoped>
.user-management {
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

.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
