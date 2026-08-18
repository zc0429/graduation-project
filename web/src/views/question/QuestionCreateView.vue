<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type UploadFile } from 'element-plus'
import { Delete, Plus } from '@element-plus/icons-vue'
import { aiApi, questionApi, subjectApi, type Subject } from '@/api'

const router = useRouter()
const subjects = ref<Subject[]>([])
const submitting = ref(false)
const imageBase64 = ref('')
const imagePreview = ref('')

const form = reactive({
  subjectId: undefined as number | undefined,
  stem: '',
  answer: '',
  source: '',
})

onMounted(async () => {
  subjects.value = await subjectApi.list()
})

function onImageChange(file: UploadFile) {
  const raw = file.raw
  if (!raw) return
  if (raw.size > 10 * 1024 * 1024) {
    ElMessage.warning('图片大小不能超过 10MB')
    return
  }
  const reader = new FileReader()
  reader.onload = () => {
    imageBase64.value = reader.result as string
    imagePreview.value = reader.result as string
  }
  reader.readAsDataURL(raw)
}

function removeImage() {
  imageBase64.value = ''
  imagePreview.value = ''
}

async function submit() {
  if (!form.subjectId) {
    ElMessage.warning('请选择科目')
    return
  }
  if (!form.stem.trim()) {
    ElMessage.warning('请填写题干')
    return
  }
  submitting.value = true
  try {
    const id = await questionApi.create({
      subjectId: form.subjectId,
      stem: form.stem,
      answer: form.answer || undefined,
      source: form.source || undefined,
      imageBase64: imageBase64.value || undefined,
    })
    await aiApi.analyze(id)
    ElMessage.success('录入成功，AI 解析中，稍后可在详情页查看结果')
    router.push(`/question/${id}`)
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div>
    <h2 class="page-title">错题录入</h2>
    <p class="page-subtitle">提交后系统将自动触发 AI 解析：知识点归类、错因分析与解析生成。</p>
    <div class="paper-card form-card">
      <el-form label-position="top">
        <el-form-item label="科目" required>
          <el-select v-model="form.subjectId" placeholder="请选择科目" style="width: 280px">
            <el-option v-for="s in subjects" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="题干" required>
          <el-input
            v-model="form.stem"
            type="textarea"
            :rows="5"
            maxlength="2000"
            show-word-limit
            placeholder="请输入错题题干，支持文本描述"
          />
        </el-form-item>
        <el-form-item label="题目图片（选填，不超过 10MB）">
          <div class="upload-area">
            <el-upload
              v-if="!imagePreview"
              :auto-upload="false"
              :show-file-list="false"
              accept="image/*"
              :on-change="onImageChange"
              drag
              class="uploader"
            >
              <el-icon :size="28" color="#0f766e"><Plus /></el-icon>
              <div class="upload-tip">点击或拖拽图片到此处</div>
            </el-upload>
            <div v-else class="preview-wrap">
              <el-image :src="imagePreview" fit="contain" class="preview-img" />
              <el-button circle type="danger" :icon="Delete" class="preview-del" @click="removeImage" />
            </div>
          </div>
        </el-form-item>
        <el-form-item label="答案（选填）">
          <el-input v-model="form.answer" type="textarea" :rows="3" maxlength="2000" placeholder="正确答案或你的作答" />
        </el-form-item>
        <el-form-item label="来源（选填）">
          <el-input v-model="form.source" placeholder="如：作业 / 期中试卷 / 单元测验" style="width: 280px" />
        </el-form-item>
        <el-button type="primary" size="large" :loading="submitting" @click="submit">提交并解析</el-button>
      </el-form>
    </div>
  </div>
</template>

<style scoped>
.form-card {
  max-width: 760px;
}

.upload-tip {
  font-size: 12px;
  color: var(--wb-ink-secondary);
  margin-top: 6px;
}

.uploader :deep(.el-upload-dragger) {
  width: 240px;
  padding: 18px 0;
}

.preview-wrap {
  position: relative;
  display: inline-block;
}

.preview-img {
  width: 240px;
  height: 150px;
  border: 1px solid var(--wb-border);
  border-radius: 8px;
}

.preview-del {
  position: absolute;
  top: -10px;
  right: -10px;
}
</style>
