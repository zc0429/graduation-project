<script setup>
import { computed, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { listSubjects, recognizeQuestion, saveQuestion } from '../../api/student.js'
import { errorMessage } from '../../api/request.js'
import LoadState from '../../components/LoadState.vue'
import { useLoad } from '../../composables/use-load.js'
import { recognitionImage } from '../../utils/images.js'

const { data: subjects, loading, error, load } = useLoad(listSubjects)
const subjectId = ref(null)
const selected = computed(() => subjects.value?.findIndex((item) => item.id === subjectId.value) ?? -1)
const stem = ref('')
const answer = ref('')
const source = ref('')
const filePath = ref('')
const imageBase64 = ref('')
const candidate = ref(null)
const recognizing = ref(false)
const imageError = ref('')
const saving = ref(false)
const savedId = ref(null)
const saveError = ref('')

onShow(() => { if (!subjects.value) load() })

function changeSubject(event) {
  subjectId.value = subjects.value[Number(event.detail.value)].id
}

function clearImage() {
  filePath.value = ''
  imageBase64.value = ''
  candidate.value = null
  imageError.value = ''
}

async function recognize() {
  if (!imageBase64.value || recognizing.value) return
  recognizing.value = true
  imageError.value = ''
  try {
    const result = await recognizeQuestion(imageBase64.value)
    if (!result?.stem?.trim()) throw new Error('图片中未识别到题干，可以重新选图或手动录入')
    candidate.value = result
  } catch (cause) {
    imageError.value = errorMessage(cause)
  } finally {
    recognizing.value = false
  }
}

function chooseImage() {
  uni.chooseImage({
    count: 1,
    sourceType: ['album'],
    sizeType: ['compressed'],
    async success({ tempFiles }) {
      clearImage()
      const file = tempFiles[0]
      if (!file) return
      recognizing.value = true
      try {
        imageBase64.value = await recognitionImage(file)
        filePath.value = file.path
      } catch (cause) {
        imageError.value = errorMessage(cause)
      } finally {
        recognizing.value = false
      }
      await recognize()
    },
    fail(cause) {
      if (!/cancel/i.test(cause?.errMsg || '')) imageError.value = '无法打开相册，请重试或手动录入'
    },
  })
}

function applyCandidate() {
  const result = candidate.value
  if (subjects.value.some((item) => item.id === result.subjectId)) subjectId.value = result.subjectId
  stem.value = result.stem
  if (result.studentAnswer) answer.value = result.studentAnswer
  if (result.source) source.value = result.source
  candidate.value = null
}

function openSavedQuestion() {
  uni.redirectTo({
    url: `/pages/detail/index?id=${savedId.value}&analyze=1`,
    fail: () => { saveError.value = '错题已保存，详情暂时打不开，请重试' },
  })
}

async function submit() {
  if (saving.value || recognizing.value || candidate.value) return
  if (savedId.value) {
    openSavedQuestion()
    return
  }
  if (selected.value < 0 || !stem.value.trim()) {
    saveError.value = '请选择科目并填写题干'
    return
  }
  saving.value = true
  saveError.value = ''
  try {
    savedId.value = await saveQuestion({
      subjectId: subjectId.value,
      stem: stem.value.trim(),
      answer: answer.value.trim() || undefined,
      source: source.value.trim() || undefined,
      imageBase64: imageBase64.value || undefined,
    })
    openSavedQuestion()
  } catch (cause) {
    saveError.value = errorMessage(cause)
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <view class="screen">
    <LoadState :loading="loading" :error="error" :empty="!subjects?.length" empty-text="暂无可用科目，请联系管理员" @retry="load">
      <view class="card">
        <text class="heading">图片辅助录入</text>
        <button class="action" :loading="recognizing" :disabled="recognizing || saving || !!savedId" @tap="chooseImage">从相册选图</button>
        <image v-if="filePath" class="preview" :src="filePath" mode="widthFix" />
        <button v-if="filePath" class="action" :disabled="recognizing || saving || !!savedId" @tap="clearImage">移除图片</button>
        <text v-if="recognizing" class="muted">正在读取或识别图片…</text>
        <view v-if="imageError">
          <text class="copy error">{{ imageError }}</text>
          <button v-if="imageBase64" class="action" :disabled="saving || !!savedId" @tap="recognize">重试识别</button>
        </view>
        <view v-if="candidate" class="candidate">
          <text class="heading">识别候选</text>
          <text v-if="candidate.subjectName" class="copy muted">科目 · {{ candidate.subjectName }}</text>
          <text class="copy">{{ candidate.stem }}</text>
          <text v-if="candidate.studentAnswer" class="copy muted">作答 · {{ candidate.studentAnswer }}</text>
          <text v-if="candidate.source" class="copy muted">来源 · {{ candidate.source }}</text>
          <button class="action" @tap="applyCandidate">填入表单并核对</button>
          <button class="action" @tap="candidate = null">忽略候选</button>
        </view>
      </view>
      <view class="card">
        <text class="heading">错题内容</text>
        <text class="label">科目</text>
        <picker :range="subjects" range-key="name" :value="selected < 0 ? 0 : selected" :disabled="saving || !!savedId" @change="changeSubject">
          <view class="field">{{ selected < 0 ? '请选择科目' : subjects[selected].name }} ▾</view>
        </picker>
        <text class="label">题干</text>
        <textarea v-model="stem" class="field" maxlength="2000" :disabled="saving || !!savedId" placeholder="输入题干" />
        <text class="label">答案或原作答</text>
        <textarea v-model="answer" class="field" maxlength="2000" :disabled="saving || !!savedId" placeholder="输入答案（选填）" />
        <text class="label">来源</text>
        <input v-model="source" class="field" maxlength="100" :disabled="saving || !!savedId" placeholder="输入试卷或教材名称（选填）" />
        <text v-if="saveError" class="copy error">{{ saveError }}</text>
        <button class="action primary" :loading="saving" :disabled="saving || recognizing || !!candidate" @tap="submit">
          {{ savedId ? '打开已保存的错题' : saveError ? '重新提交' : '确认保存' }}
        </button>
      </view>
    </LoadState>
  </view>
</template>

<style scoped>
.candidate { margin-top: 24rpx; padding-top: 20rpx; border-top: 1px solid #e0e7eb; }
</style>
