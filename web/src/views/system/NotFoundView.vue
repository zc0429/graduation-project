<script setup lang="ts">
import { useRouter } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'
import PaperPanel from '@/components/PaperPanel.vue'

const router = useRouter()
</script>

<template>
  <PaperPanel variant="lined" class="not-found">
    <span class="error-mark">404</span>
    <p>这张书签没有对应页面。</p>
    <h1>页面未找到</h1>
    <span>链接可能已经失效，或当前功能并不存在。返回工作台继续学习。</span>
    <el-button type="primary" :icon="ArrowLeft" @click="router.replace('/')">返回今日工作台</el-button>
  </PaperPanel>
</template>

<style scoped>
.not-found{min-height:460px;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center}.error-mark{color:var(--cinnabar);font:italic 62px var(--font-display);transform:rotate(-4deg)}.not-found p{margin:10px 0 0;color:var(--cinnabar);font-size:11px;font-weight:800;letter-spacing:.15em}.not-found h1{margin:9px 0;color:var(--navy);font:800 38px var(--font-display)}.not-found>span:not(.error-mark){margin-bottom:23px;color:var(--ink-soft);font-size:13px}
</style>
