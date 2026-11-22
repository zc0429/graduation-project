<script setup>
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { login } from '../../api/student.js'
import { errorMessage, storedToken } from '../../api/request.js'

const username = ref('')
const password = ref('')
const saving = ref(false)
const error = ref('')

function openHome() {
  uni.switchTab({ url: '/pages/home/index' })
}

onShow(() => {
  if (storedToken()) openHome()
})

async function submit(event) {
  if (saving.value) return
  username.value = event.detail.value.username
  password.value = event.detail.value.password
  if (!username.value.trim() || !password.value) {
    error.value = '请输入账号和密码'
    return
  }

  saving.value = true
  error.value = ''
  try {
    await login(username.value.trim(), password.value)
    password.value = ''
    openHome()
  } catch (cause) {
    error.value = errorMessage(cause)
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <view class="screen login">
    <view class="card">
      <text class="title">AI 错题本</text>
      <form @submit="submit">
        <text class="label">账号</text>
        <input class="field" name="username" :value="username" placeholder="输入学生账号" maxlength="50" />
        <text class="label">密码</text>
        <input class="field" name="password" :value="password" password placeholder="输入密码" maxlength="72" />
        <text v-if="error" class="copy error">{{ error }}</text>
        <button class="action primary" form-type="submit" :loading="saving" :disabled="saving">
          {{ error ? '重新登录' : '登录' }}
        </button>
      </form>
    </view>
  </view>
</template>

<style scoped>
.login { padding-top: 110rpx; }
</style>
