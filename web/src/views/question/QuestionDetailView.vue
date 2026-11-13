<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type UploadFile } from 'element-plus'
import { Delete, EditPen, MagicStick, Picture, Refresh, Timer, View } from '@element-plus/icons-vue'
import {
  kpApi,
  practiceApi,
  questionApi,
  recommendApi,
  subjectApi,
  variantApi,
  type KpNode,
  type PracticeTarget,
  type Question,
  type QuestionPayload,
  type Subject,
  type VariantQuestion,
} from '@/api'
import QuestionEditor from '@/components/QuestionEditor.vue'
import LearningResources from '@/components/LearningResources.vue'
import QuestionContent from '@/components/QuestionContent.vue'
import { questionHtml, questionText } from '@/utils/question-content'
import AsyncState from '@/components/AsyncState.vue'
import MasteryIndicator from '@/components/MasteryIndicator.vue'
import PageHeader from '@/components/PageHeader.vue'
import PaperPanel from '@/components/PaperPanel.vue'
import { useAiAnalysisPolling } from '@/composables/useAiAnalysisPolling'

const MAX_IMAGE_SIZE = 10 * 1024 * 1024
const ACCEPTED_IMAGE_TYPES = new Set(['image/png', 'image/jpeg', 'image/gif', 'image/webp'])

const route = useRoute()
const router = useRouter()
const questionId = computed(() => Number(route.params.id))
const question = ref<Question>()
const subjects = ref<Subject[]>([])
const knowledgeTree = ref<KpNode[]>([])
const variants = ref<VariantQuestion[]>([])
const similarQuestions = ref<Question[]>([])
const pageLoading = ref(true)
const pageError = ref('')
const variantLoading = ref(false)
const variantError = ref('')
const similarLoading = ref(false)
const similarError = ref('')
const similarLoaded = ref(false)
const generating = ref(false)
const deleting = ref(false)
const activeTab = ref('analysis')
const answerVisible = ref(false)

const editVisible = ref(false)
const editSaving = ref(false)
const editError = ref('')
const editForm = reactive({ subjectId: undefined as number | undefined, stem: '', answer: '', source: '' })
const editImageBase64 = ref('')
const editImagePreview = ref('')
const editImageName = ref('')
const editImageSize = ref(0)
const editImageReading = ref(false)
const editImageError = ref('')
const analysisStale = ref(false)
let editImageReadVersion = 0
let variantRequestVersion = 0
let similarRequestVersion = 0

const practiceVisible = ref(false)
const practiceSaving = ref(false)
const practiceError = ref('')
const practiceTitle = ref('')
const practiceForm = reactive({
  target: undefined as PracticeTarget | undefined,
  userAnswer: '',
  isCorrect: undefined as 0 | 1 | undefined,
  duration: undefined as number | undefined,
})

const polling = useAiAnalysisPolling(questionId, {
  onSuccess: async () => {
    analysisStale.value = false
    similarQuestions.value = []
    similarLoaded.value = false
    ElMessage.success('AI 智能解析已完成')
    await loadQuestion()
    if (activeTab.value === 'similar') await loadSimilar()
  },
})

const editImageSizeText = computed(() => {
  if (!editImageSize.value) return ''
  return editImageSize.value >= 1024 * 1024
    ? `${(editImageSize.value / 1024 / 1024).toFixed(1)} MB`
    : `${Math.ceil(editImageSize.value / 1024)} KB`
})

const referenceIds = computed<number[]>(() => {
  try {
    const parsed = JSON.parse(polling.analysis.value?.referenceIds || '[]')
    return Array.isArray(parsed) ? parsed.map(Number).filter((id) => Number.isSafeInteger(id) && id > 0) : []
  } catch {
    return []
  }
})

const analysisPartial = computed(() => polling.state.value === 'success' && (
  !polling.analysis.value?.analysis || !polling.analysis.value?.errorCause || !polling.analysis.value?.llmModel
))

function subjectName(id?: number) {
  return subjects.value.find((item) => item.id === id)?.name || '科目未识别'
}

function knowledgeName(id?: number) {
  if (!id) return '尚未归类'
  const queue = [...knowledgeTree.value]
  while (queue.length) {
    const node = queue.shift()!
    if (node.id === id) return node.name
    queue.push(...(node.children || []))
  }
  return '知识点未识别'
}

function difficultyText(value?: number) {
  return value ? `${value} / 5` : '待评估'
}

async function loadQuestion() {
  question.value = await questionApi.detail(questionId.value)
}

async function loadVariants() {
  const requestVersion = ++variantRequestVersion
  variantLoading.value = true
  variantError.value = ''
  try {
    const result = await variantApi.list(questionId.value)
    if (requestVersion !== variantRequestVersion) return
    variants.value = result
  } catch (error) {
    if (requestVersion !== variantRequestVersion) return
    variantError.value = error instanceof Error ? error.message : '变式题暂时无法加载。'
  } finally {
    if (requestVersion === variantRequestVersion) variantLoading.value = false
  }
}

async function loadSimilar() {
  if (analysisStale.value) return
  const requestVersion = ++similarRequestVersion
  similarLoading.value = true
  similarError.value = ''
  try {
    const result = await recommendApi.similar(questionId.value)
    if (requestVersion !== similarRequestVersion) return
    similarQuestions.value = result
    similarLoaded.value = true
  } catch (error) {
    if (requestVersion !== similarRequestVersion) return
    similarError.value = error instanceof Error ? error.message : '相似题暂时无法加载。'
  } finally {
    if (requestVersion === similarRequestVersion) similarLoading.value = false
  }
}

async function loadPage() {
  if (!Number.isSafeInteger(questionId.value) || questionId.value <= 0) {
    pageLoading.value = false
    pageError.value = '错题编号无效。'
    return
  }
  pageLoading.value = true
  pageError.value = ''
  answerVisible.value = false
  variants.value = []
  similarRequestVersion += 1
  similarQuestions.value = []
  similarLoading.value = false
  similarLoaded.value = false
  similarError.value = ''
  analysisStale.value = false
  polling.stop()
  try {
    if (!subjects.value.length) {
      const [subjectData, knowledgeData] = await Promise.all([subjectApi.list(), kpApi.tree()])
      subjects.value = subjectData
      knowledgeTree.value = knowledgeData
    }
    await loadQuestion()
    await Promise.allSettled([polling.sync(), loadVariants()])
    if (activeTab.value === 'similar' && !analysisStale.value) await loadSimilar()
  } catch (error) {
    pageError.value = error instanceof Error ? error.message : '错题详情暂时无法加载。'
  } finally {
    pageLoading.value = false
  }
}

async function triggerAnalysis() {
  try {
    await polling.trigger()
  } catch {
    // The composable exposes the normalized error for the inline state.
  }
}

async function retryAnalysisSync() {
  try {
    const result = await polling.sync()
    if (result?.status === 1) {
      analysisStale.value = false
      await loadQuestion()
    }
  } catch {
    // The polling composable exposes the normalized error for the inline state.
  }
}

async function generateVariants() {
  if (generating.value) return
  generating.value = true
  variantError.value = ''
  try {
    const generated = await variantApi.generate(questionId.value)
    ElMessage.success(`已取得 ${generated.length} 道可用变式题`)
    await loadVariants()
  } catch (error) {
    variantError.value = error instanceof Error ? error.message : '变式题生成失败，请稍后重试。'
  } finally {
    generating.value = false
  }
}

async function loadPageAfterPractice() { await Promise.allSettled([loadQuestion(), loadVariants()]) }

function rejectEditImage(message: string) {
  editImageError.value = message
  ElMessage.warning(message)
}

function clearEditImage() {
  editImageReadVersion += 1
  editImageBase64.value = ''
  editImagePreview.value = ''
  editImageName.value = ''
  editImageSize.value = 0
  editImageReading.value = false
  editImageError.value = ''
}

function onEditImageChange(file: UploadFile) {
  const raw = file.raw
  if (!raw) return
  editImageError.value = ''

  if (!ACCEPTED_IMAGE_TYPES.has(raw.type)) {
    rejectEditImage('仅支持 PNG、JPG、GIF 或 WebP 图片')
    return
  }
  if (raw.size > MAX_IMAGE_SIZE) {
    rejectEditImage('图片大小不能超过 10MB')
    return
  }

  const currentRead = ++editImageReadVersion
  const reader = new FileReader()
  editImageReading.value = true
  reader.onload = () => {
    if (currentRead !== editImageReadVersion || typeof reader.result !== 'string') return
    editImageBase64.value = reader.result
    editImagePreview.value = reader.result
    editImageName.value = raw.name
    editImageSize.value = raw.size
  }
  reader.onerror = () => {
    if (currentRead !== editImageReadVersion) return
    rejectEditImage('图片读取失败，请重新选择')
  }
  reader.onloadend = () => {
    if (currentRead === editImageReadVersion) editImageReading.value = false
  }
  reader.readAsDataURL(raw)
}

function openEdit() {
  if (!question.value) return
  editForm.subjectId = question.value.subjectId
  editForm.stem = question.value.stem
  editForm.answer = question.value.answer || ''
  editForm.source = question.value.source || ''
  editError.value = ''
  clearEditImage()
  editVisible.value = true
}

async function saveEdit() {
  if (!editForm.subjectId || !questionText(editForm.stem) || questionText(editForm.stem).length > 2000) {
    editError.value = '请选择科目，并填写 1—2000 字题干。'
    return
  }
  if (editImageReading.value) {
    editError.value = '图片仍在读取，请稍候再保存。'
    return
  }
  editSaving.value = true
  editError.value = ''
  const payload: QuestionPayload = {
    subjectId: editForm.subjectId,
    stem: questionHtml(editForm.stem),
    answer: editForm.answer.trim(),
    source: editForm.source.trim(),
    imageBase64: editImageBase64.value || undefined,
  }
  try {
    await questionApi.update(questionId.value, payload)
    const coreChanged = payload.subjectId !== question.value?.subjectId
      || payload.stem !== questionHtml(question.value?.stem || '')
      || payload.answer !== (question.value?.answer || '') || Boolean(payload.imageBase64)
    if (coreChanged) {
      variantRequestVersion += 1
      variantLoading.value = false
      polling.stop()
      polling.analysis.value = null
      analysisStale.value = true
      variants.value = []
      variantError.value = ''
      similarRequestVersion += 1
      similarQuestions.value = []
      similarLoading.value = false
      similarLoaded.value = false
      similarError.value = ''
    }
    editVisible.value = false
    try {
      await loadQuestion()
      ElMessage.success(coreChanged ? '错题内容已更新，可重新获取解析与学习资源' : '错题来源已更新')
    } catch {
      ElMessage.warning('错题已保存，但最新内容暂未重新加载，请刷新页面')
    }
  } catch (error) {
    editError.value = error instanceof Error ? error.message : '错题保存失败。'
  } finally {
    editSaving.value = false
  }
}

async function removeQuestion() {
  try {
    await ElMessageBox.confirm('删除后，相关 AI 解析、变式题与复习计划也会被清理。确认继续吗？', '删除错题', {
      confirmButtonText: '确认删除', cancelButtonText: '保留错题', type: 'warning',
    })
  } catch {
    return
  }
  deleting.value = true
  try {
    await questionApi.remove(questionId.value)
    ElMessage.success('错题已删除')
    await router.replace('/question/list')
  } finally {
    deleting.value = false
  }
}

function openPractice(target: PracticeTarget, title: string) {
  practiceForm.target = target
  practiceForm.userAnswer = ''
  practiceForm.isCorrect = undefined
  practiceForm.duration = undefined
  practiceError.value = ''
  practiceTitle.value = title
  practiceVisible.value = true
}

async function submitPractice() {
  if (!practiceForm.target) return
  const isCorrect = practiceForm.isCorrect
  if (isCorrect === undefined) {
    practiceError.value = '请根据本次实际作答选择“答对了”或“仍然答错”。'
    return
  }
  practiceSaving.value = true
  practiceError.value = ''
  try {
    await practiceApi.submit({
      ...practiceForm.target,
      userAnswer: practiceForm.userAnswer.trim() || undefined,
      isCorrect,
      duration: practiceForm.duration,
    })
    practiceVisible.value = false
    await Promise.all([loadQuestion(), loadVariants()])
    ElMessage.success('练习结果已记录，掌握度已更新')
  } catch (error) {
    practiceError.value = error instanceof Error ? error.message : '练习记录提交失败。'
  } finally {
    practiceSaving.value = false
  }
}

watch(questionId, loadPage)
watch(activeTab, (tab) => {
  if (tab === 'similar' && !analysisStale.value && !similarLoaded.value && !similarLoading.value) void loadSimilar()
})
onMounted(loadPage)
</script>

<template>
  <div class="question-detail-page">
    <PageHeader eyebrow="错题详情与 AI 智能解析" :title="question ? `错题 #${question.id}` : '错题详情'" description="查看原题、修订内容，并沿着解析—变式—练习完成一次学习闭环。">
      <template v-if="question" #actions>
        <el-button :icon="EditPen" @click="openEdit">编辑错题</el-button>
        <el-button type="danger" plain :icon="Delete" :loading="deleting" @click="removeQuestion">删除</el-button>
      </template>
    </PageHeader>

    <AsyncState v-if="pageLoading" status="loading" title="正在打开错题详情" />
    <AsyncState v-else-if="pageError || !question" status="error" title="错题详情加载失败" :description="pageError" @retry="loadPage" />

    <template v-else>
      <section class="question-overview">
        <PaperPanel variant="lined" class="question-sheet">
          <div class="question-tags"><span>{{ subjectName(question.subjectId) }}</span><span class="jade">{{ knowledgeName(question.knowledgePointId) }}</span><span class="amber">难度 {{ difficultyText(question.difficulty) }}</span></div>
          <span class="correction-mark" aria-hidden="true">错</span>
          <QuestionContent class="stem" :content="question.stem" />
          <el-image v-if="question.imageUrl" :src="question.imageUrl" alt="题目图片" fit="contain" class="question-image" :preview-src-list="[question.imageUrl]" />
          <p class="question-meta">来源：{{ question.source || '未标注' }}　·　录入：{{ question.createTime }}　·　最近更新：{{ question.updateTime }}</p>
          <button class="answer-toggle" type="button" aria-controls="question-answer" :aria-expanded="answerVisible" @click="answerVisible = !answerVisible"><el-icon><View /></el-icon>{{ answerVisible ? '收起正确答案' : '查看正确答案' }}</button>
          <p v-if="answerVisible" id="question-answer" class="answer-block">{{ question.answer || '这道题尚未填写答案。' }}</p>
        </PaperPanel>

        <PaperPanel class="mastery-side">
          <h2>掌握度笔记</h2>
          <MasteryIndicator :value="question.mastery" />
          <dl><div><dt>当前难度</dt><dd>{{ difficultyText(question.difficulty) }}</dd></div><div><dt>下一动作</dt><dd>重做并自评</dd></div></dl>
          <el-button class="jade-action" @click="openPractice({ questionId: question.id }, '重做这道错题')">开始重做</el-button>
          <el-button text :icon="Timer" @click="router.push('/practice/history')">查看练习历史</el-button>
        </PaperPanel>
      </section>

      <PaperPanel :padded="false" class="analysis-workbench">
        <div v-if="analysisStale" class="derived-stale-note" role="status">
          <span aria-hidden="true">!</span>
          <div>
            <strong>题目内容已经修改</strong>
            <p>旧的 AI 解析、RAG 参考与变式题可能不再对应当前题目，系统已隐藏过期内容。</p>
          </div>
        </div>
        <el-tabs v-model="activeTab" class="analysis-tabs">
          <el-tab-pane label="AI 智能解析" name="analysis">
            <div class="tab-content" :aria-busy="polling.isPolling.value">
              <div class="analysis-topline"><div><span>解析状态</span><strong>{{ polling.isPolling.value ? '处理中' : analysisStale ? '结果已过期' : polling.state.value === 'success' ? '已完成' : polling.state.value === 'failed' ? '失败' : polling.state.value === 'timeout' ? '等待超时' : polling.state.value === 'error' ? '查询异常' : '尚未解析' }}</strong></div><div><span>模型标识</span><strong>{{ analysisStale ? '等待重新解析' : polling.analysis.value?.llmModel || '后端未返回' }}</strong></div><el-button v-if="!polling.isPolling.value" type="primary" plain :icon="Refresh" @click="triggerAnalysis">{{ analysisStale ? '重新解析当前题目' : polling.state.value === 'success' ? '重新解析' : '触发解析' }}</el-button></div>
              <AsyncState v-if="polling.isPolling.value" status="loading" compact title="AI 正在分析这道错题" description="系统会定期查询处理状态；90 秒仍未完成时会停止等待，你可以稍后重试。" />
              <AsyncState v-else-if="polling.state.value === 'failed'" status="error" compact title="AI 解析失败" description="后端只返回失败状态，没有更具体原因。可以重新触发解析。" @retry="triggerAnalysis" />
              <AsyncState v-else-if="polling.state.value === 'timeout'" status="error" compact title="等待解析超时" description="这只表示前端停止等待，不代表后端任务一定失败。可稍后重新查询或触发解析。" @retry="retryAnalysisSync" />
              <AsyncState v-else-if="polling.state.value === 'error'" status="error" compact title="解析状态查询失败" :description="polling.error.value?.message" @retry="retryAnalysisSync" />
              <AsyncState v-else-if="analysisStale" status="empty" compact title="旧解析已隐藏" description="重新解析成功后，这里才会展示与当前题目一致的知识点、错因和解析思路。">
                <template #action><el-button type="primary" :icon="MagicStick" @click="triggerAnalysis">重新解析当前题目</el-button></template>
              </AsyncState>
              <template v-else-if="polling.state.value === 'success' && polling.analysis.value">
                <p v-if="analysisPartial" class="partial-result">后端返回了部分结果；缺失字段会明确显示，不会由前端补写。</p>
                <div class="analysis-section"><strong>知识点归类</strong><p>{{ knowledgeName(polling.analysis.value.knowledgePointId) }}</p></div>
                <div class="analysis-section"><strong>错因分析</strong><p>{{ polling.analysis.value.errorCause || '后端未返回错因分析。' }}</p></div>
                <div class="analysis-section"><strong>解析思路</strong><p class="pre-line">{{ polling.analysis.value.analysis || '后端未返回解析内容。' }}</p></div>
              </template>
              <AsyncState v-else status="empty" compact title="尚未生成 AI 解析" description="点击“触发解析”后，系统将异步归类知识点并生成错因与解析。">
                <template #action><el-button type="primary" :icon="MagicStick" @click="triggerAnalysis">触发 AI 智能解析</el-button></template>
              </AsyncState>
            </div>
          </el-tab-pane>

          <el-tab-pane label="RAG 参考" name="references">
            <div class="tab-content">
              <div class="truth-note"><strong>证据边界</strong><p>后端当前只返回参考题 ID 字符串，没有可核验的参考正文或文献接口。因此这里只显示真实 ID，不补写模拟内容。</p></div>
              <AsyncState v-if="analysisStale" status="empty" compact title="旧 RAG 参考已隐藏" description="题目修改后需要重新解析，成功后才会显示当前解析返回的参考 ID。" />
              <AsyncState v-else-if="referenceIds.length === 0" status="empty" compact title="本次没有返回参考 ID" description="可能尚未解析，也可能检索没有命中。" />
              <div v-else class="reference-list"><span v-for="id in referenceIds" :key="id">参考题 ID {{ id }}</span></div>
            </div>
          </el-tab-pane>

          <el-tab-pane :label="`相似题 · ${similarQuestions.length}`" name="similar">
            <div class="tab-content">
              <div class="truth-note"><strong>推荐边界</strong><p>相似题只从当前学生自己的错题中检索，优先匹配同知识点与相近难度，并用语义向量补足。</p></div>
              <AsyncState v-if="analysisStale" status="empty" compact title="旧相似题已隐藏" description="重新解析当前题目后，系统才会重新检索相似题。" />
              <AsyncState v-else-if="similarLoading" status="loading" compact title="正在检索相似题" />
              <AsyncState v-else-if="similarError" status="error" compact title="相似题加载失败" :description="similarError" @retry="loadSimilar" />
              <AsyncState v-else-if="similarLoaded && similarQuestions.length === 0" status="empty" compact title="暂未找到相似题" description="当前账号的题目数量或知识点数据可能不足。" />
              <div v-else-if="similarQuestions.length" class="similar-list">
                <button v-for="item in similarQuestions" :key="item.id" type="button" @click="router.push(`/question/${item.id}`)">
                  <span>{{ subjectName(item.subjectId) }} · {{ knowledgeName(item.knowledgePointId) }} · 难度 {{ difficultyText(item.difficulty) }}</span>
                  <QuestionContent :content="item.stem" />
                </button>
              </div>
            </div>
          </el-tab-pane>

          <el-tab-pane label="学习与练习" name="learning" lazy>
              <div class="tab-content"><LearningResources :question-id="questionId" :revision="JSON.stringify([question.subjectId,question.stem,question.answer,question.knowledgePointId])" @practiced="loadPageAfterPractice" /></div>
            </el-tab-pane>
            <el-tab-pane :label="`AI 变式题 · ${variants.length}`" name="variants">
            <div class="tab-content">
              <div class="variant-head"><p>优先复用已有未练变式题；耗尽后才生成并保存新题。</p><el-button type="primary" :icon="MagicStick" :loading="generating" @click="generateVariants">获取未练变式题</el-button></div>
              <AsyncState v-if="variantLoading" status="loading" compact title="正在读取变式题" />
              <AsyncState v-else-if="variantError" status="error" compact title="变式题操作失败" :description="variantError" @retry="loadVariants" />
              <AsyncState v-else-if="variants.length === 0" status="empty" compact title="还没有变式题" description="生成后可逐题作答并提交自评。" />
              <div v-else class="variant-list"><article v-for="(item, index) in variants" :key="item.id"><div><span>变式 {{ index + 1 }}</span><em>难度 {{ difficultyText(item.difficulty) }}</em></div><QuestionContent :content="item.stem" /><details><summary>查看参考答案</summary><p>{{ item.answer || '后端未返回答案。' }}</p></details><el-button @click="openPractice({ variantId: item.id }, `作答变式 ${index + 1}`)">{{ item.practiced ? '重新练习' : '作答并记录' }}</el-button></article></div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </PaperPanel>

      <el-dialog v-model="editVisible" title="编辑错题" width="min(680px, calc(100vw - 28px))" destroy-on-close @closed="clearEditImage">
        <el-form label-position="top" @submit.prevent="saveEdit">
          <el-form-item label="科目" required><el-select v-model="editForm.subjectId" style="width:100%"><el-option v-for="item in subjects" :key="item.id" :label="item.name" :value="item.id" /></el-select></el-form-item>
          <el-form-item label="题干" required><QuestionEditor v-model="editForm.stem" :disabled="editSaving" /></el-form-item>
          <el-form-item label="答案"><el-input v-model="editForm.answer" type="textarea" :rows="3" maxlength="2000" /></el-form-item>
          <el-form-item label="来源"><el-input v-model="editForm.source" maxlength="128" show-word-limit /></el-form-item>
          <el-form-item label="题目图片">
            <div class="edit-image-field" :aria-busy="editImageReading">
              <div v-if="question.imageUrl && !editImagePreview" class="current-image-row">
                <el-image :src="question.imageUrl" alt="当前题目图片" fit="cover" class="current-image-thumb" :preview-src-list="[question.imageUrl]" />
                <p><strong>当前图片会继续保留</strong><span>选择一张新图后才会替换；后端暂不支持直接移除已有图片。</span></p>
              </div>
              <el-upload
                v-if="!editImagePreview"
                class="edit-uploader"
                drag
                :auto-upload="false"
                :show-file-list="false"
                accept="image/png,image/jpeg,image/gif,image/webp"
                :on-change="onEditImageChange"
                aria-label="选择新图片替换题目图片"
              >
                <el-icon :size="24"><Picture /></el-icon>
                <strong>{{ editImageReading ? '正在读取图片…' : question.imageUrl ? '选择新图替换当前图片' : '添加题目图片' }}</strong>
                <span>PNG / JPG / GIF / WebP，最大 10MB</span>
              </el-upload>
              <div v-else class="edit-image-preview">
                <el-image :src="editImagePreview" :alt="editImageName || '新题目图片预览'" fit="contain" :preview-src-list="[editImagePreview]" />
                <div><strong>{{ editImageName }}</strong><span>{{ editImageSizeText }} · 保存后替换当前图片</span><el-button type="danger" plain :icon="Delete" @click="clearEditImage">取消替换</el-button></div>
              </div>
              <p v-if="editImageError" class="image-error" role="alert">{{ editImageError }}</p>
            </div>
          </el-form-item>
          <p class="dialog-note">修改题目后，旧的 AI、RAG 与变式题结果会被标记为过期并隐藏。</p>
          <p class="dialog-error" aria-live="polite">{{ editError }}</p>
        </el-form>
        <template #footer><el-button @click="editVisible=false">取消</el-button><el-button type="primary" :loading="editSaving" :disabled="editImageReading" @click="saveEdit">保存修改</el-button></template>
      </el-dialog>

      <el-dialog v-model="practiceVisible" :title="practiceTitle" width="min(560px, calc(100vw - 28px))" destroy-on-close>
        <QuestionContent v-if="question" :content="practiceForm.target?.variantId ? variants.find(item => item.id === practiceForm.target?.variantId)?.stem : question.stem" />
        <p class="dialog-note">请先独立作答，再根据实际结果自评。自评会改变掌握度。</p>
        <el-form label-position="top" @submit.prevent="submitPractice">
          <el-form-item label="我的作答"><el-input v-model="practiceForm.userAnswer" type="textarea" :rows="4" maxlength="2000" /></el-form-item>
          <el-form-item label="结果自评" required><el-radio-group v-model="practiceForm.isCorrect" aria-required="true" @change="practiceError = ''"><el-radio-button :value="1">答对了</el-radio-button><el-radio-button :value="0">仍然答错</el-radio-button></el-radio-group></el-form-item>
          <el-form-item label="用时（秒，可选）"><el-input-number v-model="practiceForm.duration" :min="0" :max="7200" /></el-form-item>
          <p class="dialog-error" aria-live="polite">{{ practiceError }}</p>
        </el-form>
        <template #footer><el-button @click="practiceVisible=false">取消</el-button><el-button type="primary" :loading="practiceSaving" @click="submitPractice">提交练习记录</el-button></template>
      </el-dialog>
    </template>
  </div>
</template>

<style scoped>
.question-detail-page{display:grid;gap:20px}.question-overview{display:grid;grid-template-columns:minmax(0,2fr) minmax(280px,.7fr);gap:20px}.question-sheet{position:relative;padding-left:72px!important}.correction-mark{position:absolute;left:22px;top:25px;display:grid;place-items:center;width:38px;height:38px;border:2px solid var(--cinnabar);border-radius:50%;color:var(--cinnabar);font:800 17px var(--font-display);transform:rotate(-7deg)}.question-tags{display:flex;flex-wrap:wrap;gap:7px;margin-bottom:23px}.question-tags span{padding:5px 9px;border:1px solid var(--line-strong);border-radius:999px;background:#edf2f4;color:var(--navy);font-size:10px;font-weight:700}.question-tags .jade{border-color:var(--jade-light);background:var(--jade-pale);color:var(--jade-dark)}.question-tags .amber{border-color:var(--amber-light);background:var(--amber-pale);color:#795017}.stem{margin:0;color:var(--navy);font:500 18px/2 var(--font-serif);white-space:pre-line}.question-image{width:min(100%,520px);max-height:300px;margin-top:17px;border:1px solid var(--line);border-radius:10px;background:#fff}.question-meta{margin:24px 0 0;padding-top:13px;border-top:1px dashed var(--line);color:var(--ink-faint);font:9px var(--font-mono)}.answer-toggle{display:flex;align-items:center;gap:7px;margin-top:17px;border:0;background:transparent;color:var(--jade-dark);font-size:11px;font-weight:800;cursor:pointer}.answer-block{margin:13px 0 0;padding:14px;border-left:3px solid var(--jade);background:var(--jade-pale);color:var(--navy);font-size:13px;line-height:1.8;white-space:pre-line}.mastery-side{display:flex;flex-direction:column;gap:20px}.mastery-side h2{margin:0;color:var(--navy);font:800 20px var(--font-display)}.mastery-side dl{margin:0}.mastery-side dl>div{display:flex;justify-content:space-between;padding:11px 0;border-bottom:1px dashed var(--line);font-size:11px}.mastery-side dt{color:var(--ink-faint)}.mastery-side dd{margin:0;color:var(--navy);font-weight:800}.jade-action{border-color:var(--jade-light)!important;background:var(--jade-pale)!important;color:var(--jade-dark)!important}.analysis-workbench{overflow:hidden}.analysis-tabs :deep(.el-tabs__header){margin:0;padding:15px 25px 0;background:var(--paper-deep)}.analysis-tabs :deep(.el-tabs__nav-wrap::after){height:1px;background:var(--line)}.analysis-tabs :deep(.el-tabs__item){height:46px;font-size:12px;font-weight:800}.tab-content{padding:24px 27px 30px}.analysis-topline{display:flex;align-items:center;gap:25px;margin-bottom:18px;padding-bottom:16px;border-bottom:1px dashed var(--line)}.analysis-topline>div{display:grid;gap:4px}.analysis-topline span{color:var(--ink-faint);font-size:9px}.analysis-topline strong{color:var(--navy);font-size:11px}.analysis-topline :deep(.el-button){margin-left:auto}.analysis-section{display:grid;grid-template-columns:130px minmax(0,1fr);gap:18px;padding:18px 0;border-bottom:1px dashed var(--line)}.analysis-section strong{color:var(--jade-dark);font:800 14px var(--font-display)}.analysis-section p{margin:0;color:var(--ink-soft);font-size:13px;line-height:1.85}.pre-line{white-space:pre-line}.partial-result,.risk-note{margin:0 0 12px;padding:10px 13px;border-left:3px solid var(--amber);background:var(--amber-pale);color:#73501c;font-size:11px;line-height:1.65}.risk-note{border-left-color:var(--cinnabar);background:var(--cinnabar-pale);color:var(--cinnabar-dark)}.truth-note{padding:18px;border:1px solid var(--amber-light);border-radius:11px;background:var(--amber-pale)}.truth-note strong{color:#795017;font:800 15px var(--font-display)}.truth-note p{margin:7px 0 0;color:#73501c;font-size:11px;line-height:1.7}.reference-list{display:flex;flex-wrap:wrap;gap:9px;margin-top:20px}.reference-list span{padding:9px 12px;border:1px solid var(--line);border-radius:9px;background:var(--paper-bright);color:var(--navy);font:10px var(--font-mono)}.similar-list{display:grid;gap:9px}.similar-list button{display:grid;gap:6px;padding:14px 16px;border:1px solid var(--line);border-radius:10px;background:var(--paper-bright);text-align:left;cursor:pointer}.similar-list button:hover{border-color:var(--jade)}.similar-list span{color:var(--ink-faint);font-size:9px}.similar-list strong{overflow:hidden;color:var(--navy);font-size:12px;text-overflow:ellipsis;white-space:nowrap}.variant-head{display:flex;align-items:center;justify-content:space-between;gap:15px;margin-bottom:18px}.variant-head p{margin:0;color:var(--ink-soft);font-size:11px}.variant-list{display:grid;gap:12px}.variant-list article{padding:18px;border:1px solid var(--line);border-radius:12px;background:var(--paper-bright)}.variant-list article>div:first-child{display:flex;justify-content:space-between}.variant-list span{color:var(--cinnabar);font:800 14px var(--font-display)}.variant-list em{color:var(--ink-faint);font-size:10px;font-style:normal}.variant-list article>p,.variant-list details p{color:var(--navy);font-size:13px;line-height:1.8}.variant-list summary{color:var(--jade-dark);font-size:11px;cursor:pointer}.variant-list :deep(.el-button){margin-top:12px}.dialog-note{margin:0 0 14px;padding:10px 12px;border-left:3px solid var(--amber);background:var(--amber-pale);color:#73501c;font-size:11px;line-height:1.6}.dialog-error{min-height:18px;margin:0;color:var(--cinnabar);font-size:11px}
.derived-stale-note{display:flex;align-items:flex-start;gap:12px;padding:14px 25px;border-bottom:1px solid var(--amber-light);background:var(--amber-pale);color:#73501c}.derived-stale-note>span{display:grid;flex:0 0 28px;width:28px;height:28px;place-items:center;border:2px solid var(--amber);border-radius:50%;font:900 13px var(--font-display)}.derived-stale-note strong{display:block;color:#795017;font:800 14px var(--font-display)}.derived-stale-note p{margin:4px 0 0;font-size:11px;line-height:1.65}.stale-variants{margin-top:4px}.edit-image-field{display:grid;width:100%;gap:10px}.current-image-row{display:grid;grid-template-columns:92px minmax(0,1fr);gap:12px;align-items:center;padding:10px;border:1px solid var(--line);border-radius:11px;background:var(--paper-bright)}.current-image-thumb{width:92px;height:66px;border:1px solid var(--line);border-radius:8px;background:var(--paper-deep)}.current-image-row p{display:grid;gap:4px;margin:0}.current-image-row strong{color:var(--navy);font-size:12px}.current-image-row span{color:var(--ink-faint);font-size:10px;line-height:1.55}.edit-uploader,.edit-uploader :deep(.el-upload),.edit-uploader :deep(.el-upload-dragger){width:100%}.edit-uploader :deep(.el-upload-dragger){display:grid;min-height:112px;padding:18px;place-items:center;align-content:center;border:1px dashed var(--line-strong);background:repeating-linear-gradient(180deg,transparent 0 28px,rgba(37,78,102,.05) 28px 29px),rgba(255,253,248,.8)}.edit-uploader :deep(.el-upload-dragger:hover){border-color:var(--jade)}.edit-uploader :deep(.el-icon){margin-bottom:6px;color:var(--jade-dark)}.edit-uploader strong{color:var(--navy);font-size:12px}.edit-uploader span{margin-top:3px;color:var(--ink-faint);font-size:10px}.edit-image-preview{display:grid;grid-template-columns:minmax(180px,260px) minmax(0,1fr);gap:14px;align-items:center;padding:11px;border:1px solid var(--jade-light);border-radius:12px;background:var(--jade-pale)}.edit-image-preview :deep(.el-image){width:100%;height:145px;border:1px solid var(--line);border-radius:9px;background:var(--paper-bright)}.edit-image-preview>div{display:grid;gap:7px;justify-items:start;min-width:0}.edit-image-preview strong{max-width:100%;overflow:hidden;color:var(--navy);font-size:12px;text-overflow:ellipsis;white-space:nowrap}.edit-image-preview span{color:var(--ink-faint);font-size:10px}.image-error{margin:0;color:var(--cinnabar-dark);font-size:11px}
@media(max-width:900px){.question-overview{grid-template-columns:1fr}.mastery-side{display:grid;grid-template-columns:1fr 1fr;align-items:center}.mastery-side h2{grid-column:1/-1}.analysis-section{grid-template-columns:1fr}.variant-head{align-items:flex-start}}
@media(max-width:600px){.question-sheet{padding:70px 18px 24px 40px!important}.correction-mark{left:8px;top:21px}.question-tags{position:absolute;left:55px;right:10px;top:23px;flex-wrap:nowrap;overflow-x:auto}.stem{font-size:16px}.mastery-side{display:flex;align-items:stretch}.derived-stale-note{padding:13px 15px}.analysis-tabs :deep(.el-tabs__header){padding-inline:13px}.analysis-tabs :deep(.el-tabs__nav-scroll){overflow-x:auto}.tab-content{padding:20px 15px 24px}.analysis-topline{display:grid;grid-template-columns:1fr 1fr}.analysis-topline :deep(.el-button){grid-column:1/-1;width:100%;margin-left:0}.variant-head{display:grid}.variant-head :deep(.el-button){width:100%}.edit-image-preview{grid-template-columns:1fr}.current-image-row{grid-template-columns:74px minmax(0,1fr)}.current-image-thumb{width:74px;height:58px}.question-meta{line-height:1.7}}
</style>
