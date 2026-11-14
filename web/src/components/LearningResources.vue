<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from 'vue'
import { learningApi, practiceApi, type KnowledgeResource, type PracticeResource } from '@/api/learning'
import QuestionContent from '@/components/QuestionContent.vue'

const props = defineProps<{ questionId: number; revision: string }>()
const emit = defineEmits<{ practiced: [] }>()
const knowledge = ref<KnowledgeResource>()
const target = ref<PracticeResource>()
const knowledgeLoading = ref(false)
const practiceLoading = ref(false)
const saving = ref(false)
const knowledgeError = ref('')
const practiceError = ref('')
const answer = ref('')
const correct = ref<0 | 1>()
const duration = ref<number>()
const completed = ref(false)
let version = 0
function reset() {
  version += 1
  knowledge.value = undefined; target.value = undefined
  knowledgeLoading.value = false; practiceLoading.value = false; saving.value = false
  knowledgeError.value = ''; practiceError.value = ''
  resetAnswer()
}
function resetAnswer() { answer.value = ''; correct.value = undefined; duration.value = undefined; completed.value = false }
watch(() => [props.questionId, props.revision], reset)
onBeforeUnmount(() => { version += 1 })
async function readKnowledge() {
  if (knowledgeLoading.value) return
  const requestVersion = version
  knowledgeLoading.value = true; knowledgeError.value = ''
  try {
    const result = await learningApi.knowledge(props.questionId)
    if (version === requestVersion) knowledge.value = result
  } catch (error) {
    if (version === requestVersion) knowledgeError.value = error instanceof Error ? error.message : '知识内容暂时无法获取，可查看原题解析后重试。'
  } finally { if (version === requestVersion) knowledgeLoading.value = false }
}
async function nextPractice() {
  if (practiceLoading.value || saving.value) return
  const requestVersion = version
  practiceLoading.value = true; practiceError.value = ''
  try {
    const result = await learningApi.next(props.questionId)
    if (version !== requestVersion) return
    target.value = result; resetAnswer()
  } catch (error) {
    if (version === requestVersion) practiceError.value = error instanceof Error ? error.message : '暂时无法获取新题，可重做原题或已保存的变式题。'
  } finally { if (version === requestVersion) practiceLoading.value = false }
}
async function submit() {
  if (!target.value || saving.value || completed.value) return
  if (correct.value === undefined) { practiceError.value = '请根据实际作答选择结果自评。'; return }
  const requestVersion = version
  const selected = target.value
  saving.value = true; practiceError.value = ''
  try {
    await practiceApi.submit({
      ...(selected.variantId ? { variantId: selected.variantId } : { questionId: selected.questionId! }),
      userAnswer: answer.value.trim() || undefined, isCorrect: correct.value, duration: duration.value,
    })
    if (version !== requestVersion) return
    completed.value = true; emit('practiced')
  } catch (error) {
    if (version === requestVersion) practiceError.value = error instanceof Error ? error.message : '练习记录未保存，请重试。'
  } finally { if (version === requestVersion) saving.value = false }
}
</script>

<template>
  <section class="learning-resources" aria-label="知识学习与持续练习">
    <p class="resource-intro">优先使用本人已有内容和未练题；缺少资源时再生成。已练题仍可主动重做。</p>
    <section class="resource-panel">
      <div class="resource-heading"><h3>学习知识</h3><el-button :loading="knowledgeLoading" @click="readKnowledge">{{ knowledge ? '再次查看知识内容' : '获取知识内容' }}</el-button></div>
      <p v-if="knowledgeLoading" role="status">正在查询已有内容，缺少时生成并保存，请稍候。</p>
      <p v-if="knowledgeError" class="resource-error" role="alert">{{ knowledgeError }}</p>
      <template v-if="knowledge"><p class="resource-source">{{ knowledge.reused ? '已复用保存的知识内容' : '知识内容已生成并保存' }}</p><div class="knowledge-text">{{ knowledge.content }}</div></template>
    </section>
    <section class="resource-panel">
      <div class="resource-heading"><h3>做题练习</h3><el-button type="primary" :loading="practiceLoading" :disabled="saving" @click="nextPractice">{{ target ? '继续练习' : '开始练习' }}</el-button></div>
      <p v-if="practiceLoading" role="status">正在查询未练题；题目耗尽时生成新题，请稍候。</p>
      <p v-if="practiceError" class="resource-error" role="alert">{{ practiceError }} 原题与已保存的变式题仍可在其他页签中重做。</p>
      <div v-if="target" class="practice-resource">
        <p class="resource-source">{{ target.source === 'original' ? '优先练习本人原题' : target.source === 'existing' ? '复用本人已有未练题' : '新题已生成并保存' }}</p>
        <QuestionContent :content="target.stem" />
        <details><summary>查看参考答案</summary><p class="knowledge-text">{{ target.answer || '暂无参考答案，请结合解析自评。' }}</p></details>
        <el-form v-if="!completed" label-position="top" @submit.prevent="submit">
          <el-form-item label="本题作答"><el-input v-model="answer" type="textarea" :rows="3" maxlength="2000" /></el-form-item>
          <el-form-item label="本题结果自评" required><el-radio-group v-model="correct"><el-radio-button :value="1">答对了</el-radio-button><el-radio-button :value="0">仍然答错</el-radio-button></el-radio-group></el-form-item>
          <el-form-item label="本题用时（秒，可选）"><el-input-number v-model="duration" :min="0" :max="7200" /></el-form-item>
          <el-button type="primary" :loading="saving" @click="submit">保存本次练习</el-button>
        </el-form>
        <div v-else class="practice-completed"><p role="status">本次练习已记录。继续练习将重新查询未练题。</p><el-button @click="resetAnswer">重新练习本题</el-button></div>
      </div>
    </section>
  </section>
</template>

<style scoped>
.learning-resources{display:grid;gap:18px}.resource-intro{margin:0;color:var(--ink-soft);line-height:1.8}.resource-panel{padding:18px;border:1px solid var(--line);border-radius:10px;background:var(--paper-bright)}.resource-heading{display:flex;align-items:center;justify-content:space-between;gap:12px}.resource-heading h3{margin:0;font-size:16px;color:var(--navy)}.resource-source{font-size:12px;color:var(--jade-dark)}.knowledge-text{white-space:pre-wrap;overflow-wrap:anywhere;font-size:14px;line-height:1.9}.resource-error{color:var(--cinnabar);line-height:1.7}.practice-resource details{margin:15px 0}.practice-resource summary{cursor:pointer;color:var(--jade-dark)}.practice-completed{color:var(--jade-dark)}@media(max-width:600px){.resource-heading{align-items:flex-start;flex-direction:column}.resource-panel{padding:13px}}
</style>
