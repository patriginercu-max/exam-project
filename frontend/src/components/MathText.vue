<script setup lang="ts">
import { computed } from 'vue'

import { renderRichText } from '../utils/math'

const props = withDefaults(
  defineProps<{
    source: string
    /** 是否解析 $...$ / $$...$$，选择题的纯文本作答可关掉 */
    math?: boolean
  }>(),
  { math: true },
)

const html = computed(() => renderRichText(props.source, { math: props.math }))
</script>

<template>
  <div class="rich-text" v-html="html"></div>
</template>
