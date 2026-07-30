<template>
  <div class="admin-dashboard">
    <h2 class="page-title">⚙️ 管理后台</h2>

    <!-- 统计概览 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="24" :sm="8" :md="4">
        <div class="stat-card">
          <div class="stat-icon" style="background: #409EFF;">
            <el-icon :size="28"><User /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ overview.total_users }}</div>
            <div class="stat-label">成员总数</div>
          </div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="8" :md="4">
        <div class="stat-card">
          <div class="stat-icon" style="background: #67C23A;">
            <el-icon :size="28"><CircleCheck /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ overview.approved_records }}</div>
            <div class="stat-label">已审核打卡</div>
          </div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="8" :md="4">
        <div class="stat-card">
          <div class="stat-icon" style="background: #E6A23C;">
            <el-icon :size="28"><Clock /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ overview.pending_records }}</div>
            <div class="stat-label">待审核</div>
          </div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="8" :md="4">
        <div class="stat-card">
          <div class="stat-icon" style="background: #F56C6C;">
            <el-icon :size="28"><TrendCharts /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ overview.total_distance }}</div>
            <div class="stat-label">总跑量(km)</div>
          </div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="8" :md="4">
        <div class="stat-card">
          <div class="stat-icon" style="background: #909399;">
            <el-icon :size="28"><Calendar /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ overview.total_activities || 0 }}</div>
            <div class="stat-label">活动总数</div>
          </div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="8" :md="4">
        <div class="stat-card">
          <div class="stat-icon" style="background: #9C27B0;">
            <el-icon :size="28"><Document /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ overview.total_notices || 0 }}</div>
            <div class="stat-label">公告总数</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 快捷入口 -->
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :xs="24" :sm="8">
        <el-card class="quick-card" shadow="hover" @click="$router.push('/admin/users')">
          <el-icon :size="48" color="#409EFF"><UserFilled /></el-icon>
          <h3>成员管理</h3>
          <p>管理跑团成员信息、分组</p>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="8">
        <el-card class="quick-card" shadow="hover" @click="$router.push('/admin/reviews')">
          <el-icon :size="48" color="#67C23A"><CircleCheck /></el-icon>
          <h3>数据审核</h3>
          <p>审核队员打卡记录</p>
          <el-badge v-if="overview.pending_records > 0" :value="overview.pending_records" class="badge" />
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="8">
        <el-card class="quick-card" shadow="hover" @click="$router.push('/admin/notices')">
          <el-icon :size="48" color="#E6A23C"><Bell /></el-icon>
          <h3>公告管理</h3>
          <p>发布社团公告通知</p>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :xs="24" :sm="8">
        <el-card class="quick-card" shadow="hover" @click="$router.push('/admin/activities')">
          <el-icon :size="48" color="#E6A23C"><Calendar /></el-icon>
          <h3>活动管理</h3>
          <p>管理活动报名信息</p>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="8">
        <el-card class="quick-card" shadow="hover" @click="$router.push('/admin/export')">
          <el-icon :size="48" color="#909399"><Download /></el-icon>
          <h3>数据导出</h3>
          <p>导出训练数据报表</p>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="8">
        <el-card class="quick-card" shadow="hover" @click="$router.push('/admin/checkin')">
          <el-icon :size="48" color="#409EFF"><Upload /></el-icon>
          <h3>代成员打卡</h3>
          <p>管理员帮助成员完成打卡</p>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { adminApi } from '@/api'
import { User, CircleCheck, Clock, TrendCharts, UserFilled, Bell, Download, List, Upload, Calendar, Document } from '@element-plus/icons-vue'

const overview = ref({
  total_users: 0,
  total_records: 0,
  approved_records: 0,
  pending_records: 0,
  total_distance: 0,
  total_activities: 0,
  total_notices: 0
})

const loadOverview = async () => {
  try {
    overview.value = await adminApi.getStatsOverview()
  } catch (e) {
    console.error(e)
  }
}

onMounted(() => {
  loadOverview()
})
</script>

<style scoped>
.admin-dashboard {
  max-width: 1200px;
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

.quick-card {
  border-radius: 12px;
  cursor: pointer;
  text-align: center;
  padding: 32px 16px;
  transition: transform 0.3s;
  position: relative;
}

.quick-card:hover {
  transform: translateY(-4px);
}

.quick-card h3 {
  margin: 16px 0 8px;
  font-size: 18px;
  color: #333;
}

.quick-card p {
  margin: 0;
  font-size: 14px;
  color: #999;
}

.badge {
  position: absolute;
  top: 16px;
  right: 16px;
}
</style>
