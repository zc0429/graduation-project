import { createRouter, createWebHistory, type RouterHistory, type RouteRecordRaw } from 'vue-router'
import { useUserStore } from '@/store/user'
import { subscribeUnauthorized } from '@/utils/request'

declare module 'vue-router' {
  interface RouteMeta {
    title?: string
    roles?: string[]
    public?: boolean
  }
}

export const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/LoginView.vue'),
    meta: { title: '登录', public: true },
  },
  {
    path: '/',
    component: () => import('@/layout/AppLayout.vue'),
    children: [
      { path: '', name: 'home', component: () => import('@/views/HomeView.vue'), meta: { title: '今日工作台' } },
      {
        path: 'question/create',
        name: 'question-create',
        component: () => import('@/views/question/QuestionCreateView.vue'),
        meta: { title: '错题录入', roles: ['student'] },
      },
      {
        path: 'question/list',
        name: 'question-list',
        component: () => import('@/views/question/QuestionListView.vue'),
        meta: { title: '错题本', roles: ['student'] },
      },
      {
        path: 'question/:id',
        name: 'question-detail',
        component: () => import('@/views/question/QuestionDetailView.vue'),
        meta: { title: '错题详情', roles: ['student'] },
      },
      {
        path: 'practice/history',
        name: 'practice-history',
        component: () => import('@/views/practice/PracticeHistoryView.vue'),
        meta: { title: '练习历史', roles: ['student'] },
      },
      {
        path: 'review',
        name: 'review',
        component: () => import('@/views/review/ReviewPlanView.vue'),
        meta: { title: '复习计划', roles: ['student'] },
      },
      {
        path: 'report',
        name: 'report',
        component: () => import('@/views/report/ReportView.vue'),
        meta: { title: '学情报告', roles: ['student', 'teacher'] },
      },
      { path: 'message', name: 'message', component: () => import('@/views/message/MessageView.vue'), meta: { title: '消息中心' } },
      { path: 'announcement', name: 'announcement', component: () => import('@/views/announcement/AnnouncementView.vue'), meta: { title: '系统公告' } },
      { path: 'profile', name: 'profile', component: () => import('@/views/profile/ProfileView.vue'), meta: { title: '个人中心' } },
      {
        path: 'admin/user',
        name: 'admin-user',
        component: () => import('@/views/admin/AdminUserView.vue'),
        meta: { title: '用户管理', roles: ['admin'] },
      },
      {
        path: 'admin/subject',
        name: 'admin-subject',
        component: () => import('@/views/admin/AdminSubjectView.vue'),
        meta: { title: '科目管理', roles: ['admin'] },
      },
      {
        path: 'admin/knowledge',
        name: 'admin-knowledge',
        component: () => import('@/views/admin/AdminKnowledgeView.vue'),
        meta: { title: '知识点管理', roles: ['admin'] },
      },
      {
        path: ':pathMatch(.*)*',
        name: 'not-found',
        component: () => import('@/views/system/NotFoundView.vue'),
        meta: { title: '页面未找到' },
      },
    ],
  },
]

export function createAppRouter(history: RouterHistory = createWebHistory()) {
  const router = createRouter({ history, routes })

  router.beforeEach(async (to) => {
    const store = useUserStore()
    document.title = `${to.meta.title || '学习工作台'} · 知错`

    if (to.meta.public) {
      if (to.name !== 'login' || !store.isLogin) return true
      if (to.query.reason) return true
      try {
        return (await store.ensureSession()) ? { name: 'home' } : true
      } catch {
        return true
      }
    }

    if (!store.isLogin) {
      return { name: 'login', query: { redirect: to.fullPath } }
    }

    try {
      const valid = await store.ensureSession()
      if (!valid) return { name: 'login', query: { reason: 'expired', redirect: to.fullPath } }
    } catch {
      // A transient profile failure must not discard a locally restored user.
      if (!store.user) return { name: 'login', query: { reason: 'network', redirect: to.fullPath } }
    }

    const roles = to.meta.roles
    if (roles && !roles.includes(store.role)) {
      return { name: 'home', query: { notice: 'forbidden' } }
    }
    return true
  })

  subscribeUnauthorized(() => {
    const current = router.currentRoute.value
    if (current.name === 'login') return
    void router.replace({ name: 'login', query: { reason: 'expired', redirect: current.fullPath } })
  })

  return router
}

export default createAppRouter()
