<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { subjectApi, type Subject } from '@/api'

const list = ref<Subject[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const saving = ref(false)
const editingId = ref<number>()
const form = reactive({ name: '', code: '', sort: 0 })

async function load() {
  loading.value = true
  try {
    list.value = await subjectApi.list()
  } finally {
    loading.value = false
  }
}

function openDialog(row?: Subject) {
  editingId.value = row?.id
  form.name = row?.name || ''
  form.code = row?.code || ''
  form.sort = row?.sort ?? 0
  dialogVisible.value = true
}

async function save() {
  if (!form.name.trim()) {
    ElMessage.warning('请填写科目名称')
    return
  }
  saving.value = true
  try {
    if (editingId.value) {
      await subjectApi.update(editingId.value, form)
      ElMessage.success('科目已更新')
    } else {
      await subjectApi.add(form)
      ElMessage.success('科目已新增')
    }
    dialogVisible.value = false
    await load()
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<template>
  <div>
    <div class="head-row">
      <div>
        <h2 class="page-title">科目管理</h2>
        <p class="page-subtitle">维护系统涉及的学科信息（如数学、物理、英语）。</p>
      </div>
      <el-button type="primary" :icon="Plus" @click="openDialog()">新增科目</el-button>
    </div>
    <div class="paper-card">
      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="科目名称" min-width="140" />
        <el-table-column prop="code" label="科目编码" min-width="140" />
        <el-table-column prop="sort" label="排序号" width="100" />
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="openDialog(row)">编辑</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑科目' : '新增科目'" width="440px">
      <el-form label-width="88px">
        <el-form-item label="科目名称" required>
          <el-input v-model="form.name" maxlength="32" />
        </el-form-item>
        <el-form-item label="科目编码">
          <el-input v-model="form.code" maxlength="32" placeholder="选填，如 MATH" />
        </el-form-item>
        <el-form-item label="排序号">
          <el-input-number v-model="form.sort" :min="0" :max="999" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.head-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}
</style>
