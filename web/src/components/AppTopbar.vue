<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Bell, UserFilled } from '@element-plus/icons-vue'
import { ElMessageBox } from 'element-plus'
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
  review: '处理到期与逾期任务',
  report: '查看本周学习反馈',
  message: '接收复习与报告提醒',
  announcement: '查看系统通知',
  profile: '维护个人资料',
  'admin-user': '查询与维护有效用户',
  'admin-subject': '维护系统科目',
  'admin-knowledge': '维护两级知识结构',
}

const pageTitle = computed(() => String(route.meta.title || '今日工作台'))
const pageSubtitle = computed(() => pageSubtitles[String(route.name || '')] || '知错学习工作台')
const displayName = computed(() => store.nickname || store.user?.username || '用户')
const avatarText = computed(() => displayName.value.slice(0, 1))

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
