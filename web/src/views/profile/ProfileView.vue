<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Check, SwitchButton } from '@element-plus/icons-vue'
import { userApi } from '@/api'
import AsyncState from '@/components/AsyncState.vue'
import PageHeader from '@/components/PageHeader.vue'
import PaperPanel from '@/components/PaperPanel.vue'
import { useUserStore } from '@/store/user'

const router = useRouter()
const store = useUserStore()
const formRef = ref<FormInstance>()
const loading = ref(true)
const saving = ref(false)
const error = ref('')
const saveError = ref('')
const form = reactive({ nickname: '', email: '', className: '' })
const roleText: Record<string, string> = { student: '学生', teacher: '教师', admin: '管理员' }

const rules: FormRules = {
  nickname: [{ max: 32, message: '昵称最多 32 个字符', trigger: 'blur' }],
  email: [{ type: 'email', message: '请输入有效的邮箱地址', trigger: ['blur', 'change'] }],
  className: [{ max: 64, message: '班级名称最多 64 个字符', trigger: 'blur' }],
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const profile = await userApi.profile()
    store.setUser(profile)
    form.nickname = profile.nickname || ''
    form.email = profile.email || ''
    form.className = profile.className || ''
  } catch (cause) {
    error.value = cause instanceof Error ? cause.message : '个人资料暂时无法加载。'
  } finally {
    loading.value = false
  }
}

async function save() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  saveError.value = ''
  try {
    await userApi.updateProfile({
      nickname: form.nickname.trim() || undefined,
      email: form.email.trim() || undefined,
      className: form.className.trim() || undefined,
    })
    const profile = await userApi.profile()
    store.setUser(profile)
    ElMessage.success('个人资料已更新')
  } catch (cause) {
    saveError.value = cause instanceof Error ? cause.message : '个人资料保存失败。'
  } finally {
    saving.value = false
  }
}

async function logout() {
  try {
    await ElMessageBox.confirm('确定退出当前账号吗？', '退出登录', { confirmButtonText: '退出', cancelButtonText: '取消', type: 'warning' })
  } catch {
    return
  }
  store.logout()
  await router.replace('/login')
}

onMounted(load)
</script>

<template>
  <div class="profile-page">
    <PageHeader eyebrow="账号与学习档案" title="个人中心" description="资料修改只作用于当前账号；角色由系统确定，前端不提供角色变更。">
      <template #actions><el-button type="danger" plain :icon="SwitchButton" @click="logout">退出登录</el-button></template>
    </PageHeader>

    <AsyncState v-if="loading" status="loading" title="正在读取个人资料" />
    <AsyncState v-else-if="error" status="error" title="个人资料加载失败" :description="error" @retry="load" />
    <section v-else class="profile-layout">
      <PaperPanel variant="lined" class="identity-card">
        <div class="profile-avatar" aria-hidden="true">{{ (store.nickname || '?').slice(0, 1) }}</div>
        <p>当前账号</p>
        <h2>{{ store.nickname }}</h2>
        <span>@{{ store.user?.username }}</span>
        <dl><div><dt>角色</dt><dd>{{ roleText[store.role] || store.role }}</dd></div><div><dt>用户编号</dt><dd>#{{ store.user?.id }}</dd></div></dl>
        <p class="identity-note">角色控制只用于界面展示；服务端权限仍是最终边界。</p>
      </PaperPanel>

      <PaperPanel>
        <h2 class="form-title">编辑公开资料</h2>
        <p class="form-description">昵称会显示在工作台；邮箱和班级均为选填信息。</p>
        <el-form ref="formRef" :model="form" :rules="rules" label-position="top" class="profile-form" @submit.prevent="save">
          <el-form-item label="昵称" prop="nickname"><el-input v-model="form.nickname" maxlength="32" show-word-limit autocomplete="nickname" /></el-form-item>
          <el-form-item label="邮箱" prop="email"><el-input v-model="form.email" maxlength="64" placeholder="选填" autocomplete="email" /></el-form-item>
          <el-form-item label="班级" prop="className"><el-input v-model="form.className" maxlength="64" placeholder="选填，如：2023级软件工程1班" /></el-form-item>
          <p class="save-error" aria-live="polite">{{ saveError }}</p>
          <el-button type="primary" :icon="Check" :loading="saving" @click="save">保存修改</el-button>
        </el-form>
      </PaperPanel>
    </section>
  </div>
</template>

<style scoped>
.profile-page{display:grid;gap:20px}.profile-layout{display:grid;grid-template-columns:minmax(260px,.65fr) minmax(0,1.4fr);gap:20px;align-items:start}.identity-card{display:flex;flex-direction:column;align-items:center;text-align:center}.profile-avatar{display:grid;place-items:center;width:82px;height:82px;margin:7px 0 17px;border-radius:26px 26px 26px 8px;background:var(--navy);color:#fff;font:800 33px var(--font-display);box-shadow:8px 8px 0 var(--paper-deep)}.identity-card>p{margin:0;color:var(--ink-faint);font-size:10px;letter-spacing:.12em}.identity-card h2{margin:7px 0 3px;color:var(--navy);font:800 25px var(--font-display)}.identity-card>span{color:var(--ink-faint);font:10px var(--font-mono)}.identity-card dl{width:100%;margin:25px 0 0}.identity-card dl>div{display:flex;justify-content:space-between;padding:11px 0;border-bottom:1px dashed var(--line);font-size:11px}.identity-card dt{color:var(--ink-faint)}.identity-card dd{margin:0;color:var(--navy);font-weight:800}.identity-note{margin-top:22px!important;padding:11px;border-left:3px solid var(--amber);background:var(--amber-pale);color:#73501c!important;line-height:1.7;text-align:left}.form-title{margin:0;color:var(--navy);font:800 21px var(--font-display)}.form-description{margin:7px 0 24px;color:var(--ink-soft);font-size:11px}.profile-form{max-width:580px}.save-error{min-height:19px;margin:0 0 8px;color:var(--cinnabar);font-size:11px}
@media(max-width:800px){.profile-layout{grid-template-columns:1fr}.identity-card{display:grid;grid-template-columns:90px 1fr;text-align:left}.profile-avatar{grid-row:1/5}.identity-card dl,.identity-note{grid-column:1/-1}.identity-card>p,.identity-card h2,.identity-card>span{grid-column:2}.identity-card h2{margin-block:0}}
@media(max-width:500px){.identity-card{display:flex;text-align:center}}
</style>
