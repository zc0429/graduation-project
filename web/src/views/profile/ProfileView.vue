<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { userApi } from '@/api'
import { useUserStore } from '@/store/user'

const store = useUserStore()
const saving = ref(false)
const form = reactive({ nickname: '', email: '', className: '' })

const roleText: Record<string, string> = { student: '学生', teacher: '教师', admin: '管理员' }

onMounted(async () => {
  const profile = await userApi.profile()
  store.setUser(profile)
  form.nickname = profile.nickname || ''
  form.email = profile.email || ''
  form.className = profile.className || ''
})

async function save() {
  saving.value = true
  try {
    await userApi.updateProfile({
      nickname: form.nickname || undefined,
      email: form.email || undefined,
      className: form.className || undefined,
    })
    const profile = await userApi.profile()
    store.setUser(profile)
    ElMessage.success('个人信息已更新')
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div>
    <h2 class="page-title">个人中心</h2>
    <p class="page-subtitle">查看与修改个人信息。</p>
    <div class="paper-card profile-card">
      <div class="profile-head">
        <div class="avatar">{{ (store.nickname || '?').slice(0, 1) }}</div>
        <div>
          <div class="p-name">{{ store.nickname }}</div>
          <div class="p-meta">
            {{ store.user?.username }} ·
            <el-tag size="small" effect="plain">{{ roleText[store.role] || store.role }}</el-tag>
          </div>
        </div>
      </div>
      <el-divider />
      <el-form label-width="88px" style="max-width: 460px">
        <el-form-item label="昵称">
          <el-input v-model="form.nickname" maxlength="32" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="form.email" maxlength="64" placeholder="选填" />
        </el-form-item>
        <el-form-item label="班级">
          <el-input v-model="form.className" maxlength="64" placeholder="选填，如：2023级软件工程1班" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="saving" @click="save">保存修改</el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<style scoped>
.profile-card {
  max-width: 640px;
}

.profile-head {
  display: flex;
  align-items: center;
  gap: 14px;
}

.avatar {
  width: 52px;
  height: 52px;
  border-radius: 12px;
  background: var(--el-color-primary-light-8);
  color: var(--wb-primary-dark);
  font-size: 22px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}

.p-name {
  font-size: 17px;
  font-weight: 700;
}

.p-meta {
  font-size: 12px;
  color: var(--wb-ink-secondary);
  margin-top: 4px;
  display: flex;
  align-items: center;
  gap: 6px;
}
</style>
