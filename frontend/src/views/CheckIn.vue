<template>
  <div class="checkin-page">
    <h2 class="page-title">🏃 跑步打卡</h2>

    <el-row :gutter="24">
      <el-col :xs="24" :lg="12">
        <el-card class="upload-card">
          <template #header>
            <span>上传跑步截图</span>
          </template>

          <el-upload
            ref="uploadRef"
            class="upload-area"
            drag
            :auto-upload="false"
            :show-file-list="false"
            :on-change="handleFileChange"
            accept="image/*"
          >
            <div v-if="!imageUrl" class="upload-placeholder">
              <el-icon :size="48"><UploadFilled /></el-icon>
              <p>拖拽图片到此处或点击上传</p>
              <p class="upload-tip">支持跑步APP截图、手表数据截图</p>
            </div>
            <div v-else class="image-preview">
              <el-image :src="imageUrl" fit="contain" />
              <el-button class="remove-btn" type="danger" :icon="Delete" circle @click.stop="removeImage" />
            </div>
          </el-upload>

          <div class="upload-actions">
            <el-button type="primary" :loading="recognizing" :disabled="!selectedFile" @click="handleOCR">
              {{ recognizing ? '识别中...' : '智能识别' }}
            </el-button>
            <el-button @click="resetForm">重置</el-button>
          </div>

          <el-alert
            v-if="ocrResult && !ocrResult.success"
            title="未能识别到跑步数据"
            type="warning"
            :closable="false"
            show-icon
            style="margin-top: 16px;"
          >
            请手动填写下方表单
          </el-alert>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="12">
        <el-card class="form-card">
          <template #header>
            <span>打卡信息 <el-tag v-if="form.check_in_method === 'auto'" type="success" size="small">识别</el-tag><el-tag v-else type="info" size="small">手动</el-tag></span>
          </template>

          <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
            <el-form-item label="跑步日期" prop="run_date">
              <el-date-picker
                v-model="form.run_date"
                type="date"
                placeholder="选择日期"
                style="width: 100%;"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
              />
            </el-form-item>

            <el-form-item label="跑步距离" prop="distance">
              <el-input-number
                v-model="form.distance"
                :precision="2"
                :step="0.1"
                :min="0.1"
                :max="100"
                placeholder="km"
                style="width: 100%;"
                @change="onFieldChanged"
              />
              <span class="unit">km</span>
            </el-form-item>

            <el-form-item label="运动时长" prop="duration">
              <el-input v-model="durationDisplay" placeholder="HH:MM:SS" @blur="handleDurationBlur">
                <template #append>
                  <el-button @click="showDurationPicker = !showDurationPicker">选择</el-button>
                </template>
              </el-input>
              <div v-if="showDurationPicker" class="duration-picker">
                <el-time-picker
                  v-model="durationTime"
                  placeholder="选择时长"
                  format="HH:mm:ss"
                  value-format="HH:mm:ss"
                  style="width: 100%;"
                  @change="handleDurationChange"
                />
              </div>
            </el-form-item>

            <el-form-item label="平均速度">
              <el-input
                :model-value="calculatedPace || '--'"
                style="width: 100%;"
                disabled
              />
              <span class="unit">km/h</span>
              <span class="hint">（根据距离和时长自动计算）</span>
            </el-form-item>

            <el-form-item label="平均心率" prop="heart_rate">
              <el-input-number
                v-model="form.heart_rate"
                :step="1"
                :min="0"
                :max="300"
                placeholder="bpm"
                style="width: 100%;"
                @change="onFieldChanged"
              />
              <span class="unit">bpm</span>
            </el-form-item>

            <el-form-item label="训练类型" prop="training_type">
              <el-select v-model="form.training_type" placeholder="选择训练类型" style="width: 100%;" @change="onFieldChanged">
                <el-option label="轻松跑" value="轻松跑" />
                <el-option label="马拉松配速" value="马拉松配速" />
                <el-option label="间歇跑" value="间歇跑" />
                <el-option label="节奏跑" value="节奏跑" />
                <el-option label="长距离" value="长距离" />
              </el-select>
            </el-form-item>

            <el-form-item>
              <el-button type="primary" :loading="submitting" @click="handleSubmit" style="width: 100%;">
                提交打卡
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled, Delete } from '@element-plus/icons-vue'
import { runRecordApi } from '@/api'

const uploadRef = ref(null)
const formRef = ref(null)
const selectedFile = ref(null)
const imageUrl = ref('')
const recognizing = ref(false)
const submitting = ref(false)
const showDurationPicker = ref(false)
const durationTime = ref('')
const ocrResult = ref(null)

const form = reactive({
  run_date: (() => {
    const d = new Date()
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
  })(),
  distance: null,
  duration: null,
  pace: null,
  heart_rate: null,
  training_type: '',
  check_in_method: 'manual'
})

const rules = {
  run_date: [{ required: true, message: '请选择日期', trigger: 'change' }],
  distance: [{ required: true, message: '请输入距离', trigger: 'blur' }],
  duration: [{ required: true, message: '请输入时长', trigger: 'blur' }]
}

// 记录OCR原始值，用于判断用户是否手动修改
const ocrOriginal = reactive({
  distance: null,
  duration: null,
  heart_rate: null,
  training_type: ''
})

// 计算速度 km/h
const calculatedPace = computed(() => {
  if (form.distance && form.duration && form.duration > 0) {
    const hours = form.duration / 3600
    return (form.distance / hours).toFixed(2)
  }
  return null
})

// 时长显示格式 HH:MM:SS
const durationDisplay = computed({
  get: () => form.duration ? formatDuration(form.duration) : '',
  set: (val) => {
    // 由用户输入触发
  }
})

// 字段被手动修改时调用
const onFieldChanged = () => {
  // 如果有OCR结果且用户修改了识别到的字段，改为手动模式
  if (ocrResult.value && ocrResult.value.success) {
    const original = ocrOriginal
    if (
      form.distance !== original.distance ||
      form.duration !== original.duration ||
      form.heart_rate !== original.heart_rate ||
      form.training_type !== original.training_type
    ) {
      form.check_in_method = 'manual'
    }
  } else {
    form.check_in_method = 'manual'
  }
}

const handleFileChange = (file) => {
  selectedFile.value = file.raw
  imageUrl.value = URL.createObjectURL(file.raw)
  ocrResult.value = null
}

const removeImage = () => {
  selectedFile.value = null
  imageUrl.value = ''
  ocrResult.value = null
  uploadRef.value?.clearFiles()
}

const handleOCR = async () => {
  if (!selectedFile.value) return

  recognizing.value = true
  try {
    const result = await runRecordApi.ocrRecognize(selectedFile.value)
    ocrResult.value = result

    if (result.success) {
      // 保存OCR原始值
      ocrOriginal.distance = result.distance
      ocrOriginal.duration = result.duration
      ocrOriginal.heart_rate = result.heart_rate
      ocrOriginal.training_type = result.training_type || ''

      // 自动填充表单
      form.distance = result.distance
      form.duration = result.duration
      form.heart_rate = result.heart_rate
      form.training_type = result.training_type || ''
      form.check_in_method = 'auto'

      ElMessage.success('识别成功，请检查数据并提交')
    } else {
      ElMessage.warning(result.message)
    }
  } catch (e) {
    ElMessage.error('识别失败，请手动填写')
  } finally {
    recognizing.value = false
  }
}

const handleDurationBlur = () => {
  const match = durationDisplay.value.match(/^(\d+):(\d{2})(?::(\d{2}))?$/)
  if (match) {
    const hours = parseInt(match[1])
    const minutes = parseInt(match[2])
    const seconds = match[3] ? parseInt(match[3]) : 0
    form.duration = hours * 3600 + minutes * 60 + seconds
    onFieldChanged()
  }
}

const handleDurationChange = (val) => {
  if (val) {
    const parts = val.split(':')
    form.duration = parseInt(parts[0]) * 3600 + parseInt(parts[1]) * 60 + parseInt(parts[2] || 0)
    onFieldChanged()
  }
}

const resetForm = () => {
  form.distance = null
  form.duration = null
  form.heart_rate = null
  form.training_type = ''
  form.check_in_method = 'manual'
  ocrOriginal.distance = null
  ocrOriginal.duration = null
  ocrOriginal.heart_rate = null
  ocrOriginal.training_type = ''
  removeImage()
  ocrResult.value = null
}

const handleSubmit = async () => {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  // 自动计算速度
  if (form.distance && form.duration && form.duration > 0) {
    const hours = form.duration / 3600
    form.pace = parseFloat((form.distance / hours).toFixed(2))
  }

  submitting.value = true
  try {
    await runRecordApi.createRecord(form)
    ElMessage.success('打卡成功，等待管理员审核')
    resetForm()
  } catch (e) {
    // 错误已处理
  } finally {
    submitting.value = false
  }
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
</script>

<style scoped>
.checkin-page {
  max-width: 1200px;
  margin: 0 auto;
}

.page-title {
  font-size: 24px;
  color: #333;
  margin-bottom: 24px;
}

.upload-card,
.form-card {
  border-radius: 12px;
}

.upload-area {
  width: 100%;
}

.upload-placeholder {
  padding: 40px;
  text-align: center;
  color: #999;
}

.upload-placeholder p {
  margin: 8px 0 0;
}

.upload-tip {
  font-size: 12px;
  color: #bbb;
}

.image-preview {
  position: relative;
  padding: 20px;
  text-align: center;
}

.image-preview .el-image {
  max-height: 300px;
}

.remove-btn {
  position: absolute;
  top: 10px;
  right: 10px;
}

.upload-actions {
  margin-top: 16px;
  text-align: center;
  display: flex;
  gap: 12px;
  justify-content: center;
}

.unit {
  margin-left: 8px;
  color: #999;
}

.hint {
  margin-left: 8px;
  color: #909399;
  font-size: 12px;
}
</style>
