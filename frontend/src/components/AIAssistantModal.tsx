import React, { useState, useEffect, useRef } from 'react'
import {
  Bot,
  User,
  Navigation,
  Zap,
  Trash2,
  Send,
  AlertCircle,
  X,
  Minus,
  Sparkles,
} from 'lucide-react'
import type { Message, SuggestionItem } from '../types'
import { sendChatMessage, getSuggestions } from '../api'
import { ProductCarousel } from './ProductCarousel'

// Safe markdown & link renderer without emojis
function FormattedContent({ text }: { text: string }) {
  const formatText = (content: string) => {
    let formatted = content.replace(
      /\[(.*?)\]\((https?:\/\/[^\s]+)\)/g,
      '<a href="$2" target="_blank" rel="noopener noreferrer" class="product-link">$1</a>'
    )
    formatted = formatted.replace(
      /(?<!href=")(https?:\/\/[^\s<]+)/g,
      '<a href="$1" target="_blank" rel="noopener noreferrer" class="product-link">View Product</a>'
    )
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    return formatted.replace(/\n/g, '<br/>')
  }

  return (
    <div
      className="formatted-content"
      dangerouslySetInnerHTML={{ __html: formatText(text) }}
    />
  )
}

interface AIAssistantModalProps {
  isOpen: boolean
  onClose: () => void
  onToggle: () => void
  initialQuery?: string
}

export const AIAssistantModal: React.FC<AIAssistantModalProps> = ({
  isOpen,
  onClose,
  onToggle,
  initialQuery,
}) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content:
        'Hello! I am your **AI Shopping Assistant**.\nI can answer store policy questions (FAQ) or search our footwear catalog (Text-to-SQL). How can I assist you today?',
      route: 'system',
    },
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [suggestions, setSuggestions] = useState<SuggestionItem[]>([])
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    if (isOpen) {
      scrollToBottom()
      setTimeout(() => inputRef.current?.focus(), 150)
    }
  }, [isOpen, messages, isLoading])

  useEffect(() => {
    getSuggestions()
      .then((items) => setSuggestions(items))
      .catch((err) => console.error('Suggestions error:', err))
  }, [])

  // Handle triggered query from outer storefront
  useEffect(() => {
    if (initialQuery && initialQuery.trim()) {
      handleSend(initialQuery)
    }
  }, [initialQuery])

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
        content: 'Chat history cleared. How can I assist you with products or store policies?',
        route: 'system',
      },
    ])
  }

  return (
    <>
      {/* Floating Launcher Button with Circling Animation */}
      <div className="ai-launcher-wrapper">
        <button
          className={`ai-launcher-btn ${isOpen ? 'active' : ''}`}
          onClick={onToggle}
          title={isOpen ? 'Close AI Assistant' : 'Chat with AI Shopping Assistant'}
          aria-label="Toggle AI Shopping Assistant"
        >
          {/* Animated Circling Glow Ring */}
          <span className="circling-ring-outer"></span>
          <span className="circling-ring-inner"></span>

          <div className="launcher-icon-box">
            {isOpen ? <X size={20} /> : <Sparkles size={20} className="sparkle-icon" />}
          </div>
          <span className="launcher-text">
            {isOpen ? 'Close' : 'Ask AI'}
          </span>
          <span className="online-indicator-dot" title="Assistant Online"></span>
        </button>
      </div>

      {/* Floating Small Modal Window */}
      {isOpen && (
        <div className="ai-modal-container">
          <div className="ai-modal-window">
            {/* Modal Header */}
            <header className="ai-modal-header">
              <div className="modal-title-group">
                <div className="modal-avatar-badge">
                  <Bot size={18} />
                </div>
                <div>
                  <h3 className="modal-title">AI Shopping Assistant</h3>
                  <div className="modal-status-line">
                    <span className="status-dot-green"></span>
                    <span>Online &bull; ChromaDB + SQLite Text-to-SQL</span>
                  </div>
                </div>
              </div>
              <div className="modal-actions-group">
                <button
                  className="modal-icon-btn"
                  onClick={clearChat}
                  title="Clear conversation"
                  aria-label="Clear chat"
                >
                  <Trash2 size={15} />
                </button>
                <button
                  className="modal-icon-btn"
                  onClick={onClose}
                  title="Minimize"
                  aria-label="Minimize"
                >
                  <Minus size={16} />
                </button>
                <button
                  className="modal-icon-btn close-btn"
                  onClick={onClose}
                  title="Close Assistant"
                  aria-label="Close"
                >
                  <X size={17} />
                </button>
              </div>
            </header>

            {/* Modal Message Area */}
            <main className="ai-modal-body">
              {messages.map((msg) => (
                <div key={msg.id} className={`modal-message-row ${msg.role}`}>
                  {msg.role === 'assistant' && (
                    <div className="modal-avatar assistant">
                      <Bot size={15} />
                    </div>
                  )}
                  <div className="modal-message-wrapper">
                    <div className="modal-bubble">
                      {msg.route === 'fallback' && msg.content.startsWith('Error:') ? (
                        <div className="error-content">
                          <AlertCircle size={15} className="text-danger mr-1" />
                          <FormattedContent text={msg.content} />
                        </div>
                      ) : (
                        <FormattedContent text={msg.content} />
                      )}

                      {/* Meta Pills */}
                      <div className="modal-meta-row">
                        {msg.route && msg.route !== 'system' && (
                          <span className={`route-pill ${msg.route}`}>
                            <Navigation size={10} className="mr-1" />
                            <span>{msg.route.toUpperCase()}</span>
                          </span>
                        )}
                        {msg.elapsedSeconds !== undefined && (
                          <span className="timing-pill">
                            <Zap size={10} className="mr-1 text-warning" />
                            <span>{msg.elapsedSeconds}s</span>
                          </span>
                        )}
                        {msg.timestamp && <span className="time-stamp">{msg.timestamp}</span>}
                      </div>
                    </div>

                    {/* Scrollable Product Card Carousel */}
                    {msg.products && msg.products.length > 0 && (
                      <ProductCarousel products={msg.products} />
                    )}
                  </div>
                  {msg.role === 'user' && (
                    <div className="modal-avatar user">
                      <User size={15} />
                    </div>
                  )}
                </div>
              ))}

              {isLoading && (
                <div className="modal-message-row assistant">
                  <div className="modal-avatar assistant">
                    <Bot size={15} />
                  </div>
                  <div className="modal-bubble loading-bubble">
                    <div className="typing-dots">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                    <span className="loading-caption">Searching catalog and formulating response...</span>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </main>

            {/* Suggestion Chips */}
            {suggestions.length > 0 && messages.length <= 2 && (
              <div className="modal-suggestions">
                <span className="suggestions-prompt">Quick queries:</span>
                <div className="modal-pills-row">
                  {suggestions.map((item, idx) => (
                    <button
                      key={idx}
                      className="modal-suggestion-chip"
                      onClick={() => handleSend(item.text)}
                      disabled={isLoading}
                    >
                      <span className="chip-cat">{item.category}</span>
                      <span className="chip-label">{item.text}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Modal Footer Input */}
            <footer className="ai-modal-footer">
              <div className="modal-input-box">
                <input
                  ref={inputRef}
                  type="text"
                  placeholder="Ask about Nike, Puma, ratings, prices, or store policies..."
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  disabled={isLoading}
                />
                <button
                  className="modal-send-btn"
                  onClick={() => handleSend(input)}
                  disabled={!input.trim() || isLoading}
                  aria-label="Send query"
                >
                  <Send size={16} />
                </button>
              </div>
            </footer>
          </div>
        </div>
      )}
    </>
  )
}
