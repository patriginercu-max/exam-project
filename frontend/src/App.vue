<script setup lang="ts">
import { useRouter } from 'vue-router'

import { api } from './api/client'
import { clearSession, currentStudent } from './state/session'

const router = useRouter()

async function logout(): Promise<void> {
  try {
    await api.logout()
  } finally {
    clearSession()
    await router.replace({ name: 'login' })
  }
}
</script>

<template>
  <div class="app">
    <header class="app__bar">
      <span class="app__brand">错题整理与个人笔记</span>
      <nav v-if="currentStudent" class="app__nav">
        <span class="app__user">{{ currentStudent.name }}</span>
        <button class="btn btn--ghost" type="button" @click="logout">退出登录</button>
      </nav>
    </header>
    <RouterView />
  </div>
</template>
