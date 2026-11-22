import { ref, shallowRef } from 'vue'
import { errorMessage, requireSession } from '../api/request.js'

export function useLoad(fetchData) {
  const data = shallowRef(null)
  const loading = ref(true)
  const error = ref('')
  let running = false

  async function load() {
    if (running || !requireSession()) return
    running = true
    loading.value = true
    error.value = ''
    try {
      data.value = await fetchData()
    } catch (cause) {
      error.value = errorMessage(cause)
    } finally {
      loading.value = false
      running = false
    }
  }

  return { data, loading, error, load }
}
