<script setup>
import { onPullDownRefresh, onShow } from '@dcloudio/uni-app'
import { dueReviews, listSubjects } from '../../api/student.js'
import LoadState from '../../components/LoadState.vue'
import { useLoad } from '../../composables/use-load.js'
import { chinaDate } from '../../utils/date.js'

const { data, loading, error, load } = useLoad(async () => {
  const [plans, subjects] = await Promise.all([dueReviews(), listSubjects()])
  const today = chinaDate()
  return plans.map((plan) => ({
    ...plan,
    overdue: plan.status === 2 || plan.planDate < today,
    subject: subjects.find((subject) => subject.id === plan.subjectId)?.name || '未标注科目',
  }))
})
onShow(load)
onPullDownRefresh(async () => {
  await load()
  uni.stopPullDownRefresh()
})
</script>

<template>
  <view class="screen">
    <LoadState :loading="loading" :error="error" :empty="!data?.length" empty-text="今天没有到期或逾期的复习任务" @retry="load">
      <view v-for="plan in data" :key="plan.id" class="card">
        <view class="meta muted">
          <text>{{ plan.overdue ? '已逾期' : '今日到期' }}</text>
          <text>{{ plan.subject }}</text>
          <text>第 {{ plan.reviewStage }} 轮</text>
        </view>
        <text class="heading">{{ plan.stemSummary || '错题 #' + plan.questionId }}</text>
        <text class="muted">{{ plan.planDate }}</text>
        <navigator class="action-link" :url="'/pages/practice/index?id=' + plan.questionId + '&reviewId=' + plan.id">去复习</navigator>
      </view>
    </LoadState>
  </view>
</template>
