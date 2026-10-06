<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { api, describeError } from '../api/client'
import type { Course, Note, WrongRecord } from '../api/types'
import FilterSidebar from '../components/FilterSidebar.vue'
import RecordDetail from '../components/RecordDetail.vue'
import RecordList from '../components/RecordList.vue'

interface FilterState {
  courseId: string
  knowledgePoint: string
  keyword: string
}

const route = useRoute()
const router = useRouter()

const courses = ref<Course[]>([])
const knowledgePoints = ref<string[]>([])
const records = ref<WrongRecord[]>([])
const detail = ref<WrongRecord | null>(null)
const listLoading = ref(false)
const detailLoading = ref(false)
const listError = ref('')
const detailError = ref('')

function asString(value: unknown): string {
  if (Array.isArray(value)) {
    return typeof value[0] === 'string' ? value[0] : ''
  }
  return typeof value === 'string' ? value : ''
}

// 筛选条件全部存在 URL query 里：刷新、前进/后退、从详情返回都不会丢
const filters = computed<FilterState>(() => ({
  courseId: asString(route.query.courseId),
  knowledgePoint: asString(route.query.knowledgePoint),
  keyword: asString(route.query.keyword),
}))

const selectedId = computed(() => asString(route.query.recordId))

function activeQuery(): Record<string, string> {
  const query: Record<string, string> = {}
  if (filters.value.courseId) query.courseId = filters.value.courseId
  if (filters.value.knowledgePoint) query.knowledgePoint = filters.value.knowledgePoint
  if (filters.value.keyword) query.keyword = filters.value.keyword
  return query
}

function go(query: Record<string, string>, replace = false): void {
  const target = { query }
  void (replace ? router.replace(target) : router.push(target))
}

function applyFilters(patch: FilterState | Partial<FilterState>): void {
  const merged = { ...filters.value, ...patch }
  const query: Record<string, string> = {}
  if (merged.courseId) query.courseId = merged.courseId
  if (merged.knowledgePoint) query.knowledgePoint = merged.knowledgePoint
  if (merged.keyword) query.keyword = merged.keyword

  // 只改关键词时用 replace，避免输入过程中塞满历史记录
  const changedKeys = Object.keys(patch)
  const onlyKeyword = changedKeys.length === 1 && changedKeys[0] === 'keyword'
  // 筛选变化后之前选中的记录可能已不在结果里，因此顺带取消选中
  go(query, onlyKeyword)
}

function selectRecord(id: string): void {
  go({ ...activeQuery(), recordId: id })
}

function closeDetail(): void {
  go(activeQuery())
}

async function loadRecords(): Promise<void> {
  listLoading.value = true
  listError.value = ''
  try {
    const response = await api.listRecords(filters.value)
    records.value = response.records
  } catch (error) {
    records.value = []
    listError.value = describeError(error)
  } finally {
    listLoading.value = false
  }
}

async function loadDetail(id: string): Promise<void> {
  detailError.value = ''
  if (!id) {
    detail.value = null
    return
  }
  detailLoading.value = true
  try {
    detail.value = await api.getRecord(id)
  } catch (error) {
    detail.value = null
    detailError.value = describeError(error)
  } finally {
    detailLoading.value = false
  }
}

function onNoteSaved(note: Note): void {
  const currentId = detail.value?.id
  if (!currentId) {
    return
  }
  if (detail.value) {
    detail.value = { ...detail.value, note }
  }
  const index = records.value.findIndex((record) => record.id === currentId)
  if (index >= 0) {
    records.value[index] = { ...records.value[index], note }
  }
}

watch(filters, loadRecords, { immediate: true, deep: true })
watch(selectedId, loadDetail, { immediate: true })

onMounted(async () => {
  try {
    courses.value = await api.listCourses()
  } catch {
    courses.value = []
  }
  try {
    knowledgePoints.value = await api.listKnowledgePoints()
  } catch {
    knowledgePoints.value = []
  }
})
</script>

<template>
  <main class="workspace">
    <FilterSidebar
      :courses="courses"
      :knowledge-points="knowledgePoints"
      :course-id="filters.courseId"
      :knowledge-point="filters.knowledgePoint"
      :keyword="filters.keyword"
      :total="records.length"
      :loading="listLoading"
      @change="applyFilters"
    />

    <RecordList
      :records="records"
      :selected-id="selectedId"
      :loading="listLoading"
      :error="listError"
      @select="selectRecord"
    />

    <RecordDetail
      :record="detail"
      :loading="detailLoading"
      :error="detailError"
      @close="closeDetail"
      @saved="onNoteSaved"
    />
  </main>
</template>
