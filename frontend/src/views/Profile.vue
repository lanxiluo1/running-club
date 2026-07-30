<template>
  <div class="profile-page">
    <h2 class="page-title">👤 个人中心</h2>

    <el-row :gutter="24">
      <el-col :xs="24" :lg="12">
        <el-card class="profile-card">
          <template #header>
            <span>个人信息</span>
          </template>

          <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
            <el-form-item label="学号">
              <el-input v-model="form.student_id" disabled />
            </el-form-item>

            <el-form-item label="姓名" prop="username">
              <el-input v-model="form.username" placeholder="请输入姓名" />
            </el-form-item>

            <el-form-item label="学院" prop="academy">
              <el-input v-model="form.academy" placeholder="请输入学院" />
            </el-form-item>

            <el-form-item label="年级" prop="grade">
              <el-input v-model="form.grade" placeholder="如：2024级" />
            </el-form-item>

            <el-form-item label="组别" prop="group_type">
              <el-select v-model="form.group_type" style="width: 100%;">
                <el-option label="新手组" value="beginner" />
                <el-option label="进阶组" value="advanced" />
              </el-select>
            </el-form-item>

            <el-form-item>
              <el-button type="primary" :loading="saving" @click="handleSave">
                保存修改
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="12">
        <!-- 修改密码 -->
        <el-card class="password-card">
          <template #header>
            <span>修改密码</span>
          </template>
          <el-form ref="passwordFormRef" :model="passwordForm" :rules="passwordRules" label-width="100px">
            <el-form-item label="原密码" prop="oldPassword">
              <el-input v-model="passwordForm.oldPassword" type="password" placeholder="请输入原密码" show-password />
            </el-form-item>
            <el-form-item label="新密码" prop="newPassword">
              <el-input v-model="passwordForm.newPassword" type="password" placeholder="请输入新密码" show-password />
            </el-form-item>
            <el-form-item label="确认新密码" prop="confirmPassword">
              <el-input v-model="passwordForm.confirmPassword" type="password" placeholder="请再次输入新密码" show-password />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="passwordLoading" @click="handleChangePassword">
                修改密码
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <el-card class="stats-card">
          <template #header>
            <span>我的数据</span>
          </template>

          <div class="stats-grid">
            <div class="stat-item">
              <div class="stat-value">{{ stats.total_distance || 0 }}</div>
              <div class="stat-label">累计跑量(km)</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ stats.total_runs || 0 }}</div>
              <div class="stat-label">打卡次数</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ stats.avg_pace || '--' }}</div>
              <div class="stat-label">平均配速</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ stats.avg_heart_rate || '--' }}</div>
              <div class="stat-label">平均心率</div>
            </div>
          </div>
        </el-card>

        <el-card class="achievement-card" style="margin-top: 20px;">
          <template #header>
            <span>我的成就</span>
          </template>
          <div class="achievements">
            <div class="achievement-item" v-for="badge in badges" :key="badge.id">
              <span class="badge-icon">{{ badge.icon }}</span>
              <span class="badge-name">{{ badge.name }}</span>
            </div>
            <el-empty v-if="badges.length === 0" description="暂无成就，继续加油！" :image-size="60" />
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { userApi, runRecordApi } from '@/api'

const userStore = useUserStore()
const formRef = ref(null)
const passwordFormRef = ref(null)
const saving = ref(false)
const passwordLoading = ref(false)
const stats = ref({})

const form = reactive({
  student_id: '',
  username: '',
  academy: '',
  grade: '',
  group_type: 'beginner'
})

const rules = {
  username: [{ required: true, message: '请输入姓名', trigger: 'blur' }]
}

const passwordForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const validateConfirmPassword = (rule, value, callback) => {
  if (value !== passwordForm.newPassword) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const passwordRules = {
  oldPassword: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

const badges = ref([])

const loadProfile = async () => {
  try {
    const userInfo = await userApi.getProfile()
    form.student_id = userInfo.student_id
    form.username = userInfo.username
    form.academy = userInfo.academy || ''
    form.grade = userInfo.grade || ''
    form.group_type = userInfo.group_type || 'beginner'
    userStore.setUserInfo(userInfo)
  } catch (e) {
    console.error(e)
  }
}

const loadStats = async () => {
  try {
    stats.value = await runRecordApi.getStats()
    updateBadges()
  } catch (e) {
    console.error(e)
  }
}

const updateBadges = () => {
  badges.value = []
  if (stats.value.total_runs >= 1) {
    badges.value.push({ id: 1, icon: '🎯', name: '首次打卡' })
  }
  if (stats.value.total_runs >= 10) {
    badges.value.push({ id: 2, icon: '🔥', name: '打卡达人' })
  }
  if (stats.value.total_distance >= 10) {
    badges.value.push({ id: 3, icon: '📏', name: '累计10公里' })
  }
  if (stats.value.total_distance >= 50) {
    badges.value.push({ id: 4, icon: '🏃', name: '累计50公里' })
  }
  if (stats.value.total_distance >= 100) {
    badges.value.push({ id: 5, icon: '💯', name: '累计100公里' })
  }
}

const handleSave = async () => {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  saving.value = true
  try {
    await userApi.updateProfile({
      username: form.username,
      academy: form.academy,
      grade: form.grade,
      group_type: form.group_type
    })
    ElMessage.success('保存成功')
    loadProfile()
  } catch (e) {
    // 错误已处理
  } finally {
    saving.value = false
  }
}

const handleChangePassword = async () => {
  const valid = await passwordFormRef.value.validate().catch(() => false)
  if (!valid) return

  passwordLoading.value = true
  try {
    await userApi.changePassword({
      old_password: passwordForm.oldPassword,
      new_password: passwordForm.newPassword,
      confirm_password: passwordForm.confirmPassword
    })
    ElMessage.success('密码修改成功')
    passwordForm.oldPassword = ''
    passwordForm.newPassword = ''
    passwordForm.confirmPassword = ''
  } catch (e) {
    if (e.response?.data?.detail) {
      ElMessage.error(e.response.data.detail)
    }
  } finally {
    passwordLoading.value = false
  }
}

onMounted(() => {
  loadProfile()
  loadStats()
})
</script>

<style scoped>
.profile-page {
  max-width: 1000px;
  margin: 0 auto;
}

.page-title {
  font-size: 24px;
  color: #333;
  margin-bottom: 24px;
}

.profile-card,
.stats-card,
.achievement-card,
.password-card {
  border-radius: 12px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

.stat-item {
  text-align: center;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 12px;
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

.achievements {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.achievement-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: #f5f7fa;
  border-radius: 8px;
}

.badge-icon {
  font-size: 24px;
}

.badge-name {
  font-size: 14px;
  color: #333;
}
</style>
