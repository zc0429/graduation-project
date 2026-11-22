<script setup>
import { computed, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { dueReviews, finishReview, nextPractice, question, savePractice } from '../../api/student.js'
import { errorMessage } from '../../api/request.js'
import AnalysisPanel from '../../components/AnalysisPanel.vue'
import LoadState from '../../components/LoadState.vue'
import QuestionImage from '../../components/QuestionImage.vue'
import QuestionText from '../../components/QuestionText.vue'
import { useLoad } from '../../composables/use-load.js'

const id = ref(0)
const reviewId = ref(null)
const answer = ref('')
const checking = ref(false)
const grade = ref(null)
const saving = ref(false)
const recordId = ref(null)
const reviewFinished = ref(false)
const submitError = ref('')
const { data, loading, error, load } = useLoad(async () => {
  if (!Number.isSafeInteger(id.value) || id.value < 1) throw new Error('缺少有效的错题编号')
  if (reviewId.value !== null) {
    const plans = await dueReviews()
    if (!plans.some((plan) => plan.id === reviewId.value && plan.questionId === id.value)) {
      throw new Error('这项复习计划已完成或不再待复习')
    }
    const original = await question(id.value)
    return { ...original, questionId: id.value, source: 'original' }
  }
  const target = await nextPractice(id.value)
  if (target?.source === 'original') {
    const original = await question(id.value)
    return { ...target, imageUrl: original.imageUrl }
  }
  return target
})
const label = computed(() => {
  if (reviewId.value !== null) return '复习原题'
  return data.value?.source === 'original' ? '未练原题' : '变式题'
})

onLoad((query) => {
  id.value = Number(query.id)
  reviewId.value = query.reviewId ? Number(query.reviewId) : null
  if (reviewId.value !== null) uni.setNavigationBarTitle({ title: '复习作答' })
  load()
})

function changeGrade(event) {
  grade.value = Number(event.detail.value)
  submitError.value = ''
}

async function submit() {
  if (saving.value || !data.value || reviewFinished.value) return
  if (grade.value !== 0 && grade.value !== 1) {
    submitError.value = '请核对答案后选择自评结果'
    return
  }
  saving.value = true
  submitError.value = ''
  try {
    if (recordId.value === null) {
      const target = data.value.variantId == null
        ? { questionId: data.value.questionId }
        : { variantId: data.value.variantId }
      recordId.value = await savePractice({ ...target, userAnswer: answer.value.trim() || undefined, isCorrect: grade.value })
    }
    if (reviewId.value !== null) {
      try {
        await finishReview(reviewId.value)
      } catch (cause) {
        // The server may have completed the previous write before its response was lost.
        if (cause.code !== 400 || cause.message !== '该复习任务已完成') throw cause
      }
      reviewFinished.value = true
    }
  } catch (cause) {
    submitError.value = errorMessage(cause)
  } finally {
    saving.value = false
  }
}

function continuePractice() {
  answer.value = ''
  grade.value = null
  checking.value = false
  recordId.value = null
  submitError.value = ''
  load()
}
</script>

<template>
  <view class="screen">
    <LoadState
      :loading="loading"
      :error="error"
      :empty="!data"
      loading-text="正在获取题目…"
      empty-text="暂时没有可用题目"
      @retry="load"
    >
      <view class="card">
        <text class="heading">{{ label }}</text>
        <QuestionText :content="data.stem" />
        <QuestionImage v-if="data.imageUrl" :image-url="data.imageUrl" />
        <text class="label">我的作答</text>
        <textarea v-model="answer" class="field" maxlength="2000" :disabled="checking || saving" placeholder="输入本次作答" />
        <button v-if="!checking" class="action primary" @tap="checking = true">核对参考答案</button>
      </view>

      <view v-if="checking" class="card">
        <text class="heading">{{ data.variantId == null ? '原题录入答案' : '变式题参考答案' }}</text>
        <QuestionText :content="data.answer || '暂无参考答案，可结合原题解析自评。'" />
        <template v-if="recordId === null">
          <text class="label">作答自评</text>
          <radio-group class="choices" @change="changeGrade">
            <label><radio value="1" :checked="grade === 1" :disabled="saving" color="#155c50" />答对了</label>
            <label><radio value="0" :checked="grade === 0" :disabled="saving" color="#155c50" />仍然答错</label>
          </radio-group>
          <button class="action" :disabled="saving" @tap="checking = false; grade = null; submitError = ''">返回修改作答</button>
        </template>
        <text v-else class="label">已记录自评 · {{ grade === 1 ? '答对了' : '仍然答错' }}</text>
        <text v-if="submitError" class="copy error">{{ submitError }}</text>
        <button
          v-if="recordId === null || (reviewId !== null && !reviewFinished)"
          class="action primary"
          :loading="saving"
          :disabled="saving"
          @tap="submit"
        >
          {{ recordId !== null ? '重试完成复习' : submitError ? '重新提交作答' : '提交作答' }}
        </button>
        <button v-else-if="reviewId === null" class="action primary" @tap="continuePractice">继续下一题</button>
        <view v-else>
          <text class="label">复习计划已完成</text>
          <navigator class="action-link primary" url="/pages/review/index" open-type="switchTab">返回复习计划</navigator>
        </view>
      </view>

      <AnalysisPanel v-if="checking" :question-id="id" />
    </LoadState>
  </view>
</template>

<style scoped>
.choices { display: flex; flex-wrap: wrap; gap: 16rpx 24rpx; }
.choices label { display: flex; align-items: center; min-height: 62rpx; }
</style>
