import axios, { type AxiosResponse } from 'axios'
import { ElMessage } from 'element-plus'

/** 与后端统一响应结构对应 */
export interface RestResponse<T = unknown> {
  code: number
  message: string
  data: T
}

const request = axios.create({
  baseURL: '/api',
  timeout: 15000,
})

// 请求拦截：携带 JWT
request.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截：统一解包 {code, message, data}，非 0 抛错并提示
request.interceptors.response.use(
  (response: AxiosResponse<RestResponse>) => {
    const body = response.data
    if (body.code === 0) {
      return body.data as never
    }
    ElMessage.error(body.message || '请求失败')
    return Promise.reject(new Error(body.message))
  },
  (error) => {
    ElMessage.error(error.response?.data?.message || error.message || '网络异常')
    return Promise.reject(error)
  },
)

export default request
