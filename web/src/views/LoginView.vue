<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { authApi } from '@/api'
import { useUserStore } from '@/store/user'

const router = useRouter()
const store = useUserStore()
const mode = ref<'login' | 'register'>('login')
const loading = ref(false)
const formRef = ref<FormInstance>()

const form = reactive({
  username: '',
  password: '',
  confirmPassword: '',
  nickname: '',
})

const rules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 4, max: 32, message: '用户名长度须为 4-32 位', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 32, message: '密码长度须为 6-32 位', trigger: 'blur' },
  ],
  confirmPassword: [
    {
      validator: (_r, value: string, cb) => {
        if (mode.value === 'register' && value !== form.password) {
          cb(new Error('两次输入的密码不一致'))
        } else {
          cb()
        }
      },
      trigger: 'blur',
    },
  ],
}

async function submit() {
  await formRef.value?.validate()
  loading.value = true
  try {
    if (mode.value === 'login') {
      const data = await authApi.login({ username: form.username, password: form.password })
      store.setLogin(data.token, data.user)
      ElMessage.success('登录成功')
      router.push('/')
    } else {
      await authApi.register({ username: form.username, password: form.password, nickname: form.nickname || undefined })
      ElMessage.success('注册成功，请登录')
      mode.value = 'login'
      form.password = ''
      form.confirmPassword = ''
    }
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-panel fade-up">
      <div class="login-brand">
        <h1>AI 错题分析与学习推荐系统</h1>
        <p>错题录入 · AI 解析 · 相似题推荐 · 遗忘曲线复习 · 学情报告</p>
      </div>
      <el-card class="login-card" shadow="never">
        <el-tabs v-model="mode" stretch>
          <el-tab-pane label="登录" name="login" />
          <el-tab-pane label="注册" name="register" />
        </el-tabs>
        <el-form ref="formRef" :model="form" :rules="rules" size="large" @keyup.enter="submit">
          <el-form-item prop="username">
            <el-input v-model="form.username" placeholder="用户名" autofocus />
          </el-form-item>
          <el-form-item v-if="mode === 'register'">
            <el-input v-model="form.nickname" placeholder="昵称（选填）" />
          </el-form-item>
          <el-form-item prop="password">
            <el-input v-model="form.password" type="password" placeholder="密码" show-password />
          </el-form-item>
          <el-form-item v-if="mode === 'register'" prop="confirmPassword">
            <el-input v-model="form.confirmPassword" type="password" placeholder="确认密码" show-password />
          </el-form-item>
          <el-button type="primary" class="submit-btn" :loading="loading" @click="submit">
            {{ mode === 'login' ? '登 录' : '注 册' }}
          </el-button>
        </el-form>
        <div class="demo-tip">演示账号：student / 123456（学生）· teacher / 123456（教师）· admin / 123456（管理员）</div>
      </el-card>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background:
    radial-gradient(1200px 500px at 80% -10%, rgba(15, 118, 110, 0.12), transparent),
    radial-gradient(800px 400px at 10% 110%, rgba(217, 119, 6, 0.08), transparent),
    var(--wb-bg);
}

.login-panel {
  width: 420px;
}

.login-brand {
  text-align: center;
  margin-bottom: 24px;
}

.login-brand h1 {
  font-size: 24px;
  color: var(--wb-ink);
  margin: 0 0 8px;
  letter-spacing: 1px;
}

.login-brand p {
  font-size: 13px;
  color: var(--wb-ink-secondary);
  margin: 0;
  letter-spacing: 0.5px;
}

.login-card {
  border-radius: 12px;
  border: 1px solid var(--wb-border);
  box-shadow: 0 12px 32px rgba(15, 118, 110, 0.08);
}

.submit-btn {
  width: 100%;
  letter-spacing: 6px;
  font-weight: 600;
}

.demo-tip {
  margin-top: 14px;
  font-size: 12px;
  color: var(--wb-ink-secondary);
  text-align: center;
}
</style>
