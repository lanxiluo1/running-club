<template>
  <div class="dashboard">
    <h2 class="page-title">欢迎回来，{{ userStore.userInfo?.username }}！</h2>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-icon" style="background: #409EFF;">
            <el-icon :size="28"><TrendCharts /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.total_distance || 0 }}</div>
            <div class="stat-label">累计跑量(km)</div>
          </div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-icon" style="background: #67C23A;">
            <el-icon :size="28"><CircleCheck /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.total_runs || 0 }}</div>
            <div class="stat-label">打卡次数</div>
          </div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-icon" style="background: #E6A23C;">
            <el-icon :size="28"><Timer /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.avg_pace || '--' }}</div>
            <div class="stat-label">平均速度(km/h)</div>
          </div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-icon" style="background: #F56C6C;">
            <el-icon :size="28"><WarnTriangleFilled /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.avg_heart_rate || '--' }}</div>
            <div class="stat-label">平均心率(bpm)</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 快捷操作 & 最新公告 -->
    <el-row :gutter="20">
      <el-col :xs="24" :sm="16">
        <el-card class="quick-actions-card">
          <template #header>
            <span>快捷操作</span>
          </template>
          <div class="quick-actions">
            <el-button type="primary" size="large" @click="$router.push('/checkin')">
              <el-icon><CircleCheck /></el-icon>
              立即打卡
            </el-button>
            <el-button size="large" @click="$router.push('/stats')">
              <el-icon><DataAnalysis /></el-icon>
              查看数据
            </el-button>
            <el-button size="large" @click="$router.push('/leaderboard')">
              <el-icon><TrendCharts /></el-icon>
              查看排行
            </el-button>
            <el-button size="large" @click="$router.push('/activities')">
              <el-icon><Calendar /></el-icon>
              活动报名
            </el-button>
          </div>
        </el-card>

        <!-- 周跑量趋势 -->
        <el-card class="chart-card">
          <template #header>
            <span>本周跑量趋势</span>
          </template>
          <div ref="weeklyChartRef" style="height: 250px;"></div>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="8">
        <el-card class="notices-card">
          <template #header>
            <div class="card-header">
              <span>最新公告</span>
              <el-button text size="small" @click="$router.push('/notices')">更多</el-button>
            </div>
          </template>
          <div v-if="notices.length === 0" class="empty-notice">
            暂无公告
          </div>
          <div v-else class="notice-list">
            <div v-for="notice in notices" :key="notice.id" class="notice-item">
              <h4>{{ notice.title }}</h4>
              <p>{{ notice.content }}</p>
              <span class="notice-time">{{ formatTime(notice.created_at) }}</span>
            </div>
          </div>
        </el-card>

      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { runRecordApi, noticeApi } from '@/api'
import { TrendCharts, CircleCheck, Timer, WarnTriangleFilled, DataAnalysis, Calendar } from '@element-plus/icons-vue'
import * as echarts from 'echarts'

const router = useRouter()
const userStore = useUserStore()

const stats = ref({})
const notices = ref([])
const weeklyChartRef = ref(null)

const formatTime = (time) => {
  const date = new Date(time)
  return `${date.getMonth() + 1}-${date.getDate()}`
}

const loadStats = async () => {
  try {
    stats.value = await runRecordApi.getStats()
    renderWeeklyChart()
  } catch (e) {
    console.error(e)
  }
}

const loadNotices = async () => {
  try {
    notices.value = (await noticeApi.getList({ limit: 1 })) || []
  } catch (e) {
    console.error(e)
  }
}

const renderWeeklyChart = () => {
  if (!weeklyChartRef.value || !stats.value.weekly_data) return

  const chart = echarts.init(weeklyChartRef.value)
  const dates = stats.value.weekly_data.map(d => d.date.slice(5))
  const distances = stats.value.weekly_data.map(d => d.distance)

  chart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: {
      type: 'category',
      data: dates,
      axisLabel: { color: '#666' }
    },
    yAxis: {
      type: 'value',
      name: 'km',
      axisLabel: { color: '#666' }
    },
    series: [{
      data: distances,
      type: 'line',
      smooth: true,
      areaStyle: { color: 'rgba(64, 158, 255, 0.2)' },
      lineStyle: { color: '#409EFF', width: 2 },
      itemStyle: { color: '#409EFF' }
    }]
  })
}

onMounted(() => {
  loadStats()
  loadNotices()
})
</script>

<style scoped>
.dashboard {
  max-width: 1400px;
  margin: 0 auto;
}

.page-title {
  font-size: 24px;
  color: #333;
  margin-bottom: 24px;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #333;
}

.stat-label {
  font-size: 14px;
  color: #999;
}

.quick-actions-card,
.chart-card,
.notices-card {
  margin-bottom: 20px;
  border-radius: 12px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.quick-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.quick-actions .el-button {
  flex: 1;
  min-width: 140px;
}

.empty-notice {
  text-align: center;
  color: #999;
  padding: 40px 0;
}

.notice-list,
.plan-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.notice-item,
.plan-item {
  padding: 12px;
  background: #f5f7fa;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
}

.notice-item:hover,
.plan-item:hover {
  background: #ecf5ff;
}

.notice-item h4,
.plan-item h4 {
  margin: 0 0 8px;
  font-size: 14px;
  color: #333;
}

.notice-item p,
.plan-item p {
  margin: 0 0 8px;
  font-size: 12px;
  color: #666;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.notice-time {
  font-size: 12px;
  color: #999;
}

.plan-meta {
  display: flex;
  gap: 8px;
  align-items: center;
}
</style>
