import { useState } from 'react'
import {
  AssistantRuntimeProvider,
  AssistantModalPrimitive,
} from '@assistant-ui/react'
import { ShoppingBag, X } from 'lucide-react'
import { useRagChatRuntime } from '../lib/customRuntime'
import { AssistantThread } from './AssistantThread'
import './assistant-ui.css'

export function AssistantModal() {
  const runtime = useRagChatRuntime()
  const [isOpen, setIsOpen] = useState(false)

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <AssistantModalPrimitive.Root open={isOpen} onOpenChange={setIsOpen}>
        <AssistantModalPrimitive.Trigger asChild>
          <button className="aui-floating-trigger" title="Open AI Shopping Assistant">
            <ShoppingBag size={18} className="aui-trigger-icon-lucide" />
            <span className="aui-trigger-text">AI Assistant</span>
          </button>
        </AssistantModalPrimitive.Trigger>
        <AssistantModalPrimitive.Content className="aui-modal-content">
          <div className="aui-modal-header">
            <div className="aui-modal-title">
              <div className="aui-icon-badge">
                <ShoppingBag size={18} />
              </div>
              <div>
                <h4>E-Commerce AI Assistant</h4>
                <p>ChromaDB RAG &bull; Gemini Text-to-SQL</p>
              </div>
            </div>
            <button
              className="aui-close-btn"
              onClick={() => setIsOpen(false)}
              aria-label="Close Assistant"
            >
              <X size={18} />
            </button>
          </div>
          <div className="aui-modal-body">
            <AssistantThread />
          </div>
        </AssistantModalPrimitive.Content>
      </AssistantModalPrimitive.Root>
    </AssistantRuntimeProvider>
  )
}
