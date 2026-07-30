import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { guest: true }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/Register.vue'),
    meta: { guest: true }
  },
  {
    path: '/',
    component: () => import('@/views/Layout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue')
      },
      {
        path: 'checkin',
        name: 'CheckIn',
        component: () => import('@/views/CheckIn.vue')
      },
      {
        path: 'stats',
        name: 'DataStats',
        component: () => import('@/views/DataStats.vue')
      },
      {
        path: 'leaderboard',
        name: 'Leaderboard',
        component: () => import('@/views/Leaderboard.vue')
      },
      {
        path: 'activities',
        name: 'Activities',
        component: () => import('@/views/Activities.vue')
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('@/views/Profile.vue')
      },
      {
        path: 'notices',
        name: 'Notices',
        component: () => import('@/views/Notices.vue')
      },
      {
        path: 'admin',
        name: 'Admin',
        component: () => import('@/views/admin/AdminDashboard.vue'),
        meta: { admin: true }
      },
      {
        path: 'admin/users',
        name: 'UserManagement',
        component: () => import('@/views/admin/UserManagement.vue'),
        meta: { admin: true }
      },
      {
        path: 'admin/reviews',
        name: 'ReviewManagement',
        component: () => import('@/views/admin/ReviewManagement.vue'),
        meta: { admin: true }
      },
      {
        path: 'admin/notices',
        name: 'NoticeManagement',
        component: () => import('@/views/admin/NoticeManagement.vue'),
        meta: { admin: true }
      },
      {
        path: 'admin/export',
        name: 'DataExport',
        component: () => import('@/views/admin/DataExport.vue'),
        meta: { admin: true }
      },
      {
        path: 'admin/activities',
        name: 'ActivityManagement',
        component: () => import('@/views/admin/ActivityManagement.vue'),
        meta: { admin: true }
      },
      {
        path: 'admin/checkin',
        name: 'AdminCheckIn',
        component: () => import('@/views/admin/AdminCheckIn.vue'),
        meta: { admin: true }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  const userRole = localStorage.getItem('userRole')

  if (to.meta.requiresAuth && !token) {
    next('/login')
  } else if (to.meta.guest && token) {
    next('/')
  } else if (to.meta.admin && userRole !== 'admin') {
    next('/')
  } else {
    next()
  }
})

export default router
