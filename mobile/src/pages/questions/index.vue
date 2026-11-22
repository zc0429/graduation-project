<script setup>
import { computed, ref } from 'vue'
import { onPullDownRefresh, onReachBottom, onShow } from '@dcloudio/uni-app'
import { listSubjects, questions } from '../../api/student.js'
import { errorMessage, requireSession } from '../../api/request.js'
import LoadState from '../../components/LoadState.vue'
import QuestionText from '../../components/QuestionText.vue'

const pageSize = 15
const subjectId = ref(null)
const subjects = ref([])
const items = ref([])
const page = ref(0)
const total = ref(0)
const loading = ref(true)
const error = ref('')
const moreError = ref('')
const loadingMore = ref(false)
let version = 0
const options = computed(() => [{ id: null, name: '全部科目' }, ...subjects.value])
const selected = computed(() => Math.max(0, options.value.findIndex((item) => item.id === subjectId.value)))

function subjectName(id) {
  return subjects.value.find((item) => item.id === id)?.name || '未标注科目'
}

async function load() {
  if (!requireSession()) return
  const current = ++version
  loading.value = true
  loadingMore.value = false
  error.value = ''
  moreError.value = ''
  try {
    const available = await listSubjects()
    if (current !== version) return
    subjects.value = available
    subjectId.value = options.value[selected.value].id
    const result = await questions(1, pageSize, subjectId.value)
    if (current !== version) return
    items.value = result.records
    page.value = result.current
    total.value = result.total
  } catch (cause) {
    if (current === version) error.value = errorMessage(cause)
  } finally {
    if (current === version) loading.value = false
  }
}

function changeSubject(event) {
  subjectId.value = options.value[Number(event.detail.value)].id
  return load()
}

async function loadMore() {
  if (loading.value || loadingMore.value || error.value || page.value * pageSize >= total.value) return
  const current = version
  loadingMore.value = true
  moreError.value = ''
  try {
    const next = await questions(page.value + 1, pageSize, subjectId.value)
    if (current !== version) return
    const existingIds = new Set(items.value.map((item) => item.id))
    items.value = [...items.value, ...next.records.filter((item) => !existingIds.has(item.id))]
    page.value = next.current
    total.value = next.total
  } catch (cause) {
    if (current === version) moreError.value = errorMessage(cause)
  } finally {
    if (current === version) loadingMore.value = false
  }
}

onShow(load)
onReachBottom(loadMore)
onPullDownRefresh(async () => {
  await load()
  uni.stopPullDownRefresh()
})
</script>

<template>
  <view class="screen">
    <view class="card">
      <picker :range="options" range-key="name" :value="selected" :disabled="loading" @change="changeSubject">
        <view class="field">科目 · {{ options[selected].name }} ▾</view>
      </picker>
      <navigator class="action-link primary" url="/pages/create/index">录入错题</navigator>
    </view>
    <LoadState :loading="loading" :error="error" :empty="!items.length" empty-text="当前科目暂无错题" @retry="load">
      <navigator v-for="item in items" :key="item.id" class="card link-card" :url="'/pages/detail/index?id=' + item.id">
        <view class="meta muted"><text>{{ subjectName(item.subjectId) }}</text><text>{{ item.createTime?.slice(0, 10) }}</text></view>
        <view class="excerpt"><QuestionText :content="item.stem" /></view>
      </navigator>
      <LoadState v-if="moreError" :error="moreError" @retry="loadMore" />
      <button v-else-if="page * pageSize < total" class="action" :loading="loadingMore" :disabled="loadingMore" @tap="loadMore">加载更多</button>
    </LoadState>
  </view>
</template>

<style scoped>
.excerpt { max-height: 285rpx; overflow: hidden; }
</style>
