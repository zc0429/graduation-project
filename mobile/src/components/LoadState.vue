<script setup>
defineProps({
  loading: Boolean,
  error: String,
  empty: Boolean,
  loadingText: { type: String, default: '正在加载…' },
  emptyText: { type: String, default: '暂无数据' },
})
defineEmits(['retry'])
</script>

<template>
  <view v-if="loading" class="card muted">{{ loadingText }}</view>
  <view v-else-if="error" class="card">
    <text class="copy error">{{ error }}</text>
    <button class="action" @tap="$emit('retry')">重试</button>
  </view>
  <view v-else-if="empty" class="card muted">{{ emptyText }}</view>
  <slot v-else />
</template>
