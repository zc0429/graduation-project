<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { ArrowRight, Hide, View } from '@element-plus/icons-vue'
import { authApi } from '@/api'
import AppBrand from '@/components/AppBrand.vue'
import { useUserStore } from '@/store/user'

const route = useRoute()
const router = useRouter()
const store = useUserStore()
const mode = ref<'login' | 'register'>('login')
const loading = ref(false)
const formError = ref('')
const formRef = ref<FormInstance>()
const passwordVisible = ref(false)
const form = reactive({ username: '', password: '', confirmPassword: '', nickname: '' })

const statusNotice = computed(() => {
  if (route.query.reason === 'expired') return '登录状态已过期，请重新登录。'
  if (route.query.reason === 'forbidden') return '当前账号无权访问该页面。'
  if (route.query.reason === 'network') return '暂时无法验证已有登录状态，你可以重新登录或稍后重试。'
  return ''
})

const rules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 4, max: 32, message: '用户名长度须为 4–32 位', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 32, message: '密码长度须为 6–32 位', trigger: 'blur' },
  ],
  confirmPassword: [{
    validator: (_rule, value: string, callback) => {
      if (mode.value === 'register' && !value) callback(new Error('请再次输入密码'))
      else if (mode.value === 'register' && value !== form.password) callback(new Error('两次输入的密码不一致'))
      else callback()
    },
    trigger: ['blur', 'change'],
  }],
}

watch(mode, () => {
  formError.value = ''
  form.confirmPassword = ''
  formRef.value?.clearValidate()
})

async function submit() {
  if (loading.value) return
  formError.value = ''
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  loading.value = true
  try {
    if (mode.value === 'register') {
      await authApi.register({ username: form.username.trim(), password: form.password, nickname: form.nickname.trim() || undefined })
      mode.value = 'login'
      form.password = ''
      form.confirmPassword = ''
      ElMessage.success('注册成功，请使用新账号登录')
      return
    }
    const data = await authApi.login({ username: form.username.trim(), password: form.password })
    store.setLogin(data.token, data.user)
    const redirect = typeof route.query.redirect === 'string' && route.query.redirect.startsWith('/') ? route.query.redirect : '/'
    await router.replace(redirect)
  } catch (error) {
    formError.value = error instanceof Error ? error.message : '暂时无法完成请求，请稍后重试。'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <main class="auth-page">
    <section class="auth-story" aria-labelledby="auth-story-title">
      <div class="auth-topline">
        <AppBrand subtitle="AI 错题分析与学习推荐" />
        <span class="system-proof"><i />毕业设计系统</span>
      </div>
      <p class="auth-kicker">数字错题本 · 个性化学习工作台</p>
      <h1 id="auth-story-title">把每一道错题，<br>变成<span>会生长</span>的学习线索。</h1>
      <p class="auth-lead">从错题录入、智能解析到复习反馈，让零散的错误沉淀为清晰、可执行的个人学习路径。</p>
      <ol class="learning-loop" aria-label="学习闭环">
        <li><strong>录入</strong><span>留住问题</span></li>
        <li><strong>解析</strong><span>定位错因</span></li>
        <li><strong>推荐</strong><span>举一反三</span></li>
        <li><strong>复习</strong><span>按时巩固</span></li>
        <li><strong>反馈</strong><span>看见进步</span></li>
      </ol>
      <p class="thesis-title">基于智谱GLM模型的AI错题分析与学习推荐系统设计与实现</p>
    </section>

    <section class="auth-card-wrap" aria-labelledby="auth-form-title">
      <div class="auth-card">
        <header><p>继续你的学习记录</p><h2 id="auth-form-title">{{ mode === 'login' ? '回到学习桌' : '建立学习档案' }}</h2></header>
        <div class="auth-tabs" role="group" aria-label="账号操作">
          <button type="button" :aria-pressed="mode === 'login'" :class="{ active: mode === 'login' }" @click="mode = 'login'">登录</button>
          <button type="button" :aria-pressed="mode === 'register'" :class="{ active: mode === 'register' }" @click="mode = 'register'">注册</button>
        </div>
        <p v-if="statusNotice" class="status-notice" role="status">{{ statusNotice }}</p>
        <el-form ref="formRef" :model="form" :rules="rules" label-position="top" size="large" @submit.prevent="submit">
          <el-form-item label="用户名" prop="username">
            <el-input v-model="form.username" name="username" autocomplete="username" maxlength="32" placeholder="请输入用户名" />
          </el-form-item>
          <el-form-item v-if="mode === 'register'" label="昵称（选填）" prop="nickname">
            <el-input v-model="form.nickname" name="nickname" autocomplete="nickname" maxlength="32" placeholder="用于学习空间中的称呼" />
          </el-form-item>
          <el-form-item label="密码" prop="password">
            <el-input v-model="form.password" name="password" :type="passwordVisible ? 'text' : 'password'" :autocomplete="mode === 'login' ? 'current-password' : 'new-password'" maxlength="32" placeholder="6–32 位">
              <template #suffix><button class="password-toggle" type="button" :aria-label="passwordVisible ? '隐藏密码' : '显示密码'" @click="passwordVisible = !passwordVisible"><el-icon><component :is="passwordVisible ? Hide : View" /></el-icon></button></template>
            </el-input>
          </el-form-item>
          <el-form-item v-if="mode === 'register'" label="确认密码" prop="confirmPassword">
            <el-input v-model="form.confirmPassword" name="confirmPassword" type="password" autocomplete="new-password" maxlength="32" placeholder="请再次输入密码" />
          </el-form-item>
          <p class="form-feedback" :class="{ success: formError.startsWith('注册成功') }" aria-live="polite">{{ formError }}</p>
          <button class="auth-submit" type="submit" :disabled="loading"><span>{{ loading ? '请稍候…' : mode === 'login' ? '进入知错工作台' : '创建学生账号' }}</span><el-icon v-if="!loading"><ArrowRight /></el-icon></button>
        </el-form>
        <p class="privacy-note">正式页面不展示测试账号或密码。登录失败与令牌过期会明确提示；账号停用目前由后端统一返回登录失败。</p>
      </div>
    </section>
  </main>
</template>

<style scoped>
.auth-page{min-height:100vh;display:grid;grid-template-columns:minmax(0,1.35fr) minmax(390px,.8fr);align-items:center;gap:clamp(48px,8vw,130px);padding:clamp(34px,6vw,92px);background:linear-gradient(rgba(24,52,74,.045) 1px,transparent 1px),linear-gradient(90deg,rgba(24,52,74,.045) 1px,transparent 1px),radial-gradient(circle at 15% 15%,rgba(22,129,114,.09),transparent 32%),radial-gradient(circle at 90% 82%,rgba(183,67,50,.08),transparent 29%),var(--paper,#f7f1e7);background-size:32px 32px,32px 32px,auto,auto,auto;overflow:hidden}.auth-story{max-width:790px}.auth-topline{display:flex;align-items:center;justify-content:space-between;margin-bottom:clamp(70px,11vh,132px)}.system-proof{display:inline-flex;align-items:center;gap:7px;padding:6px 11px;border:1px solid rgba(183,67,50,.28);border-radius:999px;background:rgba(255,253,248,.72);color:var(--cinnabar,#b74332);font-size:12px;font-weight:700}.system-proof i{width:7px;height:7px;border-radius:50%;background:currentColor;box-shadow:0 0 0 4px rgba(183,67,50,.09)}.auth-kicker{margin:0 0 17px;color:var(--cinnabar,#b74332);font-size:12px;font-weight:800;letter-spacing:.18em}.auth-story h1{margin:0;color:var(--navy,#18344a);font-family:var(--font-display);font-size:clamp(50px,5vw,76px);font-weight:800;line-height:1.17;letter-spacing:-.04em}.auth-story h1 span{position:relative;color:#963427;white-space:nowrap}.auth-story h1 span::after{content:'';position:absolute;left:-2%;right:-3%;bottom:-3px;height:2px;background:var(--cinnabar,#b74332);transform:rotate(-2deg)}.auth-lead{max-width:650px;margin:26px 0 34px;color:var(--ink-soft,#526270);font-size:16px;line-height:1.95}.learning-loop{display:grid;grid-template-columns:repeat(5,1fr);margin:0;padding:20px 0;list-style:none;border-block:1px solid rgba(24,52,74,.2)}.learning-loop li{position:relative;display:grid;gap:5px;text-align:center;color:var(--ink-soft,#526270);font-size:11px}.learning-loop li:not(:last-child)::after{content:'→';position:absolute;right:-7px;top:7px;color:var(--cinnabar,#b74332)}.learning-loop strong{color:var(--navy,#18344a);font-family:var(--font-display);font-size:15px}.thesis-title{margin:31px 0 0;color:var(--ink-faint,#7d8a94);font-size:11px}.auth-card-wrap{position:relative;width:min(100%,490px);justify-self:end}.auth-card-wrap::before{content:'';position:absolute;inset:22px -18px -18px 22px;border:1px solid rgba(24,52,74,.18);border-radius:20px;background:#e7ddcd;transform:rotate(1deg)}.auth-card{position:relative;padding:45px 48px 40px 66px;border:1px solid rgba(24,52,74,.2);border-radius:20px;background:linear-gradient(90deg,transparent 0 49px,rgba(183,67,50,.17) 49px 51px,transparent 51px),repeating-linear-gradient(#fffdf8 0 35px,#dfe4e3 36px,#fffdf8 37px);box-shadow:0 20px 45px rgba(24,52,74,.12)}.auth-card::before{content:'';position:absolute;left:17px;top:14px;bottom:14px;width:10px;background:repeating-linear-gradient(to bottom,#bcc8cb 0 1px,transparent 1px 28px)}.auth-card header p{margin:0 0 5px;color:var(--ink-soft,#526270);font-size:12px}.auth-card h2{margin:0;color:var(--navy,#18344a);font-family:var(--font-display);font-size:31px}.auth-tabs{display:grid;grid-template-columns:1fr 1fr;margin:25px 0 24px;border-bottom:1px solid rgba(24,52,74,.22)}.auth-tabs button{position:relative;min-height:45px;border:0;background:transparent;color:var(--ink-soft,#526270);font:700 15px var(--font-display);cursor:pointer}.auth-tabs button.active{color:var(--navy,#18344a)}.auth-tabs button.active::after{content:'';position:absolute;left:16%;right:16%;bottom:-1px;height:3px;border-radius:3px;background:var(--cinnabar,#b74332)}.status-notice{margin:-8px 0 15px;padding:9px 11px;border-left:3px solid var(--amber,#b87723);background:#fff0cf;color:#765016;font-size:12px}.password-toggle{display:grid;place-items:center;border:0;background:transparent;color:var(--ink-soft,#526270);cursor:pointer}.form-feedback{min-height:20px;margin:-3px 0 10px;color:var(--cinnabar,#b74332);font-size:12px;line-height:1.5}.form-feedback.success{color:var(--jade,#168172)}.auth-submit{width:100%;min-height:50px;display:flex;align-items:center;justify-content:center;gap:10px;border:0;border-radius:11px;background:var(--navy,#18344a);color:#fff;font:800 15px var(--font-body);cursor:pointer;box-shadow:0 9px 18px rgba(24,52,74,.18)}.auth-submit:disabled{cursor:wait;opacity:.68}.privacy-note{margin:22px 0 0;padding-top:16px;border-top:1px dashed rgba(24,52,74,.22);color:var(--ink-faint,#7d8a94);font-size:10px;line-height:1.7}
@media(max-width:980px){.auth-page{grid-template-columns:1fr;overflow:visible}.auth-story{max-width:720px}.auth-topline{margin-bottom:55px}.auth-card-wrap{width:min(100%,600px);justify-self:start}}
@media(max-width:620px){.auth-page{display:block;padding:22px 17px 48px}.auth-topline{margin-bottom:34px}.system-proof,.thesis-title{display:none}.auth-story h1{font-size:39px}.auth-lead{font-size:14px}.learning-loop{overflow-x:auto;grid-template-columns:repeat(5,minmax(60px,1fr))}.auth-card-wrap{margin-top:35px}.auth-card{padding:34px 22px 31px 42px}.auth-card-wrap::before{right:-4px}}
</style>
