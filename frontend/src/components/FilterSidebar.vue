<script setup lang="ts">
import { ref, watch } from 'vue'

import type { Course } from '../api/types'

const props = defineProps<{
  courses: Course[]
  knowledgePoints: string[]
  courseId: string
  knowledgePoint: string
  keyword: string
  total: number
  loading: boolean
}>()

const emit = defineEmits<{
  (
    event: 'change',
    patch: { courseId?: string; knowledgePoint?: string; keyword?: string },
  ): void
}>()

const keywordDraft = ref(props.keyword)
let debounceTimer: number | undefined

// URL 是筛选状态的唯一来源，外部变化（前进/后退、登录跳回）要同步回输入框
watch(
  () => props.keyword,
  (value) => {
    if (value !== keywordDraft.value) {
      keywordDraft.value = value
    }
  },
)

function emitKeyword(): void {
  if (debounceTimer !== undefined) {
    window.clearTimeout(debounceTimer)
    debounceTimer = undefined
  }
  emit('change', { keyword: keywordDraft.value.trim() })
}

function onKeywordInput(): void {
  if (debounceTimer !== undefined) {
    window.clearTimeout(debounceTimer)
  }
  debounceTimer = window.setTimeout(emitKeyword, 400)
}

function reset(): void {
  keywordDraft.value = ''
  emit('change', { courseId: '', knowledgePoint: '', keyword: '' })
}
</script>

<template>
  <aside class="filter-panel">
    <div class="filter-panel__head">
      <h2>筛选</h2>
      <button class="btn btn--link" @click="reset">重置</button>
    </div>

    <label class="field">
      <span class="field__label">课程</span>
      <select
        class="field__input"
        :value="courseId"
        @change="emit('change', { courseId: ($event.target as HTMLSelectElement).value })"
      >
        <option value="">全部课程</option>
        <option v-for="course in courses" :key="course.id" :value="course.id">
          {{ course.name }}
        </option>
      </select>
    </label>

    <label class="field">
      <span class="field__label">知识点</span>
      <select
        class="field__input"
        :value="knowledgePoint"
        @change="emit('change', { knowledgePoint: ($event.target as HTMLSelectElement).value })"
      >
        <option value="">全部知识点</option>
        <option v-for="point in knowledgePoints" :key="point" :value="point">
          {{ point }}
        </option>
      </select>
    </label>

    <label class="field">
      <span class="field__label">题干关键词</span>
      <input
        v-model="keywordDraft"
        class="field__input"
        type="search"
        placeholder="例如：写出四阶"
        @input="onKeywordInput"
        @keyup.enter="emitKeyword"
        @blur="emitKeyword"
      />
    </label>

    <p class="filter-panel__count">
      <template v-if="loading">筛选中…</template>
      <template v-else>共 {{ total }} 条错题</template>
    </p>
  </aside>
</template>
