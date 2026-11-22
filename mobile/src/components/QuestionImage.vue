<script setup>
import { onBeforeUnmount, ref, watch } from 'vue'
import { errorMessage } from '../api/request.js'
import { previewFile, removePreview } from '../utils/images.js'

const props = defineProps({ imageUrl: String })
const path = ref('')
const error = ref('')
let version = 0

async function load() {
  const current = ++version
  removePreview(path.value)
  path.value = ''
  error.value = ''
  if (!props.imageUrl) return
  try {
    const filePath = await previewFile(props.imageUrl)
    if (current !== version) {
      removePreview(filePath)
      return
    }
    path.value = filePath
    if (!filePath) error.value = '题图不可用'
  } catch (cause) {
    if (current === version) error.value = errorMessage(cause)
  }
}

watch(() => props.imageUrl, load, { immediate: true })
onBeforeUnmount(() => {
  version += 1
  removePreview(path.value)
})

function showPreview() {
  uni.previewImage({ urls: [path.value] })
}
</script>

<template>
  <image
    v-if="path && !error"
    class="preview"
    :src="path"
    mode="widthFix"
    @tap="showPreview"
    @error="error = '题图显示失败'"
  />
  <view v-else-if="error">
    <text class="error">{{ error }}</text>
    <button class="action" @tap="load">重试题图</button>
  </view>
</template>
