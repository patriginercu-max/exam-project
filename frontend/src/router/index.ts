import { createRouter, createWebHistory } from 'vue-router'

import { ensureSession } from '../state/session'
import LoginView from '../views/LoginView.vue'
import RecordsView from '../views/RecordsView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/records' },
    { path: '/login', name: 'login', component: LoginView, meta: { public: true } },
    { path: '/records', name: 'records', component: RecordsView },
    { path: '/:pathMatch(.*)*', redirect: '/records' },
  ],
})

router.beforeEach(async (to) => {
  if (to.meta.public) {
    return true
  }
  const student = await ensureSession()
  if (student) {
    return true
  }
  // 带上完整路径（含筛选参数），登录后可以回到原来的筛选状态
  return { name: 'login', query: { redirect: to.fullPath } }
})

export default router
