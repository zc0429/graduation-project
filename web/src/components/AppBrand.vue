<script setup lang="ts">
withDefaults(
  defineProps<{
    compact?: boolean
    subtitle?: string
  }>(),
  {
    compact: false,
    subtitle: '学习工作台',
  },
)
</script>

<template>
  <RouterLink class="app-brand" :class="{ 'is-compact': compact }" to="/" aria-label="知错首页">
    <span class="brand-mark" aria-hidden="true">
      <svg viewBox="0 0 32 32" focusable="false">
        <path d="M7.2 5.5h7.1c2.2 0 3.9 1.8 3.9 3.9v16.1h-7.1a3.9 3.9 0 0 0-3.9 3.9V5.5Z" />
        <path d="M24.8 5.5h-6.6v20h6.6V5.5Z" />
        <path class="brand-check" d="m12 15.8 2.3 2.3 5.6-6.2" />
      </svg>
    </span>
    <span class="brand-copy">
      <strong>知错</strong>
      <span>{{ subtitle }}</span>
    </span>
  </RouterLink>
</template>

<style scoped>
.app-brand {
  display: inline-flex;
  align-items: center;
  gap: 11px;
  min-width: 0;
  color: var(--navy);
  text-decoration: none;
}

.brand-mark {
  position: relative;
  display: grid;
  place-items: center;
  width: 42px;
  height: 42px;
  flex: 0 0 auto;
  border: 1px solid rgba(24, 52, 74, 0.18);
  border-radius: 13px 13px 13px 5px;
  background: var(--paper-bright);
  box-shadow: 0 5px 14px rgba(24, 52, 74, 0.09);
  transform: rotate(-1.5deg);
}

.brand-mark::after {
  position: absolute;
  right: -4px;
  bottom: 5px;
  width: 13px;
  height: 3px;
  border-radius: 2px;
  background: var(--cinnabar);
  content: '';
  transform: rotate(-8deg);
}

.brand-mark svg {
  width: 29px;
  height: 29px;
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.6;
}

.brand-mark .brand-check {
  stroke: var(--cinnabar);
  stroke-width: 2.1;
}

.brand-copy {
  display: flex;
  min-width: 0;
  flex-direction: column;
  line-height: 1.15;
}

.brand-copy strong {
  font-family: var(--font-display);
  font-size: 27px;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.brand-copy span {
  margin-top: 3px;
  color: var(--ink-faint);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.13em;
  white-space: nowrap;
}

.app-brand.is-compact .brand-copy {
  display: none;
}

@media (max-width: 1180px) {
  .brand-copy {
    display: none;
  }
}
</style>
