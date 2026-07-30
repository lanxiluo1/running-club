<template>
  <div class="leaderboard-page">
    <h2 class="page-title">🏆 排行榜</h2>

    <!-- Tab切换 -->
    <el-tabs v-model="activeTab" class="leaderboard-tabs">
      <el-tab-pane name="weekly">
        <template #label>
          <span class="tab-label">📅 周跑量榜</span>
        </template>
      </el-tab-pane>
      <el-tab-pane name="monthly">
        <template #label>
          <span class="tab-label">📆 月跑量榜</span>
        </template>
      </el-tab-pane>
      <el-tab-pane name="attendance">
        <template #label>
          <span class="tab-label">📝 打卡出勤榜</span>
        </template>
      </el-tab-pane>
    </el-tabs>

    <!-- 时间范围显示 -->
    <div class="time-range">
      <span v-if="activeTab === 'weekly'">本周：{{ weekRange }}</span>
      <span v-else-if="activeTab === 'monthly'">本月：{{ monthRange }}</span>
      <span v-else>本月：{{ monthRange }}</span>
    </div>

    <!-- 刷新按钮 -->
    <div class="filter-bar">
      <el-button type="primary" size="small" @click="loadLeaderboard" :loading="loading">
        <el-icon><Refresh /></el-icon>
        刷新
      </el-button>
      <el-radio-group v-model="groupType" size="default">
        <el-radio-button label="">全部成员</el-radio-button>
        <el-radio-button label="beginner">新手组</el-radio-button>
        <el-radio-button label="advanced">进阶组</el-radio-button>
      </el-radio-group>
    </div>

    <!-- 排行榜 -->
    <div class="leaderboard-list">
      <div v-if="loading" class="loading-container">
        <el-icon class="is-loading"><Loading /></el-icon>
        加载中...
      </div>

      <template v-else>
        <!-- 前三名领奖台 -->
        <div v-if="topThree.length > 0" class="podium">
          <!-- 第二名 -->
          <div v-if="topThree[1]" class="podium-item rank-2">
            <div class="podium-avatar">
              <el-avatar :size="56" :icon="UserFilled" />
            </div>
            <div class="podium-rank">🥈</div>
            <div class="podium-name">{{ topThree[1].username }}</div>
            <div class="podium-value">{{ topThree[1].total_distance || topThree[1].total_runs }} {{ activeTab === 'attendance' ? '次' : 'km' }}</div>
          </div>

          <!-- 第一名 -->
          <div v-if="topThree[0]" class="podium-item rank-1">
            <div class="podium-avatar">
              <el-avatar :size="72" :icon="UserFilled" />
            </div>
            <div class="podium-rank">🥇</div>
            <div class="podium-name">{{ topThree[0].username }}</div>
            <div class="podium-value">{{ topThree[0].total_distance || topThree[0].total_runs }} {{ activeTab === 'attendance' ? '次' : 'km' }}</div>
          </div>

          <!-- 第三名 -->
          <div v-if="topThree[2]" class="podium-item rank-3">
            <div class="podium-avatar">
              <el-avatar :size="48" :icon="UserFilled" />
            </div>
            <div class="podium-rank">🥉</div>
            <div class="podium-name">{{ topThree[2].username }}</div>
            <div class="podium-value">{{ topThree[2].total_distance || topThree[2].total_runs }} {{ activeTab === 'attendance' ? '次' : 'km' }}</div>
          </div>
        </div>

        <!-- 其他人列表 -->
        <el-card class="rest-list" v-if="restList.length > 0">
          <div class="rest-item" v-for="item in restList" :key="item.user_id">
            <span class="rest-rank">{{ item.rank }}</span>
            <span class="rest-name">{{ item.username }}</span>
            <span class="rest-value">{{ item.total_distance || item.total_runs }} {{ activeTab === 'attendance' ? '次' : 'km' }}</span>
          </div>
        </el-card>

        <el-empty v-if="leaderboard.length === 0" description="暂无数据" />
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { UserFilled, Loading, Refresh } from '@element-plus/icons-vue'
import { leaderboardApi } from '@/api'

const activeTab = ref('weekly')
const groupType = ref('')
const loading = ref(false)
const leaderboard = ref([])

// 计算本周日期范围
const weekRange = computed(() => {
  const now = new Date()
  const dayOfWeek = now.getDay()
  const monday = new Date(now)
  monday.setDate(now.getDate() - (dayOfWeek === 0 ? 6 : dayOfWeek - 1))
  const sunday = new Date(monday)
  sunday.setDate(monday.getDate() + 6)
  return `${monday.getFullYear()}.${monday.getMonth() + 1}.${monday.getDate()} - ${sunday.getMonth() + 1}.${sunday.getDate()}`
})

// 计算本月日期范围
const monthRange = computed(() => {
  const now = new Date()
  return `${now.getFullYear()}年${now.getMonth() + 1}月`
})

const loadLeaderboard = async () => {
  loading.value = true
  try {
    let data = []
    if (activeTab.value === 'weekly') {
      data = await leaderboardApi.getWeekly({ group_type: groupType.value })
    } else if (activeTab.value === 'monthly') {
      data = await leaderboardApi.getMonthly({ group_type: groupType.value })
    } else {
      data = await leaderboardApi.getAttendance({ group_type: groupType.value })
    }
    leaderboard.value = data || []
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const topThree = computed(() => leaderboard.value.slice(0, 3))
const restList = computed(() => leaderboard.value.slice(3))

watch([activeTab, groupType], () => {
  loadLeaderboard()
})

onMounted(() => {
  loadLeaderboard()
})
</script>

<style scoped>
.leaderboard-page {
  max-width: 800px;
  margin: 0 auto;
}

.page-title {
  font-size: 24px;
  color: #333;
  margin-bottom: 24px;
}

.leaderboard-tabs {
  background: white;
  border-radius: 12px 12px 0 0;
  padding: 0 16px;
}

.tab-label {
  font-size: 15px;
}

.time-range {
  background: white;
  padding: 12px 16px;
  text-align: center;
  color: #409EFF;
  font-weight: 500;
}

.filter-bar {
  background: white;
  padding: 16px;
  border-radius: 0 0 12px 12px;
  margin-bottom: 20px;
  display: flex;
  gap: 12px;
}

.leaderboard-list {
  background: white;
  border-radius: 12px;
  padding: 24px;
}

.loading-container {
  text-align: center;
  padding: 60px;
  color: #999;
}

/* 领奖台样式 */
.podium {
  display: flex;
  justify-content: center;
  align-items: flex-end;
  gap: 16px;
  margin-bottom: 24px;
  padding: 0 20px;
}

.podium-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px 12px;
  border-radius: 12px;
  min-width: 120px;
}

.podium-item.rank-1 {
  background: linear-gradient(180deg, #fff9e6 0%, #ffe4b3 100%);
  order: 2;
}

.podium-item.rank-2 {
  background: linear-gradient(180deg, #f5f5f5 0%, #e0e0e0 100%);
  order: 1;
}

.podium-item.rank-3 {
  background: linear-gradient(180deg, #fff0e6 0%, #ffd9b3 100%);
  order: 3;
}

.podium-avatar {
  margin-bottom: 8px;
}

.podium-rank {
  font-size: 28px;
  margin-bottom: 4px;
}

.podium-name {
  font-size: 16px;
  font-weight: bold;
  color: #333;
  margin-bottom: 4px;
}

.podium-value {
  font-size: 20px;
  font-weight: bold;
  color: #409EFF;
}

.rank-1 .podium-value {
  font-size: 24px;
}

/* 其他人列表 */
.rest-list {
  border-radius: 12px;
}

.rest-item {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #f0f0f0;
}

.rest-item:last-child {
  border-bottom: none;
}

.rest-rank {
  width: 40px;
  font-weight: bold;
  color: #666;
  font-size: 14px;
}

.rest-name {
  flex: 1;
  color: #333;
}

.rest-value {
  font-weight: bold;
  color: #409EFF;
}
</style>
