import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/store/user'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { title: '登录' },
    },
    {
      path: '/',
      component: () => import('@/layout/AppLayout.vue'),
      children: [
        { path: '', name: 'home', component: () => import('@/views/HomeView.vue'), meta: { title: '首页' } },
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
        {
          path: 'message',
          name: 'message',
          component: () => import('@/views/message/MessageView.vue'),
          meta: { title: '消息中心' },
        },
        {
          path: 'announcement',
          name: 'announcement',
          component: () => import('@/views/announcement/AnnouncementView.vue'),
          meta: { title: '公告' },
        },
        {
          path: 'profile',
          name: 'profile',
          component: () => import('@/views/profile/ProfileView.vue'),
          meta: { title: '个人中心' },
        },
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
      ],
    },
  ],
})

router.beforeEach((to) => {
  const store = useUserStore()
  if (to.path === '/login') {
    return store.isLogin ? '/' : true
  }
  if (!store.isLogin) {
    return '/login'
  }
  const roles = to.meta.roles as string[] | undefined
  if (roles && !roles.includes(store.role)) {
    return '/'
  }
  document.title = `${(to.meta.title as string) || ''} · AI 错题分析与学习推荐系统`
  return true
})

export default router
