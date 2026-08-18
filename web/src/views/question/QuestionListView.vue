<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Download, Plus } from '@element-plus/icons-vue'
import { kpApi, questionApi, subjectApi, type KpNode, type PageData, type Question, type Subject } from '@/api'

const router = useRouter()
const subjects = ref<Subject[]>([])
const kpTree = ref<KpNode[]>([]) // 筛选面板展示树（随科目切换）
const allKpTree = ref<KpNode[]>([]) // 全量树（名称映射用）
const page = ref<PageData<Question>>({ records: [], total: 0, current: 1, size: 10 })
const loading = ref(false)
const filterSubjectId = ref<number>()
const filterKpId = ref<number>()
const pageNum = ref(1)
const pageSize = 9

const treeProps = { label: 'name', children: 'children' }

async function loadSubjects() {
  subjects.value = await subjectApi.list()
}

async function loadFilterTree() {
  kpTree.value = filterSubjectId.value ? await kpApi.tree(filterSubjectId.value) : []
}

async function loadPage() {
  loading.value = true
  try {
    page.value = await questionApi.page({
      pageNum: pageNum.value,
      pageSize,
      subjectId: filterSubjectId.value,
      knowledgePointId: filterKpId.value,
    })
  } finally {
    loading.value = false
  }
}

function onSubjectChange() {
  filterKpId.value = undefined
  pageNum.value = 1
  loadFilterTree()
  loadPage()
}

function onNodeClick(node: KpNode) {
  filterKpId.value = node.id
  pageNum.value = 1
  loadPage()
}

function clearFilter() {
  filterSubjectId.value = undefined
  filterKpId.value = undefined
  pageNum.value = 1
  loadFilterTree()
  loadPage()
}

function subjectName(id: number) {
  return subjects.value.find((s) => s.id === id)?.name || '-'
}

function kpName(id?: number) {
  if (!id) return '未归类'
  for (const root of allKpTree.value) {
    if (root.id === id) return root.name
    for (const c of root.children) if (c.id === id) return c.name
  }
  return '未归类'
}

function masteryColor(m: number) {
  if (m < 40) return '#dc2626'
  if (m < 70) return '#d97706'
  return '#16a34a'
}

function difficultyText(d?: number) {
  return d ? '★'.repeat(d) : '待评估'
}

function doExport() {
  window.open(questionApi.exportUrl(filterSubjectId.value, filterKpId.value), '_blank')
}

onMounted(async () => {
  allKpTree.value = await kpApi.tree()
  await loadSubjects()
  await loadPage()
})
</script>

<template>
  <div>
    <div class="head-row">
      <div>
        <h2 class="page-title">错题本</h2>
        <p class="page-subtitle">按科目与知识点筛选，掌握度随练习动态更新。</p>
      </div>
      <div>
        <el-button :icon="Download" @click="doExport">导出错题本</el-button>
        <el-button type="primary" :icon="Plus" @click="router.push('/question/create')">录入错题</el-button>
      </div>
    </div>
    <div class="list-layout">
      <div class="paper-card filter-panel">
        <div class="filter-title">科目筛选</div>
        <el-select v-model="filterSubjectId" placeholder="全部科目" clearable style="width: 100%" @change="onSubjectChange">
          <el-option v-for="s in subjects" :key="s.id" :label="s.name" :value="s.id" />
        </el-select>
        <div class="filter-title" style="margin-top: 16px">
          知识点
          <el-link v-if="filterKpId" type="primary" :underline="false" style="font-size: 12px" @click="clearFilter">
            清除
          </el-link>
        </div>
        <el-tree
          v-if="filterSubjectId"
          :data="kpTree"
          :props="treeProps"
          node-key="id"
          highlight-current
          :default-expanded-keys="kpTree.map((n) => n.id)"
          @node-click="onNodeClick"
        />
        <div v-else class="tree-tip">选择科目后展示对应知识点树</div>
      </div>
      <div class="list-panel" v-loading="loading">
        <el-empty v-if="page.records.length === 0" description="暂无错题，点击右上角录入第一道题" />
        <div class="card-grid">
          <div
            v-for="q in page.records"
            :key="q.id"
            class="paper-card hoverable q-card"
            @click="router.push(`/question/${q.id}`)"
          >
            <div class="q-tags">
              <el-tag size="small">{{ subjectName(q.subjectId) }}</el-tag>
              <el-tag size="small" type="success" effect="plain">{{ kpName(q.knowledgePointId) }}</el-tag>
              <span class="q-difficulty num">{{ difficultyText(q.difficulty) }}</span>
            </div>
            <div class="q-stem">{{ q.stem }}</div>
            <div class="q-foot">
              <span class="q-source">{{ q.source || '未标注来源' }}</span>
              <div class="q-mastery">
                <el-progress
                  :percentage="q.mastery"
                  :stroke-width="6"
                  :color="masteryColor(q.mastery)"
                  style="width: 90px"
                />
                <span class="num mastery-text" :style="{ color: masteryColor(q.mastery) }">{{ q.mastery }}</span>
              </div>
            </div>
          </div>
        </div>
        <el-pagination
          v-if="page.total > pageSize"
          v-model:current-page="pageNum"
          :total="page.total"
          :page-size="pageSize"
          layout="prev, pager, next, total"
          class="pager"
          @current-change="loadPage"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.head-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.list-layout {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}

.filter-panel {
  width: 220px;
  flex-shrink: 0;
}

.filter-title {
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 8px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.tree-tip {
  font-size: 12px;
  color: var(--wb-ink-secondary);
  padding: 8px 2px;
}

.list-panel {
  flex: 1;
  min-height: 400px;
}

.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 14px;
}

.q-card {
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.q-tags {
  display: flex;
  align-items: center;
  gap: 6px;
}

.q-difficulty {
  margin-left: auto;
  font-size: 12px;
  color: var(--wb-accent);
}

.q-stem {
  font-size: 13px;
  line-height: 1.6;
  color: var(--wb-ink);
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  min-height: 62px;
}

.q-foot {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.q-source {
  font-size: 12px;
  color: var(--wb-ink-secondary);
}

.q-mastery {
  display: flex;
  align-items: center;
  gap: 6px;
}

.mastery-text {
  font-size: 12px;
  font-weight: 600;
}

.pager {
  margin-top: 18px;
  justify-content: center;
}
</style>
