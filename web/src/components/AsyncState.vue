<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    status: 'loading' | 'empty' | 'error' | 'forbidden'
    title?: string
    description?: string
    compact?: boolean
    retryLabel?: string
  }>(),
  {
    title: '',
    description: '',
    compact: false,
    retryLabel: '重新加载',
  },
)

const emit = defineEmits<{
  retry: []
}>()

const defaults = {
  loading: ['正在整理内容', '请稍候，知错正在装订这一页。'],
  empty: ['这一页还是空的', '完成第一步后，内容会出现在这里。'],
  error: ['内容加载失败', '请检查网络后再试一次。'],
  forbidden: ['暂时无法查看', '当前账号没有访问此内容的权限。'],
} as const

const visibleTitle = computed(() => props.title || defaults[props.status][0])
const visibleDescription = computed(() => props.description || defaults[props.status][1])
const liveRole = computed(() => (props.status === 'error' || props.status === 'forbidden' ? 'alert' : 'status'))
</script>

<template>
  <section
    class="async-state"
    :class="[`is-${status}`, { 'is-compact': compact }]"
    :role="liveRole"
    :aria-busy="status === 'loading'"
    aria-live="polite"
  >
    <span class="state-mark" aria-hidden="true">
      <span v-if="status === 'loading'" class="loading-ring" />
      <svg v-else viewBox="0 0 32 32" focusable="false">
        <path v-if="status === 'empty'" d="M6 8.5h8.2c2.1 0 3.8 1.7 3.8 3.8V26h-8.2A3.8 3.8 0 0 0 6 29.8V8.5Zm20 0h-8V26h8V8.5Z" />
        <path v-else-if="status === 'forbidden'" d="M9 14V9a7 7 0 0 1 14 0v5M7 14h18v14H7V14Zm9 6v4" />
        <path v-else d="M16 4 29 27H3L16 4Zm0 8v7m0 4h.01" />
      </svg>
    </span>
    <h2>{{ visibleTitle }}</h2>
    <p>{{ visibleDescription }}</p>
    <div v-if="status === 'error' || $slots.action" class="state-actions">
      <slot name="action">
        <button type="button" @click="emit('retry')">{{ retryLabel }}</button>
      </slot>
    </div>
  </section>
</template>

<style scoped>
.async-state {
  display: grid;
  min-height: 250px;
  place-items: center;
  align-content: center;
  padding: 34px 20px;
  color: var(--ink-soft);
  text-align: center;
}

.state-mark {
  display: grid;
  width: 58px;
  height: 58px;
  margin-bottom: 15px;
  place-items: center;
  border: 1px solid var(--line);
  border-radius: 17px 17px 17px 6px;
  background: var(--paper-bright);
  color: var(--jade-dark);
  box-shadow: var(--shadow-soft);
  transform: rotate(-1.5deg);
}

.state-mark svg {
  width: 30px;
  height: 30px;
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.7;
}

.is-error .state-mark,
.is-forbidden .state-mark {
  color: var(--cinnabar);
}

.loading-ring {
  width: 26px;
  height: 26px;
  border: 3px solid var(--jade-pale);
  border-top-color: var(--jade);
  border-radius: 50%;
  animation: state-spin 800ms linear infinite;
}

@keyframes state-spin {
  to {
    transform: rotate(360deg);
  }
}

h2 {
  margin: 0;
  color: var(--navy);
  font-family: var(--font-serif);
  font-size: 19px;
}

p {
  max-width: 420px;
  margin: 8px 0 0;
  font-size: 12px;
  line-height: 1.7;
}

.state-actions {
  margin-top: 18px;
}

.state-actions button {
  min-height: 38px;
  padding: 8px 16px;
  border: 1px solid var(--navy);
  border-radius: 9px;
  background: var(--navy);
  color: #fff;
  cursor: pointer;
  font-size: 12px;
  font-weight: 700;
}

.async-state.is-compact {
  min-height: 170px;
  padding: 24px 16px;
}

.async-state.is-compact .state-mark {
  width: 48px;
  height: 48px;
}

@media (prefers-reduced-motion: reduce) {
  .loading-ring {
    animation-duration: 1.8s;
  }
}
</style>
