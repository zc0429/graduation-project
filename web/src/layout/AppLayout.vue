<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import {
  ArrowDown,
  Bell,
  Collection,
  DataAnalysis,
  Document,
  EditPen,
  Files,
  HomeFilled,
  List,
  Notebook,
  Reading,
  User,
  UserFilled,
} from '@element-plus/icons-vue'
import { useUserStore } from '@/store/user'
import { messageApi } from '@/api'

const route = useRoute()
const router = useRouter()
const store = useUserStore()
const unread = ref(0)

interface MenuItem {
  path: string
  title: string
  icon: unknown
  roles?: string[]
}

const menus: MenuItem[] = [
  { path: '/', title: '首页', icon: HomeFilled },
  { path: '/question/create', title: '错题录入', icon: EditPen, roles: ['student'] },
  { path: '/question/list', title: '错题本', icon: Notebook, roles: ['student'] },
  { path: '/review', title: '复习计划', icon: Reading, roles: ['student'] },
  { path: '/report', title: '学情报告', icon: DataAnalysis, roles: ['student', 'teacher'] },
  { path: '/message', title: '消息中心', icon: Bell },
  { path: '/announcement', title: '公告', icon: Document },
  { path: '/admin/user', title: '用户管理', icon: User, roles: ['admin'] },
  { path: '/admin/subject', title: '科目管理', icon: Collection, roles: ['admin'] },
  { path: '/admin/knowledge', title: '知识点管理', icon: List, roles: ['admin'] },
  { path: '/profile', title: '个人中心', icon: UserFilled },
]

const visibleMenus = computed(() => menus.filter((m) => !m.roles || m.roles.includes(store.role)))
const activePath = computed(() => (route.path.startsWith('/question/') && route.path !== '/question/create' ? '/question/list' : route.path))

async function loadUnread() {
  try {
    unread.value = await messageApi.unreadCount()
  } catch {
    /* 忽略角标加载失败 */
  }
}

async function handleLogout() {
  await ElMessageBox.confirm('确定退出登录吗？', '提示', { type: 'warning' })
  store.logout()
  router.push('/login')
}

onMounted(loadUnread)
</script>

<template>
  <el-container class="layout">
    <el-aside width="216px" class="aside">
      <div class="brand">
        <el-icon :size="22" color="#0f766e"><Files /></el-icon>
        <div class="brand-text">
          <span class="brand-name">AI 错题本</span>
          <span class="brand-sub">学习推荐系统</span>
        </div>
      </div>
      <el-menu :default-active="activePath" router class="menu">
        <el-menu-item v-for="m in visibleMenus" :key="m.path" :index="m.path">
          <el-icon><component :is="m.icon" /></el-icon>
          <span>{{ m.title }}</span>
          <el-badge v-if="m.path === '/message' && unread > 0" :value="unread" :max="99" class="menu-badge" />
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="header" height="56px">
        <span class="header-title">{{ route.meta.title }}</span>
        <div class="header-right">
          <el-tag size="small" effect="plain" class="role-tag">
            {{ { student: '学生', teacher: '教师', admin: '管理员' }[store.role] || store.role }}
          </el-tag>
          <el-dropdown trigger="click">
            <span class="user-entry">
              {{ store.nickname }}
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="router.push('/profile')">个人中心</el-dropdown-item>
                <el-dropdown-item divided @click="handleLogout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      <el-main class="main">
        <router-view v-slot="{ Component }">
          <component :is="Component" class="fade-up" />
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.layout {
  height: 100vh;
}

.aside {
  background: var(--wb-paper);
  border-right: 1px solid var(--wb-border);
  display: flex;
  flex-direction: column;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 18px 20px 14px;
  border-bottom: 1px solid var(--wb-border);
}

.brand-text {
  display: flex;
  flex-direction: column;
  line-height: 1.25;
}

.brand-name {
  font-size: 16px;
  font-weight: 700;
  color: var(--wb-primary);
  letter-spacing: 0.5px;
}

.brand-sub {
  font-size: 11px;
  color: var(--wb-ink-secondary);
}

.menu {
  border-right: none;
  flex: 1;
  padding: 8px;
}

.menu :deep(.el-menu-item) {
  border-radius: 8px;
  margin-bottom: 2px;
  height: 44px;
}

.menu :deep(.el-menu-item.is-active) {
  background: var(--el-color-primary-light-9);
  font-weight: 600;
}

.menu-badge {
  margin-left: auto;
}

.header {
  background: var(--wb-paper);
  border-bottom: 1px solid var(--wb-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
}

.header-title {
  font-size: 15px;
  font-weight: 600;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 14px;
}

.role-tag {
  color: var(--wb-primary);
  border-color: var(--el-color-primary-light-7);
}

.user-entry {
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 14px;
  color: var(--wb-ink);
}

.main {
  background: var(--wb-bg);
  padding: 24px;
  overflow-y: auto;
}
</style>
