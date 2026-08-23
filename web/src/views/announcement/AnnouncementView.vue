<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { announcementApi, type Announcement } from '@/api'
import { useUserStore } from '@/store/user'
import { toApiError } from '@/utils/api-error'
import AdminSectionTabs from '@/components/AdminSectionTabs.vue'
import AsyncState from '@/components/AsyncState.vue'
import PageHeader from '@/components/PageHeader.vue'
import PaperPanel from '@/components/PaperPanel.vue'

const store = useUserStore()
const list = ref<Announcement[]>([])
const loading = ref(false)
const errorMessage = ref('')
const dialogVisible = ref(false)
const publishing = ref(false)
const titleError = ref('')
const form = reactive({ title: '', content: '' })

const isAdmin = computed(() => store.role === 'admin')

async function load() {
  loading.value = true
  errorMessage.value = ''
  try {
    list.value = await announcementApi.list()
  } catch (error) {
    errorMessage.value = toApiError(error, '公告加载失败').message
  } finally {
    loading.value = false
  }
}

function openPublishDialog() {
  form.title = ''
  form.content = ''
  titleError.value = ''
  dialogVisible.value = true
}

async function publish() {
  const title = form.title.trim()
  const content = form.content.trim()
  if (!title) {
    titleError.value = '请填写公告标题'
    return
  }

  titleError.value = ''
  publishing.value = true
  try {
    await announcementApi.publish({ title, content: content || undefined })
    ElMessage.success('公告已发布')
    dialogVisible.value = false
    await load()
  } finally {
    publishing.value = false
  }
}

function dateParts(value: string) {
  const normalized = value.replace('T', ' ')
  const [date = '', time = ''] = normalized.split(' ')
  const [, month = '', day = ''] = date.split('-')
  return {
    day: day || '—',
    month: month ? `${month}月` : '',
    dateTime: time ? `${date} ${time.slice(0, 5)}` : date || '—',
  }
}

onMounted(load)
</script>

<template>
  <div class="announcement-page">
    <PageHeader
      eyebrow="SYSTEM NOTICEBOARD"
      title="系统公告"
      :description="isAdmin ? '查看并发布系统公告。当前接口不提供公告编辑、下线或删除。' : '查看系统发布的重要通知与学习安排。'"
    >
      <template v-if="isAdmin" #actions>
        <el-button type="primary" :icon="Plus" @click="openPublishDialog">发布公告</el-button>
      </template>
    </PageHeader>

    <AdminSectionTabs v-if="isAdmin" />

    <PaperPanel variant="lined" class="announcement-board">
      <div class="board-heading">
        <div>
          <span class="board-seal" aria-hidden="true">告</span>
          <div><strong>公告栏</strong><p>按发布时间查看当前有效公告</p></div>
        </div>
        <span v-if="!loading && !errorMessage" class="board-count">共 <strong class="num">{{ list.length }}</strong> 条</span>
      </div>

      <AsyncState v-if="loading" status="loading" title="正在翻阅公告" />
      <AsyncState
        v-else-if="errorMessage"
        status="error"
        title="公告加载失败"
        :description="errorMessage"
        @retry="load"
      />
      <AsyncState
        v-else-if="list.length === 0"
        status="empty"
        title="目前没有公告"
        :description="isAdmin ? '发布第一条公告后，所有用户都能在这里查看。' : '有新通知时会出现在这里。'"
      >
        <template v-if="isAdmin" #action>
          <el-button type="primary" :icon="Plus" @click="openPublishDialog">发布第一条公告</el-button>
        </template>
      </AsyncState>

      <div v-else class="announcement-list" aria-label="系统公告列表">
        <article v-for="announcement in list" :key="announcement.id" class="announcement-item">
          <time class="announcement-date" :datetime="announcement.createTime">
            <strong class="num">{{ dateParts(announcement.createTime).day }}</strong>
            <span>{{ dateParts(announcement.createTime).month }}</span>
          </time>
          <div class="announcement-copy">
            <div class="announcement-meta">
              <span>系统公告</span>
              <time class="num" :datetime="announcement.createTime">{{ dateParts(announcement.createTime).dateTime }}</time>
            </div>
            <h2>{{ announcement.title }}</h2>
            <p v-if="announcement.content">{{ announcement.content }}</p>
          </div>
        </article>
      </div>
    </PaperPanel>

    <el-dialog
      v-if="isAdmin"
      v-model="dialogVisible"
      title="发布公告"
      width="540px"
      destroy-on-close
      append-to-body
    >
      <p class="dialog-description">公告发布后立即对全部用户可见。当前系统不支持发布后的编辑或下线，请提交前仔细检查。</p>
      <el-form label-position="top" @submit.prevent="publish">
        <el-form-item label="公告标题" required :error="titleError">
          <el-input id="announcement-title" v-model="form.title" maxlength="128" show-word-limit placeholder="请输入清晰、简短的标题" />
        </el-form-item>
        <el-form-item label="公告内容">
          <el-input
            id="announcement-content"
            v-model="form.content"
            type="textarea"
            :rows="5"
            maxlength="2000"
            show-word-limit
            placeholder="说明通知内容、时间或需要完成的事项"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="publishing" @click="publish">确认发布</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.announcement-board {
  min-height: 440px;
}

.board-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 10px;
  padding-bottom: 17px;
  border-bottom: 1px dashed var(--line);
}

.board-heading > div {
  display: flex;
  align-items: center;
  gap: 12px;
}

.board-seal {
  display: grid;
  width: 43px;
  height: 43px;
  flex: 0 0 auto;
  place-items: center;
  border: 2px solid rgba(183, 67, 50, 0.45);
  border-radius: 50%;
  color: var(--cinnabar-dark);
  font-family: var(--font-serif);
  font-size: 18px;
  font-weight: 700;
  transform: rotate(-7deg);
}

.board-heading strong {
  color: var(--navy);
  font-family: var(--font-serif);
  font-size: 17px;
}

.board-heading p {
  margin: 3px 0 0;
  color: var(--ink-faint);
  font-size: 10px;
}

.board-count {
  color: var(--ink-faint);
  font-size: 10px;
}

.board-count strong {
  color: var(--navy);
  font-family: var(--font-mono);
  font-size: 12px;
}

.announcement-list {
  display: grid;
}

.announcement-item {
  display: grid;
  grid-template-columns: 68px minmax(0, 1fr);
  gap: 18px;
  padding: 22px 8px;
  border-bottom: 1px dashed var(--line);
}

.announcement-item:last-child {
  border-bottom: 0;
}

.announcement-date {
  display: flex;
  width: 62px;
  height: 66px;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(183, 67, 50, 0.28);
  border-radius: 6px 15px 15px 15px;
  background: var(--cinnabar-pale);
  color: var(--cinnabar-dark);
  text-decoration: none;
}

.announcement-date strong {
  font-family: var(--font-mono);
  font-size: 22px;
  line-height: 1;
}

.announcement-date span {
  margin-top: 5px;
  font-size: 9px;
  font-weight: 700;
}

.announcement-copy {
  min-width: 0;
}

.announcement-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  color: var(--ink-faint);
  font-size: 9px;
}

.announcement-meta > span {
  color: var(--jade-dark);
  font-weight: 800;
  letter-spacing: 0.08em;
}

.announcement-copy h2 {
  margin: 8px 0 7px;
  color: var(--navy);
  font-family: var(--font-serif);
  font-size: 18px;
  line-height: 1.45;
}

.announcement-copy > p {
  margin: 0;
  color: var(--ink-soft);
  font-size: 12px;
  line-height: 1.8;
  white-space: pre-line;
}

.dialog-description {
  margin: -4px 0 18px;
  padding: 10px 12px;
  border-left: 3px solid var(--cinnabar);
  background: var(--cinnabar-pale);
  color: var(--cinnabar-dark);
  font-size: 11px;
  line-height: 1.7;
}

@media (max-width: 700px) {
  .announcement-item {
    grid-template-columns: 52px minmax(0, 1fr);
    gap: 13px;
    padding: 18px 2px;
  }

  .announcement-date {
    width: 50px;
    height: 56px;
  }

  .announcement-date strong {
    font-size: 18px;
  }

  .announcement-meta {
    display: grid;
    gap: 3px;
  }

  .announcement-copy h2 {
    font-size: 16px;
  }
}
</style>
