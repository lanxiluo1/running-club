<template>
  <div class="review-management">
    <h2 class="page-title">✅ 数据审核</h2>

    <el-card>
      <template #header>
        <div class="card-header">
          <span>打卡记录</span>
          <el-button type="primary" size="small" @click="loadRecords">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </template>

      <!-- 状态筛选 -->
      <el-tabs v-model="activeStatus" class="status-tabs">
        <el-tab-pane name="pending">
          <template #label>
            <span>待审核 <el-badge :value="actualPendingCount" :hidden="actualPendingCount === 0" /></span>
          </template>
        </el-tab-pane>
        <el-tab-pane label="已通过" name="approved" />
        <el-tab-pane label="已驳回" name="rejected" />
      </el-tabs>

      <!-- 待审核操作按钮 -->
      <div v-if="activeStatus === 'pending'" class="batch-actions">
        <el-button type="success" @click="handleBatchApprove" :disabled="records.length === 0">
          <el-icon><Check /></el-icon>
          一键通过
        </el-button>
        <el-button type="danger" @click="handleBatchReject" :disabled="records.length === 0">
          <el-icon><Close /></el-icon>
          一键驳回
        </el-button>
      </div>

      <!-- 已通过操作按钮 -->
      <div v-if="activeStatus === 'approved'" class="batch-actions">
        <el-button type="warning" @click="handleBatchRevertApproved" :disabled="records.length === 0">
          <el-icon><RefreshLeft /></el-icon>
          一键退回
        </el-button>
      </div>

      <!-- 已驳回操作按钮 -->
      <div v-if="activeStatus === 'rejected'" class="batch-actions">
        <el-button type="warning" @click="handleBatchRevert" :disabled="records.length === 0">
          <el-icon><RefreshLeft /></el-icon>
          批量退回
        </el-button>
        <el-button type="danger" @click="handleBatchDelete" :disabled="records.length === 0">
          <el-icon><Delete /></el-icon>
          一键删除
        </el-button>
      </div>

      <el-table :data="paginatedRecords" stripe v-loading="loading">
        <el-table-column label="用户" width="120">
          <template #default="{ row }">
            <div class="user-cell">
              <el-avatar :size="32" :icon="UserFilled" />
              <span>{{ row.username }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="run_date" label="日期" width="100" />
        <el-table-column prop="distance" label="距离(km)" width="100">
          <template #default="{ row }">
            <span class="distance-text">{{ row.distance }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="duration" label="时长" width="100">
          <template #default="{ row }">
            {{ formatDuration(row.duration) }}
          </template>
        </el-table-column>
        <el-table-column prop="pace" label="速度(km/h)" width="100">
          <template #default="{ row }">
            {{ row.pace ? row.pace.toFixed(2) : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="heart_rate" label="心率" width="80">
          <template #default="{ row }">
            {{ row.heart_rate || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="check_in_method" label="方式" width="80">
          <template #default="{ row }">
            <el-tag :type="row.check_in_method === 'auto' ? 'success' : 'info'" size="small">
              {{ row.check_in_method === 'auto' ? '识别' : '手动' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="提交时间" min-width="120" />
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <template v-if="row.status === 'pending'">
              <el-button type="success" size="small" @click="handleApprove(row)">通过</el-button>
              <el-button type="danger" size="small" @click="handleReject(row)">驳回</el-button>
            </template>
            <template v-else-if="row.status === 'approved'">
              <el-button type="warning" size="small" @click="handleRevert(row)">退回</el-button>
            </template>
            <template v-else>
              <el-button type="warning" size="small" @click="handleRevert(row)">退回</el-button>
              <el-button type="danger" size="small" @click="handleDelete(row)">删除</el-button>
            </template>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页器 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 50]"
          :total="filteredRecords.length"
          layout="total, sizes, prev, pager, next"
          @current-change="handlePageChange"
          @size-change="handleSizeChange"
        />
      </div>

      <el-empty v-if="records.length === 0 && !loading" description="暂无记录" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, UserFilled, Check, Close, Delete, RefreshLeft } from '@element-plus/icons-vue'
import { adminApi } from '@/api'

const loading = ref(false)
const records = ref([])
const activeStatus = ref('pending')
const actualPendingCount = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)

// 根据状态过滤的记录
const filteredRecords = computed(() => {
  return records.value.filter(r => r.status === activeStatus.value)
})

// 分页后的记录
const paginatedRecords = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredRecords.value.slice(start, end)
})

const loadRecords = async () => {
  loading.value = true
  try {
    const allRecords = await adminApi.getAllRecords()
    // 计算实际待审核数量（不受当前tab影响）
    actualPendingCount.value = allRecords.filter(r => r.status === 'pending').length
    records.value = allRecords
    currentPage.value = 1  // 切换tab时重置页码
  } catch (e) {
    console.error('加载失败:', e)
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

const handleApprove = async (row) => {
  try {
    await adminApi.reviewRecord(row.id, 'approved')
    ElMessage.success('已通过')
    loadRecords()
  } catch (e) {
    console.error('操作失败:', e)
    ElMessage.error('操作失败')
  }
}

const handleReject = async (row) => {
  try {
    await ElMessageBox.confirm('确定要驳回这条打卡记录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await adminApi.reviewRecord(row.id, 'rejected')
    ElMessage.success('已驳回')
    loadRecords()
  } catch (e) {
    if (e !== 'cancel') {
      console.error('操作失败:', e)
      ElMessage.error('操作失败')
    }
  }
}

const handleRevert = async (row) => {
  try {
    await ElMessageBox.confirm('确定要退回这条打卡记录到待审核吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await adminApi.reviewRecord(row.id, 'pending')
    ElMessage.success('已退回')
    loadRecords()
  } catch (e) {
    if (e !== 'cancel') {
      console.error('操作失败:', e)
      ElMessage.error('操作失败')
    }
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除这条打卡记录吗？此操作不可恢复！', '警告', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await adminApi.deleteRecord(row.id)
    ElMessage.success('已删除')
    loadRecords()
  } catch (e) {
    if (e !== 'cancel') {
      console.error('删除失败:', e)
      ElMessage.error('删除失败')
    }
  }
}

const handleBatchApprove = async () => {
  if (filteredRecords.value.length === 0) return
  try {
    await ElMessageBox.confirm(`确定要通过所有 ${filteredRecords.value.length} 条待审核记录吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    let success = 0
    for (const row of filteredRecords.value) {
      try {
        await adminApi.reviewRecord(row.id, 'approved')
        success++
      } catch (e) {
        console.error(e)
      }
    }
    ElMessage.success(`已通过 ${success} 条记录`)
    loadRecords()
  } catch (e) {
    if (e !== 'cancel') {
      console.error('批量操作失败:', e)
    }
  }
}

const handleBatchReject = async () => {
  if (filteredRecords.value.length === 0) return
  try {
    await ElMessageBox.confirm(`确定要驳回所有 ${filteredRecords.value.length} 条待审核记录吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    let success = 0
    for (const row of filteredRecords.value) {
      try {
        await adminApi.reviewRecord(row.id, 'rejected')
        success++
      } catch (e) {
        console.error(e)
      }
    }
    ElMessage.success(`已驳回 ${success} 条记录`)
    loadRecords()
  } catch (e) {
    if (e !== 'cancel') {
      console.error('批量操作失败:', e)
    }
  }
}

const handleBatchDelete = async () => {
  if (filteredRecords.value.length === 0) return
  try {
    await ElMessageBox.confirm(`确定要删除所有 ${filteredRecords.value.length} 条已${activeStatus.value === 'approved' ? '通过' : '驳回'}记录吗？此操作不可恢复！`, '警告', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning'
    })
    let success = 0
    for (const row of filteredRecords.value) {
      try {
        await adminApi.deleteRecord(row.id)
        success++
      } catch (e) {
        console.error(e)
      }
    }
    ElMessage.success(`已删除 ${success} 条记录`)
    loadRecords()
  } catch (e) {
    if (e !== 'cancel') {
      console.error('批量操作失败:', e)
    }
  }
}

const handleBatchRevert = async () => {
  if (filteredRecords.value.length === 0) return
  try {
    await ElMessageBox.confirm(`确定要退回所有 ${filteredRecords.value.length} 条已驳回记录到待审核吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    let success = 0
    for (const row of filteredRecords.value) {
      try {
        await adminApi.reviewRecord(row.id, 'pending')
        success++
      } catch (e) {
        console.error(e)
      }
    }
    ElMessage.success(`已退回 ${success} 条记录`)
    loadRecords()
  } catch (e) {
    if (e !== 'cancel') {
      console.error('批量操作失败:', e)
    }
  }
}

const handleBatchRevertApproved = async () => {
  if (filteredRecords.value.length === 0) return
  try {
    await ElMessageBox.confirm(`确定要退回所有 ${filteredRecords.value.length} 条已通过记录到待审核吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    let success = 0
    for (const row of filteredRecords.value) {
      try {
        await adminApi.reviewRecord(row.id, 'pending')
        success++
      } catch (e) {
        console.error(e)
      }
    }
    ElMessage.success(`已退回 ${success} 条记录`)
    loadRecords()
  } catch (e) {
    if (e !== 'cancel') {
      console.error('批量操作失败:', e)
    }
  }
}

const formatDuration = (seconds) => {
  if (!seconds) return '-'
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  return `${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

watch(activeStatus, () => {
  currentPage.value = 1
})

const handlePageChange = (page) => {
  currentPage.value = page
}

const handleSizeChange = (size) => {
  pageSize.value = size
  currentPage.value = 1
}

onMounted(() => {
  loadRecords()
})
</script>

<style scoped>
.review-management {
  max-width: 1400px;
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

.status-tabs {
  margin-bottom: 16px;
}

.batch-actions {
  margin-bottom: 16px;
  display: flex;
  gap: 12px;
}

.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.user-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.distance-text {
  font-weight: bold;
  color: #409EFF;
}
</style>
