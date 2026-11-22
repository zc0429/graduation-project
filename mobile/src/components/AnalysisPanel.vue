<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { readAnalysis, startAnalysis } from '../api/student.js'
import { errorMessage } from '../api/request.js'
import LoadState from './LoadState.vue'
import QuestionText from './QuestionText.vue'

const props = defineProps({
  questionId: { type: Number, required: true },
  allowStart: Boolean,
  autoStart: Boolean,
})
const emit = defineEmits(['attempt'])
const analysis = ref(null)
const loading = ref(true)
const starting = ref(false)
const error = ref('')
const startFailed = ref(false)
const pending = computed(() => analysis.value?.status === 0)
let timer
let remaining = 20
let version = 0
let alive = true

async function sync(showLoading = true) {
  clearTimeout(timer)
  const current = ++version
  loading.value = showLoading
  error.value = ''
  startFailed.value = false
  try {
    const result = await readAnalysis(props.questionId)
    if (!alive || current !== version) return
    analysis.value = result
    if (pending.value && remaining > 0) {
      remaining -= 1
      timer = setTimeout(() => sync(false), 3000)
    }
  } catch (cause) {
    if (alive && current === version) error.value = errorMessage(cause)
  } finally {
    if (alive && current === version) loading.value = false
  }
}

function refresh() {
  remaining = 20
  return sync()
}

async function analyze() {
  if (starting.value) return
  starting.value = true
  startFailed.value = false
  error.value = ''
  emit('attempt')
  try {
    await startAnalysis(props.questionId)
    if (alive) await refresh()
  } catch (cause) {
    error.value = errorMessage(cause)
    startFailed.value = true
  } finally {
    starting.value = false
  }
}

function retry() {
  return startFailed.value ? analyze() : refresh()
}

onMounted(async () => {
  await sync()
  if (alive && props.autoStart && !analysis.value && !error.value) await analyze()
})
onBeforeUnmount(() => {
  alive = false
  clearTimeout(timer)
})
</script>

<template>
  <view class="card">
    <text class="heading">原题 AI 解析</text>
    <LoadState v-if="loading || error || starting" :loading="loading || starting" :error="error" @retry="retry" />
    <view v-else-if="analysis?.status === 1">
      <view v-if="analysis.errorCause">
        <text class="label">错因</text>
        <QuestionText :content="analysis.errorCause" />
      </view>
      <QuestionText v-if="analysis.analysis" :content="analysis.analysis" />
      <text v-else class="muted">暂无解题步骤</text>
    </view>
    <view v-else>
      <text class="copy muted">{{ pending ? 'AI 正在处理，可稍后刷新。' : analysis?.status === 2 ? (analysis.analysis || 'AI 解析失败，可稍后重试。') : '这道错题暂无 AI 解析。' }}</text>
      <button v-if="allowStart && !pending" class="action" :loading="starting" :disabled="starting" @tap="analyze">
        {{ analysis?.status === 2 ? '重新解析' : '获取 AI 解析' }}
      </button>
      <button v-else class="action" @tap="refresh">刷新解析</button>
    </view>
  </view>
</template>
