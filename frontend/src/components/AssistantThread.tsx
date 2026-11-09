import {
  ThreadPrimitive,
  ComposerPrimitive,
  MessagePrimitive,
} from '@assistant-ui/react'

export function AssistantThread() {
  return (
    <ThreadPrimitive.Root className="aui-thread-root">
      <ThreadPrimitive.Viewport className="aui-thread-viewport">
        <ThreadPrimitive.Empty>
          <div className="aui-empty-state">
            <div className="aui-empty-icon">🛍️</div>
            <h3>How can I assist you today?</h3>
            <p>
              Ask about store return policies, shipping, or search 900+ products
              in our catalog.
            </p>
          </div>
        </ThreadPrimitive.Empty>
        <ThreadPrimitive.Messages
          components={{
            UserMessage: () => (
              <MessagePrimitive.Root className="aui-message-row user">
                <div className="aui-message-bubble user">
                  <MessagePrimitive.Content />
                </div>
              </MessagePrimitive.Root>
            ),
            AssistantMessage: () => (
              <MessagePrimitive.Root className="aui-message-row assistant">
                <div className="aui-avatar">🤖</div>
                <div className="aui-message-bubble assistant">
                  <MessagePrimitive.Content />
                </div>
              </MessagePrimitive.Root>
            ),
          }}
        />
      </ThreadPrimitive.Viewport>
      <ComposerPrimitive.Root className="aui-composer-root">
        <ComposerPrimitive.Input
          placeholder="Ask about store policies, prices, discounts, or products..."
          className="aui-composer-input"
        />
        <ComposerPrimitive.Send className="aui-composer-send">
          Send
        </ComposerPrimitive.Send>
      </ComposerPrimitive.Root>
    </ThreadPrimitive.Root>
  )
}
