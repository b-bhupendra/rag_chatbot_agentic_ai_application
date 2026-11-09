import React, { useState, useEffect } from 'react'
import './App.css'
import type { Product, HealthInfo } from './types'
import { getHealth, getFeaturedProducts } from './api'
import { AIAssistantModal } from './components/AIAssistantModal'
import {
  ShoppingBag,
  Search,
  Star,
  ExternalLink,
  ShieldCheck,
  RotateCcw,
  Truck,
  Sparkles,
  Bot,
  Tag,
  Package,
  ArrowRight,
} from 'lucide-react'

export function App() {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [modalInitialQuery, setModalInitialQuery] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [featuredProducts, setFeaturedProducts] = useState<Product[]>([])
  const [health, setHealth] = useState<HealthInfo | null>(null)
  const [selectedBrand, setSelectedBrand] = useState('ALL')

  useEffect(() => {
    getHealth()
      .then((data) => setHealth(data))
      .catch((err) => console.error('Health check error:', err))

    getFeaturedProducts()
      .then((products) => setFeaturedProducts(products))
      .catch((err) => console.error('Featured products error:', err))
  }, [])

  const triggerAssistantWithQuery = (query: string) => {
    setModalInitialQuery(query)
    setIsModalOpen(true)
  }

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (searchQuery.trim()) {
      triggerAssistantWithQuery(searchQuery.trim())
      setSearchQuery('')
    }
  }

  const formatDiscount = (discount?: number): string | null => {
    if (discount === undefined || discount === null || discount <= 0) return null
    const pct = discount <= 1.0 ? Math.round(discount * 100) : Math.round(discount)
    return pct > 0 ? `${pct}% OFF` : null
  }

  const formatReviewsCount = (count?: number): string => {
    if (!count) return ''
    if (count >= 1000) return `${(count / 1000).toFixed(1)}k`
    return `${count}`
  }

  const filteredProducts = selectedBrand === 'ALL'
    ? featuredProducts
    : featuredProducts.filter((p) => p.brand?.trim().toUpperCase().includes(selectedBrand))

  return (
    <div className="storefront-app">
      {/* 1. Global Navigation Bar */}
      <header className="store-navbar">
        <div className="navbar-container">
          <div className="navbar-left">
            <div className="store-logo">
              <div className="logo-icon-bg">
                <ShoppingBag size={22} className="logo-icon" />
              </div>
              <div className="logo-text-group">
                <span className="logo-brand">SoleKart</span>
                <span className="logo-sub">AI Store</span>
              </div>
            </div>

            <nav className="nav-links">
              <button
                className={`nav-link-btn ${selectedBrand === 'ALL' ? 'active' : ''}`}
                onClick={() => setSelectedBrand('ALL')}
              >
                All Footwear
              </button>
              <button
                className={`nav-link-btn ${selectedBrand === 'NIKE' ? 'active' : ''}`}
                onClick={() => setSelectedBrand('NIKE')}
              >
                Nike
              </button>
              <button
                className={`nav-link-btn ${selectedBrand === 'PUMA' ? 'active' : ''}`}
                onClick={() => setSelectedBrand('PUMA')}
              >
                Puma
              </button>
              <button
                className={`nav-link-btn ${selectedBrand === 'CAMPUS' ? 'active' : ''}`}
                onClick={() => setSelectedBrand('CAMPUS')}
              >
                Campus
              </button>
              <button
                className={`nav-link-btn ${selectedBrand === 'SPARX' ? 'active' : ''}`}
                onClick={() => setSelectedBrand('SPARX')}
              >
                Sparx
              </button>
            </nav>
          </div>

          <div className="navbar-center">
            <form onSubmit={handleSearchSubmit} className="store-search-form">
              <Search size={18} className="search-icon" />
              <input
                type="text"
                placeholder="Ask AI: 'Puma running shoes under 3000'..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
              <button type="submit" className="search-btn">
                Ask AI
              </button>
            </form>
          </div>

          <div className="navbar-right">
            {health && (
              <div className="system-pill" title={`Chroma: ${health.faq_count} FAQs | SQLite: ${health.product_count} items`}>
                <span className="live-dot"></span>
                <span>{health.product_count} items in Catalog</span>
              </div>
            )}
            <button
              className="open-assistant-nav-btn"
              onClick={() => setIsModalOpen(true)}
              title="Open AI Shopping Assistant"
            >
              <Bot size={16} />
              <span>AI Assistant</span>
            </button>
          </div>
        </div>
      </header>

      {/* 2. Hero Section */}
      <section className="store-hero">
        <div className="hero-content">
          <div className="hero-badge">
            <Sparkles size={14} className="hero-badge-icon" />
            <span>Agentic RAG Footwear Discovery &bull; Gemini 3.5 Flash-Lite</span>
          </div>

          <h1 className="hero-title">
            Find the Best Shoes with <span className="highlight-text">Conversational AI</span>
          </h1>

          <p className="hero-subtitle">
            Skip tedious filters. Ask our intelligent assistant in natural language for top-rated
            running shoes, prices, heavy discounts, and store return policies.
          </p>

          <div className="hero-actions">
            <button
              className="hero-primary-btn"
              onClick={() => triggerAssistantWithQuery('Show me top rated Nike shoes')}
            >
              <span>Explore Top Nike Shoes</span>
              <ArrowRight size={16} />
            </button>
            <button
              className="hero-secondary-btn"
              onClick={() => triggerAssistantWithQuery('What is your return policy?')}
            >
              <span>Store Return Policy</span>
            </button>
          </div>

          {/* Prompt Suggestion Chips */}
          <div className="hero-prompt-chips">
            <span className="chips-title">Popular AI Questions:</span>
            <div className="chips-list">
              <button
                className="prompt-chip"
                onClick={() => triggerAssistantWithQuery('Show me Nike shoes with rating above 4')}
              >
                Nike shoes rating &gt; 4
              </button>
              <button
                className="prompt-chip"
                onClick={() => triggerAssistantWithQuery('Find Puma shoes under 3000')}
              >
                Puma shoes under ₹3000
              </button>
              <button
                className="prompt-chip"
                onClick={() => triggerAssistantWithQuery('Are there any running shoes with 50% discount?')}
              >
                Running shoes 50% off
              </button>
              <button
                className="prompt-chip"
                onClick={() => triggerAssistantWithQuery('Can I pay when the product arrives at my house?')}
              >
                Cash on delivery policy
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* 3. Trust & Benefits Strip */}
      <section className="trust-strip">
        <div className="trust-grid">
          <div className="trust-item">
            <div className="trust-icon-box">
              <Truck size={22} />
            </div>
            <div>
              <h4>Free Fast Delivery</h4>
              <p>On all footwear orders across India</p>
            </div>
          </div>

          <div className="trust-item">
            <div className="trust-icon-box">
              <RotateCcw size={22} />
            </div>
            <div>
              <h4>30-Day Easy Returns</h4>
              <p>Instant refunds & hassle-free pickups</p>
            </div>
          </div>

          <div className="trust-item">
            <div className="trust-icon-box">
              <ShieldCheck size={22} />
            </div>
            <div>
              <h4>100% Genuine Footwear</h4>
              <p>Direct authentic products from top brands</p>
            </div>
          </div>

          <div className="trust-item">
            <div className="trust-icon-box">
              <Bot size={22} />
            </div>
            <div>
              <h4>AI Powered Recommendations</h4>
              <p>Semantic vector search & Text-to-SQL</p>
            </div>
          </div>
        </div>
      </section>

      {/* 4. Featured Catalog Showcase Grid */}
      <main className="catalog-showcase-section">
        <div className="section-header">
          <div>
            <h2 className="section-title">
              Featured Top-Rated Shoes
            </h2>
            <p className="section-subtitle">
              Ranked by high customer ratings and verified review counts from SQLite
            </p>
          </div>
          <button
            className="filter-ai-btn"
            onClick={() => triggerAssistantWithQuery('Show me the best products in the catalog')}
          >
            <Sparkles size={14} className="mr-1" />
            <span>Ask AI to Recommend</span>
          </button>
        </div>

        <div className="catalog-grid">
          {filteredProducts.map((product, idx) => {
            const discountLabel = formatDiscount(product.discount)
            return (
              <div key={idx} className="showcase-card">
                <div className="showcase-card-visual">
                  <div className="showcase-placeholder">
                    <Package size={44} className="placeholder-icon" />
                    <span className="brand-badge-overlay">{product.brand || 'Footwear'}</span>
                  </div>

                  {discountLabel && (
                    <span className="showcase-discount-tag">
                      <Tag size={11} className="mr-1" />
                      {discountLabel}
                    </span>
                  )}
                </div>

                <div className="showcase-card-body">
                  <div className="showcase-meta-row">
                    <span className="showcase-brand">{product.brand}</span>
                    {product.avg_rating && (
                      <div className="showcase-rating">
                        <Star size={13} className="star-icon fill-gold" />
                        <span className="rating-value">{product.avg_rating}</span>
                        {product.total_ratings ? (
                          <span className="reviews-count">({formatReviewsCount(product.total_ratings)})</span>
                        ) : null}
                      </div>
                    )}
                  </div>

                  <h3 className="showcase-title" title={product.title}>
                    {product.title}
                  </h3>

                  <div className="showcase-footer">
                    <div className="showcase-price">
                      <span className="currency-symbol">₹</span>
                      <span className="amount-num">
                        {typeof product.price === 'number'
                          ? product.price.toLocaleString('en-IN')
                          : product.price}
                      </span>
                    </div>

                    <div className="showcase-cta-group">
                      <button
                        className="card-ai-btn"
                        onClick={() => triggerAssistantWithQuery(`Tell me about ${product.brand} ${product.title}`)}
                        title="Ask AI Assistant about this shoe"
                      >
                        <Bot size={14} />
                      </button>

                      {product.product_link && (
                        <a
                          href={product.product_link}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="card-buy-btn"
                          title="View on Flipkart"
                        >
                          <span>Buy</span>
                          <ExternalLink size={13} />
                        </a>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </main>

      {/* 5. Store Footer */}
      <footer className="store-footer">
        <div className="footer-content">
          <div className="footer-brand-col">
            <div className="footer-logo">
              <ShoppingBag size={20} className="text-emerald" />
              <span>SoleKart AI</span>
            </div>
            <p>
              Next-generation e-commerce shopping experience combining ChromaDB vector FAQ retrieval
              and Gemini Text-to-SQL catalog search.
            </p>
          </div>

          <div className="footer-col">
            <h4>Store Policies</h4>
            <ul>
              <li><button onClick={() => triggerAssistantWithQuery('What is your return policy?')}>30-Day Return Policy</button></li>
              <li><button onClick={() => triggerAssistantWithQuery('What payment methods do you accept?')}>Payment Options & COD</button></li>
              <li><button onClick={() => triggerAssistantWithQuery('Can I exchange my footwear size?')}>Size Exchange</button></li>
            </ul>
          </div>

          <div className="footer-col">
            <h4>Popular Searches</h4>
            <ul>
              <li><button onClick={() => triggerAssistantWithQuery('Show me top Nike running shoes')}>Nike Running Shoes</button></li>
              <li><button onClick={() => triggerAssistantWithQuery('Find Puma shoes under 3000')}>Puma Under ₹3000</button></li>
              <li><button onClick={() => triggerAssistantWithQuery('Find Campus walking shoes')}>Campus Walking Shoes</button></li>
            </ul>
          </div>

          <div className="footer-col">
            <h4>System Architecture</h4>
            <p className="architecture-notes">
              Router: <strong>Semantic Router</strong><br />
              FAQ RAG: <strong>ChromaDB + all-MiniLM-L6-v2</strong><br />
              Text-to-SQL: <strong>Gemini 3.5 Flash-Lite (Pydantic)</strong><br />
              Database: <strong>SQLite (900+ Products)</strong>
            </p>
          </div>
        </div>

        <div className="footer-bottom">
          <p>&copy; {new Date().getFullYear()} SoleKart AI. All rights reserved. Zero emojis &bull; 100% SVG Icons.</p>
        </div>
      </footer>

      {/* 6. Professional Floating AI Assistant Modal with Circling Dot Animation */}
      <AIAssistantModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onToggle={() => setIsModalOpen(!isModalOpen)}
        initialQuery={modalInitialQuery}
      />
    </div>
  )
}

export default App
