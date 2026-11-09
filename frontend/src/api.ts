import type { ChatResponse, HealthInfo, SuggestionItem, Product } from './types'

export async function sendChatMessage(message: string): Promise<ChatResponse> {
  const response = await fetch('/api/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ message }),
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw new Error(errorData.detail || `Server error: ${response.status}`)
  }

  return response.json()
}

export async function getHealth(): Promise<HealthInfo> {
  const response = await fetch('/api/health')
  if (!response.ok) {
    throw new Error(`Health check failed with status: ${response.status}`)
  }
  return response.json()
}

export async function getSuggestions(): Promise<SuggestionItem[]> {
  const response = await fetch('/api/suggestions')
  if (!response.ok) {
    throw new Error(`Failed to load suggestions: ${response.status}`)
  }
  return response.json()
}

export async function getFeaturedProducts(): Promise<Product[]> {
  const response = await fetch('/api/products/featured')
  if (!response.ok) {
    return []
  }
  return response.json()
}

