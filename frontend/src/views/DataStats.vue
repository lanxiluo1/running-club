<template>
  <div class="data-stats-page">
    <h2 class="page-title">📊 数据看板</h2>

    <!-- 统计概览 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-value">{{ stats.total_distance || 0 }}</div>
          <div class="stat-label">累计跑量(km)</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-value">{{ stats.total_runs || 0 }}</div>
          <div class="stat-label">打卡次数</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-value">{{ stats.avg_pace || '--' }}</div>
          <div class="stat-label">平均速度(km/h)</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-value">{{ stats.avg_heart_rate || '--' }}</div>
          <div class="stat-label">平均心率(bpm)</div>
        </div>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="20">
      <el-col :xs="24" :lg="12">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>跑量趋势</span>
              <el-radio-group v-model="trendType" size="small">
                <el-radio-button label="weekly">本周</el-radio-button>
                <el-radio-button label="monthly">本月</el-radio-button>
              </el-radio-group>
            </div>
          </template>
          <div ref="trendChartRef" style="height: 300px;"></div>
        </el-card>
      </el-col>
      <el-col :xs="24" :lg="12">
        <el-card class="chart-card">
          <template #header>
            <span>配速分析（最近10次）</span>
          </template>
          <div ref="paceChartRef" style="height: 300px;"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :xs="24">
        <el-card class="chart-card">
          <template #header>
            <span>心率-配速关联分析</span>
          </template>
          <div ref="heartRateChartRef" style="height: 300px;"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 历史记录 -->
    <el-card class="records-card" style="margin-top: 20px;">
      <template #header>
        <span>历史打卡记录</span>
      </template>
      <el-table :data="records" stripe>
        <el-table-column prop="run_date" label="日期" width="120" />
        <el-table-column prop="distance" label="距离(km)" width="100" />
        <el-table-column prop="duration" label="时长" width="100">
          <template #default="{ row }">
            {{ formatDuration(row.duration) }}
          </template>
        </el-table-column>
        <el-table-column prop="pace" label="速度(km/h)" width="120">
          <template #default="{ row }">
            {{ row.pace ? row.pace.toFixed(2) : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="heart_rate" label="心率(bpm)" width="100">
          <template #default="{ row }">
            {{ row.heart_rate || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="training_type" label="训练类型" width="100" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 50]"
          :total="totalCount"
          layout="total, sizes, prev, pager, next"
          @current-change="handlePageChange"
          @size-change="handleSizeChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import * as echarts from 'echarts'
import { runRecordApi } from '@/api'

const trendType = ref('weekly')
const paceType = ref('10')
const stats = ref({})
const records = ref([])
const currentPage = ref(1)
const pageSize = ref(10)
const totalCount = ref(0)

const trendChartRef = ref(null)
const paceChartRef = ref(null)
const heartRateChartRef = ref(null)

let trendChart = null
let paceChart = null
let heartRateChart = null

const loadStats = async () => {
  try {
    stats.value = await runRecordApi.getStats()
  } catch (e) {
    console.error(e)
  }
}

const loadRecords = async () => {
  try {
    const skip = (currentPage.value - 1) * pageSize.value
    const response = await runRecordApi.getMyRecords({ skip, limit: pageSize.value })

    if (Array.isArray(response)) {
      records.value = response
      totalCount.value = response.length
    } else if (response && typeof response === 'object') {
      records.value = response.data || []
      totalCount.value = response.total || 0
    } else {
      records.value = []
      totalCount.value = 0
    }
  } catch (e) {
    console.error(e)
  }
}

const handlePageChange = (page) => {
  currentPage.value = page
  loadRecords()
}

const handleSizeChange = (size) => {
  pageSize.value = size
  currentPage.value = 1
  loadRecords()
}

const renderCharts = () => {
  renderTrendChart()
  renderPaceChart()
  renderHeartRateChart()
}

const renderTrendChart = () => {
  if (!trendChartRef.value) return
  if (!trendChart) trendChart = echarts.init(trendChartRef.value)

  const data = trendType.value === 'weekly' ? stats.value.weekly_data : stats.value.monthly_data
  const dates = data.map(d => d.date.slice(5))
  const distances = data.map(d => d.distance)

  trendChart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: dates, axisLabel: { color: '#666' } },
    yAxis: { type: 'value', name: 'km', axisLabel: { color: '#666' } },
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

const renderPaceChart = () => {
  if (!paceChartRef.value) return
  if (!paceChart) paceChart = echarts.init(paceChartRef.value)

  // 从records中提取最近10次配速数据
  const paceData = records.value
    .filter(r => r.pace && r.status === 'approved')
    .slice(0, 10)
    .reverse()

  const dates = paceData.map(r => r.run_date.slice(5))
  const paces = paceData.map(r => r.pace)

  paceChart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: dates, axisLabel: { color: '#666' } },
    yAxis: {
      type: 'value',
      name: 'km/h',
      axisLabel: { color: '#666' }
    },
    series: [{
      data: paces,
      type: 'line',
      smooth: true,
      areaStyle: { color: 'rgba(103, 194, 58, 0.2)' },
      lineStyle: { color: '#67C23A', width: 2 },
      itemStyle: { color: '#67C23A' }
    }]
  })
}

const renderHeartRateChart = () => {
  if (!heartRateChartRef.value) return
  if (!heartRateChart) heartRateChart = echarts.init(heartRateChartRef.value)

  const data = records.value
    .filter(r => r.pace && r.heart_rate && r.status === 'approved')
    .map(r => ({ pace: r.pace, heartRate: r.heart_rate, type: r.training_type || '其他' }))

  const types = [...new Set(data.map(d => d.type))]
  const series = types.map(type => ({
    name: type,
    data: data.filter(d => d.type === type).map(d => [d.pace, d.heartRate]),
    type: 'scatter',
    symbolSize: 10
  }))

  heartRateChart.setOption({
    tooltip: {
      trigger: 'item',
      formatter: (p) => `速度: ${p.data[0].toFixed(2)} km/h<br>心率: ${p.data[1]} bpm`
    },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'value', name: '速度(km/h)', axisLabel: { color: '#666' } },
    yAxis: { type: 'value', name: '心率(bpm)', axisLabel: { color: '#666' } },
    legend: { data: types.map(t => t + ' (km/h)'), bottom: 0 },
    series
  })
}

const formatDuration = (seconds) => {
  if (!seconds) return '-'
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  return `${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

const getStatusType = (status) => {
  const map = { pending: 'warning', approved: 'success', rejected: 'danger' }
  return map[status] || 'info'
}

const getStatusText = (status) => {
  const map = { pending: '待审核', approved: '已通过', rejected: '已驳回' }
  return map[status] || status
}

watch(trendType, () => {
  renderTrendChart()
})

onMounted(async () => {
  await Promise.all([loadStats(), loadRecords()])
  renderCharts()
  window.addEventListener('resize', () => {
    trendChart?.resize()
    paceChart?.resize()
    heartRateChart?.resize()
  })
})
</script>

<style scoped>
.data-stats-page {
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
  padding: 24px;
  text-align: center;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: #409EFF;
}

.stat-label {
  font-size: 14px;
  color: #999;
  margin-top: 8px;
}

.chart-card,
.records-card {
  border-radius: 12px;
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
