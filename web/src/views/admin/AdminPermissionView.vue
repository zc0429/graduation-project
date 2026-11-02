<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Refresh } from '@element-plus/icons-vue'
import { permissionApi, type PermissionPayload, type PermissionRecord } from '@/api'
import { toApiError } from '@/utils/api-error'
import AdminSectionTabs from '@/components/AdminSectionTabs.vue'
import AsyncState from '@/components/AsyncState.vue'
import PageHeader from '@/components/PageHeader.vue'
import PaperPanel from '@/components/PaperPanel.vue'

const all = ref<PermissionRecord[]>([])
const loading = ref(false)
const errorMessage = ref('')
const typeFilter = ref<string>()
const keyword = ref('')

const formVisible = ref(false)
const formRef = ref<FormInstance>()
const editingId = ref<number>()
const saving = ref(false)
const form = reactive<PermissionPayload>({
  parentId: 0,
  name: '',
  permissionKey: '',
  type: 'menu',
  path: '',
  sort: 0,
  status: 1,
})
const rules: FormRules<PermissionPayload> = {
  name: [{ required: true, message: '请输入权限名称', trigger: 'blur' }],
  permissionKey: [{ required: true, message: '请输入权限标识，如 system:role:list', trigger: 'blur' }],
  type: [{ required: true, message: '请选择权限类型', trigger: 'change' }],
}

const menuOptions = computed(() => all.value.filter((item) => item.type === 'menu'))

const filtered = computed(() =>
  all.value.filter((item) => {
    if (typeFilter.value !== undefined && item.type !== typeFilter.value) return false
    const kw = keyword.value.trim()
    if (kw && !item.name.includes(kw) && !item.permissionKey.includes(kw)) return false
    return true
  }),
)

function parentName(parentId: number) {
  if (parentId === 0) return '—（顶级）'
  return all.value.find((item) => item.id === parentId)?.name || `已删除(${parentId})`
}

async function load() {
  loading.value = true
  errorMessage.value = ''
  try {
    all.value = await permissionApi.list()
  } catch (error) {
    errorMessage.value = toApiError(error, '权限列表加载失败').message
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editingId.value = undefined
  Object.assign(form, { parentId: 0, name: '', permissionKey: '', type: 'menu', path: '', sort: 0, status: 1 })
  formVisible.value = true
}

function openEdit(row: PermissionRecord) {
  editingId.value = row.id
  Object.assign(form, {
    parentId: row.parentId,
    name: row.name,
    permissionKey: row.permissionKey,
    type: row.type,
    path: row.path || '',
    sort: row.sort || 0,
    status: row.status,
  })
  formVisible.value = true
}

async function submitForm() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    const payload = { ...form, path: form.path?.trim() || undefined }
    if (editingId.value) {
      await permissionApi.update(editingId.value, payload)
      ElMessage.success('权限已更新')
    } else {
      await permissionApi.create(payload)
      ElMessage.success('权限已新增')
    }
    formVisible.value = false
    await load()
  } catch (error) {
    ElMessage.error(toApiError(error, '保存权限失败').message)
  } finally {
    saving.value = false
  }
}

async function remove(row: PermissionRecord) {
  const confirmed = await ElMessageBox.confirm(
    `确认删除权限“${row.name}”吗？存在下级权限时后端会拒绝删除；已授予角色的授权将一并清除。`,
    '删除权限',
    { confirmButtonText: '确认删除', cancelButtonText: '取消', type: 'warning' },
  ).then(() => true).catch(() => false)
  if (!confirmed) return
  try {
    await permissionApi.remove(row.id)
    ElMessage.success('权限已删除')
    await load()
  } catch (error) {
    ElMessage.error(toApiError(error, '删除权限失败').message)
  }
}

onMounted(load)
</script>

<template>
  <div class="admin-permission-page">
    <PageHeader
      eyebrow="RBAC · PERMISSION"
      title="权限管理"
      description="维护 permission 表的菜单与按钮权限，权限标识与后端 @SaCheckPermission 注解一一对应，改名即改授权口径。"
    >
      <template #actions>
        <span class="scope-note">权限 <strong class="num">{{ all.length }}</strong></span>
      </template>
    </PageHeader>

    <AdminSectionTabs />

    <PaperPanel :padded="false">
      <div class="permission-toolbar">
        <label class="filter-field">
          <span>权限类型</span>
          <el-select v-model="typeFilter" placeholder="全部类型" clearable>
            <el-option label="菜单" value="menu" />
            <el-option label="按钮" value="button" />
          </el-select>
        </label>
        <label class="filter-field keyword-field">
          <span>名称或权限标识</span>
          <el-input v-model="keyword" placeholder="输入关键词" clearable maxlength="64" />
        </label>
        <div class="toolbar-actions">
          <el-button :icon="Refresh" @click="load">刷新</el-button>
          <el-button type="success" :icon="Plus" @click="openCreate">新增权限</el-button>
        </div>
      </div>

      <AsyncState v-if="loading" status="loading" title="正在读取权限目录" />
      <AsyncState
        v-else-if="errorMessage"
        status="error"
        title="权限列表加载失败"
        :description="errorMessage"
        @retry="load"
      />
      <AsyncState
        v-else-if="filtered.length === 0"
        status="empty"
        title="没有找到符合条件的权限"
        description="可以调整类型或关键词后重新查询，或新增一个权限。"
      />

      <div v-else class="desktop-table">
        <el-table :data="filtered" table-layout="fixed" aria-label="权限列表">
          <el-table-column prop="name" label="权限名称" min-width="140" />
          <el-table-column prop="permissionKey" label="权限标识" min-width="210">
            <template #default="{ row }"><code>{{ row.permissionKey }}</code></template>
          </el-table-column>
          <el-table-column label="类型" width="80">
            <template #default="{ row }">
              <el-tag :type="row.type === 'menu' ? 'primary' : 'warning'" size="small">
                {{ row.type === 'menu' ? '菜单' : '按钮' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="上级菜单" min-width="120">
            <template #default="{ row }">{{ parentName(row.parentId) }}</template>
          </el-table-column>
          <el-table-column prop="path" label="路由路径" min-width="150" show-overflow-tooltip>
            <template #default="{ row }">{{ row.path || '—' }}</template>
          </el-table-column>
          <el-table-column prop="sort" label="排序" width="70" />
          <el-table-column label="状态" width="90">
            <template #default="{ row }">
              <el-tag :type="row.status === 1 ? 'success' : 'info'" size="small">
                {{ row.status === 1 ? '启用' : '停用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="150" fixed="right">
            <template #default="{ row }">
              <el-button size="small" @click="openEdit(row)">编辑</el-button>
              <el-button size="small" type="danger" plain @click="remove(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </PaperPanel>

    <el-dialog
      v-model="formVisible"
      :title="editingId ? '编辑权限' : '新增权限'"
      width="520px"
      destroy-on-close
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="92px">
        <el-form-item label="权限名称" prop="name">
          <el-input v-model="form.name" maxlength="50" placeholder="如：角色管理" />
        </el-form-item>
        <el-form-item label="权限标识" prop="permissionKey">
          <el-input v-model="form.permissionKey" maxlength="100" placeholder="如：system:role:list" />
        </el-form-item>
        <el-form-item label="权限类型" prop="type">
          <el-radio-group v-model="form.type">
            <el-radio value="menu">菜单</el-radio>
            <el-radio value="button">按钮</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="上级菜单">
          <el-select v-model="form.parentId" placeholder="顶级（无上级）" clearable>
            <el-option label="顶级（无上级）" :value="0" />
            <el-option v-for="menu in menuOptions" :key="menu.id" :label="menu.name" :value="menu.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="路由路径">
          <el-input v-model="form.path" maxlength="200" placeholder="菜单填前端路由，如 /admin/role；按钮可留空" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort" :min="0" :max="999" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="form.status" :active-value="1" :inactive-value="0" active-text="启用" inactive-text="停用" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="formVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitForm">保存</el-button>
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

.permission-toolbar {
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
  margin-left: auto;
}

.desktop-table {
  width: 100%;
  overflow-x: auto;
}

@media (max-width: 700px) {
  .permission-toolbar {
    display: grid;
    grid-template-columns: 1fr;
    padding: 16px;
  }

  .filter-field,
  .keyword-field {
    width: 100%;
  }

  .toolbar-actions {
    margin-left: 0;
  }
}
</style>
