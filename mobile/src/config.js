const configuredUrl = import.meta.env?.VITE_API_BASE_URL?.trim()

export const apiBaseUrl = (configuredUrl || 'http://127.0.0.1:8080/api').replace(/\/+$/, '')
