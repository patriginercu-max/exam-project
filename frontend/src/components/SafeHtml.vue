<script setup lang="ts">
import DOMPurify from 'dompurify'
import { computed } from 'vue'

const props = defineProps<{ html: string }>()

// 原始作答来自数据库，属于不可信输入：
// 交给 DOMPurify 清洗后再渲染，脚本、事件属性与危险 URL 都会被移除，
// 同时保留下标、上标、段落、列表等结构。
const sanitized = computed(() =>
  DOMPurify.sanitize(props.html ?? '', {
    USE_PROFILES: { html: true },
    FORBID_TAGS: ['style', 'form', 'input', 'button', 'iframe', 'object', 'embed'],
    FORBID_ATTR: ['style'],
  }),
)
</script>

<template>
  <div class="safe-html" v-html="sanitized"></div>
</template>
