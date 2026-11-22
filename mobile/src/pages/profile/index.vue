<script setup>
import { onShow } from '@dcloudio/uni-app'
import { profile } from '../../api/student.js'
import { logout } from '../../api/request.js'
import LoadState from '../../components/LoadState.vue'
import { useLoad } from '../../composables/use-load.js'

const { data, loading, error, load } = useLoad(profile)
onShow(load)
</script>

<template>
  <view class="screen">
    <LoadState :loading="loading" :error="error" :empty="!data" empty-text="暂无个人资料" @retry="load">
      <view class="card">
        <text class="heading">{{ data.nickname || data.username }}</text>
        <text class="copy">账号 {{ data.username }}</text>
        <text class="copy">角色 学生</text>
        <text v-if="data.className" class="copy">班级 {{ data.className }}</text>
        <text v-if="data.email" class="copy">邮箱 {{ data.email }}</text>
      </view>
    </LoadState>
    <button class="action" @tap="logout">退出登录</button>
  </view>
</template>
