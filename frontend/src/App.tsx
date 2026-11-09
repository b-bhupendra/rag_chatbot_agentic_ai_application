import React, { useState, useEffect, useRef } from 'react'
import './App.css'
import type { Message, SuggestionItem, HealthInfo } from './types'
import { sendChatMessage, getSuggestions, getHealth } from './api'
import { ProductCarousel } from './components/ProductCarousel'
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
  Maximize2,
  Minimize2,
  Sparkles,
} from 'lucide-react'

// Markdown & link renderer without emojis
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

// Minimalist Mountain SVG Landscape Background
function MountainBackground() {
  return (
    <div className="mountain-bg-container" aria-hidden="true">
      <svg
        className="mountain-svg"
        viewBox="0 0 1440 900"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        preserveAspectRatio="xMidYMid slice"
      >
        <defs>
          <linearGradient id="skyGrad" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#090d16" />
            <stop offset="45%" stopColor="#111827" />
            <stop offset="80%" stopColor="#1e293b" />
            <stop offset="100%" stopColor="#0f172a" />
          </linearGradient>

          <linearGradient id="mountainBack" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#1e293b" stopOpacity="0.8" />
            <stop offset="100%" stopColor="#0f172a" stopOpacity="0.95" />
          </linearGradient>

          <linearGradient id="mountainMid" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#152136" stopOpacity="0.9" />
            <stop offset="100%" stopColor="#09101d" />
          </linearGradient>

          <linearGradient id="mountainFront" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#0d1829" />
            <stop offset="100%" stopColor="#050912" />
          </linearGradient>

          <radialGradient id="sunGlow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.18" />
            <stop offset="60%" stopColor="#0284c7" stopOpacity="0.05" />
            <stop offset="100%" stopColor="transparent" stopOpacity="0" />
          </radialGradient>
        </defs>

        {/* Night / Twilight Sky */}
        <rect width="1440" height="900" fill="url(#skyGrad)" />

        {/* Ambient Moon / Star Glow */}
        <circle cx="720" cy="280" r="320" fill="url(#sunGlow)" />
        <circle cx="720" cy="280" r="48" fill="#e0f2fe" fillOpacity="0.12" />
        <circle cx="720" cy="280" r="32" fill="#ffffff" fillOpacity="0.25" />

        {/* Distant Stars */}
        <circle cx="180" cy="140" r="1.5" fill="#ffffff" fillOpacity="0.5" />
        <circle cx="340" cy="90" r="1" fill="#ffffff" fillOpacity="0.4" />
        <circle cx="520" cy="180" r="1.5" fill="#ffffff" fillOpacity="0.6" />
        <circle cx="920" cy="120" r="1.2" fill="#ffffff" fillOpacity="0.5" />
        <circle cx="1140" cy="80" r="1" fill="#ffffff" fillOpacity="0.4" />
        <circle cx="1280" cy="160" r="1.5" fill="#ffffff" fillOpacity="0.6" />
        <circle cx="850" cy="220" r="1" fill="#ffffff" fillOpacity="0.3" />

        {/* Distant Back Mountains */}
        <path
          d="M0 580 L180 430 L360 520 L580 360 L780 490 L980 340 L1180 470 L1360 380 L1440 430 L1440 900 L0 900 Z"
          fill="url(#mountainBack)"
        />

        {/* Mid-ground Mountains */}
        <path
          d="M0 660 L140 550 L310 630 L490 480 L680 610 L870 470 L1060 590 L1240 490 L1440 610 L1440 900 L0 900 Z"
          fill="url(#mountainMid)"
        />

        {/* Foreground Mountains & Ridges */}
        <path
          d="M0 740 L160 640 L340 710 L520 590 L710 690 L900 580 L1120 700 L1320 620 L1440 680 L1440 900 L0 900 Z"
          fill="url(#mountainFront)"
        />

        {/* Subtle Valley Mist Line */}
        <line x1="0" y1="710" x2="1440" y2="710" stroke="#38bdf8" strokeOpacity="0.04" strokeWidth="6" />
      </svg>

      <div className="bg-caption">
        <h2>E-Commerce AI Assistant</h2>
        <p>Agentic RAG &bull; ChromaDB Vector FAQ &bull; SQLite Text-to-SQL</p>
      </div>
    </div>
  )
}

export function App() {
  const [isOpen, setIsOpen] = useState(true)
  const [isMaximized, setIsMaximized] = useState(false)
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content:
        'Hello! Welcome to the **E-Commerce AI Assistant**.\nI can answer questions regarding store policies (FAQ) or search through 900+ products in our footwear catalog (Text-to-SQL). How can I assist you today?',
      route: 'system',
    },
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [health, setHealth] = useState<HealthInfo | null>(null)
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
  }, [isOpen, messages, isLoading, isMaximized])

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
        content: 'Chat history cleared. How can I assist you with products or store policies?',
        route: 'system',
      },
    ])
  }

  return (
    <div className="app-container">
      {/* 1. Serene SVG Mountain Background */}
      <MountainBackground />

      {/* 2. Floating Launcher Button with Circling Dot Animation (Shown when minimized) */}
      {!isOpen && (
        <div className="launcher-dock">
          <button
            className="circling-launcher-btn"
            onClick={() => setIsOpen(true)}
            title="Open AI Shopping Assistant"
            aria-label="Open AI Assistant"
          >
            {/* Animated Circling Glow Ring */}
            <span className="radar-ring-outer"></span>
            <span className="radar-ring-inner"></span>

            <div className="launcher-icon">
              <Sparkles size={20} className="sparkle-svg" />
            </div>
            <span className="launcher-label">Ask AI Assistant</span>
            <span className="live-status-dot" title="Assistant Online"></span>
          </button>
        </div>
      )}

      {/* 3. The Dedicated Chat UI (Modal or Full Screen) */}
      {isOpen && (
        <div className={`chat-window-wrapper ${isMaximized ? 'maximized' : 'modal-mode'}`}>
          <div className="chat-window-card">
            {/* Chat Header */}
            <header className="chat-window-header">
              <div className="header-title-box">
                <div className="header-bot-badge">
                  <Bot size={18} />
                </div>
                <div>
                  <h3 className="header-app-title">AI Shopping Assistant</h3>
                  <div className="header-status-line">
                    <span className="status-indicator-green"></span>
                    <span>
                      {health ? `${health.model} • ${health.product_count} products` : 'Online'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Header Action Controls */}
              <div className="header-controls">
                <button
                  className="control-icon-btn"
                  onClick={clearChat}
                  title="Clear conversation"
                  aria-label="Clear chat"
                >
                  <Trash2 size={15} />
                </button>

                {/* Maximize / Restore Button */}
                <button
                  className="control-icon-btn"
                  onClick={() => setIsMaximized(!isMaximized)}
                  title={isMaximized ? 'Restore to compact modal' : 'Maximize to full screen'}
                  aria-label={isMaximized ? 'Restore' : 'Maximize'}
                >
                  {isMaximized ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
                </button>

                {/* Minimize Down to Launcher Button */}
                <button
                  className="control-icon-btn"
                  onClick={() => setIsOpen(false)}
                  title="Minimize chat"
                  aria-label="Minimize"
                >
                  <Minus size={16} />
                </button>

                {/* Close Button */}
                <button
                  className="control-icon-btn close-btn"
                  onClick={() => setIsOpen(false)}
                  title="Close chat"
                  aria-label="Close"
                >
                  <X size={17} />
                </button>
              </div>
            </header>

            {/* Chat Messages Body */}
            <main className="chat-window-messages">
              {messages.map((msg) => (
                <div key={msg.id} className={`chat-msg-row ${msg.role}`}>
                  {msg.role === 'assistant' && (
                    <div className="msg-avatar assistant" title="Assistant">
                      <Bot size={16} />
                    </div>
                  )}

                  <div className="msg-bubble-container">
                    <div className="msg-bubble">
                      {msg.route === 'fallback' && msg.content.startsWith('Error:') ? (
                        <div className="error-wrapper">
                          <AlertCircle size={15} className="text-danger mr-1" />
                          <FormattedContent text={msg.content} />
                        </div>
                      ) : (
                        <FormattedContent text={msg.content} />
                      )}

                      {/* Meta Information Pills */}
                      <div className="msg-meta-bar">
                        {msg.route && msg.route !== 'system' && (
                          <span className={`meta-route-pill ${msg.route}`}>
                            <Navigation size={10} className="mr-1" />
                            <span>{msg.route.toUpperCase()}</span>
                          </span>
                        )}
                        {msg.elapsedSeconds !== undefined && (
                          <span className="meta-time-pill">
                            <Zap size={10} className="mr-1 text-warning" />
                            <span>{msg.elapsedSeconds}s</span>
                          </span>
                        )}
                        {msg.timestamp && <span className="meta-timestamp">{msg.timestamp}</span>}
                      </div>
                    </div>

                    {/* Horizontal Scrollable Product Carousel */}
                    {msg.products && msg.products.length > 0 && (
                      <ProductCarousel products={msg.products} />
                    )}
                  </div>

                  {msg.role === 'user' && (
                    <div className="msg-avatar user" title="You">
                      <User size={16} />
                    </div>
                  )}
                </div>
              ))}

              {isLoading && (
                <div className="chat-msg-row assistant">
                  <div className="msg-avatar assistant">
                    <Bot size={16} />
                  </div>
                  <div className="msg-bubble loading-state">
                    <div className="pulse-dots">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                    <span className="loading-caption">Thinking and retrieving from database...</span>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </main>

            {/* Interactive Suggestion Chips */}
            {suggestions.length > 0 && messages.length <= 2 && (
              <div className="chat-suggestions-dock">
                <span className="dock-label">Try asking:</span>
                <div className="dock-chips-scroll">
                  {suggestions.map((item, idx) => (
                    <button
                      key={idx}
                      className="suggestion-chip-btn"
                      onClick={() => handleSend(item.text)}
                      disabled={isLoading}
                    >
                      <span className="chip-badge">{item.category}</span>
                      <span className="chip-text">{item.text}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Chat Input Footer */}
            <footer className="chat-window-footer">
              <div className="input-field-wrapper">
                <input
                  ref={inputRef}
                  type="text"
                  placeholder="Ask about Nike, Puma, prices, discounts, or store policies..."
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  disabled={isLoading}
                  autoFocus
                />
                <button
                  className="send-msg-btn"
                  onClick={() => handleSend(input)}
                  disabled={!input.trim() || isLoading}
                  title="Send message"
                  aria-label="Send"
                >
                  <Send size={16} />
                </button>
              </div>
            </footer>
          </div>
        </div>
      )}
    </div>
  )
}

export default App
