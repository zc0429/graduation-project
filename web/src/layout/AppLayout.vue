<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, provide, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { messageApi } from '@/api'
import AppSidebar from '@/components/AppSidebar.vue'
import AppTopbar from '@/components/AppTopbar.vue'
import MobileNav from '@/components/MobileNav.vue'

const route = useRoute()
const unread = ref(0)
const mainRef = ref<HTMLElement>()
const collapsed = ref(localStorage.getItem('ui.sidebar-collapsed') === '1')

async function loadUnread() {
  try {
    unread.value = await messageApi.unreadCount()
  } catch {
    // 未读角标属于辅助信息，失败时不阻塞页面主体。
  }
}

function toggleSidebar() {
  collapsed.value = !collapsed.value
  localStorage.setItem('ui.sidebar-collapsed', collapsed.value ? '1' : '0')
}

function handleUnreadChange() {
  void loadUnread()
}

async function focusMainContent() {
  await nextTick()
  const main = mainRef.value
  main?.scrollTo({ top: 0, behavior: 'auto' })
  main?.focus({ preventScroll: true })
}

provide('refreshUnreadCount', loadUnread)

watch(
  () => route.fullPath,
  () => void focusMainContent(),
)

onMounted(() => {
  void loadUnread()
  void focusMainContent()
  window.addEventListener('message-unread-changed', handleUnreadChange)
})

onBeforeUnmount(() => {
  window.removeEventListener('message-unread-changed', handleUnreadChange)
})
</script>

<template>
  <div class="app-layout" :class="{ 'has-collapsed-sidebar': collapsed }">
    <a class="skip-link" href="#main-content">跳到主要内容</a>
    <AppSidebar :collapsed="collapsed" :unread="unread" @toggle="toggleSidebar" />

    <div class="app-workspace">
      <AppTopbar :unread="unread" />
      <main id="main-content" ref="mainRef" class="app-main" tabindex="-1">
        <router-view v-slot="{ Component }">
          <component :is="Component" :key="route.fullPath" class="route-page" />
        </router-view>
      </main>
    </div>

    <MobileNav :unread="unread" @navigated="focusMainContent" />
  </div>
</template>

<style scoped>
.app-layout {
  display: flex;
  width: 100%;
  min-width: 320px;
  min-height: 100vh;
  min-height: 100dvh;
  background: var(--paper);
}

.app-workspace {
  width: calc(100% - 244px);
  min-width: 0;
  min-height: 100vh;
  min-height: 100dvh;
  flex: 1;
}

.has-collapsed-sidebar .app-workspace {
  width: calc(100% - 84px);
}

.app-main {
  position: relative;
  height: calc(100vh - 70px);
  height: calc(100dvh - 70px);
  padding: 30px clamp(22px, 3vw, 46px) 48px;
  overflow-x: hidden;
  overflow-y: auto;
  background:
    linear-gradient(rgba(24, 52, 74, 0.025) 1px, transparent 1px),
    linear-gradient(90deg, rgba(24, 52, 74, 0.025) 1px, transparent 1px),
    var(--paper);
  background-size: 24px 24px;
  scroll-behavior: smooth;
}

.app-main::before {
  position: fixed;
  z-index: 0;
  top: 70px;
  bottom: 0;
  left: calc(244px + clamp(22px, 3vw, 46px) + 16px);
  width: 2px;
  background: rgba(183, 67, 50, 0.1);
  content: '';
  pointer-events: none;
}

.has-collapsed-sidebar .app-main::before {
  left: calc(84px + clamp(22px, 3vw, 46px) + 16px);
}

.route-page {
  position: relative;
  z-index: 1;
  width: min(100%, 1440px);
  margin-inline: auto;
  animation: route-enter 360ms cubic-bezier(0.22, 0.72, 0.24, 1) both;
}

@keyframes route-enter {
  from {
    opacity: 0;
    transform: translateY(7px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 1180px) {
  .app-workspace,
  .has-collapsed-sidebar .app-workspace {
    width: calc(100% - 84px);
  }

  .app-main::before,
  .has-collapsed-sidebar .app-main::before {
    left: calc(84px + clamp(22px, 3vw, 46px) + 16px);
  }
}

@media (max-width: 700px) {
  .app-workspace,
  .has-collapsed-sidebar .app-workspace {
    width: 100%;
  }

  .app-main {
    height: calc(100vh - 62px);
    height: calc(100dvh - 62px);
    padding: 22px 14px calc(104px + env(safe-area-inset-bottom));
  }

  .app-main::before {
    display: none;
  }
}

@media (prefers-reduced-motion: reduce) {
  .app-main {
    scroll-behavior: auto;
  }

  .route-page {
    animation: none;
  }
}
</style>
