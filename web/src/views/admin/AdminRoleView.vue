<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules, type TreeInstance } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import {
  permissionApi,
  roleApi,
  type PageData,
  type PermissionRecord,
  type RolePayload,
  type RoleRecord,
} from '@/api'
import { toApiError } from '@/utils/api-error'
import AdminSectionTabs from '@/components/AdminSectionTabs.vue'
import AsyncState from '@/components/AsyncState.vue'
import PageHeader from '@/components/PageHeader.vue'
import PaperPanel from '@/components/PaperPanel.vue'

const page = ref<PageData<RoleRecord>>({ records: [], total: 0, current: 1, size: 10 })
const loading = ref(false)
const errorMessage = ref('')
const pageNum = ref(1)
const keyword = ref('')

const formVisible = ref(false)
const formRef = ref<FormInstance>()
const editingId = ref<number>()
const saving = ref(false)
const form = reactive<RolePayload>({ roleName: '', roleKey: '', sort: 0, status: 1, remark: '' })
const rules: FormRules<RolePayload> = {
  roleName: [{ required: true, message: '请输入角色名称', trigger: 'blur' }],
  roleKey: [{ required: true, message: '请输入角色标识，如 student', trigger: 'blur' }],
}

const assignVisible = ref(false)
const assignRole = ref<RoleRecord>()
const treeRef = ref<TreeInstance>()
const allPermissions = ref<PermissionRecord[]>([])
const assignSaving = ref(false)

interface PermissionNode {
  id: number
  label: string
  children?: PermissionNode[]
}

const permissionTree = computed<PermissionNode[]>(() => {
  const byParent = new Map<number, PermissionRecord[]>()
  for (const item of allPermissions.value) {
    const list = byParent.get(item.parentId) || []
    list.push(item)
    byParent.set(item.parentId, list)
  }
  const build = (parentId: number): PermissionNode[] =>
    (byParent.get(parentId) || [])
      .slice()
      .sort((a, b) => (a.sort || 0) - (b.sort || 0))
      .map((item) => ({ id: item.id, label: `${item.name}（${item.permissionKey}）`, children: build(item.id) }))
  return build(0)
})

async function load() {
  loading.value = true
  errorMessage.value = ''
  try {
    page.value = await roleApi.page({
      pageNum: pageNum.value,
      pageSize: 10,
      keyword: keyword.value.trim() || undefined,
    })
  } catch (error) {
    errorMessage.value = toApiError(error, '角色列表加载失败').message
  } finally {
    loading.value = false
  }
}

function search() {
  pageNum.value = 1
  void load()
}

function openCreate() {
  editingId.value = undefined
  Object.assign(form, { roleName: '', roleKey: '', sort: 0, status: 1, remark: '' })
  formVisible.value = true
}

function openEdit(row: RoleRecord) {
  editingId.value = row.id
  Object.assign(form, {
    roleName: row.roleName,
    roleKey: row.roleKey,
    sort: row.sort || 0,
    status: row.status,
    remark: row.remark || '',
  })
  formVisible.value = true
}

async function submitForm() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    if (editingId.value) {
      await roleApi.update(editingId.value, { ...form })
      ElMessage.success('角色已更新')
    } else {
      await roleApi.create({ ...form })
      ElMessage.success('角色已新增')
    }
    formVisible.value = false
    await load()
  } catch (error) {
    ElMessage.error(toApiError(error, '保存角色失败').message)
  } finally {
    saving.value = false
  }
}

async function remove(row: RoleRecord) {
  const confirmed = await ElMessageBox.confirm(
    `确认删除角色“${row.roleName}”吗？该角色的用户授权与权限授权将一并清除。`,
    '删除角色',
    { confirmButtonText: '确认删除', cancelButtonText: '取消', type: 'warning' },
  ).then(() => true).catch(() => false)
  if (!confirmed) return
  try {
    await roleApi.remove(row.id)
    ElMessage.success('角色已删除')
    if (page.value.records.length === 1 && pageNum.value > 1) pageNum.value -= 1
    await load()
  } catch (error) {
    ElMessage.error(toApiError(error, '删除角色失败').message)
  }
}

async function openAssign(row: RoleRecord) {
  assignRole.value = row
  try {
    if (allPermissions.value.length === 0) allPermissions.value = await permissionApi.list()
    const checked = await roleApi.permissionIds(row.id)
    assignVisible.value = true
    requestAnimationFrame(() => treeRef.value?.setCheckedKeys(checked))
  } catch (error) {
    ElMessage.error(toApiError(error, '读取角色权限失败').message)
  }
}

async function submitAssign() {
  if (!assignRole.value || !treeRef.value) return
  const ids = [
    ...(treeRef.value.getCheckedKeys() as number[]),
    ...(treeRef.value.getHalfCheckedKeys() as number[]),
  ]
  assignSaving.value = true
  try {
    await roleApi.assignPermissions(assignRole.value.id, ids)
    ElMessage.success(`已为角色“${assignRole.value.roleName}”分配 ${ids.length} 项权限`)
    assignVisible.value = false
  } catch (error) {
    ElMessage.error(toApiError(error, '分配权限失败').message)
  } finally {
    assignSaving.value = false
  }
}

function formatDateTime(value?: string) {
  if (!value) return '—'
  return value.replace('T', ' ').slice(0, 16)
}

onMounted(load)
</script>

<template>
  <div class="admin-role-page">
    <PageHeader
      eyebrow="RBAC · ROLE"
      title="角色管理"
      description="维护 role 表角色并为角色分配菜单与按钮权限（role_permission），授权结果由 Sa-Token 在接口层实时校验。"
    >
      <template #actions>
        <span class="scope-note">角色 <strong class="num">{{ page.total }}</strong></span>
      </template>
    </PageHeader>

    <AdminSectionTabs />

    <PaperPanel :padded="false">
      <form class="role-toolbar" aria-label="筛选角色" @submit.prevent="search">
        <label class="filter-field keyword-field">
          <span>角色名称或标识</span>
          <el-input v-model="keyword" placeholder="输入关键词" clearable maxlength="64" @clear="search" />
        </label>
        <div class="toolbar-actions">
          <el-button type="primary" native-type="submit" :icon="Search">查询</el-button>
          <el-button type="success" :icon="Plus" @click="openCreate">新增角色</el-button>
        </div>
      </form>

      <AsyncState v-if="loading" status="loading" title="正在读取角色目录" />
      <AsyncState
        v-else-if="errorMessage"
        status="error"
        title="角色列表加载失败"
        :description="errorMessage"
        @retry="load"
      />
      <AsyncState
        v-else-if="page.records.length === 0"
        status="empty"
        title="没有找到符合条件的角色"
        description="可以调整关键词后重新查询，或新增一个角色。"
      />

      <template v-else>
        <div class="desktop-table">
          <el-table :data="page.records" table-layout="fixed" aria-label="角色列表">
            <el-table-column prop="roleName" label="角色名称" min-width="140" />
            <el-table-column prop="roleKey" label="角色标识" min-width="140">
              <template #default="{ row }"><code>{{ row.roleKey }}</code></template>
            </el-table-column>
            <el-table-column prop="sort" label="排序" width="70" />
            <el-table-column label="状态" width="90">
              <template #default="{ row }">
                <el-tag :type="row.status === 1 ? 'success' : 'info'" size="small">
                  {{ row.status === 1 ? '启用' : '停用' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="remark" label="备注" min-width="160" show-overflow-tooltip>
              <template #default="{ row }">{{ row.remark || '—' }}</template>
            </el-table-column>
            <el-table-column label="创建时间" width="152">
              <template #default="{ row }"><span class="num">{{ formatDateTime(row.createTime) }}</span></template>
            </el-table-column>
            <el-table-column label="操作" width="230" fixed="right">
              <template #default="{ row }">
                <el-button size="small" @click="openEdit(row)">编辑</el-button>
                <el-button size="small" type="primary" plain @click="openAssign(row)">分配权限</el-button>
                <el-button size="small" type="danger" plain @click="remove(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <div class="table-footer">
          <p>内置角色 admin / teacher / student 与用户表 role 字段保持一致，删除前请确认无用户在用。</p>
          <el-pagination
            v-if="page.total > 10"
            v-model:current-page="pageNum"
            :total="page.total"
            :page-size="10"
            layout="prev, pager, next, total"
            aria-label="角色列表分页"
            @current-change="load"
          />
        </div>
      </template>
    </PaperPanel>

    <el-dialog
      v-model="formVisible"
      :title="editingId ? '编辑角色' : '新增角色'"
      width="480px"
      destroy-on-close
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="92px">
        <el-form-item label="角色名称" prop="roleName">
          <el-input v-model="form.roleName" maxlength="50" placeholder="如：教师" />
        </el-form-item>
        <el-form-item label="角色标识" prop="roleKey">
          <el-input v-model="form.roleKey" maxlength="50" placeholder="如：teacher" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort" :min="0" :max="999" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="form.status" :active-value="1" :inactive-value="0" active-text="启用" inactive-text="停用" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" maxlength="255" placeholder="可选" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="formVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitForm">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="assignVisible"
      :title="`分配权限 · ${assignRole?.roleName || ''}`"
      width="560px"
      destroy-on-close
    >
      <el-tree
        ref="treeRef"
        :data="permissionTree"
        node-key="id"
        show-checkbox
        default-expand-all
        :props="{ label: 'label', children: 'children' }"
      />
      <template #footer>
        <el-button @click="assignVisible = false">取消</el-button>
        <el-button type="primary" :loading="assignSaving" @click="submitAssign">保存授权</el-button>
      </template>
    </el-dialog>
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

.role-toolbar {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  padding: 18px 20px;
  border-bottom: 1px dashed var(--line);
  background: rgba(238, 227, 211, 0.32);
}

.filter-field {
  display: grid;
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

.desktop-table {
  width: 100%;
  overflow-x: auto;
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

@media (max-width: 700px) {
  .role-toolbar {
    display: grid;
    grid-template-columns: 1fr;
    padding: 16px;
  }

  .keyword-field {
    width: 100%;
  }

  .table-footer {
    flex-direction: column;
    align-items: stretch;
    padding-inline: 14px;
  }
}
</style>
