<template>
  <div class="notices-page">
    <h2 class="page-title">📢 公告列表</h2>

    <el-card>
      <el-table :data="notices" stripe v-loading="loading">
        <el-table-column prop="title" label="标题" min-width="150" />
        <el-table-column prop="content" label="内容" min-width="300">
          <template #default="{ row }">
            <div class="notice-content">{{ row.content }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="发布时间" width="120">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50]"
          :total="total"
          layout="total, sizes, prev, pager, next"
          @current-change="loadNotices"
          @size-change="handleSizeChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { noticeApi } from '@/api'

const loading = ref(false)
const notices = ref([])
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)

const formatTime = (time) => {
  const date = new Date(time)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

const loadNotices = async () => {
  loading.value = true
  try {
    const skip = (currentPage.value - 1) * pageSize.value
    const response = await noticeApi.getList({ skip, limit: pageSize.value })
    if (Array.isArray(response)) {
      notices.value = response
      total.value = response.length
    } else if (response && response.data) {
      notices.value = response.data
      total.value = response.total || response.data.length
    } else {
      notices.value = []
      total.value = 0
    }
  } catch (e) {
    console.error(e)
    notices.value = []
  } finally {
    loading.value = false
  }
}

const handleSizeChange = () => {
  currentPage.value = 1
  loadNotices()
}

onMounted(() => {
  loadNotices()
})
</script>

<style scoped>
.notices-page {
  max-width: 1200px;
  margin: 0 auto;
}

.page-title {
  font-size: 24px;
  color: #333;
  margin-bottom: 24px;
}

.notice-content {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
