<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { userApi, type PageData } from '@/api'
import { useUserStore, type UserInfo } from '@/store/user'

type UserRow = UserInfo & { createTime: string }

const store = useUserStore()
const page = ref<PageData<UserRow>>({ records: [], total: 0, current: 1, size: 10 })
const loading = ref(false)
const pageNum = ref(1)
const role = ref<string>()
const keyword = ref('')

const roleText: Record<string, string> = { student: '学生', teacher: '教师', admin: '管理员' }
const roleTagType: Record<string, 'primary' | 'success' | 'warning'> = { student: 'primary', teacher: 'success', admin: 'warning' }

async function load() {
  loading.value = true
  try {
    page.value = await userApi.page({ pageNum: pageNum.value, pageSize: 10, role: role.value, keyword: keyword.value || undefined })
  } finally {
    loading.value = false
  }
}

function search() {
  pageNum.value = 1
  load()
}

async function remove(row: UserRow) {
  await ElMessageBox.confirm(`确认注销用户「${row.nickname || row.username}」？注销后该账号将无法登录。`, '注销用户', { type: 'warning' })
  await userApi.remove(row.id)
  ElMessage.success('已注销')
  await load()
}

onMounted(load)
</script>

<template>
  <div>
    <h2 class="page-title">用户管理</h2>
    <p class="page-subtitle">系统用户的查询与注销（用户注册角色默认为学生）。</p>
    <div class="paper-card">
      <div class="toolbar">
        <el-select v-model="role" placeholder="全部角色" clearable style="width: 140px" @change="search">
          <el-option label="学生" value="student" />
          <el-option label="教师" value="teacher" />
          <el-option label="管理员" value="admin" />
        </el-select>
        <el-input v-model="keyword" placeholder="用户名 / 昵称" clearable style="width: 220px" @keyup.enter="search" @clear="search" />
        <el-button type="primary" @click="search">查询</el-button>
      </div>
      <el-table :data="page.records" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="username" label="用户名" width="140" />
        <el-table-column prop="nickname" label="昵称" width="140" />
        <el-table-column label="角色" width="100">
          <template #default="{ row }">
            <el-tag :type="roleTagType[row.role] || 'info'" size="small">{{ roleText[row.role] || row.role }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="className" label="班级" min-width="160" show-overflow-tooltip />
        <el-table-column prop="email" label="邮箱" min-width="150" show-overflow-tooltip />
        <el-table-column prop="createTime" label="注册时间" width="170" />
        <el-table-column label="操作" width="90" fixed="right">
          <template #default="{ row }">
            <el-button v-if="row.id !== store.user?.id" size="small" type="danger" plain @click="remove(row)">注销</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination
        v-model:current-page="pageNum"
        :total="page.total"
        :page-size="10"
        layout="prev, pager, next, total"
        class="pager"
        @current-change="load"
      />
    </div>
  </div>
</template>

<style scoped>
.toolbar {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
}

.pager {
  margin-top: 16px;
  justify-content: flex-end;
}
</style>
