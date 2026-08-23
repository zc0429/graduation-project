<script setup lang="ts">
import { useId } from 'vue'

withDefaults(
  defineProps<{
    title: string
    description?: string
    eyebrow?: string
    compact?: boolean
  }>(),
  {
    description: '',
    eyebrow: '',
    compact: false,
  },
)

const titleId = `page-title-${useId()}`
</script>

<template>
  <header class="page-header" :class="{ 'is-compact': compact }" :aria-labelledby="titleId">
    <div class="page-heading-copy">
      <p v-if="eyebrow" class="page-eyebrow">{{ eyebrow }}</p>
      <h1 :id="titleId">{{ title }}</h1>
      <p v-if="description" class="page-description">{{ description }}</p>
      <slot />
    </div>
    <div v-if="$slots.actions" class="page-header-actions">
      <slot name="actions" />
    </div>
  </header>
</template>

<style scoped>
.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 28px;
  margin-bottom: 26px;
}

.page-heading-copy {
  min-width: 0;
  max-width: 820px;
}

.page-eyebrow {
  margin: 0 0 8px;
  color: var(--cinnabar-dark);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

h1 {
  margin: 0;
  color: var(--navy);
  font-family: var(--font-serif);
  font-size: clamp(27px, 2.35vw, 38px);
  font-weight: 700;
  letter-spacing: -0.025em;
  line-height: 1.25;
}

.page-description {
  margin: 9px 0 0;
  color: var(--ink-soft);
  font-size: 13px;
  line-height: 1.75;
}

.page-header-actions {
  display: flex;
  flex: 0 0 auto;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
  gap: 9px;
  padding-top: 7px;
}

.page-header.is-compact {
  margin-bottom: 18px;
}

.page-header.is-compact h1 {
  font-size: clamp(24px, 2vw, 31px);
}

@media (max-width: 700px) {
  .page-header {
    display: block;
    margin-bottom: 20px;
  }

  h1 {
    font-size: 27px;
  }

  .page-description {
    font-size: 12px;
  }

  .page-header-actions {
    justify-content: flex-start;
    padding-top: 15px;
  }
}
</style>
