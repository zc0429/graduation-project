<script setup>
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { readKnowledge } from '../../api/student.js'
import LoadState from '../../components/LoadState.vue'
import { useLoad } from '../../composables/use-load.js'

const id = ref(0)
const { data, loading, error, load } = useLoad(() => {
  if (!Number.isSafeInteger(id.value) || id.value < 1) throw new Error('缺少有效的错题编号')
  return readKnowledge(id.value)
})

onLoad((query) => {
  id.value = Number(query.id)
  load()
})
</script>

<template>
  <view class="screen">
    <LoadState
      :loading="loading"
      :error="error"
      :empty="!data?.content"
      loading-text="正在查找知识讲解，首次生成可能需要一些时间…"
      empty-text="这道错题暂无知识讲解"
      @retry="load"
    >
      <view class="card">
        <text class="heading">相关知识讲解</text>
        <text user-select class="copy">{{ data.content }}</text>
      </view>
    </LoadState>
  </view>
</template>
