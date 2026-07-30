<template>
  <div class="layout-container">
    <!-- 顶部导航 -->
    <header class="header">
      <div class="header-left">
        <h1 class="logo">🏃 跑团管理系统</h1>
      </div>
      <div class="header-right">
        <el-dropdown @command="handleCommand">
          <span class="user-info">
            <el-avatar :size="32" :icon="UserFilled" />
            <span class="username">{{ userStore.userInfo?.username }}</span>
            <el-tag v-if="userStore.isAdmin" type="danger" size="small">管理员</el-tag>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="profile">
                <el-icon><User /></el-icon>个人中心
              </el-dropdown-item>
              <el-dropdown-item command="logout" divided>
                <el-icon><SwitchButton /></el-icon>退出登录
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </header>

    <div class="main-container">
      <!-- 侧边栏 -->
      <aside class="sidebar">
        <el-menu
          :default-active="activeMenu"
          class="sidebar-menu"
          router
        >
          <el-menu-item index="/">
            <el-icon><HomeFilled /></el-icon>
            <span>首页</span>
          </el-menu-item>

          <el-menu-item index="/checkin">
            <el-icon><CircleCheck /></el-icon>
            <span>跑步打卡</span>
          </el-menu-item>

          <el-menu-item index="/stats">
            <el-icon><DataAnalysis /></el-icon>
            <span>数据看板</span>
          </el-menu-item>

          <el-menu-item index="/leaderboard">
            <el-icon><TrendCharts /></el-icon>
            <span>排行榜</span>
          </el-menu-item>

          <el-menu-item index="/activities">
            <el-icon><Calendar /></el-icon>
            <span>活动报名</span>
          </el-menu-item>

          <el-sub-menu v-if="userStore.isAdmin" index="admin">
            <template #title>
              <el-icon><Setting /></el-icon>
              <span>管理后台</span>
            </template>
            <el-menu-item index="/admin">总览</el-menu-item>
            <el-menu-item index="/admin/users">成员管理</el-menu-item>
            <el-menu-item index="/admin/reviews">数据审核</el-menu-item>
            <el-menu-item index="/admin/notices">公告管理</el-menu-item>
            <el-menu-item index="/admin/activities">活动管理</el-menu-item>
            <el-menu-item index="/admin/export">数据导出</el-menu-item>
            <el-menu-item index="/admin/checkin">代成员打卡</el-menu-item>
          </el-sub-menu>
        </el-menu>
      </aside>

      <!-- 主内容区 -->
      <main class="content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import {
  HomeFilled, CircleCheck, DataAnalysis, TrendCharts,
  Calendar, Setting, User, UserFilled, SwitchButton
} from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { authApi } from '@/api'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const activeMenu = computed(() => route.path)

const handleCommand = async (command) => {
  if (command === 'profile') {
    router.push('/profile')
  } else if (command === 'logout') {
    try {
      await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      })
      userStore.clearAuth()
      router.push('/login')
    } catch {
      // 取消操作
    }
  }
}

// 初始化用户信息
const initUserInfo = async () => {
  if (userStore.token && !userStore.userInfo) {
    try {
      const userInfo = await authApi.getMe()
      userStore.setUserInfo(userInfo)
    } catch {
      // 忽略错误
    }
  }
}

initUserInfo()
</script>

<style scoped>
.layout-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.header {
  background: white;
  padding: 0 24px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-left .logo {
  font-size: 20px;
  color: #409EFF;
  margin: 0;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.username {
  color: #333;
  font-weight: 500;
}

.main-container {
  display: flex;
  flex: 1;
}

.sidebar {
  width: 220px;
  background: white;
  min-height: calc(100vh - 64px);
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.05);
}

.sidebar-menu {
  border-right: none;
}

.content {
  flex: 1;
  padding: 24px;
  background: #f5f7fa;
  min-height: calc(100vh - 64px);
  overflow-y: auto;
}
</style>
