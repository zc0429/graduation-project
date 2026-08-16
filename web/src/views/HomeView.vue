<script setup lang="ts">
import { onMounted, ref } from 'vue'
import request from '@/utils/request'

const health = ref('')

onMounted(async () => {
  const data = await request.get<unknown, { status: string }>('/health')
  health.value = data.status
})
</script>

<template>
  <div style="max-width: 640px; margin: 80px auto; text-align: center">
    <h2>AI 错题分析与学习推荐系统</h2>
    <el-tag v-if="health" type="success">后端连通：{{ health }}</el-tag>
    <el-tag v-else type="info">正在连接后端…</el-tag>
  </div>
</template>
