<script setup lang="ts">
import { useRoute } from 'vue-router'
import { Avatar, Collection, Document, List, Lock, User } from '@element-plus/icons-vue'

const route = useRoute()

const items = [
  { path: '/admin/user', label: '用户', icon: User },
  { path: '/admin/role', label: '角色', icon: Avatar },
  { path: '/admin/permission', label: '权限', icon: Lock },
  { path: '/admin/subject', label: '科目', icon: Collection },
  { path: '/admin/knowledge', label: '知识点', icon: List },
  { path: '/announcement', label: '公告', icon: Document },
]
</script>

<template>
  <nav class="admin-section-tabs" aria-label="管理员数据模块">
    <RouterLink
      v-for="item in items"
      :key="item.path"
      :to="item.path"
      class="admin-section-link"
      :class="{ 'is-active': route.path === item.path }"
      :aria-current="route.path === item.path ? 'page' : undefined"
    >
      <el-icon aria-hidden="true"><component :is="item.icon" /></el-icon>
      <span>{{ item.label }}</span>
    </RouterLink>
  </nav>
</template>

<style scoped>
.admin-section-tabs {
  display: flex;
  max-width: 100%;
  align-items: center;
  gap: 5px;
  margin-bottom: 20px;
  padding: 5px;
  overflow-x: auto;
  border: 1px solid var(--line);
  border-radius: 14px;
  background: rgba(255, 253, 248, 0.72);
  scrollbar-width: thin;
}

.admin-section-link {
  position: relative;
  display: inline-flex;
  min-width: 104px;
  min-height: 42px;
  flex: 1 0 auto;
  align-items: center;
  justify-content: center;
  gap: 7px;
  padding: 8px 14px;
  border: 1px solid transparent;
  border-radius: 10px;
  color: var(--ink-soft);
  font-size: 12px;
  font-weight: 700;
  text-decoration: none;
}

.admin-section-link:hover {
  color: var(--jade-dark);
}

.admin-section-link.is-active {
  border-color: rgba(24, 52, 74, 0.12);
  background: var(--navy);
  box-shadow: 0 5px 13px rgba(24, 52, 74, 0.14);
  color: #fff;
}

.admin-section-link.is-active::after {
  position: absolute;
  right: 14px;
  bottom: 6px;
  left: 14px;
  height: 2px;
  border-radius: 2px;
  background: var(--cinnabar);
  content: '';
}

@media (max-width: 700px) {
  .admin-section-tabs {
    margin-inline: -2px;
  }

  .admin-section-link {
    min-width: 94px;
  }
}
</style>
