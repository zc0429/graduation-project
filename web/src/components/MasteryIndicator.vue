<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    value: number
    label?: string
    compact?: boolean
    showLabel?: boolean
  }>(),
  {
    label: '掌握度',
    compact: false,
    showLabel: true,
  },
)

const normalizedValue = computed(() => Math.min(100, Math.max(0, Math.round(Number(props.value) || 0))))
const tone = computed(() => {
  if (normalizedValue.value < 40) return 'low'
  if (normalizedValue.value < 70) return 'medium'
  return 'high'
})
</script>

<template>
  <div
    class="mastery-indicator"
    :class="[`is-${tone}`, { 'is-compact': compact }]"
    role="progressbar"
    :aria-label="label"
    aria-valuemin="0"
    aria-valuemax="100"
    :aria-valuenow="normalizedValue"
    :aria-valuetext="`${label} ${normalizedValue}%`"
  >
    <div v-if="showLabel" class="mastery-copy">
      <span>{{ label }}</span>
      <strong class="num">{{ normalizedValue }}%</strong>
    </div>
    <div class="mastery-track" aria-hidden="true">
      <i :style="{ width: `${normalizedValue}%` }" />
    </div>
  </div>
</template>

<style scoped>
.mastery-indicator {
  --mastery-color: var(--jade);
  min-width: 112px;
}

.mastery-indicator.is-low {
  --mastery-color: var(--cinnabar);
}

.mastery-indicator.is-medium {
  --mastery-color: var(--amber);
}

.mastery-copy {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 7px;
  color: var(--ink-faint);
  font-size: 11px;
}

.mastery-copy strong {
  color: var(--mastery-color);
  font-size: 12px;
}

.mastery-track {
  height: 7px;
  overflow: hidden;
  border-radius: 999px;
  background: var(--paper-deep);
}

.mastery-track i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: var(--mastery-color);
  transition: width 300ms cubic-bezier(0.22, 0.72, 0.24, 1);
}

.mastery-indicator.is-compact {
  min-width: 82px;
}

.mastery-indicator.is-compact .mastery-copy {
  margin-bottom: 4px;
  font-size: 10px;
}

.mastery-indicator.is-compact .mastery-track {
  height: 5px;
}

@media (prefers-reduced-motion: reduce) {
  .mastery-track i {
    transition: none;
  }
}
</style>
