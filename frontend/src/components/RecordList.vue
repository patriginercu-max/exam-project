<script setup lang="ts">
import type { WrongRecord } from '../api/types'
import { formatScore, plainPreview, questionTypeLabel } from '../utils/format'

defineProps<{
  records: WrongRecord[]
  selectedId: string
  loading: boolean
  error: string
}>()

const emit = defineEmits<{
  (event: 'select', id: string): void
}>()

function hasNote(record: WrongRecord): boolean {
  return Boolean(record.note.cause || record.note.content)
}
</script>

<template>
  <section class="record-list">
    <div v-if="error" class="notice notice--error">{{ error }}</div>

    <p v-else-if="loading && records.length === 0" class="placeholder">加载中…</p>

    <p v-else-if="records.length === 0" class="placeholder">
      没有符合条件的错题，试着放宽筛选条件。
    </p>

    <ul v-else class="record-list__items">
      <li v-for="record in records" :key="record.id">
        <button
          class="record-card"
          :class="{ 'record-card--active': record.id === selectedId }"
          type="button"
          @click="emit('select', record.id)"
        >
          <span class="record-card__top">
            <span class="record-card__id">{{ record.id }}</span>
            <span class="record-card__score">
              {{ formatScore(record.score) }}<span class="record-card__max">/{{ formatScore(record.maxScore) }}</span>
            </span>
          </span>
          <span class="record-card__meta">
            {{ record.courseName }}
            <span class="dot">·</span>
            {{ questionTypeLabel(record.questionType) }}
            <span v-if="hasNote(record)" class="record-card__note-tag">已记录笔记</span>
          </span>
          <span class="record-card__preview">{{ plainPreview(record.questionText) }}</span>
        </button>
      </li>
    </ul>
  </section>
</template>
