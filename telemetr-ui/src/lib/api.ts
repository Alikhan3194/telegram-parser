// API helpers for interacting with the backend

const API = "http://127.0.0.1:8000/api"

export const putFilters = async (filters: any) => {
  const response = await fetch(`${API}/filters`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(filters)
  })
  
  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(`Ошибка при сохранении фильтров: ${response.status} ${errorText}`)
  }
  
  return response
}

export const startParse = async () => {
  const response = await fetch(`${API}/start`, {
    method: "POST"
  })
  
  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(`Ошибка при запуске парсера: ${response.status} ${errorText}`)
  }
  
  return response.json()
}

export const stopParse = async () => {
  const response = await fetch(`${API}/stop`, {
    method: "POST"
  })
  
  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(`Ошибка при остановке парсера: ${response.status} ${errorText}`)
  }
  
  return response.json()
}

export const getStatus = async () => {
  const response = await fetch(`${API}/status`)
  
  if (!response.ok) {
    throw new Error(`Ошибка при получении статуса: ${response.status}`)
  }
  
  return response.json()
}

export const download = (kind: "excel" | "json") => {
  window.open(`${API}/download/${kind}`)
}

// Type definitions for API responses
export interface ParseProgress {
  current_page: number | null
  start_page: number | null
  end_page: number | null
  channel_index: number | null
  channels_on_page: number | null
}

export interface ParseStatus {
  running: boolean
  error: string | null
  progress: ParseProgress
} 

export interface LimitItem {
  name: string
  description: string
  current: number
  maximum: number
  severity: string
}

export interface LimitsResponse {
  items: LimitItem[]
}

export const getLimits = async (): Promise<LimitsResponse> => {
  const response = await fetch(`${API}/limits`)
  if (!response.ok) {
    throw new Error(`Ошибка при получении лимитов: ${response.status}`)
  }
  return response.json()
}