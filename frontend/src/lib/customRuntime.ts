import type { ChatModelAdapter } from '@assistant-ui/react'
import { useLocalRuntime } from '@assistant-ui/react'

export const ragChatAdapter: ChatModelAdapter = {
  async run({ messages }) {
    const lastUserMessage = [...messages].reverse().find((m) => m.role === 'user')

    let queryText = ''
    if (typeof lastUserMessage?.content === 'string') {
      queryText = lastUserMessage.content
    } else if (Array.isArray(lastUserMessage?.content)) {
      queryText = lastUserMessage.content
        .filter((p): p is { type: 'text'; text: string } => p.type === 'text')
        .map((p) => p.text)
        .join(' ')
    }

    if (!queryText.trim()) {
      return {
        content: [{ type: 'text', text: 'Please enter a valid question or product query.' }],
      }
    }

    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: queryText }),
    })

    if (!response.ok) {
      const err = await response.json().catch(() => ({}))
      throw new Error(err.detail || `Server error: ${response.status}`)
    }

    const data = await response.json()
    return {
      content: [
        {
          type: 'text',
          text: data.response,
        },
      ],
      metadata: {
        custom: {
          route: data.route,
          elapsed_seconds: data.elapsed_seconds,
        },
      },
    }
  },
}

export function useRagChatRuntime() {
  return useLocalRuntime(ragChatAdapter)
}
