<script setup lang="ts">
import { computed, ref, type Component } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Bell,
  Collection,
  DataAnalysis,
  Document,
  EditPen,
  Grid,
  HomeFilled,
  List,
  MoreFilled,
  Notebook,
  Reading,
  Timer,
  User,
  UserFilled,
} from '@element-plus/icons-vue'
import { ElMessageBox } from 'element-plus'
import { useUserStore } from '@/store/user'

interface MobileItem {
  path: string
  title: string
  icon: Component
}

withDefaults(
  defineProps<{
    unread?: number
  }>(),
  {
    unread: 0,
  },
)

const emit = defineEmits<{
  navigated: []
}>()

const route = useRoute()
const router = useRouter()
const store = useUserStore()
const drawerOpen = ref(false)
const navigationPending = ref(false)

const home: MobileItem = { path: '/', title: '首页', icon: HomeFilled }
const message: MobileItem = { path: '/message', title: '消息', icon: Bell }
const announcement: MobileItem = { path: '/announcement', title: '公告', icon: Document }
const profile: MobileItem = { path: '/profile', title: '个人中心', icon: UserFilled }

const primaryItems = computed<MobileItem[]>(() => {
  if (store.role === 'student') {
    return [
      home,
      { path: '/question/list', title: '错题', icon: Notebook },
      { path: '/question/create', title: '录入', icon: EditPen },
      { path: '/review', title: '复习', icon: Reading },
    ]
  }
  if (store.role === 'teacher') {
    return [home, { path: '/report', title: '报告', icon: DataAnalysis }, message, announcement]
  }
  return [home, { path: '/admin/user', title: '管理', icon: Grid }, announcement, message]
})

const moreItems = computed<MobileItem[]>(() => {
  if (store.role === 'student') {
    return [
      { path: '/practice/history', title: '练习历史', icon: Timer },
      { path: '/report', title: '学情报告', icon: DataAnalysis },
      message,
      announcement,
      profile,
    ]
  }
  if (store.role === 'teacher') return [profile]
  return [
    { path: '/admin/subject', title: '科目管理', icon: Collection },
    { path: '/admin/knowledge', title: '知识点管理', icon: List },
    profile,
  ]
})

function isActive(path: string) {
  if (path === '/') return route.path === '/'
  if (path === '/question/list') {
    return route.path === path || (route.path.startsWith('/question/') && route.path !== '/question/create')
  }
  return route.path === path
}

const moreActive = computed(() => moreItems.value.some((item) => isActive(item.path)))

function closeDrawer() {
  navigationPending.value = true
  drawerOpen.value = false
}

function handleDrawerClosed() {
  if (!navigationPending.value) return
  navigationPending.value = false
  emit('navigated')
}

async function handleLogout() {
  try {
    await ElMessageBox.confirm('确定退出当前账号吗？', '退出登录', {
      confirmButtonText: '退出',
      cancelButtonText: '继续学习',
      type: 'warning',
    })
  } catch {
    return
  }
  drawerOpen.value = false
  store.logout()
  await router.replace('/login')
}
</script>

<template>
  <nav class="mobile-nav" aria-label="移动端核心导航">
    <RouterLink
      v-for="item in primaryItems"
      :key="item.path"
      :to="item.path"
      class="mobile-nav-link"
      :class="{ 'is-active': isActive(item.path), 'is-record': item.path === '/question/create' }"
      :aria-current="isActive(item.path) ? 'page' : undefined"
    >
      <span class="mobile-icon-wrap">
        <el-icon><component :is="item.icon" /></el-icon>
        <span v-if="item.path === '/message' && unread > 0" class="mobile-dot" aria-hidden="true" />
      </span>
      <span>{{ item.title }}</span>
    </RouterLink>
    <button
      class="mobile-nav-link"
      :class="{ 'is-active': moreActive }"
      type="button"
      aria-haspopup="dialog"
      :aria-label="moreActive ? '更多功能，当前页面在此菜单中' : '更多功能'"
      :aria-expanded="drawerOpen"
      @click="drawerOpen = true"
    >
      <span class="mobile-icon-wrap"><el-icon><MoreFilled /></el-icon></span>
      <span>更多</span>
    </button>
  </nav>

  <el-drawer
    v-model="drawerOpen"
    title="更多功能"
    direction="btt"
    size="min(72vh, 540px)"
    append-to-body
    class="mobile-more-drawer"
    @closed="handleDrawerClosed"
  >
    <div class="drawer-intro">
      <span class="drawer-seal" aria-hidden="true"><el-icon><Grid /></el-icon></span>
      <div>
        <strong>知错 · 更多功能</strong>
        <p>消息、资料与管理入口都收在这里。</p>
      </div>
    </div>
    <nav class="drawer-links" aria-label="更多功能">
      <RouterLink
        v-for="item in moreItems"
        :key="item.path"
        :to="item.path"
        class="drawer-link"
        :aria-current="isActive(item.path) ? 'page' : undefined"
        @click="closeDrawer"
      >
        <el-icon><component :is="item.icon" /></el-icon>
        <span>{{ item.title }}</span>
        <span v-if="item.path === '/message' && unread > 0" class="drawer-badge">{{ unread }} 条未读</span>
      </RouterLink>
    </nav>
    <button class="logout-button" type="button" @click="handleLogout">
      <el-icon><User /></el-icon>
      退出当前账号
    </button>
  </el-drawer>
</template>

<style scoped>
.mobile-nav {
  display: none;
}

@media (max-width: 700px) {
  .mobile-nav {
    position: fixed;
    z-index: 45;
    right: 12px;
    bottom: max(10px, env(safe-area-inset-bottom));
    left: 12px;
    display: grid;
    grid-template-columns: repeat(5, minmax(0, 1fr));
    min-height: 66px;
    padding: 7px;
    border: 1px solid rgba(24, 52, 74, 0.18);
    border-radius: 19px;
    background: rgba(255, 253, 248, 0.96);
    box-shadow: 0 14px 32px rgba(24, 52, 74, 0.2);
    backdrop-filter: blur(16px);
  }

  .mobile-nav-link {
    position: relative;
    display: flex;
    min-width: 0;
    min-height: 50px;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 3px;
    border: 0;
    border-radius: 12px;
    background: transparent;
    color: var(--ink-faint);
    cursor: pointer;
    font-size: 9px;
    font-weight: 700;
    text-decoration: none;
  }

  .mobile-icon-wrap {
    position: relative;
    display: grid;
    place-items: center;
  }

  .mobile-icon-wrap :deep(.el-icon) {
    font-size: 19px;
  }

  .mobile-nav-link.is-active {
    background: var(--jade-pale);
    color: var(--jade-dark);
  }

  .mobile-nav-link.is-record {
    color: var(--cinnabar-dark);
  }

  .mobile-nav-link.is-record .mobile-icon-wrap {
    width: 32px;
    height: 27px;
    border-radius: 9px 9px 9px 3px;
    background: var(--cinnabar-pale);
  }

  .mobile-nav-link.is-record.is-active {
    background: var(--cinnabar-pale);
  }

  .mobile-dot {
    position: absolute;
    top: -2px;
    right: -4px;
    width: 7px;
    height: 7px;
    border: 2px solid var(--paper-bright);
    border-radius: 50%;
    background: var(--cinnabar);
  }
}

.drawer-intro {
  display: flex;
  align-items: center;
  gap: 13px;
  margin-bottom: 18px;
  padding: 0 2px 17px;
  border-bottom: 1px dashed var(--line);
}

.drawer-seal {
  display: grid;
  width: 42px;
  height: 42px;
  flex: 0 0 auto;
  place-items: center;
  border-radius: 13px 13px 13px 5px;
  background: var(--navy);
  color: #fff;
}

.drawer-intro strong {
  color: var(--navy);
  font-family: var(--font-serif);
  font-size: 16px;
}

.drawer-intro p {
  margin: 4px 0 0;
  color: var(--ink-faint);
  font-size: 11px;
}

.drawer-links {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.drawer-link {
  display: grid;
  min-height: 76px;
  grid-template-columns: 28px minmax(0, 1fr);
  align-items: center;
  gap: 9px;
  padding: 13px;
  border: 1px solid var(--line);
  border-radius: 13px;
  background: var(--paper-bright);
  color: var(--ink-soft);
  text-decoration: none;
}

.drawer-link[aria-current='page'] {
  border-color: rgba(22, 129, 114, 0.35);
  background: var(--jade-pale);
  color: var(--jade-dark);
}

.drawer-link :deep(.el-icon) {
  color: var(--navy);
  font-size: 20px;
}

.drawer-link > span:nth-child(2) {
  font-size: 12px;
  font-weight: 700;
}

.drawer-badge {
  grid-column: 2;
  margin-top: -18px;
  color: var(--cinnabar-dark);
  font-size: 9px;
}

.logout-button {
  display: flex;
  width: 100%;
  min-height: 44px;
  align-items: center;
  justify-content: center;
  gap: 7px;
  margin-top: 17px;
  border: 1px solid rgba(183, 67, 50, 0.25);
  border-radius: 12px;
  background: var(--cinnabar-pale);
  color: var(--cinnabar-dark);
  cursor: pointer;
  font-weight: 700;
}
</style>

<style>
.mobile-more-drawer.el-drawer {
  border-radius: 22px 22px 0 0;
  background: var(--paper);
}

.mobile-more-drawer .el-drawer__header {
  margin-bottom: 8px;
  color: var(--navy);
  font-family: var(--font-serif);
  font-weight: 700;
}

.mobile-more-drawer .el-drawer__body {
  padding-top: 8px;
  padding-bottom: max(20px, env(safe-area-inset-bottom));
}
</style>
