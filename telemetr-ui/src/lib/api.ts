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
export interface ParseStatus {
  running: boolean
  error: string | null
} 