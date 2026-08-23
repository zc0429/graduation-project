<script setup lang="ts">
import { computed, type Component } from 'vue'
import { useRoute } from 'vue-router'
import {
  Bell,
  Collection,
  DataAnalysis,
  Document,
  EditPen,
  Fold,
  HomeFilled,
  List,
  Notebook,
  Reading,
  User,
  UserFilled,
} from '@element-plus/icons-vue'
import { useUserStore } from '@/store/user'
import AppBrand from '@/components/AppBrand.vue'

interface NavItem {
  path: string
  title: string
  icon: Component
  roles?: string[]
  accent?: boolean
}

const props = withDefaults(
  defineProps<{
    collapsed?: boolean
    unread?: number
  }>(),
  {
    collapsed: false,
    unread: 0,
  },
)

const emit = defineEmits<{
  toggle: []
}>()

const route = useRoute()
const store = useUserStore()

const primaryItems: NavItem[] = [
  { path: '/', title: '今日工作台', icon: HomeFilled },
  { path: '/question/create', title: '录入错题', icon: EditPen, roles: ['student'], accent: true },
  { path: '/question/list', title: '错题本', icon: Notebook, roles: ['student'] },
  { path: '/review', title: '复习计划', icon: Reading, roles: ['student'] },
  { path: '/report', title: '学情报告', icon: DataAnalysis, roles: ['student', 'teacher'] },
  { path: '/admin/user', title: '用户管理', icon: User, roles: ['admin'] },
  { path: '/admin/subject', title: '科目管理', icon: Collection, roles: ['admin'] },
  { path: '/admin/knowledge', title: '知识点管理', icon: List, roles: ['admin'] },
]

const utilityItems: NavItem[] = [
  { path: '/message', title: '消息中心', icon: Bell },
  { path: '/announcement', title: '系统公告', icon: Document },
  { path: '/profile', title: '个人中心', icon: UserFilled },
]

function visible(items: NavItem[]) {
  return items.filter((item) => !item.roles || item.roles.includes(store.role))
}

const visiblePrimary = computed(() => visible(primaryItems))
const visibleUtility = computed(() => visible(utilityItems))

function isActive(path: string) {
  if (path === '/') return route.path === '/'
  if (path === '/question/list') {
    return route.path === path || (route.path.startsWith('/question/') && route.path !== '/question/create')
  }
  return route.path === path
}

function accessibleLabel(item: NavItem) {
  if (item.path === '/message' && props.unread > 0) return `${item.title}，${props.unread} 条未读`
  return item.title
}
</script>

<template>
  <aside class="app-sidebar" :class="{ 'is-collapsed': collapsed }" aria-label="主导航">
    <div class="sidebar-head">
      <AppBrand :compact="collapsed" />
      <button
        class="collapse-button"
        type="button"
        :aria-label="collapsed ? '展开侧边导航' : '折叠侧边导航'"
        :aria-expanded="!collapsed"
        @click="emit('toggle')"
      >
        <el-icon><Fold /></el-icon>
      </button>
    </div>

    <nav class="sidebar-nav" aria-label="功能目录">
      <section class="nav-section" aria-labelledby="primary-nav-label">
        <p id="primary-nav-label" class="nav-caption">{{ store.role === 'admin' ? '数据目录' : '学习目录' }}</p>
        <RouterLink
          v-for="item in visiblePrimary"
          :key="item.path"
          :to="item.path"
          class="nav-link"
          :class="{ 'is-active': isActive(item.path), 'is-accent': item.accent }"
          :aria-current="isActive(item.path) ? 'page' : undefined"
          :aria-label="accessibleLabel(item)"
          :title="collapsed ? item.title : undefined"
        >
          <el-icon class="nav-icon"><component :is="item.icon" /></el-icon>
          <span class="nav-text">{{ item.title }}</span>
        </RouterLink>
      </section>

      <section class="nav-section utility-section" aria-labelledby="utility-nav-label">
        <p id="utility-nav-label" class="nav-caption">通用入口</p>
        <RouterLink
          v-for="item in visibleUtility"
          :key="item.path"
          :to="item.path"
          class="nav-link"
          :class="{ 'is-active': isActive(item.path) }"
          :aria-current="isActive(item.path) ? 'page' : undefined"
          :aria-label="accessibleLabel(item)"
          :title="collapsed ? item.title : undefined"
        >
          <el-icon class="nav-icon"><component :is="item.icon" /></el-icon>
          <span class="nav-text">{{ item.title }}</span>
          <span v-if="item.path === '/message' && unread > 0" class="unread-badge" aria-hidden="true">
            {{ unread > 99 ? '99+' : unread }}
          </span>
        </RouterLink>
      </section>
    </nav>

    <div class="sidebar-foot" aria-hidden="true">
      <span class="correction-seal">✓</span>
      <span>重做 · 自评 · 反馈<br>让错误留下线索</span>
    </div>
  </aside>
</template>

<style scoped>
.app-sidebar {
  position: sticky;
  top: 0;
  z-index: 30;
  display: flex;
  width: 244px;
  height: 100vh;
  flex: 0 0 244px;
  flex-direction: column;
  padding: 19px 15px 16px;
  border-right: 1px solid var(--line-strong);
  background:
    linear-gradient(90deg, rgba(24, 52, 74, 0.035) 1px, transparent 1px),
    var(--paper-bright);
  background-size: 24px 100%;
  box-shadow: 5px 0 25px rgba(24, 52, 74, 0.06);
  transition: width 220ms ease, flex-basis 220ms ease;
}

.app-sidebar.is-collapsed {
  width: 84px;
  flex-basis: 84px;
  padding-inline: 10px;
}

.sidebar-head {
  position: relative;
  display: flex;
  min-height: 58px;
  align-items: center;
  justify-content: space-between;
  padding: 0 4px 13px;
  border-bottom: 1px dashed var(--line);
}

.collapse-button {
  display: grid;
  width: 30px;
  height: 30px;
  flex: 0 0 auto;
  place-items: center;
  border: 1px solid var(--line);
  border-radius: 9px;
  background: var(--paper-bright);
  color: var(--ink-faint);
  cursor: pointer;
}

.is-collapsed .sidebar-head {
  justify-content: center;
}

.is-collapsed .collapse-button {
  position: absolute;
  right: -24px;
  bottom: -16px;
  transform: rotate(180deg);
}

.sidebar-nav {
  display: flex;
  min-height: 0;
  flex: 1;
  flex-direction: column;
  overflow-y: auto;
  padding-top: 15px;
  scrollbar-width: thin;
}

.nav-section {
  display: grid;
  gap: 4px;
}

.utility-section {
  margin-top: auto;
  padding-top: 18px;
}

.nav-caption {
  margin: 0 10px 6px;
  color: var(--ink-faint);
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.16em;
}

.nav-link {
  position: relative;
  display: flex;
  min-height: 45px;
  align-items: center;
  gap: 11px;
  padding: 9px 12px;
  border: 1px solid transparent;
  border-radius: 5px 12px 12px 5px;
  color: var(--ink-soft);
  text-decoration: none;
  transition: background 160ms ease, color 160ms ease, transform 160ms ease;
}

.nav-link:hover {
  background: rgba(22, 129, 114, 0.07);
  color: var(--jade-dark);
  transform: translateX(2px);
}

.nav-link.is-active {
  border-color: rgba(24, 52, 74, 0.12);
  background: var(--navy);
  box-shadow: 0 7px 16px rgba(24, 52, 74, 0.15);
  color: #fff;
  font-weight: 700;
}

.nav-link.is-active::before {
  position: absolute;
  top: 8px;
  bottom: 8px;
  left: -16px;
  width: 5px;
  border-radius: 0 4px 4px 0;
  background: var(--cinnabar);
  content: '';
}

.nav-link.is-accent:not(.is-active) {
  color: var(--cinnabar-dark);
}

.nav-icon {
  flex: 0 0 auto;
  font-size: 18px;
}

.nav-text {
  min-width: 0;
  overflow: hidden;
  font-size: 13px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.unread-badge {
  min-width: 20px;
  margin-left: auto;
  padding: 2px 5px;
  border-radius: 999px;
  background: var(--cinnabar);
  color: #fff;
  font-family: var(--font-mono);
  font-size: 9px;
  text-align: center;
}

.sidebar-foot {
  display: flex;
  align-items: center;
  gap: 9px;
  margin-top: 14px;
  padding: 11px 10px;
  border-top: 1px dashed var(--line);
  color: var(--ink-faint);
  font-size: 10px;
  line-height: 1.5;
}

.correction-seal {
  display: grid;
  width: 31px;
  height: 31px;
  flex: 0 0 auto;
  place-items: center;
  border: 1px solid rgba(183, 67, 50, 0.35);
  border-radius: 50%;
  color: var(--cinnabar);
  font-size: 18px;
  font-weight: 800;
  transform: rotate(-8deg);
}

.is-collapsed .nav-caption,
.is-collapsed .nav-text,
.is-collapsed .unread-badge,
.is-collapsed .sidebar-foot {
  display: none;
}

.is-collapsed .nav-link {
  justify-content: center;
  padding-inline: 9px;
}

.is-collapsed .nav-link.is-active::before {
  left: -10px;
}

@media (max-width: 1180px) {
  .app-sidebar,
  .app-sidebar.is-collapsed {
    width: 84px;
    flex-basis: 84px;
    padding-inline: 10px;
  }

  .sidebar-head {
    justify-content: center;
  }

  .collapse-button,
  .nav-caption,
  .nav-text,
  .unread-badge,
  .sidebar-foot {
    display: none;
  }

  .nav-link {
    justify-content: center;
    min-height: 50px;
    padding-inline: 9px;
  }

  .nav-link.is-active::before {
    left: -10px;
  }
}

@media (max-width: 700px) {
  .app-sidebar {
    display: none;
  }
}

@media (prefers-reduced-motion: reduce) {
  .app-sidebar,
  .nav-link {
    transition: none;
  }
}
</style>
