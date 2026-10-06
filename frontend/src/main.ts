import { createApp } from 'vue'

import 'katex/dist/katex.min.css'
import './styles/main.css'

import App from './App.vue'
import { setUnauthorizedHandler } from './api/client'
import router from './router'
import { clearSession } from './state/session'

// 任何接口返回 401（会话过期/被吊销）都回到登录页，
// 并把当前完整路径带在 redirect 上，登录后筛选状态不会丢。
setUnauthorizedHandler(() => {
  clearSession()
  const current = router.currentRoute.value
  if (current.name === 'login') {
    return
  }
  void router.replace({ name: 'login', query: { redirect: current.fullPath } })
})

createApp(App).use(router).mount('#app')
