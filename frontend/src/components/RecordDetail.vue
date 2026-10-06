<script setup lang="ts">
import type { Note, WrongRecord } from '../api/types'
import { formatScore, gradingSourceLabel, questionTypeLabel } from '../utils/format'
import MathText from './MathText.vue'
import NoteEditor from './NoteEditor.vue'
import SafeHtml from './SafeHtml.vue'

defineProps<{
  record: WrongRecord | null
  loading: boolean
  error: string
}>()

const emit = defineEmits<{
  (event: 'close'): void
  (event: 'saved', note: Note): void
}>()
</script>

<template>
  <section class="detail">
    <div v-if="error" class="notice notice--error">{{ error }}</div>

    <p v-else-if="loading && !record" class="placeholder">正在加载详情…</p>

    <p v-else-if="!record" class="placeholder">
      从左侧列表里选一道错题，查看题干、原始作答与历史反馈。
    </p>

    <template v-else>
      <header class="detail__head">
        <div>
          <h2 class="detail__title">{{ record.id }}</h2>
          <p class="detail__meta">
            {{ record.courseName }}
            <span class="dot">·</span>
            {{ record.assignmentTitle }}
            <span class="dot">·</span>
            {{ record.questionId }}
          </p>
        </div>
        <button class="btn btn--ghost" type="button" @click="emit('close')">返回列表</button>
      </header>

      <div class="score-row">
        <span class="score-row__value">{{ formatScore(record.score) }}</span>
        <span class="score-row__total">/ {{ formatScore(record.maxScore) }} 分</span>
        <span class="tag">{{ gradingSourceLabel(record.gradingSource) }}</span>
        <span class="tag">{{ questionTypeLabel(record.questionType) }}</span>
      </div>

      <section class="block">
        <h3>题干</h3>
        <MathText :source="record.questionText" />
      </section>

      <section class="block">
        <h3>我的原始作答 <span class="hint">来源数据，只读</span></h3>
        <SafeHtml v-if="record.answerFormat === 'html'" :html="record.originalAnswer" />
        <MathText v-else :source="record.originalAnswer" />
      </section>

      <section class="block">
        <h3>知识点</h3>
        <p v-if="record.knowledgePoints.length === 0" class="muted">未标注</p>
        <ul v-else class="chips">
          <li v-for="point in record.knowledgePoints" :key="point" class="chips__item">
            {{ point }}
          </li>
        </ul>
      </section>

      <!-- 来源反馈与自填笔记视觉上明确分区，前者只读、后者可编辑 -->
      <section class="block block--source">
        <h3>历史批改反馈 <span class="hint">来源数据，只读</span></h3>
        <p v-if="record.feedback" class="feedback">{{ record.feedback }}</p>
        <p v-else class="muted">暂无评语</p>
      </section>

      <NoteEditor :record="record" @saved="emit('saved', $event)" />
    </template>
  </section>
</template>
