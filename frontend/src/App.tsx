import React, { useState, useEffect, useRef } from 'react'
import './App.css'
import type { Message, HealthInfo, SuggestionItem } from './types'
import { sendChatMessage, getHealth, getSuggestions } from './api'
import { AssistantModal } from './components/AssistantModal'
import { ProductCarousel } from './components/ProductCarousel'
import {
  ShoppingBag,
  Bot,
  User,
  Navigation,
  Zap,
  Trash2,
  Send,
  AlertCircle,
} from 'lucide-react'

// Safe markdown & link renderer without emojis
function FormattedContent({ text }: { text: string }) {
  const formatText = (content: string) => {
    // Replace markdown links: [text](url)
    let formatted = content.replace(
      /\[(.*?)\]\((https?:\/\/[^\s]+)\)/g,
      '<a href="$2" target="_blank" rel="noopener noreferrer" class="product-link">$1</a>'
    )
    // Replace standalone URLs not inside an <a> tag
    formatted = formatted.replace(
      /(?<!href=")(https?:\/\/[^\s<]+)/g,
      '<a href="$1" target="_blank" rel="noopener noreferrer" class="product-link">View Product</a>'
    )
    // Replace **bold** with <strong>
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    // Line breaks
    return formatted.replace(/\n/g, '<br/>')
  }

  return (
    <div
      className="formatted-content"
      dangerouslySetInnerHTML={{ __html: formatText(text) }}
    />
  )
}

export function App() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content:
        'Welcome to the **E-Commerce AI Assistant**.\nI can answer questions regarding store policies (FAQ) or search through products in our catalog (Text-to-SQL). How can I assist you today?',
      route: 'system',
    },
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [health, setHealth] = useState<HealthInfo | null>(null)
  const [suggestions, setSuggestions] = useState<SuggestionItem[]>([])
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, isLoading])

  useEffect(() => {
    getHealth()
      .then((data) => setHealth(data))
      .catch((err) => console.error('Health check error:', err))

    getSuggestions()
      .then((items) => setSuggestions(items))
      .catch((err) => console.error('Suggestions error:', err))
  }, [])

  const handleSend = async (messageText: string) => {
    const text = messageText.trim()
    if (!text || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      const response = await sendChatMessage(text)
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.response,
        route: response.route,
        elapsedSeconds: response.elapsed_seconds,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        products: response.products,
        sqlQuery: response.sql_query,
      }
      setMessages((prev) => [...prev, assistantMessage])
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `Error: ${error instanceof Error ? error.message : 'Failed to connect to the backend server.'}`,
        route: 'fallback',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend(input)
    }
  }

  const clearChat = () => {
    setMessages([
      {
        id: Date.now().toString(),
        role: 'assistant',
        content: 'Chat cleared. How can I assist you with products or store policies?',
        route: 'system',
      },
    ])
  }

  return (
    <div className="chat-container">
      {/* Header */}
      <header className="chat-header">
        <div className="header-info">
          <div className="logo-badge">
            <ShoppingBag size={22} className="logo-icon" />
          </div>
          <div>
            <h1>E-Commerce AI Assistant</h1>
            <p className="subtitle">
              Agentic RAG &bull; ChromaDB Vector Search &bull; SQLite Text-to-SQL
            </p>
          </div>
        </div>
        <div className="header-actions">
          {health && (
            <div
              className="health-badge"
              title={`Chroma: ${health.faq_count} FAQs | SQLite: ${health.product_count} products`}
            >
              <span className="status-dot"></span>
              <span>{health.model}</span>
              <span className="count-pill">{health.product_count} items</span>
            </div>
          )}
          <button className="clear-btn" onClick={clearChat} title="Clear conversation history">
            <Trash2 size={14} className="mr-1" />
            <span>Clear</span>
          </button>
        </div>
      </header>

      {/* Message List */}
      <main className="messages-area">
        {messages.map((msg) => (
          <div key={msg.id} className={`message-row ${msg.role}`}>
            {msg.role === 'assistant' && (
              <div className="avatar assistant-avatar" title="Assistant">
                <Bot size={17} />
              </div>
            )}
            <div className="message-content-wrapper">
              <div className="message-bubble">
                {msg.route === 'fallback' && msg.content.startsWith('Error:') ? (
                  <div className="error-content">
                    <AlertCircle size={16} className="text-danger mr-1" />
                    <FormattedContent text={msg.content} />
                  </div>
                ) : (
                  <FormattedContent text={msg.content} />
                )}

                {/* Metadata Pills */}
                <div className="message-meta">
                  {msg.route && msg.route !== 'system' && (
                    <span className={`route-pill ${msg.route}`}>
                      <Navigation size={11} className="route-icon" />
                      <span>{msg.route.toUpperCase()}</span>
                    </span>
                  )}
                  {msg.elapsedSeconds !== undefined && (
                    <span className="timing-pill">
                      <Zap size={11} className="timing-icon" />
                      <span>{msg.elapsedSeconds}s</span>
                    </span>
                  )}
                  {msg.timestamp && <span className="time-stamp">{msg.timestamp}</span>}
                </div>
              </div>

              {/* Scrollable Product Cards Carousel */}
              {msg.products && msg.products.length > 0 && (
                <ProductCarousel products={msg.products} />
              )}
            </div>
            {msg.role === 'user' && (
              <div className="avatar user-avatar" title="User">
                <User size={17} />
              </div>
            )}
          </div>
        ))}

        {isLoading && (
          <div className="message-row assistant">
            <div className="avatar assistant-avatar">
              <Bot size={17} />
            </div>
            <div className="message-bubble loading-bubble">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
              <span className="loading-text">Analyzing query and routing intent...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </main>

      {/* Suggestion Pills */}
      {suggestions.length > 0 && messages.length <= 2 && (
        <div className="suggestions-bar">
          <span className="suggestions-label">Try asking:</span>
          <div className="pills-scroll">
            {suggestions.map((item, idx) => (
              <button
                key={idx}
                className="suggestion-pill"
                onClick={() => handleSend(item.text)}
                disabled={isLoading}
              >
                <span className="pill-category">{item.category}</span>
                <span className="pill-text">{item.text}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input Bar */}
      <footer className="chat-footer">
        <div className="input-wrapper">
          <input
            type="text"
            placeholder="Ask about store policies, prices, discounts, or products..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
            autoFocus
          />
          <button
            className="send-button"
            onClick={() => handleSend(input)}
            disabled={!input.trim() || isLoading}
            aria-label="Send message"
          >
            <Send size={18} />
          </button>
        </div>
      </footer>

      {/* Assistant UI Floating Widget Modal */}
      <AssistantModal />
    </div>
  )
}

export default App
