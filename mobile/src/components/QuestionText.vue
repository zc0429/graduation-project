<script setup>
import { computed } from 'vue'

const props = defineProps({ content: { type: String, default: '' } })
const allowedTag = /<(\/?)(p|br|strong|b|em|i|u|s|strike|del|ul|ol|li|sub|sup)\b[^>]*>/gi
const richNodes = computed(() => {
  // Escape text first and restore only the presentation tags supported by the backend.
  if (!props.content.match(allowedTag)) return ''
  const escapedText = props.content.replace(/</g, '&lt;').replace(/>/g, '&gt;')
  return escapedText.replace(/&lt;(\/?)(p|br|strong|b|em|i|u|s|strike|del|ul|ol|li|sub|sup)\b[^&]*?&gt;/gi,
    (_, closing, tag) => `<${closing}${tag.toLowerCase()}>`)
})
</script>

<template>
  <rich-text v-if="richNodes" class="copy" :nodes="richNodes" />
  <text v-else class="copy">{{ content }}</text>
</template>
