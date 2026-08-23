<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { EditPen, Plus } from '@element-plus/icons-vue'
import { subjectApi, type Subject } from '@/api'
import { toApiError } from '@/utils/api-error'
import AdminSectionTabs from '@/components/AdminSectionTabs.vue'
import AsyncState from '@/components/AsyncState.vue'
import PageHeader from '@/components/PageHeader.vue'
import PaperPanel from '@/components/PaperPanel.vue'

const list = ref<Subject[]>([])
const loading = ref(false)
const errorMessage = ref('')
const dialogVisible = ref(false)
const saving = ref(false)
const editingId = ref<number>()
const formError = ref('')
const form = reactive({ name: '', code: '', sort: 0 })

async function load() {
  loading.value = true
  errorMessage.value = ''
  try {
    list.value = await subjectApi.list()
  } catch (error) {
    errorMessage.value = toApiError(error, '科目列表加载失败').message
  } finally {
    loading.value = false
  }
}

function openDialog(row?: Subject) {
  editingId.value = row?.id
  form.name = row?.name || ''
  form.code = row?.code || ''
  form.sort = row?.sort ?? 0
  formError.value = ''
  dialogVisible.value = true
}

async function save() {
  const name = form.name.trim()
  const code = form.code.trim()
  if (!name) {
    formError.value = '请填写科目名称'
    return
  }
  formError.value = ''
  saving.value = true
  try {
    const payload = { name, code: code || undefined, sort: form.sort }
    if (editingId.value !== undefined) {
      await subjectApi.update(editingId.value, payload)
      ElMessage.success('科目信息已更新')
    } else {
      await subjectApi.add(payload)
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
  <div class="admin-subject-page">
    <PageHeader
      eyebrow="SUBJECT CATALOG"
      title="科目管理"
      description="维护错题归类所需的科目名称、编码与排序。当前接口支持新增和编辑，不提供科目删除。"
    >
      <template #actions>
        <el-button type="primary" :icon="Plus" @click="openDialog()">新增科目</el-button>
      </template>
    </PageHeader>

    <AdminSectionTabs />

    <PaperPanel>
      <AsyncState v-if="loading" status="loading" title="正在读取科目目录" />
      <AsyncState
        v-else-if="errorMessage"
        status="error"
        title="科目目录加载失败"
        :description="errorMessage"
        @retry="load"
      />
      <AsyncState
        v-else-if="list.length === 0"
        status="empty"
        title="还没有科目"
        description="先创建一个科目，再为它维护章节与考点。"
      >
        <template #action>
          <el-button type="primary" :icon="Plus" @click="openDialog()">新增第一个科目</el-button>
        </template>
      </AsyncState>

      <template v-else>
        <div class="catalog-heading">
          <div>
            <span>当前科目目录</span>
            <strong class="num">{{ list.length }}</strong>
          </div>
          <p>科目删除功能尚未提供，页面不会展示无效操作。</p>
        </div>

        <div class="subject-grid">
          <article v-for="subject in list" :key="subject.id" class="subject-card">
            <div class="subject-card-top">
              <span class="subject-index num">{{ String(subject.sort).padStart(2, '0') }}</span>
              <span class="subject-id num">ID {{ subject.id }}</span>
            </div>
            <p class="subject-code">{{ subject.code || '未设置编码' }}</p>
            <h2>{{ subject.name }}</h2>
            <div class="subject-card-foot">
              <span>排序号 <strong class="num">{{ subject.sort }}</strong></span>
              <el-button size="small" :icon="EditPen" @click="openDialog(subject)">编辑</el-button>
            </div>
          </article>
        </div>
      </template>
    </PaperPanel>

    <el-dialog
      v-model="dialogVisible"
      :title="editingId !== undefined ? '编辑科目' : '新增科目'"
      width="460px"
      destroy-on-close
      append-to-body
    >
      <p class="dialog-description">科目名称用于前台筛选；编码可选，建议使用简短的英文大写标识。</p>
      <el-form label-position="top" @submit.prevent="save">
        <el-form-item label="科目名称" required :error="formError">
          <el-input id="subject-name" v-model="form.name" maxlength="32" show-word-limit placeholder="例如：化学" />
        </el-form-item>
        <el-form-item label="科目编码">
          <el-input id="subject-code" v-model="form.code" maxlength="32" placeholder="例如：CHEMISTRY" />
        </el-form-item>
        <el-form-item label="排序号">
          <el-input-number id="subject-sort" v-model="form.sort" :min="0" :max="999" controls-position="right" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">
          {{ editingId !== undefined ? '保存修改' : '创建科目' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.catalog-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px dashed var(--line);
}

.catalog-heading > div {
  display: flex;
  align-items: baseline;
  gap: 9px;
  color: var(--navy);
  font-size: 13px;
  font-weight: 700;
}

.catalog-heading strong {
  color: var(--cinnabar);
  font-size: 20px;
}

.catalog-heading p {
  margin: 0;
  color: var(--ink-faint);
  font-size: 10px;
}

.subject-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 15px;
}

.subject-card {
  position: relative;
  min-height: 190px;
  padding: 20px;
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: 6px 17px 17px 17px;
  background:
    repeating-linear-gradient(180deg, transparent 0 31px, rgba(37, 78, 102, 0.06) 31px 32px),
    var(--paper-bright);
  transition: border-color 180ms ease, box-shadow 180ms ease, transform 180ms ease;
}

.subject-card::before {
  position: absolute;
  top: 15px;
  bottom: 15px;
  left: 0;
  width: 4px;
  border-radius: 0 4px 4px 0;
  background: var(--cinnabar);
  content: '';
}

.subject-card:hover {
  border-color: rgba(22, 129, 114, 0.3);
  box-shadow: var(--shadow-soft);
  transform: translateY(-2px);
}

.subject-card-top,
.subject-card-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.subject-index {
  display: grid;
  width: 34px;
  height: 34px;
  place-items: center;
  border-radius: 50%;
  background: var(--navy);
  color: #fff;
  font-size: 11px;
}

.subject-id,
.subject-code,
.subject-card-foot span {
  color: var(--ink-faint);
  font-size: 10px;
}

.subject-code {
  margin: 22px 0 4px;
  font-family: var(--font-mono);
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.subject-card h2 {
  margin: 0;
  color: var(--navy);
  font-family: var(--font-serif);
  font-size: 25px;
}

.subject-card-foot {
  position: absolute;
  right: 18px;
  bottom: 16px;
  left: 20px;
  padding-top: 10px;
  border-top: 1px dashed var(--line);
}

.subject-card-foot strong {
  color: var(--navy);
}

.dialog-description {
  margin: -4px 0 18px;
  color: var(--ink-faint);
  font-size: 11px;
  line-height: 1.7;
}

@media (max-width: 1100px) {
  .subject-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 700px) {
  .catalog-heading {
    align-items: flex-start;
  }

  .catalog-heading p {
    max-width: 160px;
    text-align: right;
  }

  .subject-grid {
    grid-template-columns: 1fr;
  }

  .subject-card {
    min-height: 178px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .subject-card {
    transition: none;
  }
}
</style>
