import request from '@/utils/request'

// 认证相关
export const authApi = {
  login: (data) => request.post('/auth/login', data),
  register: (data) => request.post('/auth/register', data),
  getMe: () => request.get('/auth/me')
}

// 用户相关
export const userApi = {
  getProfile: () => request.get('/users/me'),
  updateProfile: (data) => request.put('/users/me', data),
  changePassword: (data) => request.put('/users/me/password', data)
}

// 打卡记录相关
export const runRecordApi = {
  getMyRecords: (params) => request.get('/run-records/my', { params }),
  createRecord: (data) => request.post('/run-records', data),
  getStats: () => request.get('/run-records/stats'),
  ocrRecognize: (file) => {
    const formData = new FormData()
    formData.append('file', file)
    return request.post('/run-records/ocr', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  adminCheckin: (userId, data) => request.post(`/run-records/admin/checkin?target_user_id=${userId}`, data)
}

// 活动相关
export const activityApi = {
  getList: (params) => request.get('/activities', { params }),
  getById: (id) => request.get(`/activities/${id}`),
  create: (data) => request.post('/activities', data),
  delete: (id) => request.delete(`/activities/${id}`),
  signUp: (id) => request.post(`/activities/${id}/sign`),
  cancelSign: (id) => request.delete(`/activities/${id}/sign`),
  getSigns: (id) => request.get(`/activities/${id}/signs`),
  exportSigns: (id) => request.get(`/activities/${id}/export`, { responseType: 'blob' })
}

// 公告相关
export const noticeApi = {
  getList: (params) => request.get('/notices', { params }),
  create: (data) => request.post('/notices', data),
  delete: (id) => request.delete(`/notices/${id}`)
}


// 排行榜相关
export const leaderboardApi = {
  getWeekly: (params) => request.get('/leaderboard/weekly', { params }),
  getMonthly: (params) => request.get('/leaderboard/monthly', { params }),
  getAttendance: (params) => request.get('/leaderboard/attendance', { params })
}

// 管理后台相关
export const adminApi = {
  getUsers: (params) => request.get('/admin/users', { params }),
  updateUser: (id, data) => request.put(`/admin/users/${id}`, data),
  resetUserPassword: (id) => request.post(`/admin/users/${id}/reset-password`),
  deleteUser: (id) => request.delete(`/admin/users/${id}`),
  getPendingRecords: (params) => request.get('/admin/run-records/pending', { params }),
  getAllRecords: (params) => request.get('/admin/run-records/all', { params }),
  reviewRecord: (id, status) => request.put(`/admin/run-records/${id}/review`, { status }),
  deleteRecord: (id) => request.delete(`/admin/run-records/${id}`),
  getStatsOverview: () => request.get('/admin/stats/overview'),
  exportRecords: (params) => ({
    url: '/api/admin/export/run-records',
    method: 'get',
    params,
    headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
    responseType: 'blob'
  })
}
