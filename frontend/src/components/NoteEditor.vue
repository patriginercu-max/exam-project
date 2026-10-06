<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import { api, describeError } from '../api/client'
import type { Note, WrongRecord } from '../api/types'
import { formatDateTime } from '../utils/format'

const props = defineProps<{ record: WrongRecord }>()

const emit = defineEmits<{
  (event: 'saved', note: Note): void
}>()

const cause = ref('')
const content = ref('')
const saving = ref(false)
const clearing = ref(false)
const savedAt = ref<string | null>(null)
const notice = ref<{ type: 'success' | 'error'; text: string } | null>(null)

const busy = computed(() => saving.value || clearing.value)
const savedAtText = computed(() => formatDateTime(savedAt.value))
const isEmpty = computed(() => !cause.value.trim() && !content.value.trim())

function syncFromRecord(record: WrongRecord): void {
  cause.value = record.note.cause
  content.value = record.note.content
  savedAt.value = record.note.updatedAt
  notice.value = null
}

// 只跟随记录 id：保存后父组件替换了记录对象，但输入框内容不该被重置
watch(() => props.record.id, () => syncFromRecord(props.record), { immediate: true })

async function save(): Promise<void> {
  saving.value = true
  notice.value = null
  try {
    const note = await api.saveNote(props.record.id, cause.value, content.value)
    savedAt.value = note.updatedAt
    emit('saved', note)
    notice.value = {
      type: 'success',
      text: isEmpty.value ? '已保存为空笔记（清空）' : '笔记已保存',
    }
  } catch (error) {
    // 保存失败时保留当前输入，不虚报成功
    notice.value = { type: 'error', text: `保存失败：${describeError(error)}` }
  } finally {
    saving.value = false
  }
}

async function clear(): Promise<void> {
  clearing.value = true
  notice.value = null
  try {
    const note = await api.clearNote(props.record.id)
    cause.value = ''
    content.value = ''
    savedAt.value = note.updatedAt
    emit('saved', note)
    notice.value = { type: 'success', text: '错因与复习笔记已清空' }
  } catch (error) {
    notice.value = { type: 'error', text: `清空失败：${describeError(error)}` }
  } finally {
    clearing.value = false
  }
}
</script>

<template>
  <section class="block note-block">
    <header class="note-block__head">
      <h3>学生填写的错因与复习笔记</h3>
      <span class="hint">可编辑 · 与上方历史反馈相互独立</span>
    </header>

    <label class="field">
      <span class="field__label">错因</span>
      <textarea
        v-model="cause"
        class="field__input"
        rows="3"
        placeholder="记录这道题错在哪里"
        :disabled="busy"
      ></textarea>
    </label>

    <label class="field">
      <span class="field__label">复习笔记</span>
      <textarea
        v-model="content"
        class="field__input"
        rows="5"
        placeholder="记录正确的解法与需要复习的知识点"
        :disabled="busy"
      ></textarea>
    </label>

    <div class="note-block__actions">
      <button class="btn btn--primary" :disabled="busy" @click="save">
        <span v-if="saving" class="spinner" aria-hidden="true"></span>
        {{ saving ? '保存中…' : '保存笔记' }}
      </button>
      <button class="btn btn--danger" :disabled="busy" @click="clear">
        <span v-if="clearing" class="spinner" aria-hidden="true"></span>
        {{ clearing ? '清空中…' : '清空笔记' }}
      </button>
      <span v-if="savedAtText" class="note-block__saved">上次保存：{{ savedAtText }}</span>
    </div>

    <p
      v-if="notice"
      class="notice"
      :class="notice.type === 'success' ? 'notice--success' : 'notice--error'"
      role="status"
    >
      {{ notice.text }}
    </p>
    <p v-if="isEmpty" class="hint">两个字段都为空时保存即为清空笔记。</p>
  </section>
</template>
