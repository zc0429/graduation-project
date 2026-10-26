<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Download, Filter, Picture, Plus, Refresh } from '@element-plus/icons-vue'
import QuestionContent from '@/components/QuestionContent.vue'
import { questionText } from '@/utils/question-content'
import AsyncState from '@/components/AsyncState.vue'
import MasteryIndicator from '@/components/MasteryIndicator.vue'
import PageHeader from '@/components/PageHeader.vue'
import PaperPanel from '@/components/PaperPanel.vue'
import {
  kpApi,
  questionApi,
  subjectApi,
  toApiError,
  type KpNode,
  type PageData,
  type Question,
  type Subject,
} from '@/api'

type LoadState = 'loading' | 'ready' | 'empty' | 'error'
type TreeState = 'idle' | LoadState

const router = useRouter()
const pageSize = 9
const subjects = ref<Subject[]>([])
const allKpTree = ref<KpNode[]>([])
const filterKpTree = ref<KpNode[]>([])
const page = ref<PageData<Question>>({ records: [], total: 0, current: 1, size: pageSize })
const filterSubjectId = ref<number>()
const filterKpId = ref<number>()
const pageNum = ref(1)
const bootstrapState = ref<LoadState>('loading')
const pageState = ref<LoadState>('loading')
const treeState = ref<TreeState>('idle')
const bootstrapError = ref('')
const pageError = ref('')
const treeError = ref('')
const exporting = ref(false)
const exportError = ref('')
let pageRequestVersion = 0
let treeRequestVersion = 0

const treeProps = {
  label: 'name',
  children: 'children',
  disabled: (node: KpNode) => Boolean(node.children?.length),
}
const hasFilters = computed(() => filterSubjectId.value !== undefined || filterKpId.value !== undefined)
const subjectNames = computed(() => new Map(subjects.value.map((subject) => [subject.id, subject.name])))
const knowledgeNames = computed(() => {
  const names = new Map<number, string>()
  function visit(nodes: KpNode[]) {
    for (const node of nodes) {
      names.set(node.id, node.name)
      visit(node.children || [])
    }
  }
  visit(allKpTree.value)
  return names
})
const activeSubjectName = computed(() =>
  filterSubjectId.value === undefined ? '' : subjectNames.value.get(filterSubjectId.value) || '未知科目',
)
const activeKnowledgeName = computed(() =>
  filterKpId.value === undefined ? '' : knowledgeNames.value.get(filterKpId.value) || '未知知识点',
)

async function loadInitial() {
  bootstrapState.value = 'loading'
  bootstrapError.value = ''
  try {
    const [subjectList, knowledgeTree] = await Promise.all([subjectApi.list(), kpApi.tree()])
    subjects.value = subjectList
    allKpTree.value = knowledgeTree
    bootstrapState.value = 'ready'
    await loadPage()
  } catch (cause) {
    bootstrapError.value = toApiError(cause, '错题目录加载失败').message
    bootstrapState.value = 'error'
  }
}

async function loadPage() {
  const requestVersion = ++pageRequestVersion
  const requestedPage = pageNum.value
  const requestedSubject = filterSubjectId.value
  const requestedKnowledge = filterKpId.value
  pageState.value = 'loading'
  pageError.value = ''
  try {
    const result = await questionApi.page({
      pageNum: requestedPage,
      pageSize,
      subjectId: requestedSubject,
      knowledgePointId: requestedKnowledge,
    })
    if (requestVersion !== pageRequestVersion) return
    page.value = result
    pageNum.value = result.current
    pageState.value = result.records.length ? 'ready' : 'empty'
  } catch (cause) {
    if (requestVersion !== pageRequestVersion) return
    pageError.value = toApiError(cause, '错题列表加载失败').message
    pageState.value = 'error'
  }
}

async function loadFilterTree() {
  const requestVersion = ++treeRequestVersion
  const requestedSubject = filterSubjectId.value
  filterKpTree.value = []
  treeError.value = ''
  if (requestedSubject === undefined) {
    treeState.value = 'idle'
    return
  }
  treeState.value = 'loading'
  try {
    const result = await kpApi.tree(requestedSubject)
    if (requestVersion !== treeRequestVersion) return
    filterKpTree.value = result
    treeState.value = filterKpTree.value.length ? 'ready' : 'empty'
  } catch (cause) {
    if (requestVersion !== treeRequestVersion) return
    treeError.value = toApiError(cause, '知识点加载失败').message
    treeState.value = 'error'
  }
}

async function onSubjectChange() {
  filterKpId.value = undefined
  pageNum.value = 1
  await Promise.all([loadFilterTree(), loadPage()])
}

async function onNodeClick(node: KpNode) {
  if (node.children?.length) {
    ElMessage.info('章节只用于展开目录，请选择具体考点进行筛选')
    return
  }
  filterKpId.value = node.id
  pageNum.value = 1
  await loadPage()
}

async function clearKnowledgeFilter() {
  filterKpId.value = undefined
  pageNum.value = 1
  await loadPage()
}

async function clearAllFilters() {
  treeRequestVersion += 1
  filterSubjectId.value = undefined
  filterKpId.value = undefined
  filterKpTree.value = []
  treeState.value = 'idle'
  pageNum.value = 1
  await loadPage()
}

async function changePage() {
  await loadPage()
}

function subjectName(id: number) {
  return subjectNames.value.get(id) || '未知科目'
}

function kpName(id?: number) {
  return id === undefined ? '待归类' : knowledgeNames.value.get(id) || '待归类'
}

function difficultyText(difficulty?: number) {
  return difficulty ? '★'.repeat(Math.min(5, Math.max(1, difficulty))) : '待评估'
}

function difficultyLabel(difficulty?: number) {
  return difficulty ? `难度 ${difficulty} 星，共 5 星` : '难度待评估'
}

function formatDate(value?: string) {
  return value?.slice(0, 10) || '日期未知'
}

async function doExport() {
  exporting.value = true
  exportError.value = ''
  try {
    const fileName = await questionApi.download(filterSubjectId.value, filterKpId.value)
    ElMessage.success(`${fileName} 已开始下载`)
  } catch (cause) {
    exportError.value = toApiError(cause, '错题本导出失败').message
  } finally {
    exporting.value = false
  }
}

onMounted(() => void loadInitial())
</script>

<template>
  <div class="question-list-page">
    <PageHeader
      eyebrow="错题索引"
      title="错题本"
      description="按科目与知识点翻检错题；每次重做后的自评会同步更新掌握度。"
    >
      <template #actions>
        <el-button :icon="Download" :loading="exporting" @click="doExport">
          {{ hasFilters ? '导出筛选结果' : '导出错题本' }}
        </el-button>
        <el-button type="primary" :icon="Plus" @click="router.push('/question/create')">录入错题</el-button>
      </template>
    </PageHeader>

    <PaperPanel v-if="bootstrapState === 'loading'" class="bootstrap-panel">
      <AsyncState status="loading" title="正在翻检错题目录" description="科目、知识点和题目正在一起装订。" />
    </PaperPanel>
    <PaperPanel v-else-if="bootstrapState === 'error'" class="bootstrap-panel">
      <AsyncState
        status="error"
        title="错题目录没有加载完整"
        :description="bootstrapError"
        @retry="loadInitial"
      />
    </PaperPanel>

    <template v-else>
      <div v-if="exportError" class="export-alert" role="alert">
        <span><strong>导出没有完成：</strong>{{ exportError }}</span>
        <el-button size="small" :loading="exporting" @click="doExport">重试导出</el-button>
      </div>

      <div class="catalog-layout">
        <PaperPanel as="aside" class="filter-panel" aria-label="错题筛选">
          <div class="filter-heading">
            <span class="filter-icon" aria-hidden="true"><el-icon><Filter /></el-icon></span>
            <div>
              <h2>筛选索引</h2>
              <p>先选科目，再按章节或考点收窄。</p>
            </div>
          </div>

          <div class="filter-field">
            <label for="question-subject-filter">科目</label>
            <el-select
              id="question-subject-filter"
              v-model="filterSubjectId"
              placeholder="全部科目"
              clearable
              filterable
              @change="onSubjectChange"
            >
              <el-option v-for="subject in subjects" :key="subject.id" :label="subject.name" :value="subject.id" />
            </el-select>
          </div>

          <div class="knowledge-heading">
            <span>知识点 <small>（仅具体考点可筛选）</small></span>
            <button v-if="filterKpId !== undefined" type="button" @click="clearKnowledgeFilter">清除知识点</button>
          </div>

          <div class="tree-region">
            <p v-if="treeState === 'idle'" class="tree-hint">选择科目后，这里会展开对应的知识点树。</p>
            <AsyncState
              v-else-if="treeState === 'loading'"
              compact
              status="loading"
              title="正在展开知识点"
              description=""
            />
            <AsyncState
              v-else-if="treeState === 'error'"
              compact
              status="error"
              title="知识点加载失败"
              :description="treeError"
              @retry="loadFilterTree"
            />
            <AsyncState
              v-else-if="treeState === 'empty'"
              compact
              status="empty"
              title="该科目暂无知识点"
              description="仍可按科目查看错题。"
            />
            <el-tree
              v-else
              :data="filterKpTree"
              :props="treeProps"
              node-key="id"
              highlight-current
              :current-node-key="filterKpId"
              :default-expanded-keys="filterKpTree.map((node) => node.id)"
              aria-label="知识点筛选树"
              @node-click="onNodeClick"
            />
          </div>

          <div v-if="hasFilters" class="active-filters" aria-label="当前筛选条件">
            <span>正在查看</span>
            <el-tag v-if="activeSubjectName" effect="plain" closable @close="clearAllFilters">
              {{ activeSubjectName }}
            </el-tag>
            <el-tag v-if="activeKnowledgeName" type="success" effect="plain" closable @close="clearKnowledgeFilter">
              {{ activeKnowledgeName }}
            </el-tag>
            <button type="button" @click="clearAllFilters">清除全部</button>
          </div>
        </PaperPanel>

        <section class="question-results" aria-label="错题检索结果" :aria-busy="pageState === 'loading'">
          <PaperPanel v-if="pageState === 'loading'">
            <AsyncState compact status="loading" title="正在翻到这一页" description="题目很快就会出现。" />
          </PaperPanel>
          <PaperPanel v-else-if="pageState === 'error'">
            <AsyncState
              status="error"
              title="这一页暂时打不开"
              :description="pageError"
              @retry="loadPage"
            />
          </PaperPanel>
          <PaperPanel v-else-if="pageState === 'empty'">
            <AsyncState
              status="empty"
              :title="hasFilters ? '没有符合条件的错题' : '错题本还是空的'"
              :description="hasFilters ? '换一个科目或知识点继续查找。' : '录入第一道错题后，复习闭环会从这里开始。'"
            >
              <template #action>
                <el-button v-if="hasFilters" @click="clearAllFilters">清除筛选</el-button>
                <el-button v-else type="primary" :icon="Plus" @click="router.push('/question/create')">
                  录入第一道错题
                </el-button>
              </template>
            </AsyncState>
          </PaperPanel>

          <template v-else>
            <div class="result-bar" aria-live="polite">
              <p>
                共找到 <strong class="num">{{ page.total }}</strong> 道错题
                <span v-if="hasFilters">，当前筛选已生效</span>
              </p>
              <el-button :icon="Refresh" circle aria-label="刷新错题列表" @click="loadPage" />
            </div>

            <div class="question-grid">
              <PaperPanel
                v-for="question in page.records"
                :key="question.id"
                as="article"
                hoverable
                :padded="false"
                class="question-card"
              >
                <RouterLink
                  class="question-link"
                  :to="`/question/${question.id}`"
                  :aria-label="`查看错题：${questionText(question.stem)}`"
                >
                  <span class="correction-mark" aria-hidden="true">✓</span>
                  <div class="card-tags">
                    <span class="subject-chip">{{ subjectName(question.subjectId) }}</span>
                    <span class="knowledge-chip">{{ kpName(question.knowledgePointId) }}</span>
                    <span class="difficulty num" :aria-label="difficultyLabel(question.difficulty)">
                      <span aria-hidden="true">{{ difficultyText(question.difficulty) }}</span>
                    </span>
                  </div>

                  <QuestionContent class="question-card-stem" :content="question.stem" />

                  <div class="question-meta">
                    <span v-if="question.imageUrl" class="image-note">
                      <el-icon aria-hidden="true"><Picture /></el-icon> 含题图
                    </span>
                    <span>{{ question.source || '未标注来源' }}</span>
                    <time class="num" :datetime="question.createTime.replace(' ', 'T')">
                      {{ formatDate(question.createTime) }}
                    </time>
                  </div>

                  <MasteryIndicator :value="question.mastery" compact />
                </RouterLink>
              </PaperPanel>
            </div>

            <nav v-if="page.total > pageSize" class="pagination-wrap" aria-label="错题列表分页">
              <span class="pagination-copy num">第 {{ page.current }} / {{ page.pages || Math.ceil(page.total / pageSize) }} 页</span>
              <el-pagination
                v-model:current-page="pageNum"
                :total="page.total"
                :page-size="pageSize"
                layout="prev, pager, next"
                background
                @current-change="changePage"
              />
            </nav>
          </template>
        </section>
      </div>
    </template>
  </div>
</template>

<style scoped>
.bootstrap-panel {
  min-height: 320px;
}

.export-alert {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
  padding: 11px 14px;
  border: 1px solid rgba(183, 67, 50, 0.26);
  border-left: 4px solid var(--cinnabar);
  border-radius: 4px 12px 12px 4px;
  background: var(--cinnabar-pale);
  color: var(--cinnabar-dark);
  font-size: 12px;
}

.catalog-layout {
  display: grid;
  grid-template-columns: 270px minmax(0, 1fr);
  gap: 20px;
  align-items: start;
}

.filter-panel {
  position: sticky;
  top: 12px;
}

.filter-heading {
  display: flex;
  gap: 11px;
  align-items: flex-start;
  padding-bottom: 17px;
  border-bottom: 1px solid var(--line);
}

.filter-icon {
  display: grid;
  flex: 0 0 34px;
  width: 34px;
  height: 34px;
  place-items: center;
  border-radius: 11px 11px 11px 4px;
  background: var(--navy);
  color: #fff;
}

.filter-heading h2 {
  margin: 0;
  color: var(--navy);
  font-family: var(--font-serif);
  font-size: 17px;
}

.filter-heading p {
  margin: 4px 0 0;
  color: var(--ink-faint);
  font-size: 10px;
  line-height: 1.55;
}

.filter-field {
  margin-top: 18px;
}

.filter-field label,
.knowledge-heading {
  color: var(--navy);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.04em;
}

.filter-field label {
  display: block;
  margin-bottom: 7px;
}

.filter-field :deep(.el-select) {
  width: 100%;
}

.knowledge-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin: 18px 0 7px;
}

.knowledge-heading button,
.active-filters button {
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--cinnabar-dark);
  cursor: pointer;
  font-size: 10px;
  font-weight: 700;
}

.tree-region {
  max-height: 360px;
  overflow: auto;
  border: 1px solid var(--line);
  border-radius: 11px;
  background: rgba(255, 253, 248, 0.68);
}

.tree-region :deep(.async-state) {
  min-height: 150px;
}

.tree-region :deep(.el-tree) {
  padding: 8px 5px;
  background: transparent;
  color: var(--ink-soft);
  font-size: 11px;
}

.tree-region :deep(.el-tree-node__content) {
  min-height: 34px;
  border-radius: 7px;
}

.tree-region :deep(.el-tree-node.is-current > .el-tree-node__content) {
  background: var(--jade-pale);
  color: var(--jade-dark);
  font-weight: 800;
}

.tree-hint {
  margin: 0;
  padding: 18px 14px;
  color: var(--ink-faint);
  font-size: 11px;
  line-height: 1.7;
}

.active-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
  align-items: center;
  margin-top: 16px;
  padding-top: 14px;
  border-top: 1px dashed var(--line-strong);
}

.active-filters > span {
  width: 100%;
  color: var(--ink-faint);
  font-size: 10px;
}

.active-filters button {
  width: 100%;
  margin-top: 2px;
  text-align: left;
}

.question-results {
  min-width: 0;
}

.result-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 13px;
  padding: 0 2px;
}

.result-bar p {
  margin: 0;
  color: var(--ink-faint);
  font-size: 11px;
}

.result-bar strong {
  color: var(--navy);
  font-size: 13px;
}

.question-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 15px;
}

.question-card {
  min-height: 238px;
}

.question-link {
  position: relative;
  display: flex;
  height: 100%;
  min-height: 238px;
  padding: 21px 21px 18px 26px;
  flex-direction: column;
  color: inherit;
  text-decoration: none;
}

.question-link::before {
  position: absolute;
  top: 18px;
  bottom: 18px;
  left: 0;
  width: 4px;
  border-radius: 0 4px 4px 0;
  background: var(--cinnabar);
  content: '';
  opacity: 0.82;
}

.correction-mark {
  position: absolute;
  z-index: 0;
  right: 16px;
  bottom: 36px;
  color: rgba(183, 67, 50, 0.07);
  font-family: var(--font-display);
  font-size: 88px;
  font-weight: 900;
  line-height: 1;
  transform: rotate(-9deg);
}

.card-tags {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
}

.subject-chip,
.knowledge-chip {
  max-width: 40%;
  overflow: hidden;
  padding: 4px 8px;
  border-radius: 999px;
  font-size: 10px;
  font-weight: 800;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.subject-chip {
  background: rgba(24, 52, 74, 0.08);
  color: var(--navy);
}

.knowledge-chip {
  background: var(--jade-pale);
  color: var(--jade-dark);
}

.difficulty {
  margin-left: auto;
  color: var(--amber);
  font-size: 10px;
  letter-spacing: 0.04em;
  white-space: nowrap;
}

.question-card-stem {
  position: relative;
  z-index: 1;
  display: -webkit-box;
  min-height: 76px;
  margin: 18px 0 14px;
  overflow: hidden;
  color: var(--ink);
  font-family: var(--font-serif);
  font-size: 15px;
  font-weight: 700;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
  line-height: 1.7;
}

.question-meta {
  position: relative;
  z-index: 1;
  display: flex;
  min-width: 0;
  gap: 7px;
  align-items: center;
  margin: auto 0 14px;
  color: var(--ink-faint);
  font-size: 10px;
}

.question-meta > span:not(.image-note) {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.question-meta time {
  flex: 0 0 auto;
  margin-left: auto;
}

.image-note {
  display: inline-flex;
  flex: 0 0 auto;
  gap: 3px;
  align-items: center;
  color: var(--jade-dark);
}

.question-link :deep(.mastery-indicator) {
  position: relative;
  z-index: 1;
}

.pagination-wrap {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-top: 22px;
  padding: 14px 16px;
  border-top: 1px solid var(--line);
}

.pagination-copy {
  color: var(--ink-faint);
  font-size: 11px;
}

@media (max-width: 980px) {
  .catalog-layout {
    grid-template-columns: 1fr;
  }

  .filter-panel {
    position: static;
  }

  .tree-region {
    max-height: 260px;
  }
}

@media (max-width: 700px) {
  .export-alert,
  .pagination-wrap {
    align-items: stretch;
    flex-direction: column;
  }

  .question-grid {
    grid-template-columns: 1fr;
  }

  .question-card,
  .question-link {
    min-height: 220px;
  }

  .pagination-wrap :deep(.el-pagination) {
    justify-content: center;
  }
}
</style>
