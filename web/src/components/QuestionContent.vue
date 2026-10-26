<script setup lang="ts">
import { computed } from 'vue'
import { questionHtml } from '@/utils/question-content'

const props = defineProps<{ content?: string | null }>()
const html = computed(() => questionHtml(props.content))
</script>

<template>
  <div class="question-content" v-html="html" />
</template>

<style>
.question-content { overflow-wrap: anywhere; line-height: 1.8; }
.question-content p { margin: 0 0 .5em; }
.question-content p:last-child { margin-bottom: 0; }
.question-content ul, .question-content ol { padding-left: 1.6em; margin: .5em 0; }
.question-content sup, .question-content sub { font-size: .75em; }
</style>
