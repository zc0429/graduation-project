<script setup>
import { computed } from 'vue'
import { onPullDownRefresh, onShow } from '@dcloudio/uni-app'
import { dueReviews, profile, weeklyReport } from '../../api/student.js'
import LoadState from '../../components/LoadState.vue'
import { useLoad } from '../../composables/use-load.js'
import { chinaDate } from '../../utils/date.js'

const { data, loading, error, load } = useLoad(async () => {
  const [, report, plans] = await Promise.all([profile(), weeklyReport(), dueReviews()])
  const today = chinaDate()
  return {
    total: report.totalQuestionCount,
    due: plans.length,
    practiced: report.dailyPractices.find((item) => item.date === today)?.count ?? 0,
  }
})
const empty = computed(() => data.value && Object.values(data.value).every((count) => count === 0))
onShow(load)
onPullDownRefresh(async () => {
  await load()
  uni.stopPullDownRefresh()
})
</script>

<template>
  <view class="screen">
    <LoadState :loading="loading" :error="error" :empty="!data" @retry="load">
      <view class="stats">
        <view class="card stat"><text class="value">{{ data.total }}</text><text class="muted">错题总数</text></view>
        <view class="card stat"><text class="value">{{ data.due }}</text><text class="muted">待复习</text></view>
        <view class="card stat"><text class="value">{{ data.practiced }}</text><text class="muted">今日练习</text></view>
      </view>
      <view v-if="empty" class="card muted">还没有学习记录，可以先录入一道错题。</view>
    </LoadState>
    <navigator class="action-link primary" url="/pages/create/index">录入错题</navigator>
    <navigator class="action-link" url="/pages/questions/index" open-type="switchTab">查看错题本</navigator>
    <navigator class="action-link" url="/pages/review/index" open-type="switchTab">开始复习</navigator>
  </view>
</template>

<style scoped>
.stats { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12rpx; }
.stat { padding: 20rpx 10rpx; text-align: center; overflow-wrap: anywhere; }
.value { display: block; font-size: 42rpx; font-weight: 700; color: #155c50; }
</style>
