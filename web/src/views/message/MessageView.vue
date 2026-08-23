<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { Check, Refresh } from '@element-plus/icons-vue'
import { messageApi, type Message, type PageData } from '@/api'
import AsyncState from '@/components/AsyncState.vue'
import PageHeader from '@/components/PageHeader.vue'
import PaperPanel from '@/components/PaperPanel.vue'

const page = ref<PageData<Message>>({ records: [], total: 0, current: 1, size: 10 })
const loading = ref(true)
const error = ref('')
const markingId = ref<number>()
const pageNum = ref(1)
const filter = ref<'all' | 'unread' | 'read'>('all')

const typeMap: Record<string, { label: string; tone: string }> = {
  review_remind: { label: '复习提醒', tone: 'amber' },
  report: { label: '学情报告', tone: 'jade' },
  system: { label: '系统消息', tone: 'navy' },
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    page.value = await messageApi.page({
      pageNum: pageNum.value,
      pageSize: 10,
      isRead: filter.value === 'all' ? undefined : filter.value === 'read' ? 1 : 0,
    })
  } catch (cause) {
    error.value = cause instanceof Error ? cause.message : '消息暂时无法加载。'
  } finally {
    loading.value = false
  }
}

function changeFilter(value: typeof filter.value) {
  filter.value = value
  pageNum.value = 1
  void load()
}

async function markRead(message: Message) {
  markingId.value = message.id
  try {
    await messageApi.markRead(message.id)
    message.isRead = 1
    window.dispatchEvent(new Event('message-unread-changed'))
    if (filter.value === 'unread') await load()
  } finally {
    markingId.value = undefined
  }
}

onMounted(load)
</script>

<template>
  <div class="message-page">
    <PageHeader eyebrow="通知与提醒" title="消息中心" description="复习提醒、周报生成结果和系统消息会按时间保存在这里。">
      <template #actions><el-button :icon="Refresh" :loading="loading" @click="load">刷新</el-button></template>
    </PageHeader>

    <PaperPanel>
      <div class="message-toolbar" role="group" aria-label="消息状态筛选">
        <button type="button" :class="{ active: filter === 'all' }" @click="changeFilter('all')">全部</button>
        <button type="button" :class="{ active: filter === 'unread' }" @click="changeFilter('unread')">未读</button>
        <button type="button" :class="{ active: filter === 'read' }" @click="changeFilter('read')">已读</button>
        <span>共 {{ page.total }} 条</span>
      </div>

      <AsyncState v-if="loading" status="loading" compact title="正在读取消息" />
      <AsyncState v-else-if="error" status="error" compact title="消息加载失败" :description="error" @retry="load" />
      <AsyncState v-else-if="page.records.length === 0" status="empty" compact title="当前没有消息" description="新的复习提醒或周报通知会出现在这里。" />
      <div v-else class="message-list">
        <article v-for="message in page.records" :key="message.id" class="message-item" :class="{ unread: message.isRead === 0 }">
          <span class="message-type" :class="typeMap[message.type]?.tone || 'navy'">{{ typeMap[message.type]?.label || message.type }}</span>
          <div class="message-copy"><h2><i v-if="message.isRead === 0" />{{ message.title }}</h2><p>{{ message.content || '这条消息没有附加内容。' }}</p><time>{{ message.createTime }}</time></div>
          <el-button v-if="message.isRead === 0" text :icon="Check" :loading="markingId === message.id" @click="markRead(message)">标记已读</el-button>
          <span v-else class="read-mark">已读</span>
        </article>
      </div>

      <el-pagination v-if="page.total > page.size" v-model:current-page="pageNum" :page-size="page.size" :total="page.total" layout="prev, pager, next, total" class="message-pagination" @current-change="load" />
    </PaperPanel>
  </div>
</template>

<style scoped>
.message-page{display:grid;gap:20px}.message-toolbar{display:flex;align-items:center;gap:7px;margin-bottom:16px;padding-bottom:15px;border-bottom:1px solid var(--line)}.message-toolbar button{min-height:36px;padding:0 15px;border:1px solid var(--line);border-radius:999px;background:var(--paper-bright);color:var(--ink-soft);cursor:pointer}.message-toolbar button.active{border-color:var(--cinnabar);background:var(--cinnabar-pale);color:var(--cinnabar-dark);font-weight:800}.message-toolbar span{margin-left:auto;color:var(--ink-faint);font-size:10px}.message-list{display:grid}.message-item{display:grid;grid-template-columns:90px minmax(0,1fr) auto;align-items:start;gap:16px;padding:18px 4px;border-bottom:1px dashed var(--line);opacity:.72}.message-item:last-child{border-bottom:0}.message-item.unread{opacity:1}.message-type{justify-self:start;padding:5px 9px;border:1px solid var(--line);border-radius:999px;font-size:9px;font-weight:800}.message-type.amber{border-color:var(--amber-light);background:var(--amber-pale);color:#795017}.message-type.jade{border-color:var(--jade-light);background:var(--jade-pale);color:var(--jade-dark)}.message-type.navy{background:#edf2f4;color:var(--navy)}.message-copy h2{display:flex;align-items:center;gap:7px;margin:0;color:var(--navy);font-size:14px}.message-copy h2 i{width:7px;height:7px;border-radius:50%;background:var(--cinnabar)}.message-copy p{margin:7px 0;color:var(--ink-soft);font-size:12px;line-height:1.7}.message-copy time{color:var(--ink-faint);font:9px var(--font-mono)}.read-mark{padding:8px;color:var(--ink-faint);font-size:10px}.message-pagination{justify-content:flex-end;margin-top:20px}
@media(max-width:650px){.message-toolbar{flex-wrap:wrap}.message-toolbar span{width:100%;margin-left:0}.message-item{grid-template-columns:1fr}.message-type{grid-row:1}.message-copy{grid-row:2}.message-item :deep(.el-button),.read-mark{grid-row:3;justify-self:start}}
</style>
