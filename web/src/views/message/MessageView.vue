<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { messageApi, type Message, type PageData } from '@/api'

const page = ref<PageData<Message>>({ records: [], total: 0, current: 1, size: 10 })
const loading = ref(false)
const pageNum = ref(1)
const filterRead = ref<number>()

const typeMap: Record<string, { label: string; type: 'warning' | 'success' | 'info' }> = {
  review_remind: { label: '复习提醒', type: 'warning' },
  report: { label: '学情报告', type: 'success' },
  system: { label: '系统', type: 'info' },
}

async function load() {
  loading.value = true
  try {
    page.value = await messageApi.page({ pageNum: pageNum.value, pageSize: 10, isRead: filterRead.value })
  } finally {
    loading.value = false
  }
}

async function markRead(m: Message) {
  await messageApi.markRead(m.id)
  m.isRead = 1
}

function onFilterChange() {
  pageNum.value = 1
  load()
}

onMounted(load)
</script>

<template>
  <div>
    <div class="head-row">
      <div>
        <h2 class="page-title">消息中心</h2>
        <p class="page-subtitle">复习提醒、报告生成与系统通知。</p>
      </div>
      <el-radio-group v-model="filterRead" @change="onFilterChange">
        <el-radio-button :value="undefined">全部</el-radio-button>
        <el-radio-button :value="0">未读</el-radio-button>
        <el-radio-button :value="1">已读</el-radio-button>
      </el-radio-group>
    </div>
    <div class="paper-card" v-loading="loading">
      <el-empty v-if="page.records.length === 0" description="暂无消息" :image-size="80" />
      <div v-for="m in page.records" :key="m.id" class="msg-row" :class="{ unread: m.isRead === 0 }">
        <el-tag :type="typeMap[m.type]?.type || 'info'" size="small" effect="light" class="msg-type">
          {{ typeMap[m.type]?.label || m.type }}
        </el-tag>
        <div class="msg-main">
          <div class="msg-title">
            <span v-if="m.isRead === 0" class="dot" />{{ m.title }}
          </div>
          <div class="msg-content">{{ m.content }}</div>
        </div>
        <div class="msg-side">
          <span class="msg-time num">{{ m.createTime }}</span>
          <el-button v-if="m.isRead === 0" size="small" link type="primary" @click="markRead(m)">标记已读</el-button>
        </div>
      </div>
      <el-pagination
        v-if="page.total > 10"
        v-model:current-page="pageNum"
        :total="page.total"
        :page-size="10"
        layout="prev, pager, next, total"
        class="pager"
        @current-change="load"
      />
    </div>
  </div>
</template>

<style scoped>
.head-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.msg-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px 8px;
  border-bottom: 1px solid var(--wb-border);
}

.msg-row:last-child {
  border-bottom: none;
}

.msg-type {
  flex-shrink: 0;
  margin-top: 2px;
}

.msg-main {
  flex: 1;
  min-width: 0;
}

.msg-title {
  font-size: 14px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 6px;
}

.msg-row.unread .msg-title {
  color: var(--wb-primary-dark);
}

.dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--wb-accent);
  display: inline-block;
}

.msg-content {
  font-size: 13px;
  color: var(--wb-ink-secondary);
  margin-top: 4px;
  line-height: 1.6;
}

.msg-side {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
  flex-shrink: 0;
}

.msg-time {
  font-size: 12px;
  color: var(--wb-ink-secondary);
}

.pager {
  margin-top: 16px;
  justify-content: center;
}
</style>
