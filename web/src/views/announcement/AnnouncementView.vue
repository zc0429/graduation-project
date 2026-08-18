<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { announcementApi, type Announcement } from '@/api'
import { useUserStore } from '@/store/user'

const store = useUserStore()
const list = ref<Announcement[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const publishing = ref(false)
const form = reactive({ title: '', content: '' })

async function load() {
  loading.value = true
  try {
    list.value = await announcementApi.list()
  } finally {
    loading.value = false
  }
}

async function publish() {
  if (!form.title.trim()) {
    ElMessage.warning('请填写公告标题')
    return
  }
  publishing.value = true
  try {
    await announcementApi.publish({ title: form.title, content: form.content || undefined })
    ElMessage.success('公告已发布')
    dialogVisible.value = false
    form.title = ''
    form.content = ''
    await load()
  } finally {
    publishing.value = false
  }
}

onMounted(load)
</script>

<template>
  <div>
    <div class="head-row">
      <div>
        <h2 class="page-title">公告</h2>
        <p class="page-subtitle">系统公告与重要通知。</p>
      </div>
      <el-button v-if="store.role === 'admin'" type="primary" :icon="Plus" @click="dialogVisible = true">发布公告</el-button>
    </div>
    <div v-loading="loading">
      <el-empty v-if="list.length === 0" description="暂无公告" :image-size="80" />
      <div v-for="a in list" :key="a.id" class="paper-card ann-card">
        <div class="ann-head">
          <span class="ann-title">{{ a.title }}</span>
          <span class="ann-time num">{{ a.createTime }}</span>
        </div>
        <p class="ann-content">{{ a.content }}</p>
      </div>
    </div>

    <el-dialog v-model="dialogVisible" title="发布公告" width="520px">
      <el-form label-position="top">
        <el-form-item label="标题" required>
          <el-input v-model="form.title" maxlength="128" show-word-limit />
        </el-form-item>
        <el-form-item label="内容">
          <el-input v-model="form.content" type="textarea" :rows="4" maxlength="2000" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="publishing" @click="publish">发布</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.head-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.ann-card {
  margin-bottom: 12px;
}

.ann-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.ann-title {
  font-size: 15px;
  font-weight: 600;
}

.ann-time {
  font-size: 12px;
  color: var(--wb-ink-secondary);
}

.ann-content {
  font-size: 13px;
  color: var(--wb-ink);
  line-height: 1.7;
  margin: 0;
  white-space: pre-line;
}
</style>
