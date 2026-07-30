<template>
  <div class="activities-page">
    <h2 class="page-title">🎉 活动报名</h2>

    <el-row :gutter="20">
      <el-col v-if="loading" :span="24">
        <div class="loading-container">
          <el-icon class="is-loading"><Loading /></el-icon>
          加载中...
        </div>
      </el-col>

      <template v-else>
        <el-col v-if="activities.length === 0" :span="24">
          <el-empty description="暂无活动" />
        </el-col>

        <el-col v-for="activity in activities" :key="activity.id" :xs="24" :sm="12" :lg="8">
          <el-card class="activity-card" shadow="hover">
            <template #header>
              <div class="activity-header">
                <h3>{{ activity.title }}</h3>
                <el-tag :type="getTimeTagType(activity.activity_time)" size="small">
                  {{ formatActivityTime(activity.activity_time) }}
                </el-tag>
              </div>
            </template>

            <div class="activity-content">
              <div class="activity-info">
                <p><el-icon><Location /></el-icon> {{ activity.location || '待定' }}</p>
                <p><el-icon><User /></el-icon> 组织者：{{ activity.creator?.username || '管理员' }}</p>
                <p><el-icon><UserFilled /></el-icon> 已报名：{{ activity.sign_count || 0 }} 人</p>
              </div>

              <div v-if="activity.content" class="activity-desc">
                {{ activity.content }}
              </div>
            </div>

            <div class="activity-footer">
              <el-button
                v-if="isSigned(activity.id)"
                type="danger"
                plain
                @click="handleCancelSign(activity.id)"
              >
                取消报名
              </el-button>
              <el-button
                v-else
                type="primary"
                @click="handleSignUp(activity.id)"
              >
                立即报名
              </el-button>
            </div>
          </el-card>
        </el-col>
      </template>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Loading, Location, User, UserFilled } from '@element-plus/icons-vue'
import { activityApi } from '@/api'

const loading = ref(false)
const activities = ref([])
const signedActivities = ref(new Set())

const loadActivities = async () => {
  loading.value = true
  try {
    activities.value = await activityApi.getList()
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const isSigned = (activityId) => signedActivities.value.has(activityId)

const handleSignUp = async (activityId) => {
  try {
    await activityApi.signUp(activityId)
    ElMessage.success('报名成功')
    signedActivities.value.add(activityId)
    loadActivities()
  } catch (e) {
    // 错误已处理
  }
}

const handleCancelSign = async (activityId) => {
  try {
    await ElMessageBox.confirm('确定要取消报名吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await activityApi.cancelSign(activityId)
    ElMessage.success('已取消报名')
    signedActivities.value.delete(activityId)
    loadActivities()
  } catch (e) {
    if (e !== 'cancel') {
      console.error(e)
    }
  }
}

const formatActivityTime = (time) => {
  const date = new Date(time)
  const now = new Date()
  const diff = date - now

  if (diff < 0) return '已结束'
  if (diff < 24 * 60 * 60 * 1000) return '今日'
  if (diff < 2 * 24 * 60 * 60 * 1000) return '明日'
  return `${date.getMonth() + 1}月${date.getDate()}日`
}

const getTimeTagType = (time) => {
  const date = new Date(time)
  const now = new Date()
  const diff = date - now

  if (diff < 0) return 'info'
  if (diff < 24 * 60 * 60 * 1000) return 'danger'
  if (diff < 3 * 24 * 60 * 60 * 1000) return 'warning'
  return 'success'
}

onMounted(() => {
  loadActivities()
})
</script>

<style scoped>
.activities-page {
  max-width: 1200px;
  margin: 0 auto;
}

.page-title {
  font-size: 24px;
  color: #333;
  margin-bottom: 24px;
}

.loading-container {
  text-align: center;
  padding: 60px;
  color: #999;
}

.activity-card {
  border-radius: 12px;
  margin-bottom: 20px;
  transition: transform 0.3s, box-shadow 0.3s;
}

.activity-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
}

.activity-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.activity-header h3 {
  margin: 0;
  font-size: 16px;
  color: #333;
}

.activity-content {
  margin-bottom: 16px;
}

.activity-info p {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 8px 0;
  color: #666;
  font-size: 14px;
}

.activity-desc {
  margin-top: 12px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 8px;
  font-size: 13px;
  color: #666;
  line-height: 1.6;
}

.activity-footer {
  text-align: right;
}
</style>
