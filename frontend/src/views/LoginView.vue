<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { api, describeError } from '../api/client'
import { setStudent } from '../state/session'

const route = useRoute()
const router = useRouter()

const login = ref('')
const password = ref('')
const submitting = ref(false)
const error = ref('')

async function submit(): Promise<void> {
  if (submitting.value) {
    return
  }
  submitting.value = true
  error.value = ''
  try {
    const response = await api.login(login.value.trim(), password.value)
    setStudent(response.student)
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/records'
    await router.replace(redirect)
  } catch (exception) {
    error.value = describeError(exception)
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="login">
    <form class="login__card" @submit.prevent="submit">
      <h1 class="login__title">错题整理与个人笔记</h1>
      <p class="login__subtitle">用验收账号登录，只会看到属于你自己的错题。</p>

      <label class="field">
        <span class="field__label">登录名</span>
        <input v-model="login" class="field__input" type="text" autocomplete="username" required />
      </label>

      <label class="field">
        <span class="field__label">密码</span>
        <input
          v-model="password"
          class="field__input"
          type="password"
          autocomplete="current-password"
          required
        />
      </label>

      <button class="btn btn--primary btn--block" type="submit" :disabled="submitting">
        <span v-if="submitting" class="spinner" aria-hidden="true"></span>
        {{ submitting ? '登录中…' : '登录' }}
      </button>

      <p v-if="error" class="notice notice--error" role="alert">{{ error }}</p>
    </form>
  </div>
</template>
