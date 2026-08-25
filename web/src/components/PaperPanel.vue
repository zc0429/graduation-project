<script setup lang="ts">
withDefaults(
  defineProps<{
    as?: string
    variant?: 'default' | 'lined' | 'annotation'
    hoverable?: boolean
    padded?: boolean
  }>(),
  {
    as: 'div',
    variant: 'default',
    hoverable: false,
    padded: true,
  },
)
</script>

<template>
  <component
    :is="as"
    class="paper-panel"
    :class="[`is-${variant}`, { 'is-hoverable': hoverable, 'has-padding': padded }]"
  >
    <slot />
  </component>
</template>

<style scoped>
.paper-panel {
  position: relative;
  min-width: 0;
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: rgba(255, 253, 248, 0.94);
  box-shadow: var(--shadow-soft);
}

.paper-panel.has-padding {
  padding: 24px;
}

.paper-panel.is-lined {
  background:
    linear-gradient(90deg, transparent 0 38px, rgba(183, 67, 50, 0.16) 38px 40px, transparent 40px),
    repeating-linear-gradient(180deg, transparent 0 31px, rgba(37, 78, 102, 0.09) 31px 32px),
    var(--paper-bright);
}

.paper-panel.is-lined.has-padding {
  padding-left: 58px;
}

.paper-panel.is-annotation {
  border-color: rgba(183, 67, 50, 0.24);
  border-radius: 5px 16px 16px 16px;
  background: var(--cinnabar-pale);
  box-shadow: none;
  color: var(--cinnabar-dark);
  transform: rotate(-0.25deg);
}

.paper-panel.is-annotation::before {
  position: absolute;
  top: 16px;
  bottom: 16px;
  left: 0;
  width: 4px;
  border-radius: 0 3px 3px 0;
  background: var(--cinnabar);
  content: '';
}

.paper-panel.is-hoverable {
  transition: border-color 180ms ease, box-shadow 180ms ease, transform 180ms ease;
}

.paper-panel.is-hoverable:hover {
  border-color: rgba(22, 129, 114, 0.32);
  box-shadow: var(--shadow);
  transform: translateY(-2px);
}

@media (max-width: 700px) {
  .paper-panel.has-padding {
    padding: 19px 16px;
  }

  .paper-panel.is-lined.has-padding {
    padding-left: 45px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .paper-panel.is-hoverable {
    transition: none;
  }
}
</style>
