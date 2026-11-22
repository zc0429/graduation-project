<script setup>
import { ref } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import { listSubjects, question } from '../../api/student.js'
import AnalysisPanel from '../../components/AnalysisPanel.vue'
import LoadState from '../../components/LoadState.vue'
import QuestionImage from '../../components/QuestionImage.vue'
import QuestionText from '../../components/QuestionText.vue'
import { useLoad } from '../../composables/use-load.js'

const id = ref(0)
const analyzeNew = ref(false)
const { data, loading, error, load } = useLoad(async () => {
  if (!Number.isSafeInteger(id.value) || id.value < 1) throw new Error('缺少有效的错题编号')
  const [item, subjects] = await Promise.all([question(id.value), listSubjects()])
  return { item, subject: subjects.find((subject) => subject.id === item.subjectId)?.name || '未标注科目' }
})

onLoad((query) => {
  id.value = Number(query.id)
  analyzeNew.value = query.analyze === '1'
})
onShow(load)
</script>

<template>
  <view class="screen">
    <LoadState :loading="loading" :error="error" :empty="!data" empty-text="暂无错题详情" @retry="load">
      <view class="card">
        <view class="meta muted"><text>{{ data.subject }}</text><text>掌握度 {{ data.item.mastery }}%</text></view>
        <text class="heading">原题</text>
        <QuestionText :content="data.item.stem" />
        <QuestionImage v-if="data.item.imageUrl" :image-url="data.item.imageUrl" />
        <text class="label">已录入的答案</text>
        <QuestionText :content="data.item.answer || '暂无答案'" />
        <text v-if="data.item.source" class="label">来源 · {{ data.item.source }}</text>
      </view>
      <navigator class="action-link primary" :url="'/pages/practice/index?id=' + id">开始练习</navigator>
      <navigator class="action-link knowledge-link" :url="'/pages/knowledge/index?id=' + id">学习相关知识</navigator>
      <AnalysisPanel :question-id="id" allow-start :auto-start="analyzeNew" @attempt="analyzeNew = false" />
    </LoadState>
  </view>
</template>

<style scoped>
.knowledge-link { margin-bottom: 20rpx; }
</style>
