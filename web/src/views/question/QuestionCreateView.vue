<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules, type UploadFile } from 'element-plus'
import { ArrowLeft, Check, Delete, Picture } from '@element-plus/icons-vue'
import AsyncState from '@/components/AsyncState.vue'
import PageHeader from '@/components/PageHeader.vue'
import PaperPanel from '@/components/PaperPanel.vue'
import { aiApi, questionApi, subjectApi, toApiError, type Subject } from '@/api'

type SubjectState = 'loading' | 'ready' | 'empty' | 'error'

const MAX_IMAGE_SIZE = 10 * 1024 * 1024
const ACCEPTED_IMAGE_TYPES = new Set(['image/png', 'image/jpeg', 'image/gif', 'image/webp'])

const router = useRouter()
const formRef = ref<FormInstance>()
const subjects = ref<Subject[]>([])
const subjectState = ref<SubjectState>('loading')
const subjectError = ref('')
const submitting = ref(false)
const submitError = ref('')
const imageBase64 = ref('')
const imagePreview = ref('')
const imageName = ref('')
const imageSize = ref(0)
const imageReading = ref(false)
const imageError = ref('')
let imageReadVersion = 0

const form = reactive({
  subjectId: undefined as number | undefined,
  stem: '',
  answer: '',
  source: '',
})

const rules: FormRules = {
  subjectId: [{ required: true, message: '请选择科目', trigger: 'change' }],
  stem: [{ required: true, message: '请填写题干', trigger: 'blur' }],
}

const imageSizeText = computed(() => {
  if (!imageSize.value) return ''
  return imageSize.value >= 1024 * 1024
    ? `${(imageSize.value / 1024 / 1024).toFixed(1)} MB`
    : `${Math.ceil(imageSize.value / 1024)} KB`
})

async function loadSubjects() {
  subjectState.value = 'loading'
  subjectError.value = ''
  try {
    subjects.value = await subjectApi.list()
    subjectState.value = subjects.value.length ? 'ready' : 'empty'
  } catch (cause) {
    subjectError.value = toApiError(cause, '科目加载失败').message
    subjectState.value = 'error'
  }
}

function rejectImage(message: string) {
  imageError.value = message
  ElMessage.warning(message)
}

function onImageChange(file: UploadFile) {
  const raw = file.raw
  if (!raw) return
  imageError.value = ''

  if (!ACCEPTED_IMAGE_TYPES.has(raw.type)) {
    rejectImage('仅支持 PNG、JPG、GIF 或 WebP 图片')
    return
  }
  if (raw.size > MAX_IMAGE_SIZE) {
    rejectImage('图片大小不能超过 10MB')
    return
  }

  const currentRead = ++imageReadVersion
  const reader = new FileReader()
  imageReading.value = true
  reader.onload = () => {
    if (currentRead !== imageReadVersion || typeof reader.result !== 'string') return
    imageBase64.value = reader.result
    imagePreview.value = reader.result
    imageName.value = raw.name
    imageSize.value = raw.size
  }
  reader.onerror = () => {
    if (currentRead !== imageReadVersion) return
    rejectImage('图片读取失败，请重新选择')
  }
  reader.onloadend = () => {
    if (currentRead === imageReadVersion) imageReading.value = false
  }
  reader.readAsDataURL(raw)
}

function removeImage() {
  imageReadVersion += 1
  imageBase64.value = ''
  imagePreview.value = ''
  imageName.value = ''
  imageSize.value = 0
  imageReading.value = false
  imageError.value = ''
}

async function submit() {
  submitError.value = ''
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  const stem = form.stem.trim()
  if (!stem) {
    ElMessage.warning('题干不能只包含空格')
    return
  }
  if (!form.subjectId || imageReading.value) return

  submitting.value = true
  try {
    const id = await questionApi.create({
      subjectId: form.subjectId,
      stem,
      answer: form.answer.trim() || undefined,
      source: form.source.trim() || undefined,
      imageBase64: imageBase64.value || undefined,
    })

    let analysisAccepted = true
    try {
      await aiApi.analyze(id)
    } catch {
      analysisAccepted = false
    }

    if (analysisAccepted) {
      ElMessage.success('错题已归档，AI 解析正在后台进行')
    } else {
      ElMessage.warning('错题已归档，但 AI 解析暂未启动，可在详情页重新触发')
    }
    await router.push(`/question/${id}`)
  } catch (cause) {
    submitError.value = toApiError(cause, '错题保存失败').message
  } finally {
    submitting.value = false
  }
}

onMounted(() => void loadSubjects())
</script>

<template>
  <div class="question-create-page">
    <PageHeader
      eyebrow="错题归档"
      title="录入一道值得重做的题"
      description="保存后会建立第 1、2、4、7、15 天复习节点，并尝试在后台启动知识点归类与错因解析。"
    >
      <template #actions>
        <el-button :icon="ArrowLeft" @click="router.push('/question/list')">返回错题本</el-button>
      </template>
    </PageHeader>

    <PaperPanel v-if="subjectState !== 'ready'" class="subject-state-panel">
      <AsyncState
        v-if="subjectState === 'loading'"
        status="loading"
        title="正在取出科目目录"
        description="表单会在科目加载完成后展开。"
      />
      <AsyncState
        v-else-if="subjectState === 'error'"
        status="error"
        title="科目目录加载失败"
        :description="subjectError"
        @retry="loadSubjects"
      />
      <AsyncState
        v-else
        status="empty"
        title="还没有可用科目"
        description="请联系管理员先维护科目，再回来录入错题。"
      >
        <template #action>
          <el-button @click="loadSubjects">重新检查</el-button>
        </template>
      </AsyncState>
    </PaperPanel>

    <div v-else class="create-grid">
      <PaperPanel variant="lined" class="form-panel">
        <div class="panel-heading">
          <span class="step-number num" aria-hidden="true">01</span>
          <div>
            <h2>整理题目原貌</h2>
            <p>题干与科目必填，答案、来源和图片可稍后补充。</p>
          </div>
        </div>

        <div v-if="submitError" class="form-alert" role="alert">
          <strong>没有保存成功</strong>
          <span>{{ submitError }}</span>
        </div>

        <el-form ref="formRef" :model="form" :rules="rules" label-position="top" @submit.prevent="submit">
          <div class="field-row">
            <el-form-item label="科目" prop="subjectId" required>
              <el-select v-model="form.subjectId" placeholder="选择所属科目" filterable>
                <el-option v-for="subject in subjects" :key="subject.id" :label="subject.name" :value="subject.id" />
              </el-select>
            </el-form-item>
            <el-form-item label="来源（选填）">
              <el-input v-model="form.source" maxlength="100" show-word-limit placeholder="如：期中试卷 · 第 18 题" />
            </el-form-item>
          </div>

          <el-form-item label="题干" prop="stem" required>
            <el-input
              v-model="form.stem"
              type="textarea"
              :rows="6"
              maxlength="2000"
              show-word-limit
              resize="vertical"
              placeholder="完整抄录题目条件与问题，便于后续检索和解析"
            />
          </el-form-item>

          <el-form-item label="正确答案或订正（选填）">
            <el-input
              v-model="form.answer"
              type="textarea"
              :rows="4"
              maxlength="2000"
              show-word-limit
              resize="vertical"
              placeholder="记录正确答案、关键步骤或自己的订正"
            />
          </el-form-item>

          <el-form-item label="题目图片（选填）">
            <div class="upload-area" :aria-busy="imageReading">
              <el-upload
                v-if="!imagePreview"
                class="uploader"
                drag
                :auto-upload="false"
                :show-file-list="false"
                accept="image/png,image/jpeg,image/gif,image/webp"
                :on-change="onImageChange"
                aria-label="选择或拖拽题目图片"
              >
                <el-icon class="upload-icon" :size="30"><Picture /></el-icon>
                <strong>{{ imageReading ? '正在读取图片…' : '拖入题目截图，或点击选择' }}</strong>
                <span>PNG / JPG / GIF / WebP，最大 10MB</span>
              </el-upload>

              <div v-else class="preview-wrap">
                <el-image
                  :src="imagePreview"
                  :alt="imageName || '题目图片预览'"
                  fit="contain"
                  class="preview-image"
                  :preview-src-list="[imagePreview]"
                />
                <div class="preview-meta">
                  <span>
                    <strong>{{ imageName }}</strong>
                    <small class="num">{{ imageSizeText }}</small>
                  </span>
                  <el-button :icon="Delete" type="danger" plain aria-label="移除题目图片" @click="removeImage">
                    移除图片
                  </el-button>
                </div>
              </div>
              <p v-if="imageError" class="image-error" role="alert">{{ imageError }}</p>
            </div>
          </el-form-item>

          <div class="form-actions">
            <el-button :icon="ArrowLeft" @click="router.push('/question/list')">暂不录入</el-button>
            <el-button
              type="primary"
              size="large"
              :icon="Check"
              :loading="submitting"
              :disabled="imageReading"
              native-type="submit"
            >
              保存并启动解析
            </el-button>
          </div>
        </el-form>
      </PaperPanel>

      <aside class="create-aside" aria-label="录入说明">
        <PaperPanel variant="annotation" class="annotation-card">
          <p class="annotation-kicker">校勘提示</p>
          <h2>先保留原题，再写订正</h2>
          <p>清晰的题干、完整条件和可靠答案，会让知识点归类与相似题检索更有依据。</p>
        </PaperPanel>

        <PaperPanel class="flow-card">
          <h2>归档后会发生什么</h2>
          <ol class="flow-list">
            <li>
              <span class="num">1</span>
              <div><strong>错题安全保存</strong><small>即使 AI 暂时不可用，题目也不会丢失。</small></div>
            </li>
            <li>
              <span class="num">2</span>
              <div><strong>建立复习节点</strong><small>系统按 1 / 2 / 4 / 7 / 15 天安排任务。</small></div>
            </li>
            <li>
              <span class="num">3</span>
              <div><strong>后台尝试解析</strong><small>详情页会显示进行中、成功或失败状态。</small></div>
            </li>
          </ol>
        </PaperPanel>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.subject-state-panel {
  max-width: 860px;
}

.create-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 310px;
  gap: 22px;
  align-items: start;
}

.form-panel {
  min-width: 0;
}

.panel-heading {
  display: flex;
  gap: 14px;
  align-items: flex-start;
  margin-bottom: 22px;
}

.step-number {
  display: grid;
  flex: 0 0 38px;
  width: 38px;
  height: 38px;
  place-items: center;
  border-radius: 12px 12px 12px 4px;
  background: var(--navy);
  color: #fff;
  font-size: 12px;
  font-weight: 800;
}

.panel-heading h2,
.create-aside h2 {
  margin: 0;
  color: var(--navy);
  font-family: var(--font-serif);
  font-size: 18px;
}

.panel-heading p {
  margin: 5px 0 0;
  color: var(--ink-faint);
  font-size: 12px;
  line-height: 1.65;
}

.field-row {
  display: grid;
  grid-template-columns: minmax(0, 0.82fr) minmax(0, 1.18fr);
  gap: 16px;
}

.field-row :deep(.el-select) {
  width: 100%;
}

.form-alert {
  display: flex;
  gap: 5px;
  flex-direction: column;
  margin-bottom: 18px;
  padding: 12px 15px;
  border: 1px solid rgba(183, 67, 50, 0.26);
  border-left: 4px solid var(--cinnabar);
  border-radius: 4px 11px 11px 4px;
  background: var(--cinnabar-pale);
  color: var(--cinnabar-dark);
  font-size: 12px;
  line-height: 1.55;
}

.upload-area {
  width: 100%;
}

.uploader,
.uploader :deep(.el-upload),
.uploader :deep(.el-upload-dragger) {
  width: 100%;
}

.uploader :deep(.el-upload-dragger) {
  display: grid;
  min-height: 144px;
  padding: 24px;
  place-items: center;
  align-content: center;
  border: 1px dashed var(--line-strong);
  background:
    repeating-linear-gradient(180deg, transparent 0 30px, rgba(37, 78, 102, 0.05) 30px 31px),
    rgba(255, 253, 248, 0.8);
}

.uploader :deep(.el-upload-dragger:hover) {
  border-color: var(--jade);
}

.upload-icon {
  margin-bottom: 8px;
  color: var(--jade-dark);
}

.uploader strong {
  color: var(--navy);
  font-size: 13px;
}

.uploader span {
  margin-top: 4px;
  color: var(--ink-faint);
  font-size: 11px;
}

.preview-wrap {
  display: grid;
  grid-template-columns: minmax(180px, 280px) minmax(0, 1fr);
  gap: 18px;
  align-items: center;
  padding: 13px;
  border: 1px solid var(--line);
  border-radius: 14px;
  background: rgba(255, 253, 248, 0.76);
}

.preview-image {
  width: 100%;
  height: 170px;
  border: 1px solid var(--line);
  border-radius: 10px;
  background: var(--paper-deep);
}

.preview-meta,
.preview-meta > span {
  display: flex;
  min-width: 0;
  gap: 9px;
  flex-direction: column;
  align-items: flex-start;
}

.preview-meta strong {
  max-width: 100%;
  overflow: hidden;
  color: var(--navy);
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.preview-meta small {
  color: var(--ink-faint);
}

.image-error {
  margin: 8px 0 0;
  color: var(--cinnabar-dark);
  font-size: 12px;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding-top: 4px;
}

.create-aside {
  display: grid;
  gap: 16px;
}

.annotation-card {
  padding: 22px 22px 22px 26px;
}

.annotation-kicker {
  margin: 0 0 8px;
  font-size: 10px;
  font-weight: 900;
  letter-spacing: 0.16em;
}

.annotation-card h2 {
  color: var(--cinnabar-dark);
  font-size: 17px;
}

.annotation-card p:last-child {
  margin: 10px 0 0;
  font-size: 12px;
  line-height: 1.75;
}

.flow-card h2 {
  margin-bottom: 18px;
}

.flow-list {
  display: grid;
  gap: 16px;
  padding: 0;
  margin: 0;
  list-style: none;
}

.flow-list li {
  display: grid;
  grid-template-columns: 30px minmax(0, 1fr);
  gap: 11px;
  align-items: start;
}

.flow-list li > span {
  display: grid;
  width: 28px;
  height: 28px;
  place-items: center;
  border: 1px solid rgba(22, 129, 114, 0.26);
  border-radius: 9px 9px 9px 3px;
  background: var(--jade-pale);
  color: var(--jade-dark);
  font-size: 11px;
  font-weight: 800;
}

.flow-list strong,
.flow-list small {
  display: block;
}

.flow-list strong {
  color: var(--navy);
  font-size: 12px;
}

.flow-list small {
  margin-top: 3px;
  color: var(--ink-faint);
  font-size: 11px;
  line-height: 1.55;
}

@media (max-width: 980px) {
  .create-grid {
    grid-template-columns: 1fr;
  }

  .create-aside {
    grid-template-columns: minmax(0, 0.9fr) minmax(0, 1.1fr);
  }
}

@media (max-width: 700px) {
  .field-row,
  .create-aside,
  .preview-wrap {
    grid-template-columns: 1fr;
  }

  .form-actions {
    flex-direction: column-reverse;
  }

  .form-actions :deep(.el-button) {
    width: 100%;
    margin-left: 0;
  }

  .preview-image {
    height: 190px;
  }
}
</style>
