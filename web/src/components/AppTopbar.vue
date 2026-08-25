<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Bell, Search, UserFilled } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserStore } from '@/store/user'

withDefaults(
  defineProps<{
    unread?: number
  }>(),
  {
    unread: 0,
  },
)

const route = useRoute()
const router = useRouter()
const store = useUserStore()
const quickFind = ref('')

interface NavigationSuggestion {
  value: string
  hint: string
  path: string
  roles?: string[]
}

const navigationSuggestions: NavigationSuggestion[] = [
  { value: '今日工作台', hint: '返回角色首页', path: '/' },
  { value: '录入错题', hint: '新建错题并启动解析', path: '/question/create', roles: ['student'] },
  { value: '错题本', hint: '筛选、查看与导出错题', path: '/question/list', roles: ['student'] },
  { value: '复习计划', hint: '处理到期与逾期任务', path: '/review', roles: ['student'] },
  { value: '练习历史', hint: '查看已提交的练习记录', path: '/practice/history', roles: ['student'] },
  { value: '学情报告', hint: '查看本周学习反馈', path: '/report', roles: ['student', 'teacher'] },
  { value: '消息中心', hint: '查看提醒与系统消息', path: '/message' },
  { value: '系统公告', hint: '查看当前公告', path: '/announcement' },
  { value: '个人中心', hint: '维护当前账号资料', path: '/profile' },
  { value: '用户管理', hint: '查询与逻辑注销用户', path: '/admin/user', roles: ['admin'] },
  { value: '科目管理', hint: '新增与编辑科目', path: '/admin/subject', roles: ['admin'] },
  { value: '知识点管理', hint: '维护章节与考点', path: '/admin/knowledge', roles: ['admin'] },
]

const roleText: Record<string, string> = {
  student: '学生',
  teacher: '教师',
  admin: '管理员',
}

const pageSubtitles: Record<string, string> = {
  home: '把今天要做的事收在一页',
  'question-create': '留住问题，开始分析',
  'question-list': '按知识线索整理错题',
  'question-detail': '查看题目、解析与练习反馈',
  'practice-history': '回看已提交的练习反馈',
  review: '处理到期与逾期任务',
  report: '查看本周学习反馈',
  message: '接收复习与报告提醒',
  announcement: '查看系统通知',
  profile: '维护个人资料',
  'admin-user': '查询与维护有效用户',
  'admin-subject': '维护系统科目',
  'admin-knowledge': '维护两级知识结构',
  'not-found': '检查地址或返回工作台',
}

const pageTitle = computed(() => String(route.meta.title || '今日工作台'))
const pageSubtitle = computed(() => pageSubtitles[String(route.name || '')] || '知错学习工作台')
const displayName = computed(() => store.nickname || store.user?.username || '用户')
const avatarText = computed(() => displayName.value.slice(0, 1))
const visibleNavigation = computed(() => navigationSuggestions.filter((item) => !item.roles || item.roles.includes(store.role)))

async function openQuickFind() {
  const keyword = quickFind.value.trim().toLocaleLowerCase('zh-CN')
  if (!keyword) return
  const item = visibleNavigation.value.find((candidate) => candidate.value.toLocaleLowerCase('zh-CN') === keyword)
    || visibleNavigation.value.find((candidate) => `${candidate.value}${candidate.hint}`.toLocaleLowerCase('zh-CN').includes(keyword))
  if (!item) {
    ElMessage.info('没有找到可访问的功能入口')
    return
  }
  quickFind.value = ''
  await router.push(item.path)
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
  store.logout()
  await router.replace('/login')
}
</script>

<template>
  <header class="app-topbar">
    <div class="page-identity" aria-live="polite">
      <strong>{{ pageTitle }}</strong>
      <span>{{ pageSubtitle }}</span>
    </div>

    <div class="topbar-actions">
      <form class="quick-find" role="search" @submit.prevent="openQuickFind">
        <label class="sr-only" for="quick-find-input">查找功能入口，不搜索业务数据</label>
        <el-icon aria-hidden="true"><Search /></el-icon>
        <input id="quick-find-input" v-model="quickFind" type="search" list="quick-find-options" placeholder="查找功能入口" autocomplete="off" @change="openQuickFind">
        <datalist id="quick-find-options">
          <option v-for="item in visibleNavigation" :key="item.path" :value="item.value">{{ item.hint }}</option>
        </datalist>
        <button type="submit">前往</button>
      </form>

      <RouterLink
        to="/message"
        class="topbar-icon-link"
        :aria-label="unread > 0 ? `消息中心，${unread} 条未读` : '消息中心'"
      >
        <el-badge :value="unread" :max="99" :hidden="unread === 0">
          <el-icon><Bell /></el-icon>
        </el-badge>
      </RouterLink>

      <el-dropdown trigger="click">
        <button class="profile-trigger" type="button" :aria-label="`${displayName}，打开账号菜单`">
          <span class="profile-avatar" aria-hidden="true">{{ avatarText }}</span>
          <span class="profile-copy">
            <strong>{{ displayName }}</strong>
            <span>{{ roleText[store.role] || store.role }}</span>
          </span>
          <el-icon class="profile-icon" aria-hidden="true"><UserFilled /></el-icon>
        </button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item @click="router.push('/profile')">个人中心</el-dropdown-item>
            <el-dropdown-item @click="router.push('/announcement')">系统公告</el-dropdown-item>
            <el-dropdown-item divided @click="handleLogout">退出登录</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </header>
</template>

<style scoped>
.app-topbar {
  position: sticky;
  top: 0;
  z-index: 25;
  display: flex;
  min-height: 70px;
  align-items: center;
  justify-content: space-between;
  gap: 22px;
  padding: 10px 28px;
  border-bottom: 1px solid var(--line);
  background: rgba(255, 253, 248, 0.93);
  box-shadow: 0 5px 20px rgba(24, 52, 74, 0.035);
  backdrop-filter: blur(14px);
}

.page-identity {
  display: flex;
  min-width: 0;
  flex-direction: column;
}

.page-identity strong {
  overflow: hidden;
  color: var(--navy);
  font-family: var(--font-serif);
  font-size: 17px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.page-identity span {
  margin-top: 2px;
  overflow: hidden;
  color: var(--ink-faint);
  font-size: 10px;
  letter-spacing: 0.04em;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.topbar-actions {
  display: flex;
  flex: 0 0 auto;
  align-items: center;
  gap: 10px;
}

.quick-find {
  display: grid;
  grid-template-columns:auto minmax(0,1fr) auto;
  align-items: center;
  width: clamp(190px, 20vw, 280px);
  min-height: 42px;
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: 12px;
  background: var(--paper-bright);
}

.quick-find > .el-icon {
  margin-left: 12px;
  color: var(--ink-faint);
}

.quick-find input {
  min-width: 0;
  height: 40px;
  padding: 0 8px;
  border: 0;
  outline: 0;
  background: transparent;
  color: var(--ink);
  font: inherit;
}

.quick-find button {
  align-self: stretch;
  padding: 0 12px;
  border: 0;
  border-left: 1px solid var(--line);
  background: var(--paper-deep);
  color: var(--navy);
  cursor: pointer;
  font-size: 11px;
  font-weight: 800;
}

.quick-find:focus-within {
  outline: 3px solid var(--focus-ring);
  outline-offset: 2px;
}

.topbar-icon-link {
  display: grid;
  width: 42px;
  height: 42px;
  place-items: center;
  border: 1px solid var(--line);
  border-radius: 12px;
  background: var(--paper-bright);
  color: var(--navy);
  text-decoration: none;
  transition: border-color 160ms ease, color 160ms ease, transform 160ms ease;
}

.topbar-icon-link:hover,
.topbar-icon-link[aria-current='page'] {
  border-color: rgba(22, 129, 114, 0.32);
  color: var(--jade-dark);
  transform: translateY(-1px);
}

.topbar-icon-link :deep(.el-icon) {
  font-size: 19px;
}

.profile-trigger {
  display: flex;
  min-height: 44px;
  align-items: center;
  gap: 9px;
  padding: 5px 7px 5px 6px;
  border: 1px solid var(--line);
  border-radius: 14px;
  background: var(--paper-bright);
  color: var(--ink);
  cursor: pointer;
}

.profile-avatar {
  display: grid;
  width: 32px;
  height: 32px;
  place-items: center;
  border-radius: 10px 10px 10px 4px;
  background: var(--navy);
  color: #fff;
  font-family: var(--font-serif);
  font-size: 14px;
  font-weight: 700;
}

.profile-copy {
  display: flex;
  min-width: 78px;
  flex-direction: column;
  align-items: flex-start;
  line-height: 1.2;
}

.profile-copy strong {
  max-width: 120px;
  overflow: hidden;
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.profile-copy span {
  margin-top: 3px;
  color: var(--ink-faint);
  font-size: 9px;
}

.profile-icon {
  color: var(--ink-faint);
  font-size: 13px;
}

@media (max-width: 900px) {
  .app-topbar {
    padding-inline: 19px;
  }

  .profile-copy {
    display: none;
  }

  .quick-find {
    display: none;
  }
}

@media (max-width: 700px) {
  .app-topbar {
    min-height: 62px;
    padding: 8px 14px;
  }

  .page-identity strong {
    font-size: 15px;
  }

  .page-identity span {
    display: none;
  }

  .topbar-icon-link {
    width: 38px;
    height: 38px;
  }

  .profile-trigger {
    min-height: 38px;
    padding: 3px;
    border-color: transparent;
  }

  .profile-avatar {
    width: 32px;
    height: 32px;
  }

  .profile-icon {
    display: none;
  }
}

@media (prefers-reduced-motion: reduce) {
  .topbar-icon-link {
    transition: none;
  }
}
</style>
