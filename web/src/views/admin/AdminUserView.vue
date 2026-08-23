<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { userApi, type PageData, type UserRecord } from '@/api'
import { useUserStore } from '@/store/user'
import { toApiError } from '@/utils/api-error'
import AdminSectionTabs from '@/components/AdminSectionTabs.vue'
import AsyncState from '@/components/AsyncState.vue'
import PageHeader from '@/components/PageHeader.vue'
import PaperPanel from '@/components/PaperPanel.vue'

const store = useUserStore()
const page = ref<PageData<UserRecord>>({ records: [], total: 0, current: 1, size: 10 })
const loading = ref(false)
const errorMessage = ref('')
const pageNum = ref(1)
const role = ref<string>()
const keyword = ref('')
const deactivatingId = ref<number>()

const roleText: Record<string, string> = {
  student: '学生',
  teacher: '教师',
  admin: '管理员',
}

const roleTagType: Record<string, 'primary' | 'success' | 'warning'> = {
  student: 'primary',
  teacher: 'success',
  admin: 'warning',
}

async function load() {
  loading.value = true
  errorMessage.value = ''
  try {
    page.value = await userApi.page({
      pageNum: pageNum.value,
      pageSize: 10,
      role: role.value,
      keyword: keyword.value.trim() || undefined,
    })
  } catch (error) {
    errorMessage.value = toApiError(error, '用户列表加载失败').message
  } finally {
    loading.value = false
  }
}

function search() {
  pageNum.value = 1
  void load()
}

function clearFilters() {
  role.value = undefined
  keyword.value = ''
  pageNum.value = 1
  void load()
}

async function deactivate(row: UserRecord) {
  const confirmed = await ElMessageBox.confirm(
    `确认注销用户“${row.nickname || row.username}”吗？注销后该账号将无法登录。`,
    '注销用户',
    {
      confirmButtonText: '确认注销',
      cancelButtonText: '取消',
      type: 'warning',
    },
  ).then(() => true).catch(() => false)
  if (!confirmed) return

  deactivatingId.value = row.id
  try {
    await userApi.remove(row.id)
    ElMessage.success('用户已注销')
    if (page.value.records.length === 1 && pageNum.value > 1) pageNum.value -= 1
    await load()
  } finally {
    deactivatingId.value = undefined
  }
}

function formatDateTime(value?: string) {
  if (!value) return '—'
  return value.replace('T', ' ').slice(0, 16)
}

onMounted(load)
</script>

<template>
  <div class="admin-user-page">
    <PageHeader
      eyebrow="ADMIN DATA CATALOG"
      title="用户管理"
      description="查询当前有效用户并执行逻辑注销。注册角色默认为学生，当前系统不提供角色修改与账号恢复。"
    >
      <template #actions>
        <span class="scope-note">有效用户 <strong class="num">{{ page.total }}</strong></span>
      </template>
    </PageHeader>

    <AdminSectionTabs />

    <PaperPanel :padded="false">
      <form class="user-toolbar" aria-label="筛选用户" @submit.prevent="search">
        <label class="filter-field">
          <span>用户角色</span>
          <el-select v-model="role" placeholder="全部角色" clearable @change="search">
            <el-option label="学生" value="student" />
            <el-option label="教师" value="teacher" />
            <el-option label="管理员" value="admin" />
          </el-select>
        </label>
        <label class="filter-field keyword-field">
          <span>用户名或昵称</span>
          <el-input v-model="keyword" placeholder="输入关键词" clearable maxlength="64" @clear="search" />
        </label>
        <div class="toolbar-actions">
          <el-button type="primary" native-type="submit" :icon="Search">查询</el-button>
          <el-button v-if="role || keyword" @click="clearFilters">清除筛选</el-button>
        </div>
      </form>

      <AsyncState v-if="loading" status="loading" title="正在读取用户目录" />
      <AsyncState
        v-else-if="errorMessage"
        status="error"
        title="用户目录加载失败"
        :description="errorMessage"
        @retry="load"
      />
      <AsyncState
        v-else-if="page.records.length === 0"
        status="empty"
        title="没有找到符合条件的用户"
        description="可以调整角色或关键词后重新查询。"
      >
        <template v-if="role || keyword" #action>
          <el-button @click="clearFilters">清除筛选</el-button>
        </template>
      </AsyncState>

      <template v-else>
        <div class="desktop-user-table">
          <el-table :data="page.records" table-layout="fixed" aria-label="有效用户列表">
            <el-table-column label="用户" min-width="190">
              <template #default="{ row }">
                <div class="user-cell">
                  <span class="user-avatar" aria-hidden="true">{{ (row.nickname || row.username).slice(0, 1) }}</span>
                  <span><strong>{{ row.username }}</strong><small>{{ row.nickname || '未设置昵称' }}</small></span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="角色" width="100">
              <template #default="{ row }">
                <el-tag :type="roleTagType[row.role] || 'info'" size="small">{{ roleText[row.role] || row.role }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="className" label="班级" min-width="170" show-overflow-tooltip>
              <template #default="{ row }">{{ row.className || '—' }}</template>
            </el-table-column>
            <el-table-column prop="email" label="邮箱" min-width="180" show-overflow-tooltip>
              <template #default="{ row }">{{ row.email || '—' }}</template>
            </el-table-column>
            <el-table-column label="注册时间" width="152">
              <template #default="{ row }"><span class="num">{{ formatDateTime(row.createTime) }}</span></template>
            </el-table-column>
            <el-table-column label="操作" width="112" fixed="right">
              <template #default="{ row }">
                <span v-if="row.id === store.user?.id" class="self-note">当前账号</span>
                <el-button
                  v-else
                  size="small"
                  type="danger"
                  plain
                  :loading="deactivatingId === row.id"
                  :aria-label="`注销用户 ${row.nickname || row.username}`"
                  @click="deactivate(row)"
                >注销</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <div class="mobile-user-list" aria-label="有效用户列表">
          <article v-for="row in page.records" :key="row.id" class="mobile-user-card">
            <div class="mobile-user-head">
              <div class="user-cell">
                <span class="user-avatar" aria-hidden="true">{{ (row.nickname || row.username).slice(0, 1) }}</span>
                <span><strong>{{ row.nickname || row.username }}</strong><small>{{ row.username }}</small></span>
              </div>
              <el-tag :type="roleTagType[row.role] || 'info'" size="small">{{ roleText[row.role] || row.role }}</el-tag>
            </div>
            <dl>
              <div><dt>班级</dt><dd>{{ row.className || '—' }}</dd></div>
              <div><dt>邮箱</dt><dd>{{ row.email || '—' }}</dd></div>
              <div><dt>注册</dt><dd class="num">{{ formatDateTime(row.createTime) }}</dd></div>
            </dl>
            <div class="mobile-user-actions">
              <span v-if="row.id === store.user?.id" class="self-note">当前账号不可注销</span>
              <el-button
                v-else
                size="small"
                type="danger"
                plain
                :loading="deactivatingId === row.id"
                @click="deactivate(row)"
              >注销账号</el-button>
            </div>
          </article>
        </div>

        <div class="table-footer">
          <p>注销属于逻辑删除，当前接口不支持恢复账号。</p>
          <el-pagination
            v-if="page.total > 10"
            v-model:current-page="pageNum"
            :total="page.total"
            :page-size="10"
            layout="prev, pager, next, total"
            aria-label="用户列表分页"
            @current-change="load"
          />
        </div>
      </template>
    </PaperPanel>
  </div>
</template>

<style scoped>
.scope-note {
  display: inline-flex;
  min-height: 36px;
  align-items: center;
  gap: 6px;
  padding: 7px 12px;
  border: 1px solid var(--line);
  border-radius: 999px;
  background: rgba(255, 253, 248, 0.82);
  color: var(--ink-soft);
  font-size: 11px;
}

.scope-note strong {
  color: var(--navy);
  font-size: 13px;
}

.user-toolbar {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  padding: 18px 20px;
  border-bottom: 1px dashed var(--line);
  background: rgba(238, 227, 211, 0.32);
}

.filter-field {
  display: grid;
  width: 170px;
  gap: 6px;
  color: var(--navy);
  font-size: 11px;
  font-weight: 700;
}

.keyword-field {
  width: min(280px, 35vw);
}

.toolbar-actions {
  display: flex;
  gap: 8px;
}

.desktop-user-table {
  width: 100%;
  overflow-x: auto;
}

.user-cell {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 10px;
}

.user-cell > span:last-child {
  display: flex;
  min-width: 0;
  flex-direction: column;
}

.user-cell strong,
.user-cell small {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-cell strong {
  color: var(--navy);
  font-size: 12px;
}

.user-cell small {
  margin-top: 3px;
  color: var(--ink-faint);
  font-size: 10px;
}

.user-avatar {
  display: grid;
  width: 34px;
  height: 34px;
  flex: 0 0 auto;
  place-items: center;
  border-radius: 10px 10px 10px 4px;
  background: var(--jade-pale);
  color: var(--jade-dark);
  font-family: var(--font-serif);
  font-weight: 700;
}

.self-note {
  color: var(--ink-faint);
  font-size: 10px;
  font-weight: 700;
}

.mobile-user-list {
  display: none;
}

.table-footer {
  display: flex;
  min-height: 64px;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 12px 20px;
  border-top: 1px dashed var(--line);
}

.table-footer p {
  margin: 0;
  color: var(--ink-faint);
  font-size: 10px;
  line-height: 1.6;
}

@media (max-width: 900px) {
  .desktop-user-table {
    display: none;
  }

  .mobile-user-list {
    display: grid;
    gap: 10px;
    padding: 14px;
  }

  .mobile-user-card {
    padding: 15px;
    border: 1px solid var(--line);
    border-radius: 13px;
    background: rgba(255, 253, 248, 0.78);
  }

  .mobile-user-head {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 10px;
  }

  dl {
    display: grid;
    gap: 7px;
    margin: 14px 0;
  }

  dl div {
    display: grid;
    grid-template-columns: 54px minmax(0, 1fr);
    gap: 8px;
  }

  dt,
  dd {
    margin: 0;
    font-size: 11px;
    line-height: 1.5;
  }

  dt {
    color: var(--ink-faint);
  }

  dd {
    overflow-wrap: anywhere;
    color: var(--ink-soft);
  }

  .mobile-user-actions {
    display: flex;
    min-height: 33px;
    align-items: center;
    justify-content: flex-end;
    border-top: 1px dashed var(--line);
    padding-top: 10px;
  }
}

@media (max-width: 700px) {
  .user-toolbar {
    display: grid;
    grid-template-columns: 1fr;
    padding: 16px;
  }

  .filter-field,
  .keyword-field {
    width: 100%;
  }

  .toolbar-actions :deep(.el-button) {
    flex: 1;
  }

  .table-footer {
    flex-direction: column;
    align-items: stretch;
    padding-inline: 14px;
  }

  .table-footer :deep(.el-pagination) {
    justify-content: center;
  }
}
</style>
