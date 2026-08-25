<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete, Plus } from '@element-plus/icons-vue'
import { kpApi, subjectApi, type KpNode, type Subject } from '@/api'
import { toApiError } from '@/utils/api-error'
import AdminSectionTabs from '@/components/AdminSectionTabs.vue'
import AsyncState from '@/components/AsyncState.vue'
import PageHeader from '@/components/PageHeader.vue'
import PaperPanel from '@/components/PaperPanel.vue'

const subjects = ref<Subject[]>([])
const currentSubjectId = ref<number>()
const tree = ref<KpNode[]>([])
const loading = ref(false)
const errorMessage = ref('')
const dialogVisible = ref(false)
const saving = ref(false)
const deletingId = ref<number>()
const formError = ref('')
const form = reactive({ parentId: 0, name: '', sort: 0 })
let treeRequestVersion = 0

const currentSubjectName = computed(() => subjects.value.find((subject) => subject.id === currentSubjectId.value)?.name || '')
const pointCount = computed(() => tree.value.reduce((total, chapter) => total + chapter.children.length, 0))

async function loadSubjects() {
  subjects.value = await subjectApi.list()
  if (subjects.value.length > 0 && !subjects.value.some((subject) => subject.id === currentSubjectId.value)) {
    currentSubjectId.value = subjects.value[0].id
  }
}

async function loadTree() {
  const version = ++treeRequestVersion
  const requestedSubject = currentSubjectId.value
  if (!requestedSubject) {
    tree.value = []
    return
  }
  const data = await kpApi.tree(requestedSubject)
  if (version === treeRequestVersion && requestedSubject === currentSubjectId.value) tree.value = data
}

async function load() {
  loading.value = true
  errorMessage.value = ''
  try {
    await loadSubjects()
    await loadTree()
  } catch (error) {
    errorMessage.value = toApiError(error, '知识点目录加载失败').message
  } finally {
    loading.value = false
  }
}

async function onSubjectChange() {
  loading.value = true
  errorMessage.value = ''
  try {
    await loadTree()
  } catch (error) {
    errorMessage.value = toApiError(error, '知识点目录加载失败').message
  } finally {
    loading.value = false
  }
}

function openDialog(parentId: number) {
  if (!currentSubjectId.value) return
  form.parentId = parentId
  form.name = ''
  form.sort = 0
  formError.value = ''
  dialogVisible.value = true
}

async function save() {
  const name = form.name.trim()
  if (!name) {
    formError.value = form.parentId === 0 ? '请填写章节名称' : '请填写考点名称'
    return
  }
  if (!currentSubjectId.value) return

  formError.value = ''
  saving.value = true
  try {
    await kpApi.add({
      subjectId: currentSubjectId.value,
      parentId: form.parentId,
      name,
      sort: form.sort,
    })
    ElMessage.success(form.parentId === 0 ? '章节已新增' : '考点已新增')
    dialogVisible.value = false
    await loadTree()
  } finally {
    saving.value = false
  }
}

async function removeLeaf(node: KpNode, kind: 'chapter' | 'point') {
  if (node.children.length > 0) return
  const confirmed = await ElMessageBox.confirm(
    `确认删除${kind === 'chapter' ? '空章节' : '考点'}“${node.name}”吗？`,
    kind === 'chapter' ? '删除空章节' : '删除考点',
    {
      confirmButtonText: '确认删除',
      cancelButtonText: '取消',
      type: 'warning',
    },
  ).then(() => true).catch(() => false)
  if (!confirmed) return

  deletingId.value = node.id
  try {
    await kpApi.remove(node.id)
    ElMessage.success(kind === 'chapter' ? '空章节已删除' : '考点已删除')
    await loadTree()
  } finally {
    deletingId.value = undefined
  }
}

onMounted(load)
</script>

<template>
  <div class="admin-knowledge-page">
    <PageHeader
      eyebrow="KNOWLEDGE MAP"
      title="知识点管理"
      description="按科目维护一级章节与二级考点。当前接口支持新增及叶节点删除，不提供知识点编辑。"
    >
      <template #actions>
        <el-button type="primary" :icon="Plus" :disabled="!currentSubjectId" @click="openDialog(0)">新增章节</el-button>
      </template>
    </PageHeader>

    <AdminSectionTabs />

    <PaperPanel>
      <div class="knowledge-toolbar">
        <label>
          <span>当前科目</span>
          <el-select
            v-model="currentSubjectId"
            placeholder="请选择科目"
            :disabled="loading || subjects.length === 0"
            @change="onSubjectChange"
          >
            <el-option v-for="subject in subjects" :key="subject.id" :label="subject.name" :value="subject.id" />
          </el-select>
        </label>
        <div v-if="currentSubjectId" class="catalog-counts" aria-label="知识点统计">
          <span>章节 <strong class="num">{{ tree.length }}</strong></span>
          <span>考点 <strong class="num">{{ pointCount }}</strong></span>
        </div>
      </div>

      <AsyncState v-if="loading" status="loading" title="正在展开知识点目录" />
      <AsyncState
        v-else-if="errorMessage"
        status="error"
        title="知识点目录加载失败"
        :description="errorMessage"
        @retry="load"
      />
      <AsyncState
        v-else-if="subjects.length === 0"
        status="empty"
        title="还没有可用科目"
        description="知识点必须归属于一个科目，请先创建科目。"
      >
        <template #action>
          <RouterLink class="state-link" to="/admin/subject">前往科目管理</RouterLink>
        </template>
      </AsyncState>
      <AsyncState
        v-else-if="tree.length === 0"
        status="empty"
        :title="`${currentSubjectName}还没有知识点`"
        description="先创建一级章节，再在章节下添加二级考点。"
      >
        <template #action>
          <el-button type="primary" :icon="Plus" @click="openDialog(0)">新增第一个章节</el-button>
        </template>
      </AsyncState>

      <div v-else class="knowledge-tree" aria-label="两级知识点目录">
        <article v-for="(chapter, chapterIndex) in tree" :key="chapter.id" class="chapter-card">
          <header class="chapter-head">
            <span class="chapter-number num" aria-hidden="true">{{ String(chapterIndex + 1).padStart(2, '0') }}</span>
            <div>
              <p>一级章节</p>
              <h2>{{ chapter.name }}</h2>
            </div>
            <div class="chapter-actions">
              <el-button size="small" :icon="Plus" @click="openDialog(chapter.id)">添加考点</el-button>
              <el-button
                v-if="chapter.children.length === 0"
                size="small"
                type="danger"
                plain
                :icon="Delete"
                :loading="deletingId === chapter.id"
                :aria-label="`删除空章节 ${chapter.name}`"
                @click="removeLeaf(chapter, 'chapter')"
              >删除空章节</el-button>
            </div>
          </header>

          <ul v-if="chapter.children.length > 0" class="point-list">
            <li v-for="point in chapter.children" :key="point.id" class="point-item">
              <span class="point-mark" aria-hidden="true" />
              <span>{{ point.name }}</span>
              <button
                class="point-delete"
                type="button"
                :disabled="deletingId === point.id"
                :aria-label="`删除考点 ${point.name}`"
                @click="removeLeaf(point, 'point')"
              >
                <el-icon aria-hidden="true"><Delete /></el-icon>
              </button>
            </li>
          </ul>
          <p v-else class="chapter-empty">这一章还没有二级考点，可以添加考点或删除空章节。</p>
        </article>
      </div>
    </PaperPanel>

    <el-dialog
      v-model="dialogVisible"
      :title="form.parentId === 0 ? '新增章节' : '添加考点'"
      width="460px"
      destroy-on-close
      append-to-body
    >
      <p class="dialog-description">
        所属科目：<strong>{{ currentSubjectName }}</strong>。系统仅维护“章节—考点”两级结构。
      </p>
      <el-form label-position="top" @submit.prevent="save">
        <el-form-item :label="form.parentId === 0 ? '章节名称' : '考点名称'" required :error="formError">
          <el-input
            id="knowledge-name"
            v-model="form.name"
            maxlength="64"
            show-word-limit
            :placeholder="form.parentId === 0 ? '例如：统计与概率' : '例如：函数单调性'"
          />
        </el-form-item>
        <el-form-item label="排序号">
          <el-input-number id="knowledge-sort" v-model="form.sort" :min="0" :max="999" controls-position="right" />
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
.knowledge-toolbar {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 18px;
  margin-bottom: 22px;
  padding-bottom: 17px;
  border-bottom: 1px dashed var(--line);
}

.knowledge-toolbar label {
  display: grid;
  width: 220px;
  gap: 6px;
}

.knowledge-toolbar label > span {
  color: var(--navy);
  font-size: 11px;
  font-weight: 700;
}

.catalog-counts {
  display: flex;
  gap: 8px;
}

.catalog-counts span {
  min-height: 34px;
  padding: 7px 11px;
  border: 1px solid var(--line);
  border-radius: 999px;
  color: var(--ink-faint);
  font-size: 10px;
}

.catalog-counts strong {
  margin-left: 4px;
  color: var(--navy);
  font-size: 12px;
}

.knowledge-tree {
  display: grid;
  gap: 14px;
}

.chapter-card {
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: 6px 16px 16px 16px;
  background: rgba(255, 253, 248, 0.74);
}

.chapter-head {
  display: grid;
  grid-template-columns: 44px minmax(0, 1fr) auto;
  align-items: center;
  gap: 13px;
  padding: 15px 17px;
  border-bottom: 1px dashed var(--line);
  background: rgba(238, 227, 211, 0.42);
}

.chapter-number {
  display: grid;
  width: 40px;
  height: 40px;
  place-items: center;
  border-radius: 50%;
  background: var(--navy);
  color: #fff;
  font-size: 11px;
}

.chapter-head p {
  margin: 0 0 2px;
  color: var(--cinnabar-dark);
  font-size: 9px;
  font-weight: 800;
  letter-spacing: 0.13em;
}

.chapter-head h2 {
  margin: 0;
  color: var(--navy);
  font-family: var(--font-serif);
  font-size: 19px;
}

.chapter-actions {
  display: flex;
  align-items: center;
  gap: 7px;
}

.point-list {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 9px;
  margin: 0;
  padding: 16px;
  list-style: none;
}

.point-item {
  display: grid;
  min-height: 45px;
  grid-template-columns: 9px minmax(0, 1fr) 30px;
  align-items: center;
  gap: 8px;
  padding: 7px 8px 7px 12px;
  border: 1px solid rgba(22, 129, 114, 0.18);
  border-radius: 11px;
  background: var(--jade-pale);
  color: var(--jade-dark);
  font-size: 12px;
  font-weight: 700;
}

.point-mark {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--jade);
}

.point-delete {
  display: grid;
  width: 30px;
  height: 30px;
  place-items: center;
  border: 0;
  border-radius: 8px;
  background: transparent;
  color: var(--ink-faint);
  cursor: pointer;
}

.point-delete:hover {
  background: var(--cinnabar-pale);
  color: var(--cinnabar-dark);
}

.point-delete:disabled {
  cursor: wait;
  opacity: 0.5;
}

.chapter-empty {
  margin: 0;
  padding: 18px;
  color: var(--ink-faint);
  font-size: 11px;
}

.state-link {
  display: inline-flex;
  min-height: 38px;
  align-items: center;
  padding: 8px 16px;
  border-radius: 9px;
  background: var(--navy);
  color: #fff;
  font-size: 12px;
  font-weight: 700;
  text-decoration: none;
}

.dialog-description {
  margin: -4px 0 18px;
  color: var(--ink-faint);
  font-size: 11px;
  line-height: 1.7;
}

.dialog-description strong {
  color: var(--navy);
}

@media (max-width: 1050px) {
  .point-list {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 700px) {
  .knowledge-toolbar {
    align-items: flex-end;
  }

  .knowledge-toolbar label {
    width: min(210px, 62vw);
  }

  .chapter-head {
    grid-template-columns: 40px minmax(0, 1fr);
    padding: 14px;
  }

  .chapter-actions {
    grid-column: 1 / -1;
    justify-content: flex-end;
    padding-top: 9px;
    border-top: 1px dashed var(--line);
  }

  .point-list {
    grid-template-columns: 1fr;
    padding: 12px;
  }
}

@media (max-width: 430px) {
  .knowledge-toolbar {
    display: grid;
  }

  .knowledge-toolbar label {
    width: 100%;
  }

  .catalog-counts {
    justify-content: flex-end;
  }
}
</style>
