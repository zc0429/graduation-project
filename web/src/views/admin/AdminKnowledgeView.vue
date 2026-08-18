<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete, Plus } from '@element-plus/icons-vue'
import { kpApi, subjectApi, type KpNode, type Subject } from '@/api'

const subjects = ref<Subject[]>([])
const currentSubjectId = ref<number>()
const tree = ref<KpNode[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const saving = ref(false)
const form = reactive({ parentId: 0, name: '', sort: 0 })

const currentSubjectName = computed(() => subjects.value.find((s) => s.id === currentSubjectId.value)?.name || '')

async function loadSubjects() {
  subjects.value = await subjectApi.list()
  if (subjects.value.length > 0 && !currentSubjectId.value) {
    currentSubjectId.value = subjects.value[0].id
  }
}

async function loadTree() {
  if (!currentSubjectId.value) return
  loading.value = true
  try {
    tree.value = await kpApi.tree(currentSubjectId.value)
  } finally {
    loading.value = false
  }
}

function onSubjectChange() {
  loadTree()
}

function openDialog(parentId: number) {
  form.parentId = parentId
  form.name = ''
  form.sort = 0
  dialogVisible.value = true
}

async function save() {
  if (!form.name.trim()) {
    ElMessage.warning('请填写知识点名称')
    return
  }
  saving.value = true
  try {
    await kpApi.add({ subjectId: currentSubjectId.value!, parentId: form.parentId, name: form.name, sort: form.sort })
    ElMessage.success('知识点已新增')
    dialogVisible.value = false
    await loadTree()
  } finally {
    saving.value = false
  }
}

async function remove(node: KpNode) {
  await ElMessageBox.confirm(
    node.children.length > 0 ? `「${node.name}」下含 ${node.children.length} 个考点，需先删除子级` : `确认删除知识点「${node.name}」？`,
    '删除知识点',
    { type: 'warning' },
  )
  if (node.children.length > 0) return
  await kpApi.remove(node.id)
  ElMessage.success('已删除')
  await loadTree()
}

onMounted(async () => {
  await loadSubjects()
  await loadTree()
})
</script>

<template>
  <div>
    <div class="head-row">
      <div>
        <h2 class="page-title">知识点管理</h2>
        <p class="page-subtitle">维护一级章节与二级考点的两级知识点体系。</p>
      </div>
      <div class="head-actions">
        <el-select v-model="currentSubjectId" style="width: 160px" @change="onSubjectChange">
          <el-option v-for="s in subjects" :key="s.id" :label="s.name" :value="s.id" />
        </el-select>
        <el-button type="primary" :icon="Plus" @click="openDialog(0)">新增章节</el-button>
      </div>
    </div>
    <div class="paper-card" v-loading="loading">
      <el-empty v-if="tree.length === 0" description="该科目暂无知识点，点击右上角新增章节" :image-size="80" />
      <div v-for="chapter in tree" :key="chapter.id" class="chapter-block">
        <div class="chapter-head">
          <span class="chapter-name">{{ chapter.name }}</span>
          <div class="chapter-actions">
            <el-button size="small" link type="primary" :icon="Plus" @click="openDialog(chapter.id)">添加考点</el-button>
            <el-button size="small" link type="danger" :icon="Delete" @click="remove(chapter)">删除</el-button>
          </div>
        </div>
        <div class="kp-list">
          <el-tag v-for="kp in chapter.children" :key="kp.id" closable class="kp-tag" @close="remove(kp)">
            {{ kp.name }}
          </el-tag>
          <span v-if="chapter.children.length === 0" class="kp-empty">暂无考点</span>
        </div>
      </div>
    </div>

    <el-dialog v-model="dialogVisible" :title="form.parentId === 0 ? '新增章节' : '添加考点'" width="440px">
      <el-form label-width="88px">
        <el-form-item label="所属科目">
          <el-input :model-value="currentSubjectName" disabled />
        </el-form-item>
        <el-form-item :label="form.parentId === 0 ? '章节名称' : '考点名称'" required>
          <el-input v-model="form.name" maxlength="64" />
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

.head-actions {
  display: flex;
  gap: 10px;
}

.chapter-block {
  border-bottom: 1px solid var(--wb-border);
  padding: 14px 4px;
}

.chapter-block:last-child {
  border-bottom: none;
}

.chapter-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.chapter-name {
  font-size: 14px;
  font-weight: 700;
  color: var(--wb-primary-dark);
}

.kp-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.kp-tag {
  font-size: 13px;
}

.kp-empty {
  font-size: 12px;
  color: var(--wb-ink-secondary);
}
</style>
