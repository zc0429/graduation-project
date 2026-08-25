<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Check, Clock, Right, Timer } from '@element-plus/icons-vue'
import { reviewPlanApi, subjectApi, type ReviewPlanItem, type Subject } from '@/api'
import AsyncState from '@/components/AsyncState.vue'
import MasteryIndicator from '@/components/MasteryIndicator.vue'
import PageHeader from '@/components/PageHeader.vue'
import PaperPanel from '@/components/PaperPanel.vue'

const router = useRouter()
const plans = ref<ReviewPlanItem[]>([])
const subjects = ref<Subject[]>([])
const loading = ref(true)
const error = ref('')
const finishingId = ref<number>()
const filter = ref<'all' | 'overdue' | 'today'>('all')

const todayText = computed(() => new Date().toLocaleDateString('sv-SE'))
const overduePlans = computed(() => plans.value.filter(isOverdue))
const todayPlans = computed(() => plans.value.filter((plan) => !isOverdue(plan)))
const visiblePlans = computed(() => {
  if (filter.value === 'overdue') return overduePlans.value
  if (filter.value === 'today') return todayPlans.value
  return plans.value
})

function isOverdue(plan: ReviewPlanItem) {
  return plan.status === 2 || plan.planDate < todayText.value
}

function subjectName(id?: number) {
  return subjects.value.find((subject) => subject.id === id)?.name || '未标注科目'
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [planData, subjectData] = await Promise.all([reviewPlanApi.today(), subjectApi.list()])
    plans.value = planData
    subjects.value = subjectData
  } catch (cause) {
    error.value = cause instanceof Error ? cause.message : '复习任务暂时无法加载。'
  } finally {
    loading.value = false
  }
}

async function finish(plan: ReviewPlanItem) {
  try {
    await ElMessageBox.confirm(
      '“完成复习”只更新计划状态，不会自动判断作答对错。建议先进入错题重做并提交自评。确认标记为完成吗？',
      `完成第 ${plan.reviewStage} 轮复习`,
      { confirmButtonText: '确认完成', cancelButtonText: '取消', type: 'warning' },
    )
  } catch {
    return
  }
  finishingId.value = plan.id
  try {
    await reviewPlanApi.finish(plan.id)
    ElMessage.success(`第 ${plan.reviewStage} 轮复习已完成`)
    await load()
  } finally {
    finishingId.value = undefined
  }
}

onMounted(load)
</script>

<template>
  <div class="review-page">
    <PageHeader eyebrow="到期与逾期" title="复习计划工作台" description="当前接口只返回今天到期及已经逾期且尚未完成的任务，因此这里不会展示不可查询的未来日历。">
      <template #actions><el-button :icon="Timer" @click="router.push('/practice/history')">练习历史</el-button></template>
    </PageHeader>

    <PaperPanel variant="annotation" class="review-banner">
      <span class="today-seal">今日</span>
      <div><strong>先完成 {{ overduePlans.length }} 道逾期题，再处理 {{ todayPlans.length }} 道今日任务。</strong><p>完成复习只改变任务状态；掌握度需要在错题详情中重做并提交自评后更新。</p></div>
      <div class="filter-chips" role="group" aria-label="复习任务筛选">
        <button v-for="item in [{ key: 'all', label: `全部 ${plans.length}` }, { key: 'overdue', label: `已逾期 ${overduePlans.length}` }, { key: 'today', label: `今日 ${todayPlans.length}` }]" :key="item.key" type="button" :aria-pressed="filter === item.key" :class="{ active: filter === item.key }" @click="filter = item.key as typeof filter">{{ item.label }}</button>
      </div>
    </PaperPanel>

    <section class="review-layout">
      <PaperPanel class="timeline-panel">
        <div class="panel-heading"><h2><el-icon><Clock /></el-icon>复习清单</h2><span>建议按顺序处理</span></div>
        <AsyncState v-if="loading" status="loading" compact title="正在整理复习任务" />
        <AsyncState v-else-if="error" status="error" compact title="复习任务加载失败" :description="error" @retry="load" />
        <AsyncState v-else-if="visiblePlans.length === 0" status="empty" compact :title="plans.length ? '当前筛选下没有任务' : '今天没有到期或逾期任务'" description="新录入错题后，系统会按第 1、2、4、7、15 天生成复习计划。" />
        <div v-else class="timeline">
          <article v-for="plan in visiblePlans" :key="plan.id" class="review-item" :class="{ overdue: isOverdue(plan) }">
            <span class="timeline-dot" aria-hidden="true" />
            <div class="review-copy">
              <div class="review-tags"><span :class="isOverdue(plan) ? 'red' : 'jade'">{{ isOverdue(plan) ? '已逾期' : '今天' }}</span><span>第 {{ plan.reviewStage }} / 5 轮</span><span>{{ subjectName(plan.subjectId) }}</span></div>
              <h3>{{ plan.stemSummary || `错题 #${plan.questionId}` }}</h3>
              <MasteryIndicator :value="plan.mastery || 0" compact />
            </div>
            <div class="review-actions"><el-button :icon="Right" @click="router.push(`/question/${plan.questionId}`)">去重做</el-button><el-button type="primary" :icon="Check" :loading="finishingId === plan.id" @click="finish(plan)">完成复习</el-button></div>
          </article>
        </div>
      </PaperPanel>

      <aside class="review-side">
        <PaperPanel>
          <h2>五轮复习间隔</h2>
          <strong class="stage-number">1 · 2 · 4 · 7 · 15 <small>天</small></strong>
          <div class="stage-track" aria-label="复习间隔为第1、2、4、7、15天"><i v-for="day in [1,2,4,7,15]" :key="day"><span>+{{ day }}</span></i></div>
          <p>这是系统建立复习节点时使用的固定间隔，不代表个人完成进度。当前接口只返回到期和逾期任务。</p>
        </PaperPanel>
        <PaperPanel variant="annotation"><strong>不要只点“完成”</strong><p>先重做、再自评，掌握度才会更新；计划完成状态和练习结果是两个独立的后端接口。</p></PaperPanel>
      </aside>
    </section>
  </div>
</template>

<style scoped>
.today-seal{color:#70480f!important}
.review-page{display:grid;gap:20px}.review-banner{display:grid;grid-template-columns:auto 1fr auto;align-items:center;gap:18px}.today-seal{display:grid;place-items:center;width:58px;height:58px;border:2px solid var(--amber);border-radius:50%;color:#8b5d18;font:800 15px var(--font-display);transform:rotate(-4deg)}.review-banner strong{color:#795017;font:800 16px var(--font-display)}.review-banner p{margin:6px 0 0;color:#765c33;font-size:10px;line-height:1.6}.filter-chips{display:flex;gap:7px}.filter-chips button{min-height:44px;padding:0 13px;border:1px solid var(--line);border-radius:999px;background:var(--paper-bright);color:var(--ink-soft);cursor:pointer;font-size:10px;font-weight:700}.filter-chips button.active{border-color:var(--cinnabar);background:var(--cinnabar-pale);color:var(--cinnabar-dark)}.review-layout{display:grid;grid-template-columns:minmax(0,1.7fr) minmax(280px,.65fr);gap:20px}.panel-heading{display:flex;align-items:center;justify-content:space-between;padding-bottom:15px;border-bottom:1px dashed var(--line)}.panel-heading h2{display:flex;align-items:center;gap:8px;margin:0;color:var(--navy);font:800 18px var(--font-display)}.panel-heading>span{color:var(--ink-faint);font-size:10px}.timeline{position:relative;margin-top:10px;padding-left:25px}.timeline::before{content:'';position:absolute;left:7px;top:19px;bottom:19px;width:2px;background:linear-gradient(var(--cinnabar),var(--jade))}.review-item{position:relative;display:grid;grid-template-columns:minmax(0,1fr) auto;align-items:center;gap:18px;margin:14px 0;padding:17px;border:1px solid var(--line);border-radius:12px;background:var(--paper-bright)}.timeline-dot{position:absolute;left:-26px;width:16px;height:16px;border:3px solid var(--paper-bright);border-radius:50%;background:var(--jade);box-shadow:0 0 0 1px var(--jade)}.review-item.overdue .timeline-dot{background:var(--cinnabar);box-shadow:0 0 0 1px var(--cinnabar)}.review-tags{display:flex;flex-wrap:wrap;gap:6px}.review-tags span{padding:4px 8px;border:1px solid var(--line);border-radius:999px;color:var(--ink-soft);font-size:9px}.review-tags .red{border-color:var(--cinnabar-light);background:var(--cinnabar-pale);color:var(--cinnabar-dark)}.review-tags .jade{border-color:var(--jade-light);background:var(--jade-pale);color:var(--jade-dark)}.review-copy h3{margin:10px 0 13px;color:var(--navy);font-size:13px}.review-actions{display:flex;gap:7px}.review-side{display:grid;align-content:start;gap:20px}.review-side h2{margin:0 0 15px;color:var(--navy);font:800 18px var(--font-display)}.stage-number{display:block;color:var(--navy);font:800 22px var(--font-mono)}.stage-number small{color:var(--ink-faint);font-size:11px}.stage-track{display:grid;grid-template-columns:repeat(5,1fr);gap:5px;margin:18px 0}.stage-track i{height:7px;border-radius:5px;background:var(--paper-deep);font-style:normal}.stage-track span{display:block;margin-top:10px;color:var(--ink-faint);font:8px var(--font-mono);text-align:center}.review-side p{margin:30px 0 0;color:var(--ink-soft);font-size:11px;line-height:1.8}
@media(max-width:1000px){.review-layout{grid-template-columns:1fr}.review-side{grid-template-columns:1fr 1fr}.review-banner{grid-template-columns:auto 1fr}.filter-chips{grid-column:1/-1}}
@media(max-width:650px){.review-banner{grid-template-columns:1fr;padding:18px!important}.today-seal{width:48px;height:48px}.filter-chips{flex-wrap:wrap}.review-side{grid-template-columns:1fr}.timeline-panel{padding-inline:14px!important}.review-item{grid-template-columns:1fr}.review-actions{justify-content:flex-start;flex-wrap:wrap}.review-actions :deep(.el-button){flex:1 1 120px}.timeline{padding-left:20px}.timeline-dot{left:-21px}}
</style>
